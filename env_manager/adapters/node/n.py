"""Node n adapter — detects n-managed Node versions."""

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
from env_manager.platform import node_exe_name


class NodeNAdapter(BaseAdapter):
    name = "node.n"
    display_name = "Node.js (n)"
    version = "1.0.0"
    env_type = "runtime"

    def _find_n_prefix(self) -> Path:
        env_prefix = os.environ.get("N_PREFIX")
        if env_prefix:
            return Path(env_prefix) / "n" / "versions" / "node"
        candidates = [
            Path("/usr/local/n/versions/node"),
            Path.home() / "n" / "versions" / "node",
        ]
        for c in candidates:
            if c.exists():
                return c
        return candidates[0]

    def find_patterns(self) -> list[str]:
        n_prefix = self._find_n_prefix()
        if n_prefix.exists():
            return [str(n_prefix)]
        return []

    def detect(self, path: Path) -> EnvMetadata | None:
        n_prefix = self._find_n_prefix()
        if n_prefix.exists() and str(path).startswith(str(n_prefix)):
            version = path.name
            node_bin = path / "bin" / node_exe_name()
            if not node_bin.exists():
                node_bin = path / node_exe_name()
            return EnvMetadata(
                language="node",
                tool="n",
                version=version,
                path=str(path),
                size_bytes=self._du(path),
                interpreter_path=str(node_bin),
                env_type="runtime",
            )
        return None

    def inspect(self, path: Path) -> EnvMetadata:
        node_bin = path / "bin" / node_exe_name()
        if not node_bin.exists():
            node_bin = path / node_exe_name()
        return EnvMetadata(
            language="node",
            tool="n",
            version=path.name,
            path=str(path),
            size_bytes=self._du(path),
            interpreter_path=str(node_bin),
            env_type="runtime",
        )

    def get_packages(self, path: Path) -> list[Package]:
        return []

    def freeze(self, path: Path) -> FreezeResult:
        return FreezeResult(raw_content="", format="package.json", packages=[])

    def check_health(self, path: Path) -> HealthResult:
        node = path / "bin" / node_exe_name()
        if node.exists():
            return HealthResult(status="healthy")
        node = path / node_exe_name()
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
