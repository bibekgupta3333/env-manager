"""Node n adapter — detects n-managed Node versions."""

from __future__ import annotations

from pathlib import Path

from env_manager.adapters.base import BaseAdapter
from env_manager.models.env import (
    EnvMetadata,
    FreezeResult,
    HealthResult,
    Package,
)


class NodeNAdapter(BaseAdapter):
    name = "node.n"
    display_name = "Node.js (n)"
    version = "1.0.0"
    env_type = "global"

    def find_patterns(self) -> list[str]:
        n_prefix = Path("/usr/local/n/versions/node")
        if n_prefix.exists():
            return [str(n_prefix)]
        return []

    def detect(self, path: Path) -> EnvMetadata | None:
        n_prefix = Path("/usr/local/n/versions/node")
        if n_prefix.exists() and str(path).startswith(str(n_prefix)):
            version = path.name
            return EnvMetadata(
                language="node",
                tool="n",
                version=version,
                path=str(path),
                size_bytes=self._du(path),
                interpreter_path=str(path / "bin" / "node"),
                env_type="global",
            )
        return None

    def inspect(self, path: Path) -> EnvMetadata:
        return EnvMetadata(
            language="node",
            tool="n",
            version=path.name,
            path=str(path),
            size_bytes=self._du(path),
            interpreter_path=str(path / "bin" / "node"),
            env_type="global",
        )

    def get_packages(self, path: Path) -> list[Package]:
        return []

    def freeze(self, path: Path) -> FreezeResult:
        return FreezeResult(raw_content="", format="package.json", packages=[])

    def check_health(self, path: Path) -> HealthResult:
        node = path / "bin" / "node"
        if node.exists():
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
