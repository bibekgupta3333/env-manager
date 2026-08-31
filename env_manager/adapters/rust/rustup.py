"""Rust rustup adapter — detects rustup-managed Rust toolchains."""

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


class RustRustupAdapter(BaseAdapter):
    name = "rust.rustup"
    display_name = "Rust (rustup)"
    version = "1.0.0"
    env_type = "runtime"

    def find_patterns(self) -> list[str]:
        return ["**/rust-toolchain.toml", "**/rust-toolchain"]

    def detect(self, path: Path) -> EnvMetadata | None:
        toml_path = path / "rust-toolchain.toml"
        legacy_path = path / "rust-toolchain"

        version = "unknown"
        toolchain_file = None
        if toml_path.exists():
            toolchain_file = toml_path
            version = self._parse_toolchain_toml(toml_path)
        elif legacy_path.exists():
            toolchain_file = legacy_path
            version = legacy_path.read_text().strip()

        if toolchain_file and toolchain_file.exists():
            if not self._is_real_rust_project(path):
                return None
            return EnvMetadata(
                language="rust",
                tool="rustup",
                version=version,
                path=str(path),
                size_bytes=self._du(path),
                interpreter_path="rustc",
                env_type="project",
            )
        return None

    def _is_real_rust_project(self, path: Path) -> bool:
        """Check if path is a real Rust project (not test/docs)."""
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

        # Require Cargo.toml OR src/main.rs or src/lib.rs
        has_cargo_toml = (path / "Cargo.toml").exists()
        has_rust_source = False
        for candidate in [path / "src" / "main.rs", path / "src" / "lib.rs"]:
            if candidate.exists():
                has_rust_source = True
                break
        if not has_rust_source:
            try:
                src_dir = path / "src"
                if src_dir.is_dir():
                    for entry in src_dir.iterdir():
                        if entry.is_file() and entry.suffix == ".rs":
                            has_rust_source = True
                            break
            except (OSError, PermissionError):
                pass
        if not (has_cargo_toml or has_rust_source):
            return False

        indicators = 0
        if has_cargo_toml:
            indicators += 1
        if (path / "Cargo.lock").exists():
            indicators += 1
        if (path / ".git").exists():
            # .git is a strong indicator: project is under version control
            indicators += 2
        if (path / "src" / "main.rs").exists():
            indicators += 1
        if (path / "src" / "lib.rs").exists():
            indicators += 1
        if (path / "tests").is_dir():
            indicators += 1

        return indicators >= 2

    def _parse_toolchain_toml(self, toml_path: Path) -> str:
        try:
            for line in toml_path.read_text().splitlines():
                line = line.strip()
                if line.startswith("channel"):
                    return line.split("=")[-1].strip().strip('"').strip("'")
        except (OSError, UnicodeDecodeError):
            pass
        return "unknown"

    def inspect(self, path: Path) -> EnvMetadata:
        return EnvMetadata(
            language="rust",
            tool="rustup",
            version="unknown",
            path=str(path),
            size_bytes=self._du(path),
            interpreter_path="rustc",
            packages_count=0,
            env_type="runtime",
        )

    def get_packages(self, path: Path) -> list[Package]:
        return []

    def freeze(self, path: Path) -> FreezeResult:
        return FreezeResult(raw_content="", format="Cargo.toml", packages=[])

    def check_health(self, path: Path) -> HealthResult:
        rustc_bin = path / "bin" / "rustc"
        if rustc_bin.exists() and os.access(str(rustc_bin), os.X_OK):
            return HealthResult(status="healthy")
        return HealthResult(
            status="broken", errors=[f"rustc binary not found at {rustc_bin}"]
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
