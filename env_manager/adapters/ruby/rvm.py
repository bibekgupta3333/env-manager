"""Ruby rvm adapter — detects RVM-managed Ruby environments."""

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


class RubyRvmAdapter(BaseAdapter):
    name = "ruby.rvm"
    display_name = "Ruby (rvm)"
    version = "1.0.0"
    env_type = "global"

    def find_patterns(self) -> list[str]:
        rvm_base = find_vm_path("rvm") or Path.home() / ".rvm"
        rvm_dir = rvm_base / "rubies"
        if rvm_dir.exists():
            return [str(rvm_dir)]
        return ["**/.ruby-version", "**/Gemfile"]

    def detect(self, path: Path) -> EnvMetadata | None:
        rvm_base = find_vm_path("rvm") or Path.home() / ".rvm"
        rvm_root = rvm_base / "rubies"
        if rvm_root.exists() and str(path).startswith(str(rvm_root)):
            version = path.name
            return EnvMetadata(
                language="ruby",
                tool="rvm",
                version=version,
                path=str(path),
                size_bytes=self._du(path),
                interpreter_path=str(path / "bin" / "ruby"),
                env_type="global",
            )
        ver_file = path / ".ruby-version"
        if ver_file.exists():
            version = ver_file.read_text().strip()
            return EnvMetadata(
                language="ruby",
                tool="rvm",
                version=version,
                path=str(path),
                size_bytes=self._du(path),
                interpreter_path="ruby",
                env_type="global",
            )
        return None

    def inspect(self, path: Path) -> EnvMetadata:
        return EnvMetadata(
            language="ruby",
            tool="rvm",
            version="unknown",
            path=str(path),
            size_bytes=self._du(path),
            interpreter_path="ruby",
            env_type="global",
        )

    def get_packages(self, path: Path) -> list[Package]:
        return []

    def freeze(self, path: Path) -> FreezeResult:
        return FreezeResult(raw_content="", format="Gemfile", packages=[])

    def check_health(self, path: Path) -> HealthResult:
        import shutil

        if shutil.which("ruby"):
            return HealthResult(status="healthy")
        return HealthResult(status="degraded")

    def _du(self, path: Path) -> int:
        total = 0
        try:
            for f in path.rglob("*"):
                if f.is_file() and not f.is_symlink():
                    total += f.stat().st_size
        except PermissionError:
            pass
        return total
