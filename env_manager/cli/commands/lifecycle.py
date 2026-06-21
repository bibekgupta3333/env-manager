"""Lifecycle commands — create, install, uninstall, update, delete, clone, export, import, shell, activate, restore."""

from pathlib import Path

import typer

from env_manager.adapters.registry import AdapterRegistry
from env_manager.cli.db_utils import ensure_db_dir, get_db_path
from env_manager.models.states import ManagementState
from env_manager.storage.database import close_connection, get_connection, init_db
from env_manager.storage.repo_activity import ActivityRepository
from env_manager.storage.repo_env import EnvironmentRepository
from env_manager.storage.repo_project import ProjectRepository
from env_manager.storage.repo_snapshot import SnapshotRepository

app = typer.Typer()


@app.callback(invoke_without_command=True)
def create(
    lang_version: str = typer.Argument(..., help="Language and version, e.g. python@3.12"),
    path: str = typer.Argument(".", help="Target path for the environment"),
    tool: str = typer.Option("", "--tool", help="Specific tool: venv, poetry, nvm, fnm, etc."),
    dry_run: bool = typer.Option(False, "--dry-run", help="Show what would happen"),
    confirm: bool = typer.Option(False, "--confirm", help="Confirm the creation"),
) -> None:
    """Create a new environment."""
    _lifecycle_guard(dry_run, confirm, "create")

    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    try:
        language, _, version = lang_version.partition("@")
        if not language or not version:
            typer.echo("Usage: envs create <lang@version> [path]")
            typer.echo("Example: envs create python@3.12")
            raise typer.Exit(1)

        registry = AdapterRegistry(conn)
        adapters = registry.get_for_language(language)
        if tool:
            adapters = [a for a in adapters if tool in a.name]

        if not adapters:
            typer.echo(f"No adapter found for: {language}")
            typer.echo(f"Available: {[a.name for a in registry.get_all_enabled()]}")
            raise typer.Exit(1)

        adapter = adapters[0]
        target = Path(path).resolve()
        if not target.name.endswith(".venv") and not target.name.startswith("."):
            target = target / ".venv"

        if dry_run:
            typer.echo(f"Would create {adapter.name} env at {target} (Python {version})")
            return

        try:
            meta = adapter.create(target, {"version": version})
            proj_repo = ProjectRepository(conn)
            env_repo = EnvironmentRepository(conn)
            activity_repo = ActivityRepository(conn)

            proj_id, _ = proj_repo.get_or_create(name=target.parent.name, path=str(target.parent))
            env_id = env_repo.insert(
                project_id=proj_id, adapter=adapter.name, env_type=adapter.env_type,
                path=str(target), language=adapter.name.split(".")[0],
                version=meta.version, tool=meta.tool, size_bytes=meta.size_bytes,
                management_state=ManagementState.READY,
            )
            activity_repo.log(event="created", env_id=env_id, project_id=proj_id)

            typer.echo(f"Created: {target}")
            typer.echo(f"  Language: {adapter.name} | Version: {meta.version} | Size: {meta.size_bytes} bytes")
        except NotImplementedError:
            typer.echo(f"Adapter {adapter.name} does not support create.")
            raise typer.Exit(1)
    finally:
        conn.close()
        close_connection(db_path)


@app.command()
def install(
    project: str = typer.Argument(..., help="Project name or env path"),
    packages: list[str] = typer.Argument(..., help="Packages to install"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    confirm: bool = typer.Option(False, "--confirm"),
) -> None:
    """Install packages into an environment."""
    _lifecycle_guard(dry_run, confirm, "install")

    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    try:
        env = _resolve_env(conn, project)
        if not env:
            typer.echo(f"Environment not found: {project}")
            raise typer.Exit(1)

        registry = AdapterRegistry(conn)
        adapter = registry.get(env["adapter"])
        if not adapter:
            typer.echo(f"Adapter not found: {env['adapter']}")
            raise typer.Exit(1)

        if dry_run:
            typer.echo(f"Would install {len(packages)} packages into {project}:")
            for pkg in packages:
                typer.echo(f"  {pkg}")
            return

        adapter.install(Path(env["path"]), packages)
        typer.echo(f"Installed {len(packages)} packages into {project}")
    finally:
        conn.close()
        close_connection(db_path)


@app.command()
def uninstall(
    project: str = typer.Argument(..., help="Project name or env path"),
    packages: list[str] = typer.Argument(..., help="Packages to remove"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    confirm: bool = typer.Option(False, "--confirm"),
) -> None:
    """Remove packages from an environment."""
    _lifecycle_guard(dry_run, confirm, "uninstall")

    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    try:
        env = _resolve_env(conn, project)
        if not env:
            typer.echo(f"Environment not found: {project}")
            raise typer.Exit(1)

        registry = AdapterRegistry(conn)
        adapter = registry.get(env["adapter"])
        if not adapter:
            typer.echo(f"Adapter not found: {env['adapter']}")
            raise typer.Exit(1)

        if dry_run:
            typer.echo(f"Would remove {len(packages)} packages from {project}")
            return

        adapter.uninstall(Path(env["path"]), packages)
        typer.echo(f"Removed {len(packages)} packages from {project}")
    finally:
        conn.close()
        close_connection(db_path)


@app.command()
def update(
    project: str = typer.Argument(..., help="Project name or env path"),
    packages: list[str] = typer.Argument(None, help="Specific packages to update (omit for --all)"),
    all_packages: bool = typer.Option(False, "--all", help="Update all packages"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    confirm: bool = typer.Option(False, "--confirm"),
) -> None:
    """Update packages in an environment."""
    _lifecycle_guard(dry_run, confirm, "update")

    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    try:
        env = _resolve_env(conn, project)
        if not env:
            typer.echo(f"Environment not found: {project}")
            raise typer.Exit(1)

        registry = AdapterRegistry(conn)
        adapter = registry.get(env["adapter"])
        if not adapter:
            typer.echo(f"Adapter not found: {env['adapter']}")
            raise typer.Exit(1)

        pkg_list = packages if packages else []
        if all_packages:
            pkg_list = []

        if dry_run:
            typer.echo(f"Would update {'all' if all_packages else len(pkg_list)} packages in {project}")
            return

        adapter.update(Path(env["path"]), pkg_list if pkg_list else None)
        typer.echo(f"Updated packages in {project}")
    finally:
        conn.close()
        close_connection(db_path)


@app.command()
def delete(
    project: str = typer.Argument(..., help="Project name or env path"),
    snapshot: bool = typer.Option(False, "--snapshot", help="Save blueprint before deleting"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    confirm: bool = typer.Option(False, "--confirm"),
) -> None:
    """Delete an environment."""
    _lifecycle_guard(dry_run, confirm, "delete")

    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    try:
        env = _resolve_env(conn, project)
        if not env:
            typer.echo(f"Environment not found: {project}")
            raise typer.Exit(1)

        if dry_run:
            action = "snapshot and remove" if snapshot else "delete"
            typer.echo(f"Would {action}: {env['path']}")
            return

        if snapshot:
            registry = AdapterRegistry(conn)
            adapter = registry.get(env["adapter"])
            if adapter:
                try:
                    freeze_result = adapter.freeze(Path(env["path"]))
                    snap_repo = SnapshotRepository(conn)
                    snap_repo.insert(
                        env_id=env["id"],
                        frozen_deps={p.name: p.version for p in freeze_result.packages},
                        raw_lockfile=freeze_result.raw_content,
                        lockfile_format=freeze_result.format,
                    )
                    typer.echo(f"Snapshot saved ({len(freeze_result.packages)} packages)")
                except Exception:
                    typer.echo("Warning: snapshot failed, deleting without snapshot")

        env_repo = EnvironmentRepository(conn)
        env_repo.update_state(env["id"], ManagementState.SNAPSHOTTED if snapshot else ManagementState.DELETED)

        # Try to delete the actual directory
        env_path = Path(env["path"])
        if env_path.exists():
            import shutil
            if snapshot or confirm:
                shutil.rmtree(env_path, ignore_errors=True)

        freed = env.get("size_bytes", 0)
        typer.echo(f"Deleted: {env['path']} (freed {_fmt_size(freed)})")
        if snapshot:
            typer.echo("Restore anytime: envs restore " + project)
    finally:
        conn.close()
        close_connection(db_path)


@app.command()
def restore(
    project: str = typer.Argument(..., help="Project name to restore"),
    snapshot_version: int = typer.Option(None, "--snapshot", "-s", help="Specific snapshot version"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    confirm: bool = typer.Option(False, "--confirm"),
) -> None:
    """Restore an environment from a snapshot."""
    _lifecycle_guard(dry_run, confirm, "restore")

    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    try:
        snap_repo = SnapshotRepository(conn)
        env_repo = EnvironmentRepository(conn)

        snapshots = snap_repo.list_all()
        snap_envs = [
            s for s in snapshots
            if _env_matches(conn, s["env_id"], project)
        ]

        if not snapshots:
            typer.echo(f"No snapshots found for: {project}")
            raise typer.Exit(1)

        target_snap = None
        if snapshot_version:
            target_snap = next((s for s in snap_envs if s["version"] == snapshot_version), None)
        else:
            target_snap = snap_envs[0]

        if not target_snap:
            typer.echo(f"Snapshot version {snapshot_version} not found")
            raise typer.Exit(1)

        if dry_run:
            import json
            deps = json.loads(target_snap["frozen_deps"])
            typer.echo(f"Would restore {len(deps)} packages for {project}")
            return

        # Rebuild env
        env = env_repo.get_by_id(target_snap["env_id"])
        if not env:
            typer.echo("Original environment record not found, cannot restore")
            raise typer.Exit(1)

        registry = AdapterRegistry(conn)
        adapter = registry.get(env["adapter"])
        if not adapter:
            typer.echo(f"Adapter {env['adapter']} not available")
            raise typer.Exit(1)

        env_path = Path(env["path"])
        import json
        deps = json.loads(target_snap["frozen_deps"])

        adapter.create(env_path, {"version": env["version"]})
        adapter.install(env_path, list(deps.keys()))

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
    """Clone an environment to a new path."""
    _lifecycle_guard(dry_run, confirm, "clone")

    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    try:
        env = _resolve_env(conn, source)
        if not env:
            typer.echo(f"Environment not found: {source}")
            raise typer.Exit(1)

        if dry_run:
            typer.echo(f"Would clone {env['path']} -> {destination}")
            return

        registry = AdapterRegistry(conn)
        adapter = registry.get(env["adapter"])
        if not adapter:
            typer.echo(f"Adapter not found: {env['adapter']}")
            raise typer.Exit(1)

        dest_path = Path(destination).resolve()
        adapter.clone(Path(env["path"]), dest_path)
        typer.echo(f"Cloned to: {dest_path}")
    finally:
        conn.close()
        close_connection(db_path)


@app.command()
def export_env(
    project: str = typer.Argument(..., help="Project name or env path"),
    output: str = typer.Option(None, "--output", "-o", help="Output file path"),
) -> None:
    """Export an environment blueprint as portable JSON."""
    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    try:
        env = _resolve_env(conn, project)
        if not env:
            typer.echo(f"Environment not found: {project}")
            raise typer.Exit(1)

        registry = AdapterRegistry(conn)
        adapter = registry.get(env["adapter"])
        packages = []
        if adapter:
            packages = adapter.get_packages(Path(env["path"]))

        import json
        spec = {
            "version": 1,
            "language": env["language"],
            "tool": env["tool"],
            "version_req": env["version"],
            "packages": {p.name: p.version for p in packages},
        }

        json_str = json.dumps(spec, indent=2)
        if output:
            Path(output).write_text(json_str)
            typer.echo(f"Exported to: {output}")
        else:
            typer.echo(json_str)
    finally:
        conn.close()
        close_connection(db_path)


@app.command()
def import_env(
    spec_file: str = typer.Argument(..., help="Path to env-manager spec JSON file"),
    path: str = typer.Argument(None, help="Target path for the new environment"),
    dry_run: bool = typer.Option(False, "--dry-run"),
    confirm: bool = typer.Option(False, "--confirm"),
) -> None:
    """Create an environment from an exported spec."""
    _lifecycle_guard(dry_run, confirm, "import")

    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    try:
        import json
        spec = json.loads(Path(spec_file).read_text())
        lang = spec["language"]
        version = spec["version_req"]

        target = Path(path or ".").resolve()
        if not target.name.startswith("."):
            target = target / ".venv"

        if dry_run:
            typer.echo(f"Would create {lang}@{version} env at {target}")
            typer.echo(f"Would install {len(spec['packages'])} packages")
            return

        registry = AdapterRegistry(conn)
        adapters = registry.get_for_language(lang)
        if not adapters:
            typer.echo(f"No adapter for {lang}")
            raise typer.Exit(1)

        adapter = adapters[0]
        adapter.create(target, {"version": version})
        adapter.install(target, list(spec["packages"].keys()))
        typer.echo(f"Imported: {lang}@{version} at {target}")
    finally:
        conn.close()
        close_connection(db_path)


@app.command()
def activate(
    project: str = typer.Argument(..., help="Project name or env path"),
) -> None:
    """Print eval-able activation for current shell.

    Usage: eval "$(envs activate <project>)"
    """
    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    try:
        env = _resolve_env(conn, project)
        if not env:
            typer.echo("echo 'Environment not found' >&2; return 1")
            raise typer.Exit(1)

        lang = env["language"]
        env_path = Path(env["path"])

        if lang == "python":
            activate_script = env_path / "bin" / "activate"
            if activate_script.exists():
                typer.echo(f"source {activate_script}")
            else:
                typer.echo("echo 'No activate script found' >&2; return 1")
        elif lang == "node":
            path_add = env_path / "bin" if env_path.name != "node_modules" else env_path
            typer.echo(f"export PATH='{path_add}:$PATH'")
        else:
            typer.echo(f"echo 'No activation support for {lang}' >&2; return 1")
    finally:
        conn.close()
        close_connection(db_path)


@app.command()
def shell(
    project: str = typer.Argument(..., help="Project name or env path"),
) -> None:
    """Spawn a subshell with the environment activated."""
    ensure_db_dir()
    db_path = get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    try:
        env = _resolve_env(conn, project)
        if not env:
            typer.echo(f"Environment not found: {project}")
            raise typer.Exit(1)

        registry = AdapterRegistry(conn)
        adapter = registry.get(env["adapter"])
        lang = env["language"]

        env_path = Path(env["path"])
        activate_cmd = _get_activate_command(lang, adapter, env_path)
        if not activate_cmd:
            typer.echo(f"No shell activation available for {lang}")
            raise typer.Exit(1)

        import os
        import subprocess
        shell_bin = os.environ.get("SHELL", "/bin/bash")
        typer.echo(f"Spawning {shell_bin} with {lang} env activated...")
        subprocess.run([shell_bin, "-c", f"source {activate_cmd}; exec {shell_bin}"])
    finally:
        conn.close()
        close_connection(db_path)


def _get_activate_command(lang: str, adapter, env_path: Path) -> str | None:
    """Return the shell activation command for a given environment."""
    if lang == "python":
        if (env_path / "bin" / "activate").exists():
            return str(env_path / "bin" / "activate")
        return None
    if lang == "node":
        path_add = env_path / "bin" if adapter and adapter.env_type == "global" else env_path / "node_modules" / ".bin"
        return str(path_add)
    return None


def _resolve_env(conn, identifier: str):
    """Resolve an environment by project name, path, or env path."""
    env_repo = EnvironmentRepository(conn)
    proj_repo = ProjectRepository(conn)

    env = env_repo.get_by_path(identifier)
    if env:
        return env

    proj = proj_repo.get_by_path(identifier)
    if not proj:
        all_projects = proj_repo.list_all()
        proj = next((p for p in all_projects if p["name"] == identifier), None)

    if proj:
        envs = env_repo.list_by_project(proj["id"])
        if envs:
            return envs[0]

    return None


def _env_matches(conn, env_id: int, identifier: str) -> bool:
    env_repo = EnvironmentRepository(conn)
    env = env_repo.get_by_id(env_id)
    if not env:
        return False
    if env["path"] == identifier:
        return True
    if env.get("project_id"):
        proj_repo = ProjectRepository(conn)
        proj = proj_repo.get_by_id(env["project_id"])
        if proj and (proj["name"] == identifier or proj["path"] == identifier):
            return True
    return False


def _lifecycle_guard(dry_run: bool, confirm: bool, operation: str) -> None:
    if not dry_run and not confirm:
        typer.echo(f"Use --confirm to execute {operation}, or --dry-run to preview")
        raise typer.Exit(1)


def _fmt_size(size_bytes: int) -> str:
    if size_bytes >= 1_000_000_000:
        return f"{size_bytes / 1_000_000_000:.1f} GB"
    if size_bytes >= 1_000_000:
        return f"{size_bytes / 1_000_000:.1f} MB"
    if size_bytes >= 1_000:
        return f"{size_bytes / 1_000:.1f} KB"
    return f"{size_bytes} B"
