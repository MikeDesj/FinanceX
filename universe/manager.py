"""
Financial Fortress - Universe Manager
======================================

This module manages the "universe" of stocks to scan/analyze.

WHAT IS A UNIVERSE?
A universe is simply a list of stock tickers to consider for trading.
Examples:
- S&P 500: 500 large-cap US stocks
- NASDAQ 100: 100 largest NASDAQ stocks
- Custom: Your personal watchlist

WHY SEPARATE THIS?
1. Flexibility: Switch between universes easily (scan S&P today, NASDAQ tomorrow)
2. Persistence: Custom watchlists saved as YAML files
3. Presets: Built-in universes (S&P 500, etc.) without manual ticker entry

USAGE:
    manager = UniverseManager()
    tickers = manager.get_tickers("sp500")  # Returns 500 tickers
    tickers = manager.get_tickers("custom")  # Returns your watchlist
"""

import logging
from pathlib import Path

import yaml

from config.settings import get_config


logger = logging.getLogger("fortress.universe")


class UniverseManager:
    """
    Manages stock universes (watchlists and preset indices).

    Supports:
    - Preset universes: sp500, nasdaq100, dow30
    - Custom YAML watchlists
    """

    def __init__(self, watchlist_dir: str | Path | None = None):
        """
        Initialize the universe manager.

        Args:
            watchlist_dir: Directory containing custom watchlist YAMLs
        """
        self.config = get_config()

        # Default watchlist directory
        if watchlist_dir:
            self.watchlist_dir = Path(watchlist_dir)
        else:
            self.watchlist_dir = Path("universe/watchlists")

    def get_tickers(self, universe: str | None = None) -> list[str]:
        """
        Get list of tickers for a universe.

        Args:
            universe: Universe name ("sp500", "nasdaq100", "dow30", "custom")
                     None = use default from config

        Returns:
            List of ticker symbols
        """
        if universe is None:
            universe = self.config.universe.default

        universe = universe.lower()

        logger.info(f"Loading universe: {universe}")

        if universe == "custom":
            return self._load_custom_watchlist()
        elif universe == "sp500":
            return self._get_sp500()
        elif universe == "nasdaq100":
            return self._get_nasdaq100()
        elif universe == "dow30":
            return self._get_dow30()
        else:
            # Assume it's a custom watchlist filename
            return self._load_watchlist_file(universe)

    def _load_custom_watchlist(self) -> list[str]:
        """Load the default custom watchlist from config."""
        watchlist_path = Path(self.config.universe.custom_watchlist)
        return self._load_watchlist_file(watchlist_path)

    def _load_watchlist_file(self, path: str | Path) -> list[str]:
        """
        Load tickers from a YAML watchlist file.

        Expected format:
            name: "My Watchlist"
            tickers:
              - AAPL
              - MSFT
              - GOOGL
        """
        path = Path(path)

        # If path doesn't exist, try in watchlist_dir
        if not path.exists():
            path = self.watchlist_dir / f"{path}.yaml"

        if not path.exists():
            logger.warning(f"Watchlist not found: {path}")
            return []

        try:
            with open(path) as f:
                data = yaml.safe_load(f)

            tickers = data.get("tickers", [])
            name = data.get("name", path.stem)

            logger.info(f"Loaded {len(tickers)} tickers from '{name}'")
            return [t.upper() for t in tickers]

        except Exception as e:
            logger.error(f"Failed to load watchlist {path}: {e}")
            return []

    def _get_sp500(self) -> list[str]:
        """
        Get S&P 500 tickers.

        Note: This is a static list. For dynamic updates, could fetch from
        Wikipedia or use a paid data source.
        """
        # Top 50 S&P 500 components by weight (representative sample)
        # Full list would have 500+ tickers
        return [
            "AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "GOOG", "BRK.B",
            "UNH", "XOM", "LLY", "JPM", "JNJ", "V", "PG", "MA", "AVGO", "HD",
            "CVX", "MRK", "ABBV", "COST", "PEP", "KO", "ADBE", "WMT", "MCD",
            "CSCO", "CRM", "BAC", "PFE", "ACN", "TMO", "NFLX", "AMD", "LIN",
            "ORCL", "ABT", "DHR", "DIS", "CMCSA", "VZ", "INTC", "WFC", "PM",
            "NEE", "TXN", "RTX", "UPS", "HON",
        ]

    def _get_nasdaq100(self) -> list[str]:
        """Get NASDAQ 100 tickers (top 30 for now)."""
        return [
            "AAPL", "MSFT", "AMZN", "NVDA", "GOOGL", "META", "GOOG", "AVGO",
            "TSLA", "ADBE", "COST", "PEP", "CSCO", "NFLX", "AMD", "CMCSA",
            "INTC", "TMUS", "TXN", "QCOM", "AMGN", "HON", "INTU", "AMAT",
            "ISRG", "BKNG", "SBUX", "MDLZ", "GILD", "ADI",
        ]

    def _get_dow30(self) -> list[str]:
        """Get Dow Jones 30 components."""
        return [
            "AAPL", "AMGN", "AXP", "BA", "CAT", "CRM", "CSCO", "CVX", "DIS",
            "DOW", "GS", "HD", "HON", "IBM", "INTC", "JNJ", "JPM", "KO",
            "MCD", "MMM", "MRK", "MSFT", "NKE", "PG", "TRV", "UNH", "V",
            "VZ", "WBA", "WMT",
        ]

    def save_watchlist(
        self,
        name: str,
        tickers: list[str],
        description: str = ""
    ) -> Path:
        """
        Save a custom watchlist to YAML file.

        Args:
            name: Watchlist name (used as filename)
            tickers: List of ticker symbols
            description: Optional description

        Returns:
            Path to saved file
        """
        # Ensure directory exists
        self.watchlist_dir.mkdir(parents=True, exist_ok=True)

        # Create filename
        filename = name.lower().replace(" ", "_") + ".yaml"
        path = self.watchlist_dir / filename

        # Build data
        data = {
            "name": name,
            "description": description,
            "tickers": [t.upper() for t in tickers],
        }

        # Save
        with open(path, "w") as f:
            yaml.dump(data, f, default_flow_style=False)

        logger.info(f"Saved watchlist '{name}' with {len(tickers)} tickers to {path}")
        return path

    def list_watchlists(self) -> list[dict]:
        """
        List all available watchlists.

        Returns:
            List of dicts with name, path, and ticker count
        """
        watchlists = []

        # Add presets
        watchlists.extend([
            {"name": "S&P 500", "type": "preset", "count": 50},
            {"name": "NASDAQ 100", "type": "preset", "count": 30},
            {"name": "Dow 30", "type": "preset", "count": 30},
        ])

        # Add custom watchlists
        if self.watchlist_dir.exists():
            for path in self.watchlist_dir.glob("*.yaml"):
                try:
                    with open(path) as f:
                        data = yaml.safe_load(f)
                    watchlists.append({
                        "name": data.get("name", path.stem),
                        "type": "custom",
                        "path": str(path),
                        "count": len(data.get("tickers", [])),
                    })
                except Exception:
                    pass

        return watchlists
