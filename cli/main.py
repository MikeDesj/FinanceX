"""
Financial Fortress - CLI Entry Point
Click-based command line interface
"""

import click
from rich.progress import Progress, SpinnerColumn, TextColumn

from cli.logger import (
    console,
    print_banner,
    print_signals_table,
    print_portfolio_table,
    print_success,
    print_error,
    print_info,
    setup_logging,
)
from config.settings import get_config, reload_config


@click.group()
@click.option("--config", "-c", type=click.Path(exists=True), help="Path to config file")
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.pass_context
def cli(ctx, config, verbose):
    """
    💰 Financial Fortress - PowerX Trading System

    Algorithmic trading with momentum signals and options strategies.
    """
    ctx.ensure_object(dict)

    # Load configuration
    if config:
        cfg = reload_config(config)
    else:
        cfg = get_config()

    ctx.obj["config"] = cfg

    # Setup logging
    level = "DEBUG" if verbose else cfg.logging.level
    ctx.obj["logger"] = setup_logging(level, cfg.logging.file)

    # Print banner
    print_banner()


@cli.command()
@click.option("--universe", "-u", default=None, help="Universe to scan (sp500, nasdaq100, custom)")
@click.pass_context
def scan(ctx, universe):
    """Scan for PowerX momentum signals (RSI/MACD/Stochastics)"""
    cfg = ctx.obj["config"]
    universe_name = universe or cfg.universe.default

    print_info(f"Scanning universe: {universe_name}")

    with Progress(
        SpinnerColumn(),
        TextColumn("[progress.description]{task.description}"),
        console=console,
    ) as progress:
        task = progress.add_task("Fetching data...", total=None)

        # TODO: Implement actual scanning
        # For now, show placeholder
        progress.update(task, description="Analyzing indicators...")

    # Placeholder results
    print_info("Scanner not yet implemented - Phase 2 required")
    print_signals_table([
        {"symbol": "AAPL", "signal": "BUY", "rsi": 55.2, "stoch": 62.1, "macd": 0.0023},
        {"symbol": "MSFT", "signal": "NEUTRAL", "rsi": 48.5, "stoch": 51.2, "macd": -0.0012},
    ], title="Sample Output")


@cli.command("wheel-scan")
@click.option("--min-roi", type=float, default=None, help="Minimum annualized ROI %")
@click.pass_context
def wheel_scan(ctx, min_roi):
    """Scan for Wheel Strategy opportunities (put/call selling)"""
    cfg = ctx.obj["config"]
    roi_threshold = min_roi or cfg.strategy.wheel.min_annualized_roi

    print_info(f"Scanning for Wheel opportunities (min ROI: {roi_threshold}%)")
    print_info("Wheel scanner not yet implemented - Phase 5 required")


@cli.command()
@click.argument("symbol")
@click.pass_context
def analyze(ctx, symbol):
    """Deep analysis of a single ticker"""
    print_info(f"Analyzing {symbol.upper()}...")
    print_info("Analyzer not yet implemented - Phase 3 required")


@cli.command()
@click.pass_context
def portfolio(ctx):
    """Show current paper trading positions"""
    cfg = ctx.obj["config"]

    print_info(f"Paper Trading Account (${cfg.paper_trading.initial_capital:,.0f} initial)")

    # Placeholder
    print_portfolio_table([
        {
            "symbol": "AAPL",
            "quantity": 10,
            "entry_price": 175.50,
            "current_price": 182.30,
            "pnl": 68.00,
            "pnl_pct": 3.87,
        }
    ], title="Sample Positions")
    print_info("Portfolio tracking not yet implemented - Phase 4 required")


@cli.command()
@click.pass_context
def performance(ctx):
    """Display KPI dashboard (Rapid Performance Analyzer)"""
    print_info("Performance dashboard not yet implemented - Phase 4 required")

    # Show what will be available
    console.print("\n[bold]Planned KPIs:[/]")
    console.print("  • Win Rate")
    console.print("  • Profit Factor")
    console.print("  • Avg Win / Avg Loss")
    console.print("  • Average Trade Length")
    console.print("  • Realized P&L by Month")


@cli.command()
@click.pass_context
def config(ctx):
    """Display current configuration"""
    cfg = ctx.obj["config"]

    console.print("\n[bold cyan]Current Configuration:[/]\n")

    console.print("[bold]Strategy:[/]")
    console.print(f"  Name: {cfg.strategy.name}")
    console.print(f"  RSI Period: {cfg.strategy.indicators.rsi.period}")
    console.print(f"  MACD: ({cfg.strategy.indicators.macd.fast}, {cfg.strategy.indicators.macd.slow}, {cfg.strategy.indicators.macd.signal})")
    console.print(f"  Wheel Min ROI: {cfg.strategy.wheel.min_annualized_roi}%")

    console.print("\n[bold]Data:[/]")
    console.print(f"  Provider: {cfg.data.provider}")
    console.print(f"  Interval: {cfg.data.default_interval}")
    console.print(f"  Cache: {'Enabled' if cfg.cache.enabled else 'Disabled'}")

    console.print("\n[bold]Risk Management:[/]")
    console.print(f"  Stop Loss: {cfg.risk_management.stop_loss_percent}%")
    console.print(f"  Profit Target: {cfg.risk_management.profit_target_percent}%")
    console.print(f"  Max Positions: {cfg.risk_management.max_open_positions}")

    print_success("Configuration loaded successfully")


@cli.command()
@click.option("--start", type=str, help="Start date (YYYY-MM-DD)")
@click.option("--end", type=str, help="End date (YYYY-MM-DD)")
@click.pass_context
def backtest(ctx, start, end):
    """Run historical simulation"""
    print_info("Backtest engine not yet implemented - Phase 4 required")


def main():
    """Entry point"""
    cli(obj={})


if __name__ == "__main__":
    main()
