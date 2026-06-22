"""Pin command — favorite important projects, safe from cleanup."""

from pathlib import Path

import typer

from env_manager.cli.db_utils import ensure_db_dir, get_db_path
from env_manager.storage.database import (
    close_connection,
    get_connection,
    init_db,
)
from env_manager.storage.repo_project import ProjectRepository

app = typer.Typer(help="Pin important projects — safe from cleanup")


@app.callback(invoke_without_command=True)
def pin(
    project: str = typer.Argument(..., help="Project name or path to pin"),
) -> None:
    """Pin a project. Pinned projects are never cleanup candidates."""
    toggle_pin(project, True)


@app.command()
def unpin(
    project: str = typer.Argument(..., help="Project name or path to unpin"),
) -> None:
    """Unpin a project. It becomes eligible for cleanup again."""
    toggle_pin(project, False)


def toggle_pin(identifier: str, pinned: bool) -> None:
    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        repo = ProjectRepository(conn)
        proj = repo.get_by_path(identifier)
        if not proj:
            proj = repo.get_by_path(str(Path(identifier).resolve()))
        if not proj:
            all_p = repo.list_all()
            proj = next((p for p in all_p if p["name"] == identifier), None)
        if not proj:
            typer.echo(f"project not found: {identifier}")
            raise typer.Exit(1)

        repo.set_pinned(proj["id"], pinned)
        action = "Pinned" if pinned else "Unpinned"
        typer.echo(f"{action}: {proj['name']}")
    finally:
        conn.close()
        close_connection(db_path)
