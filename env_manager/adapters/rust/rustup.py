"""Rust rustup adapter — detects rustup-managed Rust toolchains."""

from __future__ import annotations

from pathlib import Path

from env_manager.adapters.base import BaseAdapter
from env_manager.models.env import EnvMetadata, FreezeResult, HealthResult, Package


class RustRustupAdapter(BaseAdapter):
    name = "rust.rustup"
    display_name = "Rust (rustup)"
    version = "1.0.0"
    env_type = "global"

    def find_patterns(self) -> list[str]:
        return ["**/rust-toolchain.toml", "**/rust-toolchain"]

    def detect(self, path: Path) -> EnvMetadata | None:
        toml_path = path / "rust-toolchain.toml"
        legacy_path = path / "rust-toolchain"
        toolchain_file = toml_path if toml_path.exists() else (legacy_path if legacy_path.exists() else None)
        if toolchain_file:
            version = toolchain_file.read_text().strip()
            rustup_dir = Path.home() / ".rustup" / "toolchains"
            return EnvMetadata(
                language="rust", tool="rustup", version=version,
                path=str(rustup_dir), size_bytes=self._du(rustup_dir),
                interpreter_path="rustc", env_type="global",
            )
        return None

    def inspect(self, path: Path) -> EnvMetadata:
        return EnvMetadata(
            language="rust", tool="rustup", version="unknown",
            path=str(path), size_bytes=self._du(path),
            interpreter_path="rustc", packages_count=0, env_type="global",
        )

    def get_packages(self, path: Path) -> list[Package]:
        return []

    def freeze(self, path: Path) -> FreezeResult:
        return FreezeResult(raw_content="", format="Cargo.toml", packages=[])

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
