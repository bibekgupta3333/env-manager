"""Python pipenv adapter — detects Pipenv-managed environments."""

from __future__ import annotations

from pathlib import Path

from env_manager.adapters.base import BaseAdapter
from env_manager.models.env import (
    EnvMetadata,
    FreezeResult,
    HealthResult,
    Package,
)


class PythonPipenvAdapter(BaseAdapter):
    name = "python.pipenv"
    display_name = "Python (pipenv)"
    version = "1.0.0"
    env_type = "local"

    def find_patterns(self) -> list[str]:
        return ["**/Pipfile"]

    def detect(self, path: Path) -> EnvMetadata | None:
        pipfile = path / "Pipfile"
        if not pipfile.exists():
            return None
        version = self._read_version(pipfile)
        return EnvMetadata(
            language="python",
            tool="pipenv",
            version=version,
            path=str(path),
            size_bytes=self._du(path),
            interpreter_path="python3",
        )

    def inspect(self, path: Path) -> EnvMetadata:
        return EnvMetadata(
            language="python",
            tool="pipenv",
            version=self._read_version(path / "Pipfile"),
            path=str(path),
            size_bytes=self._du(path),
            interpreter_path="python3",
        )

    def get_packages(self, path: Path) -> list[Package]:
        return []

    def freeze(self, path: Path) -> FreezeResult:
        lock = path / "Pipfile.lock"
        raw = lock.read_text() if lock.exists() else ""
        return FreezeResult(raw_content=raw, format="Pipfile", packages=[])

    def check_health(self, path: Path) -> HealthResult:
        return HealthResult(status="healthy")

    def _read_version(self, pipfile: Path) -> str:
        try:
            for line in pipfile.read_text().splitlines():
                line = line.strip()
                if line.startswith("python_version"):
                    return line.split("=")[-1].strip().strip('"').strip("'")
        except (OSError, UnicodeDecodeError):
            pass
        return "unknown"

    def _du(self, path: Path) -> int:
        total = 0
        try:
            for f in path.rglob("*"):
                if f.is_file() and not f.is_symlink():
                    total += f.stat().st_size
        except PermissionError:
            pass
        return total
