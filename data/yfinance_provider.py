"""
Financial Fortress - yfinance Data Provider
============================================

This is the CONCRETE implementation of DataProvider using the yfinance library.
yfinance is a free, open-source library that fetches data from Yahoo Finance.

HOW IT WORKS:
1. yfinance.Ticker("AAPL") creates a ticker object
2. .history() fetches historical OHLCV data
3. .options gives available expiration dates
4. .option_chain() fetches puts/calls for an expiration

RATE LIMITING:
- Yahoo Finance can throttle heavy usage
- This is why we have a CacheManager (implemented next)
- The cache prevents repeated API calls for the same data

USAGE:
    provider = YFinanceProvider()
    df = provider.fetch_ohlcv("AAPL", start_date, end_date, "1d")
"""

from datetime import date, datetime, timedelta
import logging

import pandas as pd
import yfinance as yf

from data.provider import DataProvider, Interval


logger = logging.getLogger("fortress.data")


class YFinanceProvider(DataProvider):
    """
    Yahoo Finance data provider implementation.

    Provides free market data including:
    - Historical OHLCV prices
    - Options chains (for Wheel Strategy)
    - Basic stock info

    Note: Subject to rate limiting. Use with CacheManager for best results.
    """

    @property
    def name(self) -> str:
        return "yfinance"

    def fetch_ohlcv(
        self,
        symbol: str,
        start: date | datetime,
        end: date | datetime,
        interval: Interval = "1d",
    ) -> pd.DataFrame:
        """
        Fetch OHLCV data from Yahoo Finance.

        Args:
            symbol: Stock ticker (e.g., "AAPL")
            start: Start date
            end: End date
            interval: Candle interval ("1d", "1h", "5m", etc.)

        Returns:
            DataFrame with standardized columns:
            [open, high, low, close, volume]
            Index is DatetimeIndex named 'date'
        """
        # Validate inputs
        symbol = self.validate_symbol(symbol)

        # Convert to date if datetime
        if isinstance(start, datetime):
            start = start.date()
        if isinstance(end, datetime):
            end = end.date()

        start, end = self.validate_date_range(start, end)

        logger.debug(f"Fetching {symbol} from {start} to {end} ({interval})")

        try:
            # Create ticker object
            ticker = yf.Ticker(symbol)

            # Fetch historical data
            # Note: yfinance end date is exclusive, so add 1 day
            df = ticker.history(
                start=start,
                end=end + timedelta(days=1),
                interval=interval,
                auto_adjust=True,  # Adjust for splits/dividends
            )

            if df.empty:
                raise ValueError(f"No data returned for {symbol}")

            # Standardize column names (yfinance uses Title Case)
            df.columns = df.columns.str.lower()

            # Keep only OHLCV columns
            required_cols = ["open", "high", "low", "close", "volume"]
            df = df[required_cols]

            # Ensure index is named 'date'
            df.index.name = "date"

            logger.info(f"Fetched {len(df)} bars for {symbol}")
            return df

        except Exception as e:
            logger.error(f"Failed to fetch {symbol}: {e}")
            raise ValueError(f"Could not fetch data for {symbol}: {e}")

    def fetch_options_chain(
        self,
        symbol: str,
        expiration: date | None = None,
    ) -> pd.DataFrame:
        """
        Fetch options chain from Yahoo Finance for Wheel Strategy analysis.

        The Wheel Strategy needs options data to:
        1. Find put strikes with 30%+ annualized ROI
        2. Analyze call premiums after assignment

        Args:
            symbol: Stock ticker
            expiration: Target expiration date (None = nearest available)

        Returns:
            DataFrame with all puts and calls for the expiration
        """
        symbol = self.validate_symbol(symbol)

        logger.debug(f"Fetching options chain for {symbol}")

        try:
            ticker = yf.Ticker(symbol)

            # Get available expirations
            expirations = ticker.options
            if not expirations:
                raise ValueError(f"No options available for {symbol}")

            # Select expiration
            if expiration is None:
                # Use nearest expiration
                exp_str = expirations[0]
            else:
                # Find closest expiration to requested date
                exp_str = self._find_closest_expiration(
                    expirations, expiration
                )

            logger.debug(f"Using expiration: {exp_str}")

            # Fetch the chain
            chain = ticker.option_chain(exp_str)

            # Combine puts and calls into single DataFrame
            calls = chain.calls.copy()
            calls["type"] = "call"

            puts = chain.puts.copy()
            puts["type"] = "put"

            df = pd.concat([puts, calls], ignore_index=True)

            # Standardize columns
            df = df.rename(columns={
                "strike": "strike",
                "lastPrice": "last",
                "bid": "bid",
                "ask": "ask",
                "volume": "volume",
                "openInterest": "open_interest",
                "impliedVolatility": "implied_volatility",
            })

            # Add expiration date
            df["expiration"] = pd.to_datetime(exp_str).date()

            # Select final columns
            final_cols = [
                "strike", "type", "bid", "ask", "last",
                "volume", "open_interest", "implied_volatility", "expiration"
            ]
            df = df[[c for c in final_cols if c in df.columns]]

            logger.info(f"Fetched {len(df)} options for {symbol} exp {exp_str}")
            return df

        except Exception as e:
            logger.error(f"Failed to fetch options for {symbol}: {e}")
            raise ValueError(f"Could not fetch options for {symbol}: {e}")

    def _find_closest_expiration(
        self,
        expirations: list[str],
        target: date
    ) -> str:
        """
        Find the expiration date closest to the target.

        Args:
            expirations: List of expiration date strings from yfinance
            target: Target date we want

        Returns:
            Closest expiration string
        """
        target_dt = datetime.combine(target, datetime.min.time())

        closest = min(
            expirations,
            key=lambda x: abs(datetime.strptime(x, "%Y-%m-%d") - target_dt)
        )
        return closest

    def get_current_price(self, symbol: str) -> float:
        """
        Get the current/last price for a symbol.

        Useful for quick checks without full OHLCV fetch.

        Args:
            symbol: Stock ticker

        Returns:
            Current price as float
        """
        symbol = self.validate_symbol(symbol)
        ticker = yf.Ticker(symbol)

        # Try to get from info, fall back to last close
        info = ticker.info
        price = info.get("currentPrice") or info.get("regularMarketPrice")

        if price is None:
            # Fallback: get last close from history
            hist = ticker.history(period="1d")
            if not hist.empty:
                price = hist["Close"].iloc[-1]

        if price is None:
            raise ValueError(f"Could not get price for {symbol}")

        return float(price)
