"""Runtimes command — list global virtual environments."""

from __future__ import annotations

from typing import Any

import typer
from rich.table import Table

from env_manager.cli.db_utils import ensure_db_dir, get_db_path
from env_manager.cli.formatters import _format_size as fmt_size
from env_manager.cli.formatters import console
from env_manager.storage.database import get_connection, init_db
from env_manager.storage.repo_env import EnvironmentRepository

_HEALTH_COLOR_MAP = {"healthy": "green", "broken": "red", "degraded": "yellow"}

app = typer.Typer()


@app.callback(invoke_without_command=True)
def runtimes(
    language: str = typer.Option(None, "--lang", help="Filter by language"),
    limit: int = typer.Option(0, "--limit", help="Max results"),
    json_output: bool = typer.Option(
        False, "--json", help="Output in JSON format"
    ),
) -> None:
    """List installed virtual environments (global runtimes)."""
    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    repo = EnvironmentRepository(conn)
    envs = repo.list_all()
    envs = [e for e in envs if e["env_type"] == "runtime"]
    if language:
        envs = [e for e in envs if e["language"] == language]
    if limit and limit > 0:
        envs = envs[:limit]

    enriched: list[dict[str, Any]] = []
    for env_row in envs:
        d: dict[str, Any] = dict(env_row)
        enriched.append(d)

    conn.close()

    if json_output:
        import json
        import sys

        sys.stdout.write(
            json.dumps({"runtimes": enriched, "count": len(enriched)}) + "\n"
        )
        return

    if not enriched:
        console.print("[dim]No virtual environments found.[/dim]")
        return

    table = Table(title="Virtual Environments")
    table.add_column("Language", style="green")
    table.add_column("Version", style="cyan")
    table.add_column("Tool")
    table.add_column("Size")
    table.add_column("Health")
    table.add_column("Path", style="dim")

    for env in enriched:
        health = env.get("last_health_result") or "unchecked"
        health_color = _HEALTH_COLOR_MAP.get(health, "")
        health_text = (
            f"[{health_color}]{health}[/{health_color}]"
            if health_color else health
        )
        table.add_row(
            env.get("language", "-"),
            env.get("version", "-"),
            env.get("tool", "-"),
            fmt_size(env.get("size_bytes", 0)),
            health_text,
            env.get("path", "-"),
        )

    console.print(table)
