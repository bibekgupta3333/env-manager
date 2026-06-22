"""Shell hook commands — install/uninstall auto-activation on cd."""

import os
from pathlib import Path

import typer

from env_manager.cli.db_utils import ensure_db_dir, get_db_path
from env_manager.platform import is_windows
from env_manager.storage.database import (
    close_connection,
    get_connection,
    init_db,
)

app = typer.Typer(help="Shell hook management for auto-detection on cd")

BASH_HOOK = """
# env-manager auto-detect hook
__envs_hook() {
    local d="$(pwd)"
    if [ -n "$ENVS_LAST_DIR" ] && [ "$ENVS_LAST_DIR" = "$d" ]; then return; fi
    export ENVS_LAST_DIR="$d"
    if command -v envs >/dev/null 2>&1; then
        envs hook --ping "$d" 2>/dev/null &
    fi
}
if [ -n "$PS1" ]; then
    PROMPT_COMMAND="__envs_hook${PROMPT_COMMAND:+;$PROMPT_COMMAND}"
fi
"""

PWSH_HOOK = """
# env-manager auto-detect hook
$env:ENVS_LAST_DIR = ""
function prompt {
    $d = (Get-Location).Path
    if ($d -ne $env:ENVS_LAST_DIR) {
        $env:ENVS_LAST_DIR = $d
        if (Get-Command envs -ErrorAction SilentlyContinue) {
            Start-Job -ScriptBlock { envs hook --ping $using:d } | Out-Null
        }
    }
    "PS $($executionContext.SessionState.Path.CurrentLocation)$('>' * ($nestedPromptLevel + 1)) "
}
"""

CMD_HOOK = """
@echo off
REM env-manager auto-detect hook
if defined ENVS_LAST_DIR (
    for /f "delims=" %%i in ('cd') do if "%ENVS_LAST_DIR%"=="%%i" goto :eof
)
for /f "delims=" %%i in ('cd') do set ENVS_LAST_DIR=%%i
where envs >nul 2>&1 && start /b envs hook --ping "%ENVS_LAST_DIR%"
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
        typer.echo("  envs hook --install     Show hook script")
        typer.echo("  envs hook --uninstall   Removal instructions")
        typer.echo("")
        typer.echo(
            "Hooks are opt-in. We never modify your shell config automatically."
        )


def _detect_shell() -> tuple[str, Path]:
    """Detect current shell and its config file."""
    if is_windows():
        shell = os.environ.get("SHELL", "")
        if "powershell" in shell.lower() or "pwsh" in shell.lower():
            profile = (
                Path(os.environ.get("USERPROFILE", str(Path.home())))
                / "Documents"
                / "PowerShell"
                / "Microsoft.PowerShell_profile.ps1"
            )
            return "powershell", profile
        return "cmd", Path.home() / "cmd_autorun.cmd"

    shell_bin = os.environ.get("SHELL", "/bin/bash")
    shell = Path(shell_bin).name
    if "zsh" in shell:
        return "zsh", Path.home() / ".zshrc"
    if "fish" in shell:
        return "fish", Path.home() / ".config" / "fish" / "config.fish"
    return "bash", Path.home() / ".bashrc"


def _do_install() -> None:
    shell, rc_file = _detect_shell()

    if shell in ("bash", "zsh", "fish"):
        hook_script = BASH_HOOK.strip()
    elif shell == "powershell":
        hook_script = PWSH_HOOK.strip()
    else:
        hook_script = CMD_HOOK.strip()

    typer.echo(f"Detected shell: {shell}")
    typer.echo(f"Config file:   {rc_file}")
    typer.echo("")
    typer.echo(
        "Add the following to your shell config "
        "to enable auto-detection on cd:"
    )
    typer.echo("")
    typer.echo("```")
    typer.echo(hook_script)
    typer.echo("```")
    typer.echo("")
    if shell in ("bash", "zsh"):
        typer.echo(
            f"To add: cat >> {rc_file} << 'EOF'  # then paste the hook, then EOF"
        )
    elif shell == "powershell":
        typer.echo(f"To add: notepad {rc_file}")
    elif shell == "fish":
        typer.echo(
            "Fish uses conf.d instead. "
            "Create ~/.config/fish/conf.d/envs.fish"
        )
    else:
        typer.echo(f"Add to your shell startup script: {rc_file}")
    typer.echo("Then restart your shell.")


def _do_uninstall() -> None:
    shell, rc_file = _detect_shell()
    typer.echo(
        f"To remove the hook, edit {rc_file} "
        f"and delete lines between '# env-manager' markers."
    )


def _handle_ping(directory: str) -> None:
    """Internal: called by shell hook on cd."""
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
