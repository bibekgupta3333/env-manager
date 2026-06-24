"""Ruby rbenv adapter — detects rbenv-managed Ruby environments."""

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


class RubyRbenvAdapter(BaseAdapter):
    name = "ruby.rbenv"
    display_name = "Ruby (rbenv)"
    version = "1.0.0"
    env_type = "runtime"

    def find_patterns(self) -> list[str]:
        return ["**/.ruby-version"]

    def detect(self, path: Path) -> EnvMetadata | None:
        rbenv_installed = find_vm_path("rbenv") is not None

        ruby_ver = path / ".ruby-version"
        if ruby_ver.exists():
            if not rbenv_installed:
                return None
            if not self._is_real_ruby_project(path):
                return None
            version = ruby_ver.read_text().strip()
            rbenv_dir = (
                find_vm_path("rbenv", "versions", version)
                or Path.home() / ".rbenv" / "versions" / version
            )
            interpreter = (
                str(rbenv_dir / "bin" / "ruby")
                if rbenv_dir.exists()
                else "ruby"
            )
            return EnvMetadata(
                language="ruby",
                tool="rbenv",
                version=version,
                path=str(rbenv_dir if rbenv_dir.exists() else path),
                size_bytes=self._du(rbenv_dir) if rbenv_dir.exists() else 0,
                interpreter_path=interpreter,
                env_type="project",
            )
        return None

    def _is_real_ruby_project(self, path: Path) -> bool:
        """Check if path is a real Ruby project (not test/docs)."""
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

        # Require Gemfile OR at least 1 .rb file in root or lib/
        has_gemfile = (path / "Gemfile").exists()
        has_ruby_source = False
        try:
            for entry in path.iterdir():
                if entry.is_file() and entry.suffix == ".rb":
                    has_ruby_source = True
                    break
            if not has_ruby_source and (path / "lib").is_dir():
                for entry in (path / "lib").iterdir():
                    if entry.is_file() and entry.suffix == ".rb":
                        has_ruby_source = True
                        break
        except (OSError, PermissionError):
            pass
        if not (has_gemfile or has_ruby_source):
            return False

        indicators = 0
        if has_gemfile:
            indicators += 1
        if (path / "Gemfile.lock").exists():
            indicators += 1
        if (path / ".git").exists():
            # .git is a strong indicator: project is under version control
            indicators += 2
        if (path / "Rakefile").exists():
            indicators += 1
        if (path / "test").is_dir() or (path / "spec").is_dir():
            indicators += 1
        if (path / "README.md").exists():
            indicators += 1

        return indicators >= 2

    def inspect(self, path: Path) -> EnvMetadata:
        return EnvMetadata(
            language="ruby",
            tool="rbenv",
            version="unknown",
            path=str(path),
            size_bytes=self._du(path),
            interpreter_path="ruby",
            packages_count=0,
            env_type="runtime",
        )

    def get_packages(self, path: Path) -> list[Package]:
        return []

    def freeze(self, path: Path) -> FreezeResult:
        return FreezeResult(raw_content="", format="Gemfile", packages=[])

    def check_health(self, path: Path) -> HealthResult:
        ruby_bin = path / "bin" / "ruby"
        if ruby_bin.exists() and os.access(str(ruby_bin), os.X_OK):
            return HealthResult(status="healthy")
        return HealthResult(
            status="broken", errors=[f"Ruby binary not found at {ruby_bin}"]
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
