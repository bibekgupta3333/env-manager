"""Python pyenv adapter — detects pyenv-managed Python versions."""

from __future__ import annotations

from pathlib import Path

from env_manager.adapters.base import BaseAdapter
from env_manager.models.env import (
    EnvMetadata,
    FreezeResult,
    HealthResult,
    Package,
)
from env_manager.platform import find_vm_path


class PythonPyenvAdapter(BaseAdapter):
    name = "python.pyenv"
    display_name = "Python (pyenv)"
    version = "1.0.0"
    env_type = "global"

    def find_patterns(self) -> list[str]:
        pyenv_root = (
            find_vm_path("pyenv", "versions")
            or Path.home() / ".pyenv" / "versions"
        )
        if pyenv_root.exists():
            return [str(pyenv_root)]
        return ["**/.python-version"]

    def detect(self, path: Path) -> EnvMetadata | None:
        # pyenv global: ~/.pyenv/versions/3.12.0/
        pyenv_root = (
            find_vm_path("pyenv", "versions")
            or Path.home() / ".pyenv" / "versions"
        )
        if not pyenv_root.exists():
            return None
        try:
            if path.parent == pyenv_root or path.parent.parent == pyenv_root:
                version = path.name
                python_bin = path / "bin" / "python"
                return EnvMetadata(
                    language="python",
                    tool="pyenv",
                    version=version,
                    path=str(path),
                    size_bytes=self._du(path),
                    interpreter_path=str(python_bin)
                    if python_bin.exists()
                    else "python3",
                    env_type="global",
                )
        except OSError:
            pass
        return None

    def inspect(self, path: Path) -> EnvMetadata:
        return EnvMetadata(
            language="python",
            tool="pyenv",
            version=path.name,
            path=str(path),
            size_bytes=self._du(path),
            interpreter_path="python3",
            env_type="global",
        )

    def get_packages(self, path: Path) -> list[Package]:
        return []

    def freeze(self, path: Path) -> FreezeResult:
        return FreezeResult(
            raw_content="", format="pyproject.toml", packages=[]
        )

    def check_health(self, path: Path) -> HealthResult:
        python_bin = path / "bin" / "python"
        if python_bin.exists():
            return HealthResult(status="healthy")
        return HealthResult(
            status="broken",
            errors=[f"Python binary not found: {python_bin}"],
        )

    def _du(self, path: Path) -> int:
        total = 0
        try:
            for f in path.rglob("*"):
                if f.is_file() and not f.is_symlink():
                    total += f.stat().st_size
        except PermissionError:
            pass
        return total
