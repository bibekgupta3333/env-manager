"""Node.js nvm adapter — detects and inspects nvm-managed Node environments."""

from __future__ import annotations

import subprocess
from pathlib import Path
from typing import Any

from env_manager.adapters.base import BaseAdapter
from env_manager.models.env import EnvMetadata, FreezeResult, HealthResult, Package


class NodeNvmAdapter(BaseAdapter):
    name = "node.nvm"
    display_name = "Node.js (nvm)"
    version = "1.0.0"
    env_type = "global"

    def find_patterns(self) -> list[str]:
        return ["**/.nvmrc"]

    def detect(self, path: Path) -> EnvMetadata | None:
        nvmrc = path / ".nvmrc"
        if nvmrc.exists():
            version = nvmrc.read_text().strip()
            nvm_path = Path.home() / ".nvm" / "versions" / "node" / f"v{version}"
            if nvm_path.exists():
                return EnvMetadata(
                    language="node", tool="nvm", version=version,
                    path=str(nvm_path), size_bytes=self._du(nvm_path),
                    interpreter_path=str(nvm_path / "bin" / "node"),
                    env_type="global",
                )
            return EnvMetadata(
                language="node", tool="nvm", version=version,
                path=str(path), size_bytes=0,
                interpreter_path="node",
                env_type="global",
            )
        return None

    def inspect(self, path: Path) -> EnvMetadata:
        version = self._get_node_version(path)
        return EnvMetadata(
            language="node", tool="nvm", version=version,
            path=str(path), size_bytes=self._du(path),
            interpreter_path=self._find_node(path),
            packages_count=len(self.get_packages(path)),
            env_type="global",
        )

    def get_packages(self, path: Path) -> list[Package]:
        node_modules: Path | None = path / "lib" / "node_modules"
        if node_modules is not None and not node_modules.exists():
            node_modules = self._find_node_modules(path)
        try:
            result = subprocess.run(
                ["npm", "list", "--json", "--depth=0", "--prefix", str(path.parent)],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode == 0 and result.stdout.strip():
                import json
                data = json.loads(result.stdout)
                deps = data.get("dependencies", {})
                return [Package(name=k, version=v.get("version", "unknown"))
                        for k, v in deps.items()]
        except Exception:
            pass
        return []

    def freeze(self, path: Path) -> FreezeResult:
        packages = self.get_packages(path)
        raw = "\n".join(f"{p.name}@{p.version}" for p in sorted(packages, key=lambda x: x.name))
        return FreezeResult(raw_content=raw, format="package.json", packages=packages)

    def check_health(self, path: Path) -> HealthResult:
        checks: list[dict[str, Any]] = []
        errors: list[str] = []
        node_bin = self._find_node(path)
        if node_bin == "node" or not Path(node_bin).exists():
            errors.append("Node binary not found")
            return HealthResult(status="broken", checks=checks, errors=errors)

        try:
            r = subprocess.run([node_bin, "--version"], capture_output=True, text=True, timeout=10)
            checks.append({"name": "node_binary", "passed": r.returncode == 0})
        except Exception as e:
            errors.append(str(e))

        status = "healthy" if len(errors) == 0 else "broken"
        return HealthResult(status=status, checks=checks, errors=errors)

    def _get_node_version(self, path: Path) -> str:
        try:
            r = subprocess.run(["node", "--version"], capture_output=True, text=True, timeout=10)
            return r.stdout.strip().lstrip("v")
        except Exception:
            return "unknown"

    def _find_node(self, path: Path) -> str:
        node_path = path / "bin" / "node"
        if node_path.exists():
            return str(node_path)
        return "node"

    def _find_node_modules(self, path: Path) -> Path | None:
        for p in [path, path.parent]:
            nm = p / "node_modules"
            if nm.exists():
                return nm
        return None

    def _du(self, path: Path) -> int:
        total = 0
        try:
            for f in path.rglob("*"):
                if f.is_file() and not f.is_symlink():
                    total += f.stat().st_size
        except PermissionError:
            pass
        return total
