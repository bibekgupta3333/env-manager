"""Go goenv adapter — detects goenv-managed Go environments."""

from __future__ import annotations

import os
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
    env_type = "runtime"

    def find_patterns(self) -> list[str]:
        return ["**/.go-version"]

    def detect(self, path: Path) -> EnvMetadata | None:
        go_ver = path / ".go-version"
        if go_ver.exists():
            if not self._is_real_go_project(path):
                return None
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
                path=str(path),
                size_bytes=self._du(path),
                interpreter_path=interpreter,
                env_type="project",
            )
        return None

    def _is_real_go_project(self, path: Path) -> bool:
        """Check if path is a real Go project (not test/docs)."""
        dir_name = path.name.lower()
        excluded_names = {
            "test", "tests", "__tests__",
            "types", "typings",
            "docs", "doc", "documentation",
            "scripts", "tools", "dev-tools",
            "config", "configs", "configuration",
            "infra", "infrastructure",
            "examples", "demo", "demos",
            "fixtures", "mocks",
            "lib", "libs", "library",
        }
        if (
            dir_name in excluded_names
            or dir_name.startswith(".")
            or "-test" in dir_name
            or "_test" in dir_name
            or "-doc" in dir_name
            or "_doc" in dir_name
            or "-types" in dir_name
            or "test-" in dir_name
            or "doc-" in dir_name
        ):
            return False

        # Require go.mod OR at least 1 .go file in root or src/
        has_go_source = False
        try:
            for entry in path.iterdir():
                if entry.is_file() and entry.suffix == ".go":
                    has_go_source = True
                    break
            if not has_go_source and (path / "src").is_dir():
                for entry in (path / "src").iterdir():
                    if entry.is_file() and entry.suffix == ".go":
                        has_go_source = True
                        break
        except (OSError, PermissionError):
            pass

        has_go_mod = (path / "go.mod").exists()
        if not (has_go_source or has_go_mod):
            return False

        indicators = 0
        if has_go_mod:
            indicators += 1
        if (path / "go.sum").exists():
            indicators += 1
        if (path / ".git").exists():
            # .git is a strong indicator: project is under version control
            indicators += 2
        if (path / "main.go").exists():
            indicators += 1
        if (path / "cmd").is_dir():
            indicators += 1

        return indicators >= 2

    def inspect(self, path: Path) -> EnvMetadata:
        return EnvMetadata(
            language="go",
            tool="goenv",
            version="unknown",
            path=str(path),
            size_bytes=self._du(path),
            interpreter_path="go",
            packages_count=0,
            env_type="runtime",
        )

    def get_packages(self, path: Path) -> list[Package]:
        return []

    def freeze(self, path: Path) -> FreezeResult:
        return FreezeResult(raw_content="", format="go.mod", packages=[])

    def check_health(self, path: Path) -> HealthResult:
        go_bin = path / "bin" / "go"
        if go_bin.exists() and os.access(str(go_bin), os.X_OK):
            return HealthResult(status="healthy")
        return HealthResult(
            status="broken", errors=[f"Go binary not found at {go_bin}"]
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
