"""CLI formatters using Rich."""

from __future__ import annotations

import json
import sys
from typing import TYPE_CHECKING

from rich.console import Console
from rich.table import Table

if TYPE_CHECKING:
    from env_manager.models.types import EnvRowDict

console = Console()

_HEALTH_COLORS: dict[str, str] = {
    "healthy": "green",
    "degraded": "yellow",
    "broken": "red",
}


def format_env_list(
    envs: list[EnvRowDict],
    *,
    by_project: bool = False,
    json_output: bool = False,
) -> None:
    if not envs:
        if json_output:
            sys.stdout.write(json.dumps({"environments": []}) + "\n")
        else:
            console.print("[dim]No environments found.[/dim]")
        return

    if json_output:
        sys.stdout.write(
            json.dumps({"environments": envs, "count": len(envs)}) + "\n"
        )
        return

    table = Table(title="Environments")
    table.add_column("Project", style="cyan")
    table.add_column("Language", style="green")
    table.add_column("Version")
    table.add_column("Size")
    table.add_column("State")
    table.add_column("Path", style="dim")

    current_project = None
    for env in envs:
        proj_name = env.get("project_name", "-")
        pin = " [yellow]\u2605[/yellow]" if env.get("is_pinned") else ""
        display_name = proj_name + pin

        if by_project and proj_name != "-" and proj_name != current_project:
            if current_project is not None:
                table.add_section()
            current_project = proj_name

        table.add_row(
            display_name,
            env.get("language", "-"),
            env.get("version", "-"),
            _format_size(env.get("size_bytes", 0)),
            env.get("management_state", "-"),
            env.get("path", "-"),
        )

    console.print(table)


def format_env_info(
    env: EnvRowDict, *, json_output: bool = False
) -> None:
    if json_output:
        sys.stdout.write(json.dumps(env) + "\n")
        return

    console.print(
        f"[bold cyan]{env.get('project_name', 'Unknown')}[/bold cyan]"
    )
    console.print(f"  Language:  {env.get('language')} {env.get('version')}")
    console.print(f"  Tool:      {env.get('tool')}")
    console.print(f"  Size:      {_format_size(env.get('size_bytes', 0))}")
    console.print(f"  State:     {env.get('management_state')}")
    console.print(f"  Path:      {env.get('path')}")
    health = env.get("last_health_result")
    if health:
        color = _HEALTH_COLORS.get(health, "")
        console.print(
            f"  Health:    [{color}]{health}[/{color}]"
        )


def _format_size(size_bytes: int) -> str:
    if size_bytes >= 1_000_000_000:
        return f"{size_bytes / 1_000_000_000:.1f} GB"
    if size_bytes >= 1_000_000:
        return f"{size_bytes / 1_000_000:.1f} MB"
    if size_bytes >= 1_000:
        return f"{size_bytes / 1_000:.1f} KB"
    return f"{size_bytes} B"
