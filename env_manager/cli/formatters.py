"""CLI formatters using Rich."""

from __future__ import annotations

from typing import Any

from rich.console import Console
from rich.table import Table

console = Console()


def format_env_list(envs: list[dict[str, Any]]) -> None:
    if not envs:
        console.print("[dim]No environments found.[/dim]")
        return

    table = Table(title="Environments")
    table.add_column("Project", style="cyan")
    table.add_column("Language", style="green")
    table.add_column("Version")
    table.add_column("Size")
    table.add_column("State")
    table.add_column("Path", style="dim")

    for env in envs:
        table.add_row(
            env.get("project_name", "-"),
            env.get("language", "-"),
            env.get("version", "-"),
            _format_size(env.get("size_bytes", 0)),
            env.get("management_state", "-"),
            env.get("path", "-"),
        )

    console.print(table)


def format_env_info(env: dict[str, Any]) -> None:
    console.print(f"[bold cyan]{env.get('project_name', 'Unknown')}[/bold cyan]")
    console.print(f"  Language:  {env.get('language')} {env.get('version')}")
    console.print(f"  Tool:      {env.get('tool')}")
    console.print(f"  Size:      {_format_size(env.get('size_bytes', 0))}")
    console.print(f"  State:     {env.get('management_state')}")
    console.print(f"  Path:      {env.get('path')}")
    if env.get("last_health_result"):
        color = {"healthy": "green", "degraded": "yellow", "broken": "red"}.get(
            env["last_health_result"], ""
        )
        console.print(f"  Health:    [{color}]{env['last_health_result']}[/{color}]")


def _format_size(size_bytes: int) -> str:
    if size_bytes >= 1_000_000_000:
        return f"{size_bytes / 1_000_000_000:.1f} GB"
    if size_bytes >= 1_000_000:
        return f"{size_bytes / 1_000_000:.1f} MB"
    if size_bytes >= 1_000:
        return f"{size_bytes / 1_000:.1f} KB"
    return f"{size_bytes} B"
