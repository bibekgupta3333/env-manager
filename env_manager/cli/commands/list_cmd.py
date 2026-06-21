"""List command — show tracked environments."""

from __future__ import annotations

from typing import Any

import typer

from env_manager.cli.db_utils import ensure_db_dir, get_db_path
from env_manager.cli.formatters import format_env_list
from env_manager.storage.database import get_connection, init_db
from env_manager.storage.repo_env import EnvironmentRepository
from env_manager.storage.repo_project import ProjectRepository

app = typer.Typer()


@app.callback(invoke_without_command=True)
def list_envs(
    by_project: bool = typer.Option(False, "--by-project", help="Group by project"),
    stale: bool = typer.Option(False, "--stale", help="Show only stale"),
    orphaned: bool = typer.Option(False, "--orphaned", help="Show only orphaned"),
    language: str = typer.Option(None, "--lang", help="Filter by language"),
) -> None:
    """List tracked environments."""
    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    repo = EnvironmentRepository(conn)
    proj_repo = ProjectRepository(conn)

    if stale:
        envs = repo.list_stale(days=30)
    elif orphaned:
        envs = repo.list_orphaned()
    elif language:
        envs = repo.list_by_language(language)
    else:
        envs = repo.list_all()

    enriched: list[dict[str, Any]] = []
    for env in envs:
        env_dict = dict(env)
        if env["project_id"]:
            proj = proj_repo.get_by_id(env["project_id"])
            env_dict["project_name"] = proj["name"] if proj else "-"
        else:
            env_dict["project_name"] = "-"
        enriched.append(env_dict)

    format_env_list(enriched)
    conn.close()

