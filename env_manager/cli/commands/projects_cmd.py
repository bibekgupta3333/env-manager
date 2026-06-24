"""Projects command — list local project environments."""

from __future__ import annotations

from typing import Any

import typer
from rich.table import Table

from env_manager.cli.db_utils import ensure_db_dir, get_db_path
from env_manager.cli.formatters import _format_size as fmt_size
from env_manager.cli.formatters import console
from env_manager.storage.database import get_connection, init_db
from env_manager.storage.repo_env import EnvironmentRepository
from env_manager.storage.repo_project import ProjectRepository

_HEALTH_COLOR_MAP = {"healthy": "green", "broken": "red", "degraded": "yellow"}

app = typer.Typer()


@app.callback(invoke_without_command=True)
def projects(
    language: str = typer.Option(None, "--lang", help="Filter by language"),
    by_project: bool = typer.Option(
        False, "--by-project", help="Group by project name"
    ),
    limit: int = typer.Option(0, "--limit", help="Max results"),
    json_output: bool = typer.Option(
        False, "--json", help="Output in JSON format"
    ),
) -> None:
    """List project environments with their associated runtime."""
    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    repo = EnvironmentRepository(conn)
    proj_repo = ProjectRepository(conn)
    envs = repo.list_all()
    envs = [e for e in envs if e["env_type"] == "project"]
    if language:
        envs = [e for e in envs if e["language"] == language]
    if limit and limit > 0:
        envs = envs[:limit]

    enriched: list[dict[str, Any]] = []
    for env_row in envs:
        d: dict[str, Any] = dict(env_row)
        if env_row["project_id"]:
            proj = proj_repo.get_by_id(env_row["project_id"])
            d["project_name"] = proj["name"] if proj else "-"
            d["is_pinned"] = bool(proj["is_pinned"]) if proj else False
        else:
            d["project_name"] = "-"
            d["is_pinned"] = False
        enriched.append(d)

    conn.close()

    if json_output:
        import json
        import sys

        sys.stdout.write(
            json.dumps({"projects": enriched, "count": len(enriched)}) + "\n"
        )
        return

    if not enriched:
        console.print("[dim]No project environments found.[/dim]")
        return

    if by_project:
        enriched.sort(
            key=lambda e: (e.get("project_name", ""), e.get("language", ""))
        )

    table = Table(title="Projects")
    table.add_column("Project", style="cyan")
    table.add_column("Runtime")
    table.add_column("Tool")
    table.add_column("Size")
    table.add_column("Health")
    table.add_column("Path", style="dim")

    current_project = None
    for env in enriched:
        proj_name = env.get("project_name", "-")
        pin = " [yellow]\u2605[/yellow]" if env.get("is_pinned") else ""
        display_name = proj_name + pin

        if by_project and proj_name != "-" and proj_name != current_project:
            if current_project is not None:
                table.add_section()
            current_project = proj_name

        lang = env.get("language", "-")
        ver = env.get("version", "-")
        tool = env.get("tool", "-")
        runtime = f"{lang} {ver}" if ver != "-" else lang

        health = env.get("last_health_result") or "unchecked"
        health_color = _HEALTH_COLOR_MAP.get(health, "")
        health_text = (
            f"[{health_color}]{health}[/{health_color}]"
            if health_color else health
        )

        table.add_row(
            display_name,
            runtime,
            tool,
            fmt_size(env.get("size_bytes", 0)),
            health_text,
            env.get("path", "-"),
        )

    console.print(table)
