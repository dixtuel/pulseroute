from rich.console import Console
from rich.panel import Panel
from rich.text import Text

console = Console()


def print_banner():
    banner = Text(
        "⚡ PulseRoute CLI — Enterprise URL Shortener & Analytics\n"
        "Modern, Ultra-Fast & Self-Hosted Link Infrastructure",
        style="bold magenta",
    )
    console.print(Panel(banner, border_style="cyan"))
