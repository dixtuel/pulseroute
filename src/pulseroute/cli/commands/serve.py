import typer
import uvicorn

from pulseroute.cli.ui import console, print_banner

serve_app = typer.Typer()


@serve_app.callback(invoke_without_command=True)
def serve(
    host: str = typer.Option("0.0.0.0", "--host", "-h", help="Host address"),
    port: int = typer.Option(8000, "--port", "-p", help="Port number"),
    reload: bool = typer.Option(False, "--reload", "-r", help="Auto-reload on code change"),
):
    """Start PulseRoute API server, Background Workers, and Web Dashboard."""
    print_banner()
    console.print(f"[bold green]Starting PulseRoute server on http://{host}:{port}[/bold green]")
    console.print(f"[cyan]Web Dashboard:[/cyan] http://localhost:{port}/dashboard")
    console.print(f"[cyan]API Docs:[/cyan]      http://localhost:{port}/docs\n")
    uvicorn.run("pulseroute.main:app", host=host, port=port, reload=reload)
