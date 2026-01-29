"""
Financial Fortress - Cache Manager
===================================

This module prevents excessive API calls by caching market data locally.

WHY CACHING IS CRITICAL:
1. Yahoo Finance rate-limits heavy usage (can block your IP!)
2. Historical data doesn't change - fetching AAPL's price from last week
   100 times is wasteful
3. Scanning 500 stocks = 500 API calls. With cache = only new/stale data

HOW IT WORKS:
1. Before fetching, check if we have cached data for this symbol+interval
2. If cache exists AND is fresh (within TTL), return cached data
3. If cache is stale or missing, fetch from API and save to cache

STORAGE FORMAT: Parquet
- Columnar format, extremely fast for DataFrames
- Compressed (~10x smaller than CSV)
- Preserves dtypes (no date parsing issues)

FILE STRUCTURE:
    cache/
    ├── AAPL_1d.parquet
    ├── AAPL_1h.parquet
    ├── MSFT_1d.parquet
    └── ...

CACHE KEY: {symbol}_{interval}.parquet

TTL (Time To Live):
- 1d (daily) data: 4 hours - markets close, data doesn't change often
- 1h (hourly) data: 30 minutes
- 5m data: 5 minutes - need fresh data for short-term trading
"""

import logging
from datetime import datetime, timedelta
from pathlib import Path

import pandas as pd

from config.settings import get_config


logger = logging.getLogger("fortress.cache")


class CacheManager:
    """
    TTL-based cache for market data using Parquet files.

    Attributes:
        cache_dir: Directory where cache files are stored
        ttl_minutes: Dict mapping intervals to TTL in minutes
        enabled: Whether caching is active
    """

    def __init__(
        self,
        cache_dir: str | Path | None = None,
        ttl_minutes: dict[str, int] | None = None,
        enabled: bool = True,
    ):
        """
        Initialize the cache manager.

        Args:
            cache_dir: Directory for cache files (default: from config)
            ttl_minutes: TTL per interval (default: from config)
            enabled: Enable/disable caching (default: from config)
        """
        config = get_config()

        # Use provided values or fall back to config
        self.cache_dir = Path(cache_dir or config.cache.directory)
        self.ttl_minutes = ttl_minutes or config.cache.ttl_minutes
        self.enabled = enabled if enabled is not None else config.cache.enabled

        # Create cache directory if it doesn't exist
        if self.enabled:
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            logger.debug(f"Cache initialized at {self.cache_dir}")

    def _get_cache_path(self, symbol: str, interval: str) -> Path:
        """
        Generate the cache file path for a symbol+interval.

        Args:
            symbol: Stock ticker (e.g., "AAPL")
            interval: Data interval (e.g., "1d")

        Returns:
            Path to the cache file
        """
        # Sanitize symbol (remove special chars)
        safe_symbol = symbol.upper().replace("/", "_").replace(".", "_")
        filename = f"{safe_symbol}_{interval}.parquet"
        return self.cache_dir / filename

    def _get_ttl(self, interval: str) -> int:
        """
        Get the TTL in minutes for a given interval.

        Args:
            interval: Data interval

        Returns:
            TTL in minutes
        """
        # Return configured TTL, or default to 60 minutes
        return self.ttl_minutes.get(interval, 60)

    def is_fresh(self, symbol: str, interval: str) -> bool:
        """
        Check if cached data is still fresh (within TTL).

        Args:
            symbol: Stock ticker
            interval: Data interval

        Returns:
            True if cache exists and is fresh, False otherwise
        """
        if not self.enabled:
            return False

        cache_path = self._get_cache_path(symbol, interval)

        if not cache_path.exists():
            return False

        # Check file modification time
        mtime = datetime.fromtimestamp(cache_path.stat().st_mtime)
        ttl = self._get_ttl(interval)
        expiry = mtime + timedelta(minutes=ttl)

        is_valid = datetime.now() < expiry

        if is_valid:
            logger.debug(f"Cache HIT: {symbol}_{interval} (expires {expiry})")
        else:
            logger.debug(f"Cache STALE: {symbol}_{interval} (expired {expiry})")

        return is_valid

    def get(self, symbol: str, interval: str) -> pd.DataFrame | None:
        """
        Retrieve data from cache if fresh.

        Args:
            symbol: Stock ticker
            interval: Data interval

        Returns:
            Cached DataFrame if fresh, None otherwise
        """
        if not self.enabled:
            return None

        if not self.is_fresh(symbol, interval):
            return None

        cache_path = self._get_cache_path(symbol, interval)

        try:
            df = pd.read_parquet(cache_path)
            logger.info(f"Loaded {len(df)} rows from cache: {symbol}_{interval}")
            return df
        except Exception as e:
            logger.warning(f"Failed to read cache {cache_path}: {e}")
            return None

    def set(self, symbol: str, interval: str, data: pd.DataFrame) -> bool:
        """
        Save data to cache.

        Args:
            symbol: Stock ticker
            interval: Data interval
            data: DataFrame to cache

        Returns:
            True if saved successfully, False otherwise
        """
        if not self.enabled:
            return False

        cache_path = self._get_cache_path(symbol, interval)

        try:
            data.to_parquet(cache_path, index=True)
            logger.debug(f"Cached {len(data)} rows: {symbol}_{interval}")
            return True
        except Exception as e:
            logger.warning(f"Failed to write cache {cache_path}: {e}")
            return False

    def invalidate(self, symbol: str | None = None, interval: str | None = None):
        """
        Invalidate (delete) cached data.

        Args:
            symbol: Specific symbol to invalidate (None = all)
            interval: Specific interval to invalidate (None = all)
        """
        if symbol and interval:
            # Invalidate specific file
            cache_path = self._get_cache_path(symbol, interval)
            if cache_path.exists():
                cache_path.unlink()
                logger.info(f"Invalidated cache: {symbol}_{interval}")
        else:
            # Invalidate matching pattern
            pattern = "*"
            if symbol:
                pattern = f"{symbol.upper()}_*.parquet"
            elif interval:
                pattern = f"*_{interval}.parquet"
            else:
                pattern = "*.parquet"

            for cache_file in self.cache_dir.glob(pattern):
                cache_file.unlink()
                logger.debug(f"Deleted: {cache_file.name}")

            logger.info(f"Invalidated cache matching: {pattern}")

    def get_stats(self) -> dict:
        """
        Get cache statistics.

        Returns:
            Dict with cache stats (file count, total size, etc.)
        """
        if not self.cache_dir.exists():
            return {"files": 0, "size_mb": 0, "enabled": self.enabled}

        files = list(self.cache_dir.glob("*.parquet"))
        total_size = sum(f.stat().st_size for f in files)

        return {
            "files": len(files),
            "size_mb": round(total_size / (1024 * 1024), 2),
            "enabled": self.enabled,
            "directory": str(self.cache_dir),
        }


# Convenience function for one-line caching
def get_or_fetch(
    symbol: str,
    interval: str,
    fetcher: callable,
    cache: CacheManager | None = None,
) -> pd.DataFrame:
    """
    Get data from cache or fetch if stale.

    This is the PRIMARY interface for cached data access.

    Args:
        symbol: Stock ticker
        interval: Data interval
        fetcher: Callable that returns DataFrame when cache misses
        cache: CacheManager instance (creates default if None)

    Returns:
        DataFrame (from cache or freshly fetched)

    Example:
        df = get_or_fetch(
            "AAPL",
            "1d",
            lambda: provider.fetch_ohlcv("AAPL", start, end, "1d")
        )
    """
    if cache is None:
        cache = CacheManager()

    # Try cache first
    cached = cache.get(symbol, interval)
    if cached is not None:
        return cached

    # Fetch fresh data
    logger.debug(f"Cache MISS: {symbol}_{interval}, fetching...")
    data = fetcher()

    # Save to cache
    cache.set(symbol, interval, data)

    return data
