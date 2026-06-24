"""Node.js fnm adapter — Fast Node Manager."""

from __future__ import annotations

import json
import os
from pathlib import Path

from env_manager.adapters.base import BaseAdapter
from env_manager.models.env import (
    EnvMetadata,
    FreezeResult,
    HealthResult,
    Package,
)
from env_manager.platform import find_vm_path, node_exe_name


class NodeFnmAdapter(BaseAdapter):
    name = "node.fnm"
    display_name = "Node.js (fnm)"
    version = "1.0.0"
    env_type = "runtime"

    def find_patterns(self) -> list[str]:
        return ["**/package.json", "**/.node-version"]

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
                    ver_dir = (
                        path.parent if path.name == "installation"
                        else path
                    )
                    return EnvMetadata(
                        language="node",
                        tool="fnm",
                        version=ver_dir.name.lstrip("v"),
                        path=str(path),
                        size_bytes=self._du(path),
                        interpreter_path=str(node_bin),
                        env_type="runtime",
                    )
            except (json.JSONDecodeError, OSError):
                pass

        # ----- PROJECT detection -----
        node_ver = path / ".node-version"
        if node_ver.exists():
            fnm_installed = find_vm_path("fnm") is not None
            if not fnm_installed:
                return None
            version = node_ver.read_text().strip()
            return EnvMetadata(
                language="node",
                tool="fnm",
                version=version,
                path=str(path),
                size_bytes=self._du(
                    path / "node_modules"
                ) if (path / "node_modules").exists() else self._du(path),
                interpreter_path="node",
                env_type="project",
            )

        # ----- Generic Node.js project (no tool file) -----
        pkg = path / "package.json"
        if pkg.exists():
            try:
                data = json.loads(pkg.read_text())
                scripts = data.get("scripts", {})
                deps = data.get("dependencies", {})

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
                    return None

                if "workspaces" in data:
                    return None

                source_extensions = (
                    ".ts", ".tsx", ".js", ".jsx", ".mjs", ".cjs",
                )
                has_source_code = False
                try:
                    for entry in path.iterdir():
                        if (
                            entry.is_file()
                            and entry.suffix in source_extensions
                        ):
                            has_source_code = True
                            break
                    if not has_source_code and (path / "src").is_dir():
                        for entry in (path / "src").iterdir():
                            if (
                                entry.is_file()
                                and entry.suffix in source_extensions
                            ):
                                has_source_code = True
                                break
                except (OSError, PermissionError):
                    pass
                if not has_source_code:
                    return None

                indicators = 0
                has_real_script = False
                for script_cmd in scripts.values():
                    if (
                        script_cmd
                        and script_cmd
                        != 'echo "Error: no test specified" && exit 1'
                        and any(
                            kw in script_cmd
                            for kw in [
                                "tsc", "build", "webpack", "vite",
                                "next", "server", "start", "dev",
                                "nodemon",
                            ]
                        )
                    ):
                        has_real_script = True
                        break

                if (path / "tsconfig.json").exists():
                    indicators += 1
                if any(
                    (path / f).exists()
                    for f in [
                        "vite.config.js", "vite.config.ts",
                        "webpack.config.js", "jest.config.js",
                        "rollup.config.js",
                    ]
                ):
                    indicators += 1
                if len(deps) >= 3:
                    indicators += 1
                if (
                    data.get("main")
                    or data.get("exports")
                    or data.get("module")
                ):
                    indicators += 1
                if any(
                    (path / f).exists()
                    for f in [
                        "package-lock.json", "yarn.lock", "pnpm-lock.yaml",
                    ]
                ):
                    indicators += 1
                if (path / ".git").exists():
                    # .git is a strong indicator: project is under
                    # version control (worth 2 indicators by itself)
                    indicators += 2
                if has_real_script:
                    indicators += 1

                if indicators < 2:
                    return None

                eng = data.get("engines", {}).get("node", "unknown")
                version = str(eng)
                size = (
                    self._du(path / "node_modules")
                    if (path / "node_modules").exists()
                    else self._du(path)
                )
                return EnvMetadata(
                    language="node",
                    tool="fnm",
                    version=version,
                    path=str(path),
                    size_bytes=size,
                    interpreter_path="node",
                    env_type="project",
                )
            except (json.JSONDecodeError, OSError, UnicodeDecodeError):
                pass

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
            env_type="runtime",
        )

    def get_packages(self, path: Path) -> list[Package]:
        return []

    def freeze(self, path: Path) -> FreezeResult:
        return FreezeResult(raw_content="", format="package.json", packages=[])

    def check_health(self, path: Path) -> HealthResult:
        # Runtime check: bin/node binary exists
        node_bin = path / "bin" / node_exe_name()
        if node_bin.exists() and os.access(str(node_bin), os.X_OK):
            return HealthResult(status="healthy")
        # Project check: valid package.json exists
        pkg = path / "package.json"
        if pkg.exists():
            try:
                json.loads(pkg.read_text())
                return HealthResult(status="healthy")
            except (json.JSONDecodeError, OSError):
                return HealthResult(
                    status="broken", errors=["Invalid package.json"]
                )
        return HealthResult(
            status="broken", errors=["No node binary or package.json found"]
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
