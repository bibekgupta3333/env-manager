"""List command — show tracked environments."""

from __future__ import annotations

import typer

from env_manager.cli.db_utils import ensure_db_dir, get_db_path
from env_manager.cli.formatters import format_env_list
from env_manager.models.types import EnvRowDict
from env_manager.storage.database import get_connection, init_db
from env_manager.storage.repo_env import EnvironmentRepository
from env_manager.storage.repo_project import ProjectRepository

app = typer.Typer()


@app.callback(invoke_without_command=True)
def list_envs(
    by_project: bool = typer.Option(
        False, "--by-project", help="Group by project"
    ),
    stale: bool = typer.Option(False, "--stale", help="Show only stale"),
    orphaned: bool = typer.Option(
        False, "--orphaned", help="Show only orphaned"
    ),
    language: str = typer.Option(None, "--lang", help="Filter by language"),
    limit: int = typer.Option(
        0, "--limit", help="Maximum number of environments to show"
    ),
    offset: int = typer.Option(
        0, "--offset", help="Number of environments to skip"
    ),
    json_output: bool = typer.Option(
        False, "--json", help="Output in JSON format (for scripting)"
    ),
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

    enriched: list[EnvRowDict] = []
    for env in envs:
        env_dict: EnvRowDict = dict(env)  # type: ignore[assignment]
        if env["project_id"]:
            proj = proj_repo.get_by_id(env["project_id"])
            env_dict["project_name"] = proj["name"] if proj else "-"
            env_dict["is_pinned"] = bool(proj["is_pinned"]) if proj else False
        else:
            env_dict["project_name"] = "-"
            env_dict["is_pinned"] = False
        enriched.append(env_dict)

    if by_project:
        enriched.sort(
            key=lambda e: (e.get("project_name", ""), e.get("language", ""))
        )

    if limit > 0 or offset > 0:
        enriched = (
            enriched[offset : offset + limit]
            if limit > 0
            else enriched[offset:]
        )

    format_env_list(enriched, by_project=by_project, json_output=json_output)
    conn.close()
