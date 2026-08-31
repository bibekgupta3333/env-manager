"""Node.js nvm adapter — detects and inspects nvm-managed Node environments."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from env_manager.adapters.base import BaseAdapter
from env_manager.models.env import (
    EnvMetadata,
    FreezeResult,
    HealthResult,
    Package,
)
from env_manager.platform import find_vm_path, node_exe_name


class NodeNvmAdapter(BaseAdapter):
    name = "node.nvm"
    display_name = "Node.js (nvm)"
    version = "1.0.0"
    env_type = "runtime"

    def find_patterns(self) -> list[str]:
        return ["**/.nvmrc", "**/package.json"]

    def detect(self, path: Path) -> EnvMetadata | None:
        if "node_modules" in path.parts:
            return None

        # ----- RUNTIME detection first -----
        node_bin = path / "bin" / node_exe_name()
        npm_pkg = path / "lib" / "node_modules" / "npm" / "package.json"
        if node_bin.exists() and npm_pkg.exists():
            try:
                data = json.loads(npm_pkg.read_text())
                if data.get("name") == "npm":
                    return EnvMetadata(
                        language="node",
                        tool="nvm",
                        version=self._get_node_version(path),
                        path=str(path),
                        size_bytes=self._du(path),
                        interpreter_path=str(node_bin),
                        env_type="runtime",
                    )
            except (json.JSONDecodeError, OSError):
                pass

        # ----- PROJECT detection -----
        nvmrc = path / ".nvmrc"
        if nvmrc.exists():
            version = nvmrc.read_text().strip()
            nvm_path = find_vm_path("nvm", "versions", "node", f"v{version}")
            nvm_installed = find_vm_path("nvm") is not None
            if not nvm_installed:
                return None
            if nvm_path and nvm_path.exists():
                return EnvMetadata(
                    language="node", tool="nvm", version=version,
                    path=str(path), size_bytes=self._du(path),
                    interpreter_path=str(
                        nvm_path / "bin" / node_exe_name()
                    ),
                    env_type="project",
                )
            return EnvMetadata(
                language="node", tool="nvm", version=version,
                path=str(path),
                size_bytes=(
                    self._du(path / "node_modules")
                    if (path / "node_modules").exists() else 0
                ),
                interpreter_path="node",
                env_type="project",
            )

        return None

    def inspect(self, path: Path) -> EnvMetadata:
        version = self._get_node_version(path)
        return EnvMetadata(
            language="node",
            tool="nvm",
            version=version,
            path=str(path),
            size_bytes=self._du(path),
            interpreter_path=self._find_node(path),
            packages_count=len(self.get_packages(path)),
            env_type="runtime",
        )

    def get_packages(self, path: Path) -> list[Package]:
        node_modules: Path = path / "lib" / "node_modules"
        if not node_modules.exists():
            found = self._find_node_modules(path)
            if found is None:
                node_modules = path / "lib" / "node_modules"
            else:
                node_modules = found
        try:
            result = subprocess.run(
                [
                    "npm",
                    "list",
                    "--json",
                    "--depth=0",
                    "--prefix",
                    str(path.parent),
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode == 0 and result.stdout.strip():
                data = json.loads(result.stdout)
                deps = data.get("dependencies", {})
                return [
                    Package(name=k, version=v.get("version", "unknown"))
                    for k, v in deps.items()
                ]
        except (
            subprocess.TimeoutExpired,
            subprocess.SubprocessError,
            json.JSONDecodeError,
            OSError,
        ):
            pass
        return []

    def freeze(self, path: Path) -> FreezeResult:
        packages = self.get_packages(path)
        raw = "\n".join(
            f"{p.name}@{p.version}"
            for p in sorted(packages, key=lambda x: x.name)
        )
        return FreezeResult(
            raw_content=raw, format="package.json", packages=packages
        )

    def check_health(self, path: Path) -> HealthResult:
        checks: list[dict[str, Any]] = []
        errors: list[str] = []
        node_bin = self._find_node(path)
        if node_bin == "node" or not Path(node_bin).exists():
            errors.append("Node binary not found")
            return HealthResult(status="broken", checks=checks, errors=errors)

        try:
            r = subprocess.run(
                [node_bin, "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            checks.append({"name": "node_binary", "passed": r.returncode == 0})
        except (
            subprocess.TimeoutExpired,
            subprocess.SubprocessError,
            OSError,
            ValueError,
        ) as e:
            errors.append(str(e))

        status = "healthy" if len(errors) == 0 else "broken"
        return HealthResult(status=status, checks=checks, errors=errors)

    def _get_node_version(self, path: Path) -> str:
        try:
            r = subprocess.run(
                ["node", "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            return r.stdout.strip().lstrip("v")
        except (
            subprocess.TimeoutExpired,
            subprocess.SubprocessError,
            FileNotFoundError,
            OSError,
        ):
            return "unknown"

    def _find_node(self, path: Path) -> str:
        node_path = path / "bin" / node_exe_name()
        if node_path.exists():
            return str(node_path)
        # nvm-windows stores node.exe in the root directory
        node_path_root = path / node_exe_name()
        if node_path_root.exists():
            return str(node_path_root)
        # Fallback: try system node via PATH
        system_node = shutil.which("node")
        if system_node:
            return system_node
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
