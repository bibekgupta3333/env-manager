"""Lifecycle commands — create, install, uninstall, update, remove,
restore, clone, export_spec, import_spec, shell, activate."""

import json
import os
import re
import shlex
import subprocess as sp
import sys
from pathlib import Path

import typer

from env_manager.adapters.registry import AdapterRegistry
from env_manager.cli.db_utils import ensure_db_dir, get_db_path
from env_manager.cli.resolve import resolve_env
from env_manager.models.states import ManagementState
from env_manager.platform import safe_rmtree
from env_manager.storage.database import (
    close_connection,
    get_connection,
    init_db,
)
from env_manager.storage.repo_env import EnvironmentRepository
from env_manager.storage.repo_project import ProjectRepository
from env_manager.storage.repo_snapshot import SnapshotRepository

app = typer.Typer(help="Create and manage environments")


@app.command()
def create(
    lang_version: str = typer.Argument(
        ..., help="Language and version, e.g. python@3.12"
    ),
    path: str = typer.Argument(".", help="Target path"),
    tool: str = typer.Option(
        "", "--tool", help="Specific tool: venv, poetry, nvm"
    ),
    dry_run: bool = typer.Option(False, "--dry-run", help="Preview"),
    confirm: bool = typer.Option(False, "--confirm", help="Execute"),
) -> None:
    """Create a new environment.

    Examples:

      envs lifecycle create python@3.12 . --confirm

      envs lifecycle create node@20 ~/my-project --tool nvm --confirm

      envs lifecycle create python@3.12 --dry-run
    """
    if not dry_run and not confirm:
        typer.echo("Use --confirm to execute, or --dry-run to preview")
        raise typer.Exit(1)

    language, _, version = lang_version.partition("@")
    if not language or not version:
        typer.echo("Usage: envs lifecycle create <lang@version> [path]")
        raise typer.Exit(1)

    if not re.match(r"^[\w\.\-\*x]+$", version):
        typer.echo(f"Invalid version: {version}")
        raise typer.Exit(1)

    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    try:
        registry = AdapterRegistry(conn)
        adapters = registry.get_for_language(language)
        if tool:
            adapters = [a for a in adapters if tool in a.name]
        # Prefer adapters that support create() over detection-only ones
        createable = [
            a
            for a in adapters
            if a.name.split(".")[-1] in ("venv", "virtualenv")
        ]
        if createable:
            adapters = createable
        if not adapters:
            typer.echo(f"no adapter for {language}")
            raise typer.Exit(1)

        adapter = adapters[0]
        target = Path(path).resolve()
        if not target.name.startswith("."):
            target = target / ".venv"

        if target.exists() and not dry_run:
            typer.echo(f"Directory already exists: {target}")
            raise typer.Exit(1)

        if dry_run:
            typer.echo(f"Would create {adapter.name} env at {target}")
            return

        try:
            meta = adapter.create(target, {"version": version})
        except NotImplementedError:
            typer.echo(f"Adapter {adapter.name} does not support create")
            raise typer.Exit(1)

        proj_repo = ProjectRepository(conn)
        env_repo = EnvironmentRepository(conn)

        proj_id, _ = proj_repo.get_or_create(
            name=target.parent.name, path=str(target.parent)
        )
        env_repo.insert(
            project_id=proj_id,
            adapter=adapter.name,
            env_type=adapter.env_type,
            path=str(target),
            language=language,
            version=meta.version,
            tool=meta.tool,
            size_bytes=meta.size_bytes,
            management_state=ManagementState.READY,
        )
        typer.echo(f"Created: {target} ({adapter.name})")
    finally:
        conn.close()
        close_connection(db_path)


@app.command()
def install(
    project: str = typer.Argument(..., help="Project name or path"),
    packages: list[str] = typer.Argument(..., help="Packages to install"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    confirm: bool = typer.Option(False, "--confirm"),
) -> None:
    """Install packages into an environment."""
    if not dry_run and not confirm:
        typer.echo("Use --confirm to execute, or --dry-run to preview")
        raise typer.Exit(1)

    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    try:
        env = resolve_env(conn, project)
        if not env:
            typer.echo(f"Not found: {project}")
            raise typer.Exit(1)

        registry = AdapterRegistry(conn)
        adapter = registry.get(env["adapter"])
        if not adapter:
            typer.echo(f"no adapter: {env['adapter']}")
            raise typer.Exit(1)

        if dry_run:
            typer.echo(f"Would install {len(packages)} packages")
            return

        adapter.install(Path(env["path"]), list(packages))
        typer.echo(f"Installed {len(packages)} packages")
    finally:
        conn.close()
        close_connection(db_path)


@app.command()
def uninstall(
    project: str = typer.Argument(..., help="Project name or path"),
    packages: list[str] = typer.Argument(..., help="Packages to remove"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    confirm: bool = typer.Option(False, "--confirm"),
) -> None:
    """Remove packages from an environment."""
    if not dry_run and not confirm:
        typer.echo("Use --confirm to execute, or --dry-run to preview")
        raise typer.Exit(1)

    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    try:
        env = resolve_env(conn, project)
        if not env:
            typer.echo(f"Not found: {project}")
            raise typer.Exit(1)

        registry = AdapterRegistry(conn)
        adapter = registry.get(env["adapter"])
        if not adapter:
            typer.echo(f"no adapter: {env['adapter']}")
            raise typer.Exit(1)

        if dry_run:
            typer.echo(f"Would remove {len(packages)} packages")
            return

        adapter.uninstall(Path(env["path"]), list(packages))
        typer.echo(f"Removed {len(packages)} packages")
    finally:
        conn.close()
        close_connection(db_path)


@app.command()
def update(
    project: str = typer.Argument(..., help="Project name or path"),
    packages: list[str] = typer.Argument(
        None, help="Packages (omit for --all)"
    ),
    all_pkgs: bool = typer.Option(False, "--all", help="Update all packages"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    confirm: bool = typer.Option(False, "--confirm"),
) -> None:
    """Update packages."""
    if not dry_run and not confirm:
        typer.echo("Use --confirm to execute, or --dry-run to preview")
        raise typer.Exit(1)

    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    try:
        env = resolve_env(conn, project)
        if not env:
            typer.echo(f"Not found: {project}")
            raise typer.Exit(1)

        registry = AdapterRegistry(conn)
        adapter = registry.get(env["adapter"])
        if not adapter:
            typer.echo(f"no adapter: {env['adapter']}")
            raise typer.Exit(1)

        if dry_run:
            typer.echo("Would update packages")
            return

        adapter.update(Path(env["path"]), list(packages) if packages else None)
        typer.echo("Updated packages")
    finally:
        conn.close()
        close_connection(db_path)


@app.command()
def remove(
    project: str = typer.Argument(..., help="Project name or path"),
    snapshot: bool = typer.Option(
        False, "--snapshot", help="Save blueprint first"
    ),
    dry_run: bool = typer.Option(False, "--dry-run"),
    confirm: bool = typer.Option(False, "--confirm"),
) -> None:
    """Delete an environment.

    Examples:

      envs lifecycle remove my-project --confirm

      envs lifecycle remove .venv --snapshot --confirm

      envs lifecycle remove my-project --dry-run
    """
    if not dry_run and not confirm:
        typer.echo("Use --confirm to execute, or --dry-run to preview")
        raise typer.Exit(1)

    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    try:
        env = resolve_env(conn, project)
        if not env:
            typer.echo(f"Not found: {project}")
            raise typer.Exit(1)

        if dry_run:
            typer.echo(
                f"Would {'snapshot + ' if snapshot else ''}"
                f"remove: {env['path']}"
            )
            return

        snapshot_created = False
        if snapshot:
            registry = AdapterRegistry(conn)
            adapter = registry.get(env["adapter"])
            if adapter:
                try:
                    fr = adapter.freeze(Path(env["path"]))
                    SnapshotRepository(conn).insert(
                        env_id=env["id"],
                        frozen_deps={p.name: p.version for p in fr.packages},
                        raw_lockfile=fr.raw_content,
                        lockfile_format=fr.format,
                    )
                    snapshot_created = True
                except (OSError, ValueError):
                    typer.echo("Warning: snapshot freeze failed, env deleted")

        env_repo = EnvironmentRepository(conn)
        env_repo.update_state(
            env["id"],
            (
                ManagementState.SNAPSHOTTED
                if snapshot_created
                else ManagementState.DELETED
            ),
        )

        env_path = Path(env["path"])
        if env_path.exists():
            safe_rmtree(env_path)

        typer.echo(f"Removed: {env['path']}")
        if snapshot:
            typer.echo(f"Restore: envs lifecycle restore {project}")
    finally:
        conn.close()
        close_connection(db_path)


@app.command()
def restore(
    project: str = typer.Argument(..., help="Project name"),
    snapshot_version: int = typer.Option(
        None, "--snapshot", "-s", help="Version to restore"
    ),
    dry_run: bool = typer.Option(False, "--dry-run"),
    confirm: bool = typer.Option(False, "--confirm"),
) -> None:
    """Restore from a snapshot."""
    if not dry_run and not confirm:
        typer.echo("Use --confirm to execute, or --dry-run to preview")
        raise typer.Exit(1)

    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    try:
        snap_repo = SnapshotRepository(conn)
        env_repo = EnvironmentRepository(conn)

        all_snaps = snap_repo.list_all()
        matching = [
            s for s in all_snaps if _env_matches_snap(conn, s, project)
        ]

        if not matching:
            typer.echo(f"no snapshots for: {project}")
            raise typer.Exit(1)

        target = matching[0]
        if snapshot_version:
            found = [s for s in matching if s["version"] == snapshot_version]
            if not found:
                typer.echo(f"Version {snapshot_version} not found")
                raise typer.Exit(1)
            target = found[0]

        if dry_run:
            deps = json.loads(target["frozen_deps"])
            typer.echo(f"Would restore {len(deps)} packages")
            return

        env = env_repo.get_by_id(target["env_id"])
        if not env:
            typer.echo("Original env record not found")
            raise typer.Exit(1)

        registry = AdapterRegistry(conn)
        adapter = registry.get(env["adapter"])
        if not adapter:
            typer.echo(f"no adapter: {env['adapter']}")
            raise typer.Exit(1)

        deps = json.loads(target["frozen_deps"])
        adapter.create(Path(env["path"]), {"version": env["version"]})
        adapter.install(Path(env["path"]), list(deps.keys()))
        env_repo.update_state(env["id"], ManagementState.READY)
        typer.echo(f"Restored: {project} ({len(deps)} packages)")
    finally:
        conn.close()
        close_connection(db_path)


@app.command()
def clone(
    source: str = typer.Argument(..., help="Source project"),
    destination: str = typer.Argument(..., help="Destination path"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    confirm: bool = typer.Option(False, "--confirm"),
) -> None:
    """Clone an environment."""
    if not dry_run and not confirm:
        typer.echo("Use --confirm to execute, or --dry-run to preview")
        raise typer.Exit(1)

    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    try:
        env = resolve_env(conn, source)
        if not env:
            typer.echo(f"Not found: {source}")
            raise typer.Exit(1)

        if dry_run:
            typer.echo(f"Would clone to {destination}")
            return

        registry = AdapterRegistry(conn)
        adapter = registry.get(env["adapter"])
        if not adapter:
            typer.echo(f"no adapter: {env['adapter']}")
            raise typer.Exit(1)

        adapter.clone(Path(env["path"]), Path(destination).resolve())
        typer.echo(f"Cloned to {destination}")
    finally:
        conn.close()
        close_connection(db_path)


@app.command()
def export_spec(
    project: str = typer.Argument(..., help="Project name or path"),
    output: str = typer.Option(None, "--output", "-o", help="Output file"),
) -> None:
    """Export environment blueprint."""
    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    try:
        env = resolve_env(conn, project)
        if not env:
            typer.echo(f"Not found: {project}")
            raise typer.Exit(1)

        registry = AdapterRegistry(conn)
        adapter = registry.get(env["adapter"])
        packages = adapter.get_packages(Path(env["path"])) if adapter else []

        spec = {
            "version": 1,
            "language": env["language"],
            "tool": env["tool"],
            "version_req": env["version"],
            "packages": {p.name: p.version for p in packages},
        }
        text = json.dumps(spec, indent=2)
        if output:
            output_path = Path(output)
            if not output_path.resolve().parent.exists():
                typer.echo(
                    f"Output directory does not exist: {output_path.parent}"
                )
                raise typer.Exit(1)
            output_path.write_text(text)
            typer.echo(f"Exported to {output}")
        else:
            typer.echo(text)
    finally:
        conn.close()
        close_connection(db_path)


@app.command()
def import_spec(
    spec_file: str = typer.Argument(..., help="Path to spec JSON"),
    path: str = typer.Argument(".", help="Target directory"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    confirm: bool = typer.Option(False, "--confirm"),
) -> None:
    """Import from an exported spec."""
    if not dry_run and not confirm:
        typer.echo("Use --confirm to execute, or --dry-run to preview")
        raise typer.Exit(1)

    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    try:
        spec_path = Path(spec_file)
        if not spec_path.exists() or not spec_path.is_file():
            typer.echo(f"File not found: {spec_file}")
            raise typer.Exit(1)
        try:
            spec = json.loads(spec_path.read_text())
        except FileNotFoundError:
            typer.echo(f"File not found: {spec_file}")
            raise typer.Exit(1)
        except json.JSONDecodeError as e:
            typer.echo(f"Invalid JSON in {spec_file}: {e}")
            raise typer.Exit(1)

        lang = spec.get("language")
        version = spec.get("version_req")
        if not lang or not version:
            typer.echo("Spec must contain 'language' and 'version_req' fields")
            raise typer.Exit(1)
        target = Path(path).resolve()
        if not target.name.startswith("."):
            target = target / ".venv"

        if dry_run:
            typer.echo(
                f"Would create {lang}@{version} "
                f"at {target} ({len(spec['packages'])} pkgs)"
            )
            return

        registry = AdapterRegistry(conn)
        adapters = registry.get_for_language(lang)
        tool = spec.get("tool", "")
        if tool:
            matched = [a for a in adapters if tool in a.name]
            if matched:
                adapters = matched
        if not adapters:
            typer.echo(f"no adapter for {lang}")
            raise typer.Exit(1)

        adapter = adapters[0]
        adapter.create(target, {"version": version})
        adapter.install(target, list(spec["packages"].keys()))
        typer.echo(f"Imported {lang}@{version} at {target}")
    finally:
        conn.close()
        close_connection(db_path)


@app.command()
def shell(
    project: str = typer.Argument(..., help="Project name or path"),
) -> None:
    """Spawn a subshell with env activated."""
    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    try:
        env = resolve_env(conn, project)
        if not env:
            typer.echo(f"Not found: {project}")
            raise typer.Exit(1)

        env_path = Path(env["path"])
        lang = env["language"]

        if lang == "python":
            activate_script = env_path / "bin" / "activate"
            if activate_script.exists():
                shell_bin = os.environ.get("SHELL", "/bin/bash")
                typer.echo(f"Spawning {shell_bin}...")
                sp.run(
                    [
                        shell_bin,
                        "-c",
                        f"source {shlex.quote(str(activate_script))};"
                        f" exec {shell_bin}",
                    ]
                )
                return

        typer.echo(f"no shell support for {lang}")
    finally:
        conn.close()
        close_connection(db_path)


@app.command()
def activate(
    project: str = typer.Argument(..., help="Project name or path"),
) -> None:
    """Print eval-able activation.

    Usage: eval \"$(envs lifecycle activate <project>)\"
    """
    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    try:
        env = resolve_env(conn, project)
        if not env:
            if sys.stdout.isatty():
                typer.echo(f"Environment not found: {project}", err=True)
                typer.echo("")
                typer.echo("To discover environments, run: envs scan")
            else:
                typer.echo("echo 'Environment not found' >&2; return 1")
            raise typer.Exit(1)

        lang = env["language"]
        env_path = Path(env["path"])
        activate_line = ""

        if lang == "python":
            if os.name == "nt":
                bat = env_path / "Scripts" / "activate.bat"
                ps1 = env_path / "Scripts" / "Activate.ps1"
                if bat.exists():
                    activate_line = str(bat)
                elif ps1.exists():
                    activate_line = (
                        "powershell -ExecutionPolicy Bypass -File" f" {ps1}"
                    )
            else:
                activate_script = env_path / "bin" / "activate"
                if activate_script.exists():
                    activate_line = f"source {activate_script}"
        elif lang == "node":
            bin_dir = "Scripts" if os.name == "nt" else "bin"
            activate_line = (
                f"set PATH={env_path / bin_dir};%PATH%"
                if os.name == "nt"
                else f"export PATH='{env_path / bin_dir}:$PATH'"
            )

        if not activate_line:
            msg = f"echo 'No activation support for {lang}' >&2; return 1"
            typer.echo(msg)
            raise typer.Exit(1)

        # TTY detection: if user ran this interactively, show help
        if sys.stdout.isatty():
            typer.echo("  To activate in your current shell, run:")
            typer.echo("")
            typer.echo(f'    eval "$(envs lifecycle activate {project})"')
            typer.echo("")
            typer.echo("  Or spawn a subshell:")
            typer.echo("")
            typer.echo(f"    envs lifecycle shell {project}")
            typer.echo("")
            typer.echo(f"  The activation command for {lang} is:")
            typer.echo(f"    {activate_line}")
        else:
            # Non-TTY: output the eval-able command directly
            typer.echo(activate_line)
    finally:
        conn.close()
        close_connection(db_path)


# ── helpers ────────────────────────────────────────────


def _env_matches_snap(conn, snap, identifier):
    env_repo = EnvironmentRepository(conn)
    proj_repo = ProjectRepository(conn)
    env = env_repo.get_by_id(snap["env_id"])
    if not env:
        return False
    # Check by env path
    if env["path"] == identifier:
        return True
    # Check by resolved path (macOS /tmp → /private/tmp)
    resolved = str(Path(identifier).resolve())
    if env["path"] == resolved or resolved in env["path"]:
        return True
    pid = env["project_id"]
    if pid:
        proj = proj_repo.get_by_id(pid)
        if proj:
            # Check by project name or path
            if proj["name"] == identifier:
                return True
            if proj["path"] == identifier or proj["path"] == resolved:
                return True
    return False
