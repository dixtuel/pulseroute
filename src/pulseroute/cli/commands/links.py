import asyncio

import typer
from rich.table import Table

from pulseroute.cli.ui import console
from pulseroute.common.qr_generator import generate_qr_ascii
from pulseroute.core.database import async_session_maker, init_db
from pulseroute.schemas.link import LinkCreate
from pulseroute.services.link_service import LinkService

links_app = typer.Typer(help="Manage short links")


@links_app.command("create")
def create(
    url: str = typer.Argument(..., help="Destination URL"),
    slug: str = typer.Option(None, "--slug", "-s", help="Custom slug"),
    title: str = typer.Option(None, "--title", "-t", help="Link title"),
    qr: bool = typer.Option(False, "--qr", help="Print ASCII QR Code to terminal"),
):
    """Create a new short link."""
    async def _run():
        await init_db()
        async with async_session_maker() as db:
            try:
                link_data = LinkCreate(destination_url=url, slug=slug, title=title)
                link = await LinkService.create_link(db, redis_cli=None, data=link_data)
                short_url = f"http://localhost:8000/{link.slug}"
                console.print("[bold green]Link created successfully.[/bold green]")
                console.print(f"[bold white]Short URL:[/bold white] [cyan]{short_url}[/cyan]")
                console.print(f"[bold white]Destination:[/bold white] {link.destination_url}")

                if qr:
                    console.print("\n[bold white]QR Code:[/bold white]")
                    console.print(generate_qr_ascii(short_url))
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {str(e)}")

    asyncio.run(_run())


@links_app.command("list")
def list_links(limit: int = typer.Option(20, "--limit", "-l")):
    """List short links."""
    async def _run():
        await init_db()
        async with async_session_maker() as db:
            links = await LinkService.list_links(db, limit=limit)
            if not links:
                console.print("[yellow]No links found.[/yellow]")
                return

            table = Table(title="PulseRoute Short Links", border_style="cyan")
            table.add_column("ID", style="dim")
            table.add_column("Slug", style="cyan bold")
            table.add_column("Destination", style="white")
            table.add_column("Clicks", justify="right", style="green bold")

            for lnk in links:
                table.add_row(str(lnk.id), f"/{lnk.slug}", lnk.destination_url[:45] + "...", str(lnk.total_clicks))

            console.print(table)

    asyncio.run(_run())
