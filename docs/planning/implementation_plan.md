# Financial Fortress - Implementation Plan

> Step-by-step checklist for building the PowerX Optimizer-inspired trading system
>
> *Enhanced with Rapid Performance Analyzer features from "Building Your Financial Fortress"*

---

## Overview

Build a modular, backtestable algorithmic trading system implementing the PowerX strategy with:
- **RSI(7)**, **Stochastics(14,3,3)**, **MACD(12,26,9)** indicators
- CLI interface with rich logging
- Paper trading execution engine
- **TTL-based data caching** to avoid API throttling
- **Concurrent scanning** for large universes
- **Universe management** (S&P 500, custom watchlists)

---

## Phase 1: Project Scaffolding

### 1.1 Initialize Project Structure

- [ ] Create directory structure per [ARCHITECTURE.md](file:///home/michael/Documents/Programmation/AI%20and%20trading/FinanceX/ARCHITECTURE.md)
- [ ] Create all `__init__.py` files for package imports
- [ ] Set up [requirements.txt](file:///home/michael/Documents/Programmation/AI%20and%20trading/FinanceX/requirements.txt) (provided)
- [ ] Create `config/default.yaml` with PowerX defaults

### 1.2 Configuration Module

- [ ] Implement `config/settings.py`:
  - Pydantic models for config validation
  - YAML loader with defaults
  - Type-safe access to strategy parameters

---

## Phase 2: Data Layer

### 2.1 Abstract Data Provider

- [ ] Create `data/provider.py`:
  - `DataProvider` ABC with `fetch_ohlcv()` method
  - Standard DataFrame schema: `[date, open, high, low, close, volume]`
  - Validation for required columns

### 2.2 yfinance Implementation

- [ ] Implement `data/yfinance_provider.py`:
  - Inherit from `DataProvider`
  - Handle rate limiting and retries
  - Date range validation
  - Symbol normalization

### 2.3 Cache Layer (Critical)

- [ ] Implement `data/cache.py`:
  - TTL-based cache using Parquet files in `cache/` directory
  - Cache key: `{symbol}_{interval}.parquet`
  - Check cache freshness before API call
  - Configurable TTL per interval (daily=4hr, hourly=30min)
  - `get_or_fetch(symbol, interval)` main interface

### 2.4 Universe Manager

- [ ] Create `universe/manager.py`:
  - Load tickers from preset (`sp500`, `nasdaq100`) or custom YAML
  - `get_tickers()` returns list of symbols

- [ ] Create `universe/presets.py`:
  - Fetch S&P 500 tickers from Wikipedia or static list
  - Cache preset lists for 24 hours

- [ ] Create `universe/watchlists/default.yaml`:
  - Example custom watchlist format

### 2.5 Concurrent Scanner

- [ ] Implement `scanner/scanner.py`:
  - Use `ThreadPoolExecutor` for parallel data fetching
  - Configurable `max_concurrent` workers (default: 10)
  - Batch delay to respect rate limits
  - Progress bar with `rich`

---

## Phase 3: Analysis Layer

### 3.1 Indicator Engine

- [ ] Create `analysis/indicators.py`:

| Indicator | Config | Library Function |
|-----------|--------|------------------|
| RSI | period=7 | `pandas_ta.rsi()` |
| Stochastics | k=14, d=3, smooth=3 | `pandas_ta.stoch()` |
| MACD | fast=12, slow=26, signal=9 | `pandas_ta.macd()` |

- [ ] Return DataFrame with columns: `rsi_7`, `stoch_k`, `stoch_d`, `macd`, `macd_signal`, `macd_hist`

### 3.2 Signal Generator

- [ ] Implement `analysis/signals.py`:

```python
# Signal Rules (PowerX Truth Table)
BUY    = (rsi > 50) & (stoch_k > 50) & (macd > signal)
SELL   = (rsi < 50) & (stoch_k < 50) & (macd < signal)
NEUTRAL = ~BUY & ~SELL
```

- [ ] Return signal column: `['BUY', 'SELL', 'NEUTRAL']`
- [ ] Include signal strength (optional: distance from thresholds)

---

## Phase 4: Execution Layer

### 4.1 Position Manager

- [ ] Create `execution/positions.py`:
  - Position dataclass: symbol, entry_price, quantity, stop_loss, take_profit
  - Calculate P&L (unrealized/realized)
  - Validate risk parameters from config

### 4.2 Paper Trading Engine

- [ ] Implement `execution/paper_trader.py`:
  - Track portfolio: cash, positions, equity
  - Execute orders at next bar open (realistic simulation)
  - Apply stop-loss and take-profit logic
  - Commission handling

### 4.3 Trade Journal (Enhanced)

- [ ] Create `persistence/journal.py`:
  - Log trades to SQLite with full metadata
  - Fields: timestamp, symbol, action, price, quantity, pnl
  - **PowerX fields**: `according_to_plan` (bool), `confidence_level` (1-5)
  - Query interface for performance calculations

### 4.4 Performance Dashboard (Rapid Performance Analyzer)

- [ ] Implement `persistence/dashboard.py`:
  - Calculate KPIs from trade journal:
    - Win rate, Profit factor, Avg win/loss ratio
    - Average trade length, Longest trade
    - Realized P&L (cumulative + by month)
    - Trades by day distribution
  - Export summary as rich table or JSON

---

## Phase 5: Wheel Strategy (Options)

### 5.1 Options Data Provider

- [ ] Extend `data/yfinance_provider.py`:
  - Add `fetch_options_chain(symbol, expiration)` method
  - Return DataFrame: strike, type, bid, ask, volume, OI, IV

### 5.2 Options Analyzer

- [ ] Create `strategy/options_analyzer.py`:
  - Calculate annualized ROI from premium
  - Formula: `(premium / strike * 100) * (365 / days_to_expiration)`
  - Filter strikes meeting 30%+ ROI threshold

### 5.3 Wheel Strategy Logic

- [ ] Implement `strategy/wheel.py`:
  - **Sell Puts**: Find strikes at prices you'd buy, 30%+ ROI
  - **Expiration Selection**: Mon/Tue→this week, Thu/Fri→next week
  - **Assignment Handling**: Track assigned positions for call selling
  - **Exit Rules**: 80% within 24hrs, 90% before expiration

---

## Phase 6: CLI Integration

### 5.1 Rich Logger

- [ ] Implement `cli/logger.py`:
  - Console handler with rich formatting
  - File handler for persistent logs
  - Trade table formatting

### 5.2 CLI Commands

- [ ] Build `cli/main.py` using Click:

| Command | Description |
|---------|-------------|
| `scan` | Scan for momentum signals |
| `wheel-scan` | Scan for Wheel Strategy opportunities |
| `analyze <symbol>` | Deep analysis of single ticker |
| `backtest` | Run historical simulation |
| `portfolio` | Show current paper positions |
| `performance` | Display KPI dashboard |
| `config` | Display/validate configuration |

---

## Phase 7: Testing & Verification

### 6.1 Unit Tests

Create under `tests/`:

- [ ] `test_indicators.py` — Verify RSI/Stoch/MACD output against known values
- [ ] `test_signals.py` — Test signal logic with edge cases
- [ ] `test_paper_trader.py` — Order execution, P&L calculation

### 6.2 Integration Tests

- [ ] End-to-end scan with mock data
- [ ] Backtest run validating trade journal output
- [ ] Cache hit/miss verification
- [ ] Concurrent scanner stress test (50+ tickers)

### 6.3 Manual Verification

- [ ] Run `scan` on 5 tickers, compare signals to TradingView
- [ ] Verify paper trade P&L matches expected calculation

---

## Verification Plan

### Automated Tests

Run all tests with:
```bash
pytest tests/ -v --cov=. --cov-report=term-missing
```

### Manual Verification

1. **Indicator Accuracy**: Compare RSI/MACD/Stoch values against TradingView for AAPL on a known date
2. **Signal Correctness**: Manually verify 3 BUY and 3 SELL signals match PowerX rules
3. **Paper Trade**: Execute 5 trades and validate P&L calculation

---

## Milestones & Acceptance Criteria

| Milestone | Criteria |
|-----------|----------|
| **M1: Data Layer** | Can fetch 60 days OHLCV for any symbol with cache |
| **M1.5: Universe** | Can load S&P 500 tickers + custom watchlist |
| **M2: Analysis Layer** | Correct indicators + signals for AAPL |
| **M2.5: Scanner** | Concurrent scan of 50 tickers < 30 seconds |
| **M3.5: Wheel Strategy** | Scan options, calculate ROI, identify trades |
| **M4: Execution Layer** | Paper trade with P&L tracking |
| **M4: CLI Complete** | All commands functional |
| **M5: Tested** | >80% coverage, all tests pass |

---

## Risk & Mitigations

| Risk | Mitigation |
|------|------------|
| yfinance rate limits | Implement caching + retry logic |
| TA-Lib installation | Use pandas-ta as primary (pure Python) |
| Float precision in signals | Use `np.isclose()` for threshold comparisons |

---

## Next Steps After Approval

1. Create project skeleton with all files
2. Implement Phase 1 (Config) + Phase 2 (Data Layer)
3. Progress through phases with tests after each
