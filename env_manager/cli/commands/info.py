"""Info command — show detailed environment info."""

import json
from pathlib import Path

import typer

from env_manager.cli.db_utils import ensure_db_dir, get_db_path
from env_manager.cli.formatters import format_env_info
from env_manager.storage.database import (
    close_connection,
    get_connection,
    init_db,
)
from env_manager.storage.repo_env import EnvironmentRepository
from env_manager.storage.repo_project import ProjectRepository


def info(
    project: str = typer.Argument(..., help="Project name or path"),
    json_output: bool = typer.Option(False, "--json", help="Output as JSON"),
) -> None:
    """Show detailed info for a project."""
    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    try:
        proj_repo = ProjectRepository(conn)
        env_repo = EnvironmentRepository(conn)

        resolved = str(Path(project).resolve())
        proj = proj_repo.get_by_path(resolved)
        if not proj:
            proj = proj_repo.get_by_path(project)
        if not proj:
            all_p = proj_repo.list_all()
            proj = next((p for p in all_p if p["name"] == project), None)

        if not proj:
            msg = f"project not found: {project}"
            typer.echo(json.dumps({"error": msg}) if json_output else msg)
            raise typer.Exit(1)

        envs = env_repo.list_by_project(proj["id"])
        if json_output:
            result = []
            for e in envs:
                d = dict(e)
                d["project_name"] = proj["name"]
                result.append(d)
            typer.echo(json.dumps(result, indent=2, default=str))
        else:
            for e in envs:
                d = dict(e)
                d["project_name"] = proj["name"]
                format_env_info(d)  # type: ignore[arg-type]
    finally:
        conn.close()
        close_connection(db_path)
