"""Node.js fnm adapter — Fast Node Manager."""

from __future__ import annotations

from pathlib import Path

from env_manager.adapters.base import BaseAdapter
from env_manager.models.env import (
    EnvMetadata,
    FreezeResult,
    HealthResult,
    Package,
)


class NodeFnmAdapter(BaseAdapter):
    name = "node.fnm"
    display_name = "Node.js (fnm)"
    version = "1.0.0"
    env_type = "global"

    def find_patterns(self) -> list[str]:
        return ["**/.node-version"]

    def detect(self, path: Path) -> EnvMetadata | None:
        node_ver = path / ".node-version"
        if node_ver.exists():
            version = node_ver.read_text().strip()
            fnm_dir = Path.home() / ".fnm" / "node-versions" / f"v{version}"
            interpreter = (
                str(fnm_dir / "installation" / "bin" / "node")
                if fnm_dir.exists()
                else "node"
            )
            return EnvMetadata(
                language="node",
                tool="fnm",
                version=version,
                path=str(fnm_dir if fnm_dir.exists() else path),
                size_bytes=self._du(fnm_dir) if fnm_dir.exists() else 0,
                interpreter_path=interpreter,
                env_type="global",
            )
        return None

    def inspect(self, path: Path) -> EnvMetadata:
        return EnvMetadata(
            language="node",
            tool="fnm",
            version="unknown",
            path=str(path),
            size_bytes=self._du(path),
            interpreter_path="node",
            packages_count=0,
            env_type="global",
        )

    def get_packages(self, path: Path) -> list[Package]:
        return []

    def freeze(self, path: Path) -> FreezeResult:
        return FreezeResult(raw_content="", format="package.json", packages=[])

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
