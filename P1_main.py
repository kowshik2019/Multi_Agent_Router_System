"""
main.py
-------
Entry point for the Multi-Agent Router System.

Supports two run modes:
  1. Interactive CLI  — run without arguments → prompts for queries in a loop.
  2. Batch demo mode  — run with `--demo` flag → processes a set of sample queries.

Usage:
  python main.py          # interactive
  python main.py --demo   # run demo batch
"""

import sys
from rich.console import Console

from agents.router_agent import RouterAgent
from utils.logger        import print_result

console = Console()

DEMO_QUERIES = [
    # Sales
    "What is the current discount for bulk orders above 500 units?",
    "I want a quote for 200 units of Model X5 with 3-year warranty.",
    # HR
    "I need to apply for 5 days of annual leave next month.",
    "What is the maternity leave policy for full-time employees?",
    # Operations
    "What is the current inventory level for SKU-48291?",
    "When will the delayed shipment from Vendor A arrive?",
    # Irrelevant
    "Tell me a joke about penguins.",
    "Who won the World Cup in 2018?",
]


def interactive_loop(router: RouterAgent) -> None:
    console.print("\n[bold cyan]Multi-Agent Router System — Interactive Mode[/bold cyan]")
    console.print("Type your query and press Enter. Type [bold red]exit[/bold red] to quit.\n")

    while True:
        try:
            query = input("You ▶  ").strip()
        except (EOFError, KeyboardInterrupt):
            console.print("\n[yellow]Session ended.[/yellow]")
            break

        if not query:
            continue
        if query.lower() in ("exit", "quit", "q"):
            console.print("[yellow]Goodbye![/yellow]")
            break

        result = router.process(query)
        print_result(result)
        console.print()


def demo_batch(router: RouterAgent) -> None:
    console.print("\n[bold cyan]Multi-Agent Router System — Demo Batch Mode[/bold cyan]\n")
    for q in DEMO_QUERIES:
        result = router.process(q)
        print_result(result)
        console.print("─" * 60)


def main() -> None:
    router = RouterAgent()

    if "--demo" in sys.argv:
        demo_batch(router)
    else:
        interactive_loop(router)


if __name__ == "__main__":
    main()
