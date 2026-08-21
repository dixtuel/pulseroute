import typer

from pulseroute.cli.commands.analytics import analytics_app
from pulseroute.cli.commands.domains import domains_app
from pulseroute.cli.commands.links import links_app
from pulseroute.cli.commands.serve import serve_app

app = typer.Typer(
    name="pulseroute",
    help="⚡ PulseRoute — Enterprise URL Shortener, Custom Domains & Real-Time Analytics CLI",
    add_completion=False,
)

app.add_typer(serve_app, name="serve")
app.add_typer(links_app, name="link")
app.add_typer(domains_app, name="domain")
app.add_typer(analytics_app, name="analytics")

if __name__ == "__main__":
    app()
