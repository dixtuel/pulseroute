import asyncio

import typer
from rich.table import Table

from pulseroute.cli.ui import console
from pulseroute.core.database import async_session_maker, init_db
from pulseroute.services.analytics_service import AnalyticsService

analytics_app = typer.Typer(help="View visitor analytics")


@analytics_app.command("summary")
def summary(days: int = typer.Option(7, "--days", "-d")):
    """Show global traffic overview."""
    async def _run():
        await init_db()
        async with async_session_maker() as db:
            data = await AnalyticsService.get_link_analytics(db, days=days)
            console.print(f"\n[bold white]PulseRoute Analytics (Last {days} Days)[/bold white]")
            console.print(f"Total Clicks:      [bold green]{data.total_clicks}[/bold green]")
            console.print(f"Unique Visitors:   [bold cyan]{data.unique_visitors}[/bold cyan]")
            console.print(f"Bot/Crawler Hits:  [bold yellow]{data.bot_clicks}[/bold yellow]\n")

            if data.devices:
                table = Table(title="Device Breakdown", border_style="cyan")
                table.add_column("Device")
                table.add_column("Clicks", justify="right")
                table.add_column("Percentage", justify="right")
                for d in data.devices:
                    table.add_row(d.name, str(d.count), f"{d.percentage}%")
                console.print(table)

    asyncio.run(_run())
