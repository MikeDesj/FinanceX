# Financial Fortress

> PowerX Optimizer-inspired algorithmic trading system in Python

A modular, backtestable trading system implementing:
- **PowerX Momentum Strategy** — RSI, Stochastics, MACD signals
- **Wheel Strategy** — Options put/call selling with 30%+ ROI targets
- **Performance Dashboard** — KPI tracking inspired by "Building Your Financial Fortress"

## Features

- 📊 Concurrent stock scanning with caching
- 🎯 Momentum signals (PowerX) + Options analysis (Wheel)
- 📈 Rapid Performance Analyzer with KPI dashboard
- 📝 Trade journal with confidence & plan-adherence tracking
- 🖥️ Rich CLI interface

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Scan for momentum signals
python -m cli.main scan

# Scan for Wheel Strategy opportunities
python -m cli.main wheel-scan

# View performance dashboard
python -m cli.main performance
```

## Documentation

- [ARCHITECTURE.md](ARCHITECTURE.md) — System design and module responsibilities
- [docs/architecture_diagram.png](docs/architecture_diagram.png) — Visual architecture

## Technology Stack

| Component | Technology |
|-----------|------------|
| Runtime | Python 3.12+ |
| Data | yfinance, Polygon.io (future) |
| Analysis | pandas-ta |
| CLI | Click + Rich |
| Config | Pydantic + PyYAML |

## License

MIT
