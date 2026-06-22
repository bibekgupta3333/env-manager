"""Shared CLI resolution helpers — find envs/projects by name or path."""

from pathlib import Path
from typing import Any

from env_manager.storage.repo_env import EnvironmentRepository
from env_manager.storage.repo_project import ProjectRepository


def resolve_env(conn: Any, identifier: str) -> Any:
    """Find an environment by path, project name, or project path.

    Handles macOS /tmp → /private/tmp symlink resolution.
    Returns sqlite3.Row or None.
    """
    env_repo = EnvironmentRepository(conn)
    proj_repo = ProjectRepository(conn)

    # Try direct env path
    env = env_repo.get_by_path(identifier)
    if env:
        return env

    # Try resolved path (macOS /tmp → /private/tmp)
    resolved = str(Path(identifier).resolve())
    if resolved != identifier:
        env = env_repo.get_by_path(resolved)
        if env:
            return env

    # Try with .venv suffix
    venv_path = str(Path(identifier).resolve() / ".venv")
    env = env_repo.get_by_path(venv_path)
    if env:
        return env

    # Try project by path
    proj = proj_repo.get_by_path(identifier) or proj_repo.get_by_path(resolved)
    if not proj:
        all_p = proj_repo.list_all()
        proj = next((p for p in all_p if p["name"] == identifier), None)

    if proj:
        envs = env_repo.list_by_project(proj["id"])
        if envs:
            return envs[0]
    return None
