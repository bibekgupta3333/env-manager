"""Ruby rbenv adapter — detects rbenv-managed Ruby environments."""

from __future__ import annotations

from pathlib import Path

from env_manager.adapters.base import BaseAdapter
from env_manager.models.env import (
    EnvMetadata,
    FreezeResult,
    HealthResult,
    Package,
)


class RubyRbenvAdapter(BaseAdapter):
    name = "ruby.rbenv"
    display_name = "Ruby (rbenv)"
    version = "1.0.0"
    env_type = "global"

    def find_patterns(self) -> list[str]:
        return ["**/.ruby-version"]

    def detect(self, path: Path) -> EnvMetadata | None:
        ruby_ver = path / ".ruby-version"
        if ruby_ver.exists():
            version = ruby_ver.read_text().strip()
            rbenv_dir = Path.home() / ".rbenv" / "versions" / version
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
                env_type="global",
            )
        return None

    def inspect(self, path: Path) -> EnvMetadata:
        return EnvMetadata(
            language="ruby",
            tool="rbenv",
            version="unknown",
            path=str(path),
            size_bytes=self._du(path),
            interpreter_path="ruby",
            packages_count=0,
            env_type="global",
        )

    def get_packages(self, path: Path) -> list[Package]:
        return []

    def freeze(self, path: Path) -> FreezeResult:
        return FreezeResult(raw_content="", format="Gemfile", packages=[])

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
