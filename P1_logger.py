"""
utils/logger.py
---------------
Rich-based pretty logger and result printer for the Multi-Agent Router System.
Provides coloured console output for agent routing decisions and responses.
"""

from rich.console import Console
from rich.panel   import Panel
from rich.table   import Table
from rich         import box

console = Console()

DEPT_COLORS = {
    "SALES":      "green",
    "HR":         "blue",
    "OPERATIONS": "yellow",
    "IRRELEVANT": "red",
}


def print_result(result: dict) -> None:
    """Pretty-print the full routing result to the console."""
    dept  = result.get("department", "UNKNOWN")
    color = DEPT_COLORS.get(dept, "white")

    # ── Routing summary table ─────────────────────────────────────────────────
    table = Table(box=box.ROUNDED, show_header=False, padding=(0, 1))
    table.add_column("Field",  style="bold cyan",  width=18)
    table.add_column("Value",  style="white")

    table.add_row("Query",        result.get("query", "")[:80])
    table.add_row("Vector Hint",  result.get("vector_hint", ""))
    table.add_row("Routed To",    f"[{color}]{dept}[/{color}]")
    table.add_row("Confidence",   f"{result.get('confidence', 0):.0%}")
    table.add_row("Reason",       result.get("reason", ""))

    console.print(table)

    # ── Department response panel ─────────────────────────────────────────────
    console.print(
        Panel(
            result.get("response", ""),
            title=f"[bold {color}]{dept} Response[/bold {color}]",
            border_style=color,
            padding=(1, 2),
        )
    )
