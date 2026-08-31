"""Daemon command — start and manage the dashboard server."""

import sys
import webbrowser
from contextlib import suppress

import typer
import uvicorn

app = typer.Typer(help="Start and manage the dashboard server")


@app.callback(invoke_without_command=True)
def daemon(
    host: str = typer.Option("127.0.0.1", "--host", "-h", help="Bind address"),
    port: int = typer.Option(9876, "--port", "-p", help="Port to listen on"),
    no_open: bool = typer.Option(
        False, "--no-open", help="Don't open browser automatically"
    ),
) -> None:
    """Start the dashboard and API server."""

    display_host = "localhost" if host in ("127.0.0.1", "0.0.0.0") else host
    typer.echo(f"Starting env-manager daemon on http://{host}:{port}")
    typer.echo(f"Dashboard: http://{display_host}:{port}")
    typer.echo("Press Ctrl+C to stop.")

    if not no_open:
        with suppress(Exception):
            webbrowser.open(f"http://localhost:{port}")

    try:
        uvicorn.run(
            "env_manager.daemon.server:app",
            host=host,
            port=port,
            log_level="info",
        )
    except KeyboardInterrupt:
        typer.echo("\nDaemon stopped.")
        sys.exit(0)
