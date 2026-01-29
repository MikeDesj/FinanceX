"""
Financial Fortress - Rich Logging Setup
Console and file logging with rich formatting
"""

import logging
import sys
from pathlib import Path

from rich.console import Console
from rich.logging import RichHandler
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

# Global console instance
console = Console()


def setup_logging(level: str = "INFO", log_file: str | None = None) -> logging.Logger:
    """
    Set up logging with Rich console handler and optional file handler.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional path to log file

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger("fortress")
    logger.setLevel(getattr(logging, level.upper()))

    # Clear existing handlers
    logger.handlers.clear()

    # Rich console handler
    console_handler = RichHandler(
        console=console,
        show_time=True,
        show_path=False,
        rich_tracebacks=True,
    )
    console_handler.setLevel(logging.DEBUG)
    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(logging.DEBUG)
        file_formatter = logging.Formatter(
            "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s"
        )
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    return logger


def print_banner():
    """Print the Financial Fortress banner"""
    banner = Text()
    banner.append("💰 ", style="bold yellow")
    banner.append("Financial Fortress", style="bold cyan")
    banner.append(" 💰", style="bold yellow")

    panel = Panel(
        banner,
        subtitle="PowerX Optimizer Trading System",
        border_style="cyan",
    )
    console.print(panel)


def print_signals_table(signals: list[dict], title: str = "Scan Results"):
    """
    Print a formatted table of trading signals.

    Args:
        signals: List of signal dicts with keys: symbol, signal, rsi, stoch, macd
        title: Table title
    """
    table = Table(title=title, show_header=True, header_style="bold magenta")

    table.add_column("Symbol", style="cyan", width=8)
    table.add_column("Signal", justify="center", width=10)
    table.add_column("RSI(7)", justify="right", width=8)
    table.add_column("Stoch", justify="right", width=8)
    table.add_column("MACD", justify="right", width=10)

    for sig in signals:
        signal_style = {
            "BUY": "bold green",
            "SELL": "bold red",
            "NEUTRAL": "dim",
        }.get(sig.get("signal", "NEUTRAL"), "dim")

        table.add_row(
            sig.get("symbol", ""),
            Text(sig.get("signal", "NEUTRAL"), style=signal_style),
            f"{sig.get('rsi', 0):.1f}",
            f"{sig.get('stoch', 0):.1f}",
            f"{sig.get('macd', 0):.4f}",
        )

    console.print(table)


def print_portfolio_table(positions: list[dict], title: str = "Portfolio"):
    """
    Print a formatted table of portfolio positions.

    Args:
        positions: List of position dicts
        title: Table title
    """
    table = Table(title=title, show_header=True, header_style="bold magenta")

    table.add_column("Symbol", style="cyan", width=8)
    table.add_column("Qty", justify="right", width=6)
    table.add_column("Entry", justify="right", width=10)
    table.add_column("Current", justify="right", width=10)
    table.add_column("P&L", justify="right", width=12)
    table.add_column("P&L %", justify="right", width=8)

    for pos in positions:
        pnl = pos.get("pnl", 0)
        pnl_pct = pos.get("pnl_pct", 0)
        pnl_style = "green" if pnl >= 0 else "red"

        table.add_row(
            pos.get("symbol", ""),
            str(pos.get("quantity", 0)),
            f"${pos.get('entry_price', 0):.2f}",
            f"${pos.get('current_price', 0):.2f}",
            Text(f"${pnl:+.2f}", style=pnl_style),
            Text(f"{pnl_pct:+.1f}%", style=pnl_style),
        )

    console.print(table)


def print_success(message: str):
    """Print a success message"""
    console.print(f"[bold green]✓[/] {message}")


def print_error(message: str):
    """Print an error message"""
    console.print(f"[bold red]✗[/] {message}")


def print_warning(message: str):
    """Print a warning message"""
    console.print(f"[bold yellow]⚠[/] {message}")


def print_info(message: str):
    """Print an info message"""
    console.print(f"[bold blue]ℹ[/] {message}")


# Default logger
logger = setup_logging()
