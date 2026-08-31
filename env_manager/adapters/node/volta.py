"""Node volta adapter — detects Volta-managed Node environments."""

from __future__ import annotations

import json
import shutil
from pathlib import Path

from env_manager.adapters.base import BaseAdapter
from env_manager.models.env import (
    EnvMetadata,
    FreezeResult,
    HealthResult,
    Package,
)
from env_manager.platform import find_vm_path


class NodeVoltaAdapter(BaseAdapter):
    name = "node.volta"
    display_name = "Node.js (volta)"
    version = "1.0.0"
    env_type = "runtime"

    def find_patterns(self) -> list[str]:
        volta_dir = find_vm_path("volta") or Path.home() / ".volta"
        if volta_dir.exists():
            return [
                str(volta_dir / "tools" / "image" / "node"),
                str(volta_dir / "tools" / "image" / "packages"),
            ]
        return []

    def detect(self, path: Path) -> EnvMetadata | None:
        if "node_modules" in path.parts:
            return None

        pkg = path / "package.json"
        if pkg.exists():
            try:
                data = json.loads(pkg.read_text())
                volta = data.get("volta", {})
                node_ver = volta.get("node", "unknown")
                if node_ver != "unknown":
                    return EnvMetadata(
                        language="node",
                        tool="volta",
                        version=str(node_ver),
                        path=str(path),
                        size_bytes=self._du(path),
                        interpreter_path="node",
                        env_type="project",
                    )
            except (json.JSONDecodeError, OSError, UnicodeDecodeError):
                pass
        return None

    def inspect(self, path: Path) -> EnvMetadata:
        return EnvMetadata(
            language="node",
            tool="volta",
            version="unknown",
            path=str(path),
            size_bytes=self._du(path),
            interpreter_path="node",
            env_type="runtime",
        )

    def get_packages(self, path: Path) -> list[Package]:
        return []

    def freeze(self, path: Path) -> FreezeResult:
        return FreezeResult(raw_content="", format="package.json", packages=[])

    def check_health(self, path: Path) -> HealthResult:
        volta_bin = shutil.which("volta")
        if volta_bin:
            return HealthResult(status="healthy")
        volta_dir = find_vm_path("volta")
        if volta_dir and (volta_dir / "tools" / "image" / "node").exists():
            return HealthResult(status="healthy")
        return HealthResult(status="degraded", errors=["volta not found"])

    def _du(self, path: Path) -> int:
        total = 0
        try:
            for f in path.rglob("*"):
                if f.is_file() and not f.is_symlink():
                    total += f.stat().st_size
        except PermissionError:
            pass
        return total
