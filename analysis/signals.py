"""
Financial Fortress - Signal Generator (PowerX Strategy)
========================================================

This module generates BUY/SELL/NEUTRAL signals based on PowerX rules.

THE POWERX STRATEGY RULES:

┌─────────────────────────────────────────────────────────────┐
│                    BUY SIGNAL (LONG)                        │
├─────────────────────────────────────────────────────────────┤
│ ALL THREE CONDITIONS MUST BE TRUE:                          │
│   1. RSI(7) > 50         (Momentum is bullish)              │
│   2. Stochastics %D > 50 (Price near range highs)           │
│   3. MACD > Signal       (Bullish crossover/trend)          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                   SELL SIGNAL (SHORT)                       │
├─────────────────────────────────────────────────────────────┤
│ ALL THREE CONDITIONS MUST BE TRUE:                          │
│   1. RSI(7) < 50         (Momentum is bearish)              │
│   2. Stochastics %D < 50 (Price near range lows)            │
│   3. MACD < Signal       (Bearish crossover/trend)          │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                      NEUTRAL (NO TRADE)                     │
├─────────────────────────────────────────────────────────────┤
│ Any condition NOT met = mixed signals, stay out             │
└─────────────────────────────────────────────────────────────┘

WHY THIS WORKS:
- Requires ALIGNMENT of multiple indicators
- Reduces false signals (each indicator has noise)
- Catches strong trend starts when all three agree

SIGNAL STRENGTH:
We also calculate "signal strength" (0-100) based on how strongly
each indicator supports the signal:
- RSI: how far above/below 50
- Stoch: how far above/below 50
- MACD: size of histogram

USAGE:
    generator = SignalGenerator()

    # From DataFrame with indicators
    signal = generator.generate_signal(df)

    # Quick check of latest bar
    signal = generator.evaluate_current(df)
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Optional

import pandas as pd

from config.settings import get_config
from analysis.indicators import IndicatorEngine


logger = logging.getLogger("fortress.signals")


class SignalType(Enum):
    """Trading signal types."""
    BUY = "BUY"
    SELL = "SELL"
    NEUTRAL = "NEUTRAL"


@dataclass
class Signal:
    """
    Trading signal with metadata.

    Attributes:
        type: BUY, SELL, or NEUTRAL
        strength: Signal strength 0-100 (higher = stronger)
        rsi: RSI value at signal time
        stoch: Stochastics %D value
        macd: MACD value
        macd_signal: MACD signal line value
        reason: Human-readable explanation
    """
    type: SignalType
    strength: float
    rsi: Optional[float]
    stoch: Optional[float]
    macd: Optional[float]
    macd_signal: Optional[float]
    reason: str

    def is_actionable(self, min_strength: float = 50) -> bool:
        """Check if signal is strong enough to act on."""
        return self.type != SignalType.NEUTRAL and self.strength >= min_strength

    def to_dict(self) -> dict:
        """Convert to dictionary for serialization."""
        return {
            "signal": self.type.value,
            "strength": round(self.strength, 1),
            "rsi": round(self.rsi, 2) if self.rsi else None,
            "stoch": round(self.stoch, 2) if self.stoch else None,
            "macd": round(self.macd, 6) if self.macd else None,
            "macd_signal": round(self.macd_signal, 6) if self.macd_signal else None,
            "reason": self.reason,
        }


class SignalGenerator:
    """
    Generates PowerX trading signals from indicator data.
    """

    def __init__(self, indicator_engine: IndicatorEngine | None = None):
        """
        Initialize the signal generator.

        Args:
            indicator_engine: Engine to calculate indicators (default: new instance)
        """
        self.config = get_config()
        self.indicators = indicator_engine or IndicatorEngine()

        # Thresholds
        self.rsi_threshold = self.config.strategy.indicators.rsi.threshold
        self.stoch_threshold = self.config.strategy.indicators.stochastics.threshold

    def evaluate_conditions(
        self,
        rsi: float,
        stoch: float,
        macd: float,
        macd_signal: float,
    ) -> tuple[SignalType, list[str]]:
        """
        Evaluate PowerX conditions for a single data point.

        Args:
            rsi: RSI value
            stoch: Stochastics %D value
            macd: MACD value
            macd_signal: MACD signal line value

        Returns:
            Tuple of (signal_type, list_of_reasons)
        """
        reasons = []

        # Check bullish conditions
        rsi_bullish = rsi > self.rsi_threshold
        stoch_bullish = stoch > self.stoch_threshold
        macd_bullish = macd > macd_signal

        # Check bearish conditions
        rsi_bearish = rsi < self.rsi_threshold
        stoch_bearish = stoch < self.stoch_threshold
        macd_bearish = macd < macd_signal

        # BUY: All three bullish
        if rsi_bullish and stoch_bullish and macd_bullish:
            reasons = [
                f"RSI({rsi:.1f}) > {self.rsi_threshold}",
                f"Stoch({stoch:.1f}) > {self.stoch_threshold}",
                f"MACD > Signal",
            ]
            return SignalType.BUY, reasons

        # SELL: All three bearish
        if rsi_bearish and stoch_bearish and macd_bearish:
            reasons = [
                f"RSI({rsi:.1f}) < {self.rsi_threshold}",
                f"Stoch({stoch:.1f}) < {self.stoch_threshold}",
                f"MACD < Signal",
            ]
            return SignalType.SELL, reasons

        # NEUTRAL: Mixed signals
        mixed = []
        if rsi_bullish:
            mixed.append("RSI bullish")
        elif rsi_bearish:
            mixed.append("RSI bearish")
        else:
            mixed.append("RSI neutral")

        if stoch_bullish:
            mixed.append("Stoch bullish")
        elif stoch_bearish:
            mixed.append("Stoch bearish")
        else:
            mixed.append("Stoch neutral")

        if macd_bullish:
            mixed.append("MACD bullish")
        else:
            mixed.append("MACD bearish")

        return SignalType.NEUTRAL, mixed

    def calculate_strength(
        self,
        signal_type: SignalType,
        rsi: float,
        stoch: float,
        macd: float,
        macd_signal: float,
    ) -> float:
        """
        Calculate signal strength (0-100).

        Strength is based on how far indicators are from their thresholds.
        Stronger signals have indicators firmly in their zone.

        Args:
            signal_type: The signal type
            rsi: RSI value
            stoch: Stochastics %D value
            macd: MACD value
            macd_signal: MACD signal line value

        Returns:
            Strength score 0-100
        """
        if signal_type == SignalType.NEUTRAL:
            return 0

        # Calculate component strengths (0-100 each)

        # RSI strength: how far from 50
        # RSI at 70 for BUY = 100 * (70-50)/50 = 40 strength
        # Capped at 50 (RSI 100 or 0)
        rsi_strength = min(abs(rsi - 50), 50) * 2

        # Stoch strength: same as RSI
        stoch_strength = min(abs(stoch - 50), 50) * 2

        # MACD strength: based on histogram size
        # This is trickier as MACD is not bounded
        macd_hist = abs(macd - macd_signal)
        # Normalize: assume typical histogram is 0-2 for stocks
        macd_strength = min(macd_hist * 50, 100)

        # Average the three
        strength = (rsi_strength + stoch_strength + macd_strength) / 3

        return min(strength, 100)

    def generate_signal(self, df: pd.DataFrame, add_indicators: bool = True) -> Signal:
        """
        Generate signal from price DataFrame.

        Args:
            df: DataFrame with OHLCV data
            add_indicators: If True, add indicators first

        Returns:
            Signal object with type, strength, and details
        """
        if df.empty:
            return Signal(
                type=SignalType.NEUTRAL,
                strength=0,
                rsi=None,
                stoch=None,
                macd=None,
                macd_signal=None,
                reason="No data",
            )

        # Add indicators if needed
        if add_indicators or "rsi" not in df.columns:
            df = self.indicators.add_all_indicators(df)

        # Get latest values
        latest = df.iloc[-1]

        rsi = latest.get("rsi")
        stoch = latest.get("stoch_d")
        macd = latest.get("macd")
        macd_signal = latest.get("macd_signal")

        # Check for NaN values (happens at start of data)
        if pd.isna(rsi) or pd.isna(stoch) or pd.isna(macd) or pd.isna(macd_signal):
            return Signal(
                type=SignalType.NEUTRAL,
                strength=0,
                rsi=float(rsi) if not pd.isna(rsi) else None,
                stoch=float(stoch) if not pd.isna(stoch) else None,
                macd=float(macd) if not pd.isna(macd) else None,
                macd_signal=float(macd_signal) if not pd.isna(macd_signal) else None,
                reason="Insufficient data for indicators",
            )

        # Evaluate conditions
        signal_type, reasons = self.evaluate_conditions(rsi, stoch, macd, macd_signal)

        # Calculate strength
        strength = self.calculate_strength(signal_type, rsi, stoch, macd, macd_signal)

        return Signal(
            type=signal_type,
            strength=strength,
            rsi=float(rsi),
            stoch=float(stoch),
            macd=float(macd),
            macd_signal=float(macd_signal),
            reason=" | ".join(reasons),
        )

    def generate_signals_batch(
        self,
        scan_results: list[dict],
    ) -> list[dict]:
        """
        Generate signals for batch of scan results.

        Args:
            scan_results: List of dicts from Scanner with 'symbol' and 'data' keys

        Returns:
            List of dicts with symbol, signal, and indicator values
        """
        signals = []

        for result in scan_results:
            symbol = result.get("symbol", "")
            data = result.get("data")

            if data is None or result.get("error"):
                signals.append({
                    "symbol": symbol,
                    "signal": "ERROR",
                    "error": result.get("error", "No data"),
                })
                continue

            try:
                signal = self.generate_signal(data)
                signals.append({
                    "symbol": symbol,
                    **signal.to_dict(),
                })
            except Exception as e:
                logger.error(f"Error generating signal for {symbol}: {e}")
                signals.append({
                    "symbol": symbol,
                    "signal": "ERROR",
                    "error": str(e),
                })

        return signals

    def filter_by_signal(
        self,
        signals: list[dict],
        signal_type: SignalType | str,
        min_strength: float = 0,
    ) -> list[dict]:
        """
        Filter signals by type and minimum strength.

        Args:
            signals: List of signal dicts
            signal_type: BUY, SELL, or signal type enum
            min_strength: Minimum strength threshold

        Returns:
            Filtered list of signals
        """
        if isinstance(signal_type, SignalType):
            target = signal_type.value
        else:
            target = signal_type.upper()

        return [
            s for s in signals
            if s.get("signal") == target and s.get("strength", 0) >= min_strength
        ]
