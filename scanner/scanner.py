"""
Financial Fortress - Concurrent Scanner
========================================

This module scans multiple stocks in PARALLEL for massive speed improvements.

THE PROBLEM:
Scanning 500 stocks sequentially = 500 API calls * ~1 second each = 8+ minutes
That's painfully slow!

THE SOLUTION:
Use ThreadPoolExecutor to fetch data concurrently.
With 10 parallel workers: 500 stocks / 10 = ~50 seconds (10x faster!)

WHY THREADS (not asyncio)?
1. yfinance is NOT async - it uses requests internally
2. I/O-bound work (network calls) benefits from threads
3. ThreadPoolExecutor is simpler than full async rewrite

RATE LIMITING:
We still respect Yahoo Finance rate limits:
- batch_delay_ms: Pause between batches to avoid throttling
- max_concurrent: Cap parallel requests

FLOW:
1. Load tickers from Universe
2. Split into batches
3. Fetch each batch concurrently with ThreadPoolExecutor
4. Analyze indicators on each ticker
5. Return signals

USAGE:
    scanner = Scanner()
    signals = scanner.scan_universe("sp500")
"""

import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
from datetime import date, timedelta
import time

from rich.progress import Progress, BarColumn, TextColumn, TimeElapsedColumn

from cli.logger import console
from config.settings import get_config
from data.cache import CacheManager, get_or_fetch
from data.yfinance_provider import YFinanceProvider
from universe.manager import UniverseManager


logger = logging.getLogger("fortress.scanner")


class Scanner:
    """
    Concurrent stock scanner with caching and progress tracking.

    Fetches data in parallel and returns analysis-ready DataFrames.
    """

    def __init__(
        self,
        provider: YFinanceProvider | None = None,
        cache: CacheManager | None = None,
        universe_manager: UniverseManager | None = None,
    ):
        """
        Initialize the scanner.

        Args:
            provider: Data provider (default: YFinanceProvider)
            cache: Cache manager (default: CacheManager)
            universe_manager: Universe manager (default: UniverseManager)
        """
        self.config = get_config()
        self.provider = provider or YFinanceProvider()
        self.cache = cache or CacheManager()
        self.universe = universe_manager or UniverseManager()

        # Scanner settings from config
        self.max_concurrent = self.config.scanner.max_concurrent
        self.batch_delay_ms = self.config.scanner.batch_delay_ms

    def fetch_symbol(
        self,
        symbol: str,
        interval: str = "1d",
        lookback_days: int | None = None,
    ) -> dict:
        """
        Fetch data for a single symbol (with caching).

        This is the unit of work executed by each thread.

        Args:
            symbol: Stock ticker
            interval: Data interval
            lookback_days: Days of history (default from config)

        Returns:
            Dict with symbol, data DataFrame, and any errors
        """
        if lookback_days is None:
            lookback_days = self.config.data.lookback_days

        end = date.today()
        start = end - timedelta(days=lookback_days)

        result = {
            "symbol": symbol,
            "data": None,
            "error": None,
        }

        try:
            # Use cache wrapper for efficient fetching
            df = get_or_fetch(
                symbol=symbol,
                interval=interval,
                fetcher=lambda: self.provider.fetch_ohlcv(symbol, start, end, interval),
                cache=self.cache,
            )
            result["data"] = df

        except Exception as e:
            logger.warning(f"Failed to fetch {symbol}: {e}")
            result["error"] = str(e)

        return result

    def scan_symbols(
        self,
        symbols: list[str],
        interval: str = "1d",
        show_progress: bool = True,
    ) -> list[dict]:
        """
        Scan multiple symbols concurrently.

        Args:
            symbols: List of ticker symbols
            interval: Data interval
            show_progress: Show progress bar

        Returns:
            List of result dicts (one per symbol)
        """
        results = []
        total = len(symbols)

        logger.info(f"Scanning {total} symbols with {self.max_concurrent} workers")

        # Create progress bar
        progress = None
        task_id = None

        if show_progress:
            progress = Progress(
                TextColumn("[progress.description]{task.description}"),
                BarColumn(),
                TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                TimeElapsedColumn(),
                console=console,
            )
            progress.start()
            task_id = progress.add_task("Scanning...", total=total)

        try:
            # Use ThreadPoolExecutor for concurrent fetching
            with ThreadPoolExecutor(max_workers=self.max_concurrent) as executor:
                # Submit all fetch tasks
                futures = {
                    executor.submit(self.fetch_symbol, symbol, interval): symbol
                    for symbol in symbols
                }

                # Collect results as they complete
                for future in as_completed(futures):
                    symbol = futures[future]

                    try:
                        result = future.result()
                        results.append(result)

                    except Exception as e:
                        logger.error(f"Error scanning {symbol}: {e}")
                        results.append({
                            "symbol": symbol,
                            "data": None,
                            "error": str(e),
                        })

                    # Update progress
                    if progress and task_id is not None:
                        progress.update(task_id, advance=1)

                    # Small delay to be nice to the API
                    if self.batch_delay_ms > 0:
                        time.sleep(self.batch_delay_ms / 1000)

        finally:
            if progress:
                progress.stop()

        # Summary
        successful = sum(1 for r in results if r["data"] is not None)
        failed = total - successful

        logger.info(f"Scan complete: {successful} succeeded, {failed} failed")

        return results

    def scan_universe(
        self,
        universe: str | None = None,
        interval: str = "1d",
        show_progress: bool = True,
    ) -> list[dict]:
        """
        Scan an entire universe of stocks.

        Args:
            universe: Universe name (sp500, nasdaq100, custom, etc.)
            interval: Data interval
            show_progress: Show progress bar

        Returns:
            List of result dicts
        """
        # Get tickers from universe
        tickers = self.universe.get_tickers(universe)

        if not tickers:
            logger.warning(f"No tickers in universe: {universe}")
            return []

        logger.info(f"Scanning universe '{universe}' ({len(tickers)} tickers)")

        return self.scan_symbols(tickers, interval, show_progress)

    def get_cache_stats(self) -> dict:
        """Get cache statistics."""
        return self.cache.get_stats()
