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
    loop_choice = "auto"
    try:
        import uvloop  # noqa: F401
        loop_choice = "uvloop"
    except ImportError:
        pass

    http_choice = "auto"
    try:
        import httptools  # noqa: F401
        http_choice = "httptools"
    except ImportError:
        pass

    uvicorn.run("pulseroute.main:app", host=host, port=port, reload=reload, loop=loop_choice, http=http_choice)
