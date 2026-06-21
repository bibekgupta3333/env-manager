"""Shell hook commands — install/uninstall auto-activation on cd."""

from pathlib import Path

import typer

from env_manager.cli.db_utils import ensure_db_dir, get_db_path
from env_manager.storage.database import (
    close_connection,
    get_connection,
    init_db,
)

app = typer.Typer(help="Shell hook management for auto-detection on cd")

HOOK_SCRIPT = r"""
# env-manager auto-detect hook — notifies daemon on cd into project dirs
__envs_hook() {
    local last_dir="$HOME/.env-manager/last_dir"
    local current="$(pwd)"
    if [ -f "$last_dir" ] && [ "$(cat "$last_dir")" = "$current" ]; then
        return
    fi
    echo "$current" > "$last_dir"
    # Notify daemon if running
    if command -v envs >/dev/null 2>&1; then
        envs hook ping "$current" 2>/dev/null &
    fi
}
# Only activate in interactive shells
if [ -n "$PS1" ]; then
    # Run on prompt instead of every cd (lighter)
    PROMPT_COMMAND="__envs_hook${PROMPT_COMMAND:+;$PROMPT_COMMAND}"
fi
"""


@app.callback(invoke_without_command=True)
def hook(
    install: bool = typer.Option(
        False, "--install", help="Generate hook script for your shell"
    ),
    uninstall: bool = typer.Option(
        False, "--uninstall", help="Remove hook from shell config"
    ),
    ping: str = typer.Option(
        None, "--ping", hidden=True, help="Internal: notify daemon of cd"
    ),
) -> None:
    """Manage shell hooks for auto-detecting environments on cd."""
    if ping:
        _handle_ping(ping)
        return

    if install:
        _do_install()
    elif uninstall:
        _do_uninstall()
    else:
        typer.echo(
            "Shell hooks auto-detect environments when you cd into a project."
        )
        typer.echo("")
        typer.echo(
            "  envs hook --install     Generate and show the hook script"
        )
        typer.echo("  envs hook --uninstall   Remove hook from shell config")
        typer.echo("")
        typer.echo(
            "Hooks are opt-in. "
            "We never modify your shell config automatically."
        )


def _do_install() -> None:
    shell = Path(__import__("os").environ.get("SHELL", "/bin/bash")).name
    rc_file = Path.home() / f".{shell}rc"

    typer.echo(f"Detected shell: {shell}")
    typer.echo(f"Config file:   {rc_file}")
    typer.echo("")
    typer.echo(
        "Add the following to your shell config "
        "to enable auto-detection on cd:"
    )
    typer.echo("")
    typer.echo("```bash")
    typer.echo(HOOK_SCRIPT.strip())
    typer.echo("```")
    typer.echo("")
    typer.echo(
        f"To add automatically, run: envs hook --install | tee -a {rc_file}"
    )
    typer.echo("Then restart your shell or run: source " + str(rc_file))


def _do_uninstall() -> None:
    shell = Path(__import__("os").environ.get("SHELL", "/bin/bash")).name
    rc_file = Path.home() / f".{shell}rc"

    typer.echo(f"To remove the hook, edit {rc_file} and delete lines between:")
    typer.echo("  # env-manager auto-detect hook")
    typer.echo("  ...")
    typer.echo("  # end env-manager hook")
    typer.echo("")
    typer.echo(
        f"Or run: grep -v 'env-manager' {rc_file} "
        f"> {rc_file}.tmp && mv {rc_file}.tmp {rc_file}"
    )


def _handle_ping(directory: str) -> None:
    """Internal: called by shell hook on cd. Notifies daemon if running."""
    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)
    try:
        from env_manager.storage.repo_env import EnvironmentRepository
        from env_manager.storage.repo_project import ProjectRepository

        env_repo = EnvironmentRepository(conn)
        proj_repo = ProjectRepository(conn)
        resolved = str(Path(directory).resolve())
        env = env_repo.get_by_path(resolved)
        if env:
            env_repo.touch(env["id"])
        proj = proj_repo.get_by_path(resolved)
        if proj:
            proj_repo.touch(proj["id"])
    except Exception:
        pass
    finally:
        conn.close()
        close_connection(db_path)
