"""Go goenv adapter — detects goenv-managed Go environments."""

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


class GoGoenvAdapter(BaseAdapter):
    name = "go.goenv"
    display_name = "Go (goenv)"
    version = "1.0.0"
    env_type = "global"

    def find_patterns(self) -> list[str]:
        return ["**/.go-version"]

    def detect(self, path: Path) -> EnvMetadata | None:
        go_ver = path / ".go-version"
        if go_ver.exists():
            version = go_ver.read_text().strip()
            goenv_dir = (
                find_vm_path("goenv", "versions", version)
                or Path.home() / ".goenv" / "versions" / version
            )
            interpreter = (
                str(goenv_dir / "bin" / "go") if goenv_dir.exists() else "go"
            )
            return EnvMetadata(
                language="go",
                tool="goenv",
                version=version,
                path=str(goenv_dir if goenv_dir.exists() else path),
                size_bytes=self._du(goenv_dir) if goenv_dir.exists() else 0,
                interpreter_path=interpreter,
                env_type="global",
            )
        return None

    def inspect(self, path: Path) -> EnvMetadata:
        return EnvMetadata(
            language="go",
            tool="goenv",
            version="unknown",
            path=str(path),
            size_bytes=self._du(path),
            interpreter_path="go",
            packages_count=0,
            env_type="global",
        )

    def get_packages(self, path: Path) -> list[Package]:
        return []

    def freeze(self, path: Path) -> FreezeResult:
        return FreezeResult(raw_content="", format="go.mod", packages=[])

    def check_health(self, path: Path) -> HealthResult:
        return HealthResult(status="healthy")

    def _du(self, path: Path) -> int:
        total = 0
        try:
            for f in path.rglob("*"):
                if f.is_file() and not f.is_symlink():
                    total += f.stat().st_size
        except PermissionError:
            pass
        return total
