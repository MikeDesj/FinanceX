"""
Financial Fortress - Configuration Management
Pydantic models for type-safe configuration validation
"""

from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, Field


class RSIConfig(BaseModel):
    """RSI indicator configuration"""
    period: int = 7
    threshold: float = 50.0


class StochasticsConfig(BaseModel):
    """Stochastics indicator configuration"""
    k_period: int = 14
    d_period: int = 3
    smooth_k: int = 3
    threshold: float = 50.0


class MACDConfig(BaseModel):
    """MACD indicator configuration"""
    fast: int = 12
    slow: int = 26
    signal: int = 9


class WheelConfig(BaseModel):
    """Wheel Strategy (options) configuration"""
    min_annualized_roi: float = 30.0
    exit_profit_fast: int = 80  # Exit at 80% within 24hrs
    exit_profit_normal: int = 90  # Exit at 90% before expiration


class IndicatorsConfig(BaseModel):
    """All indicator configurations"""
    rsi: RSIConfig = Field(default_factory=RSIConfig)
    stochastics: StochasticsConfig = Field(default_factory=StochasticsConfig)
    macd: MACDConfig = Field(default_factory=MACDConfig)


class StrategyConfig(BaseModel):
    """Strategy configuration"""
    name: str = "PowerX"
    indicators: IndicatorsConfig = Field(default_factory=IndicatorsConfig)
    wheel: WheelConfig = Field(default_factory=WheelConfig)


class RiskManagementConfig(BaseModel):
    """Risk management settings"""
    stop_loss_percent: float = 2.0
    profit_target_percent: float = 6.0
    max_position_size: int = 1000
    max_open_positions: int = 5


class DataConfig(BaseModel):
    """Data provider settings"""
    provider: Literal["yfinance", "polygon"] = "yfinance"
    default_interval: str = "1d"
    lookback_days: int = 60


class CacheTTLConfig(BaseModel):
    """Cache TTL per interval (in minutes)"""
    model_config = {"extra": "allow"}

    # Default TTLs - keys are interval strings like "1d", "1h", "5m"
    # Using Field with alias to handle dynamic keys


class CacheConfig(BaseModel):
    """Cache configuration"""
    enabled: bool = True
    directory: str = "cache/"
    ttl_minutes: dict[str, int] = Field(
        default_factory=lambda: {"1d": 240, "1h": 30, "5m": 5}
    )


class UniverseConfig(BaseModel):
    """Universe/watchlist settings"""
    default: Literal["custom", "sp500", "nasdaq100", "dow30"] = "custom"
    custom_watchlist: str = "universe/watchlists/default.yaml"


class ScannerConfig(BaseModel):
    """Scanner concurrency settings"""
    max_concurrent: int = 10
    batch_delay_ms: int = 100


class PaperTradingConfig(BaseModel):
    """Paper trading settings"""
    initial_capital: float = 100000.0
    commission_per_trade: float = 0.0


class LoggingConfig(BaseModel):
    """Logging configuration"""
    level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    file: str = "logs/trading.log"


class AppConfig(BaseModel):
    """Root application configuration"""
    strategy: StrategyConfig = Field(default_factory=StrategyConfig)
    risk_management: RiskManagementConfig = Field(default_factory=RiskManagementConfig)
    data: DataConfig = Field(default_factory=DataConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    universe: UniverseConfig = Field(default_factory=UniverseConfig)
    scanner: ScannerConfig = Field(default_factory=ScannerConfig)
    paper_trading: PaperTradingConfig = Field(default_factory=PaperTradingConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)


def load_config(config_path: Path | str | None = None) -> AppConfig:
    """
    Load configuration from YAML file.
    Falls back to defaults if no file specified or file not found.

    Args:
        config_path: Path to YAML config file. If None, uses config/default.yaml

    Returns:
        Validated AppConfig instance
    """
    # Default config path
    if config_path is None:
        config_path = Path(__file__).parent / "default.yaml"
    else:
        config_path = Path(config_path)

    # Load from file if exists
    if config_path.exists():
        with open(config_path) as f:
            data = yaml.safe_load(f) or {}
        return AppConfig(**data)

    # Return defaults
    return AppConfig()


# Global config instance (lazy loaded)
_config: AppConfig | None = None


def get_config() -> AppConfig:
    """Get the global configuration instance (singleton pattern)"""
    global _config
    if _config is None:
        _config = load_config()
    return _config


def reload_config(config_path: Path | str | None = None) -> AppConfig:
    """Reload configuration from file"""
    global _config
    _config = load_config(config_path)
    return _config
