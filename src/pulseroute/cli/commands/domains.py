import asyncio

import typer
from sqlalchemy import select

from pulseroute.cli.ui import console
from pulseroute.core.database import async_session_maker, init_db
from pulseroute.models.domain import CustomDomain
from pulseroute.services.domain_service import DomainService

domains_app = typer.Typer(help="Manage and verify custom domains")


@domains_app.command("add")
def add_domain(domain: str = typer.Argument(..., help="Domain name e.g. links.mybrand.com")):
    """Add a custom domain."""
    async def _run():
        await init_db()
        async with async_session_maker() as db:
            try:
                dom = await DomainService.add_custom_domain(db, domain)
                console.print("[bold green]✔ Custom domain added![/bold green]")
                console.print(f"Domain: [cyan]{dom.domain}[/cyan]")
                console.print(f"DNS Challenge: [yellow]_pulseroute-challenge.{dom.domain} -> TXT '{dom.verification_code}'[/yellow]")
            except Exception as e:
                console.print(f"[bold red]Error:[/bold red] {e!s}")

    asyncio.run(_run())


@domains_app.command("verify")
def verify_domain(domain: str = typer.Argument(..., help="Domain name to verify")):
    """Run DNS verification check for a custom domain."""
    async def _run():
        await init_db()
        async with async_session_maker() as db:
            result = await db.execute(select(CustomDomain).where(CustomDomain.domain == domain.strip().lower()))
            dom = result.scalar_one_or_none()
            if not dom:
                console.print(f"[bold red]Domain '{domain}' not found in PulseRoute.[/bold red]")
                return

            success, msg = await DomainService.verify_domain_dns(db, dom.id)
            if success:
                console.print(f"[bold green]✔ {msg}[/bold green]")
            else:
                console.print(f"[bold yellow]✖ {msg}[/bold yellow]")

    asyncio.run(_run())
