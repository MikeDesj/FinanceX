"""
Financial Fortress - Indicator Engine
======================================

This module calculates technical indicators used by the PowerX strategy.

WHAT ARE TECHNICAL INDICATORS?
Mathematical calculations based on price/volume that help predict future moves.
Traders use them to identify trends, momentum, and entry/exit points.

THE POWERX INDICATORS:

1. RSI (Relative Strength Index) - Period 7
   - Measures momentum on a 0-100 scale
   - > 50 = bullish momentum
   - < 50 = bearish momentum
   - RSI(7) is more sensitive than the default RSI(14)

2. Stochastics (14, 3, 3)
   - Compares closing price to price range
   - %K = raw value, %D = smoothed (we use %D)
   - > 50 = price near top of range (bullish)
   - < 50 = price near bottom of range (bearish)

3. MACD (12, 26, 9)
   - Moving Average Convergence Divergence
   - MACD line = EMA(12) - EMA(26)
   - Signal line = EMA(9) of MACD
   - MACD > Signal = bullish crossover

WHY pandas-ta?
- Vectorized operations (fast on large DataFrames)
- Well-tested, widely used
- Consistent API

USAGE:
    engine = IndicatorEngine()
    df = engine.add_all_indicators(price_df)
    # df now has columns: rsi, stoch_d, macd, macd_signal
"""

import logging

import pandas as pd
import pandas_ta as ta

from config.settings import get_config


logger = logging.getLogger("fortress.indicators")


class IndicatorEngine:
    """
    Technical indicator calculator for PowerX strategy.

    Adds RSI, Stochastics, and MACD to price DataFrames.
    """

    def __init__(self):
        """Initialize with config settings."""
        self.config = get_config()
        self.ind_config = self.config.strategy.indicators

    def add_rsi(self, df: pd.DataFrame, period: int | None = None) -> pd.DataFrame:
        """
        Add RSI (Relative Strength Index) to DataFrame.

        RSI = 100 - (100 / (1 + RS))
        where RS = avg gain / avg loss over period

        Args:
            df: DataFrame with 'close' column
            period: RSI period (default from config)

        Returns:
            DataFrame with 'rsi' column added
        """
        if period is None:
            period = self.ind_config.rsi.period

        # pandas_ta handles all the math
        df["rsi"] = ta.rsi(df["close"], length=period)

        logger.debug(f"Added RSI({period})")
        return df

    def add_stochastics(
        self,
        df: pd.DataFrame,
        k_period: int | None = None,
        d_period: int | None = None,
        smooth_k: int | None = None,
    ) -> pd.DataFrame:
        """
        Add Stochastics %K and %D to DataFrame.

        %K = (Close - Low(n)) / (High(n) - Low(n)) * 100
        %D = SMA of %K

        We use %D (smoothed) for signals to reduce noise.

        Args:
            df: DataFrame with 'high', 'low', 'close' columns
            k_period: Lookback period
            d_period: %D smoothing period
            smooth_k: %K smoothing period

        Returns:
            DataFrame with 'stoch_k' and 'stoch_d' columns added
        """
        if k_period is None:
            k_period = self.ind_config.stochastics.k_period
        if d_period is None:
            d_period = self.ind_config.stochastics.d_period
        if smooth_k is None:
            smooth_k = self.ind_config.stochastics.smooth_k

        # pandas_ta returns DataFrame with STOCHk_* and STOCHd_* columns
        stoch = ta.stoch(
            high=df["high"],
            low=df["low"],
            close=df["close"],
            k=k_period,
            d=d_period,
            smooth_k=smooth_k,
        )

        # Rename columns for clarity
        df["stoch_k"] = stoch.iloc[:, 0]  # First column is %K
        df["stoch_d"] = stoch.iloc[:, 1]  # Second column is %D

        logger.debug(f"Added Stochastics({k_period},{d_period},{smooth_k})")
        return df

    def add_macd(
        self,
        df: pd.DataFrame,
        fast: int | None = None,
        slow: int | None = None,
        signal: int | None = None,
    ) -> pd.DataFrame:
        """
        Add MACD and Signal line to DataFrame.

        MACD = EMA(fast) - EMA(slow)
        Signal = EMA(signal) of MACD
        Histogram = MACD - Signal

        Args:
            df: DataFrame with 'close' column
            fast: Fast EMA period
            slow: Slow EMA period
            signal: Signal line EMA period

        Returns:
            DataFrame with 'macd', 'macd_signal', 'macd_hist' columns
        """
        if fast is None:
            fast = self.ind_config.macd.fast
        if slow is None:
            slow = self.ind_config.macd.slow
        if signal is None:
            signal = self.ind_config.macd.signal

        # pandas_ta MACD
        macd_df = ta.macd(df["close"], fast=fast, slow=slow, signal=signal)

        # Columns are: MACD_12_26_9, MACDh_12_26_9, MACDs_12_26_9
        df["macd"] = macd_df.iloc[:, 0]  # MACD line
        df["macd_hist"] = macd_df.iloc[:, 1]  # Histogram
        df["macd_signal"] = macd_df.iloc[:, 2]  # Signal line

        logger.debug(f"Added MACD({fast},{slow},{signal})")
        return df

    def add_all_indicators(self, df: pd.DataFrame) -> pd.DataFrame:
        """
        Add all PowerX indicators to DataFrame.

        This is the main method to call for full analysis.

        Args:
            df: DataFrame with OHLCV columns

        Returns:
            DataFrame with all indicator columns added
        """
        # Make a copy to avoid modifying original
        df = df.copy()

        # Add each indicator
        df = self.add_rsi(df)
        df = self.add_stochastics(df)
        df = self.add_macd(df)

        logger.info(f"Added all indicators to DataFrame ({len(df)} rows)")
        return df

    def get_latest_values(self, df: pd.DataFrame) -> dict:
        """
        Get the most recent indicator values.

        Useful for quick signal checks.

        Args:
            df: DataFrame with indicator columns

        Returns:
            Dict with latest RSI, Stoch, MACD values
        """
        if df.empty:
            return {}

        latest = df.iloc[-1]

        return {
            "rsi": latest.get("rsi"),
            "stoch_k": latest.get("stoch_k"),
            "stoch_d": latest.get("stoch_d"),
            "macd": latest.get("macd"),
            "macd_signal": latest.get("macd_signal"),
            "macd_hist": latest.get("macd_hist"),
        }
