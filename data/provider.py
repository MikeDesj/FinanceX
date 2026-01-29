"""
Financial Fortress - Abstract Data Provider
============================================

This module defines the contract (interface) that ALL data providers must follow.
Using an Abstract Base Class (ABC) ensures any data source (yfinance, Polygon, etc.)
provides the same methods, making them interchangeable.

DESIGN PATTERN: Strategy Pattern
- DataProvider is the abstract interface
- YFinanceProvider, PolygonProvider are concrete implementations
- The system can swap providers without changing any other code

WHY THIS MATTERS:
- Today we use yfinance (free, but rate-limited)
- Tomorrow we might upgrade to Polygon.io (paid, faster)
- The rest of the system doesn't need to change!
"""

from abc import ABC, abstractmethod
from datetime import date, datetime
from typing import Literal

import pandas as pd


# Type alias for valid intervals
Interval = Literal["1m", "5m", "15m", "30m", "1h", "1d", "1wk", "1mo"]


class DataProvider(ABC):
    """
    Abstract base class for all market data providers.

    Any data source (yfinance, Polygon, Alpaca, etc.) must implement these methods.
    This guarantees consistent behavior across all providers.
    """

    @property
    @abstractmethod
    def name(self) -> str:
        """
        Human-readable name of the data provider.

        Returns:
            str: Provider name (e.g., "yfinance", "polygon")
        """
        pass

    @abstractmethod
    def fetch_ohlcv(
        self,
        symbol: str,
        start: date | datetime,
        end: date | datetime,
        interval: Interval = "1d",
    ) -> pd.DataFrame:
        """
        Fetch OHLCV (Open, High, Low, Close, Volume) price data.

        This is the PRIMARY method for getting historical price data.
        All providers MUST return data in the same format.

        Args:
            symbol: Stock ticker (e.g., "AAPL", "MSFT")
            start: Start date for data range
            end: End date for data range
            interval: Candle size ("1d" = daily, "1h" = hourly, etc.)

        Returns:
            DataFrame with columns:
                - date (index): Timestamp
                - open: Opening price
                - high: Highest price
                - low: Lowest price
                - close: Closing price
                - volume: Trading volume

        Raises:
            ValueError: If symbol not found or invalid date range
            ConnectionError: If API unavailable
        """
        pass

    @abstractmethod
    def fetch_options_chain(
        self,
        symbol: str,
        expiration: date | None = None,
    ) -> pd.DataFrame:
        """
        Fetch options chain data for Wheel Strategy analysis.

        Args:
            symbol: Stock ticker
            expiration: Specific expiration date (None = nearest)

        Returns:
            DataFrame with columns:
                - strike: Strike price
                - type: "call" or "put"
                - bid: Bid price
                - ask: Ask price
                - last: Last traded price
                - volume: Trading volume
                - open_interest: Open interest
                - implied_volatility: IV as decimal
                - expiration: Expiration date

        Raises:
            ValueError: If no options available for symbol
        """
        pass

    def validate_symbol(self, symbol: str) -> str:
        """
        Normalize and validate a stock symbol.

        This is a helper method (not abstract) that all providers can use.
        Converts to uppercase and strips whitespace.

        Args:
            symbol: Raw symbol input

        Returns:
            Cleaned symbol string
        """
        return symbol.strip().upper()

    def validate_date_range(self, start: date, end: date) -> tuple[date, date]:
        """
        Validate that date range is sensible.

        Args:
            start: Start date
            end: End date

        Returns:
            Validated (start, end) tuple

        Raises:
            ValueError: If start > end or dates in future
        """
        today = date.today()

        if start > end:
            raise ValueError(f"Start date {start} is after end date {end}")

        if start > today:
            raise ValueError(f"Start date {start} is in the future")

        # Cap end date at today
        if end > today:
            end = today

        return start, end
