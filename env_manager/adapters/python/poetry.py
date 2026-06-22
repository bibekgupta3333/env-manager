"""Python poetry adapter — detects Poetry-managed environments."""

from __future__ import annotations

import json
import subprocess
from pathlib import Path

from env_manager.adapters.base import BaseAdapter
from env_manager.models.env import (
    EnvMetadata,
    FreezeResult,
    HealthResult,
    Package,
)


class PythonPoetryAdapter(BaseAdapter):
    name = "python.poetry"
    display_name = "Python (poetry)"
    version = "1.0.0"
    env_type = "local"

    def find_patterns(self) -> list[str]:
        return ["**/pyproject.toml"]

    def detect(self, path: Path) -> EnvMetadata | None:
        toml = path / "pyproject.toml"
        if not toml.exists():
            return None
        try:
            content = toml.read_text()
            if "[tool.poetry]" not in content:
                return None
        except Exception:
            return None

        version = self._read_python_version(path)
        venv_path = self._find_venv(path)
        return EnvMetadata(
            language="python",
            tool="poetry",
            version=version,
            path=str(venv_path or path),
            size_bytes=self._du(venv_path) if venv_path else self._du(path),
            interpreter_path="python3",
        )

    def inspect(self, path: Path) -> EnvMetadata:
        version = self._read_python_version(path)
        venv_path = self._find_venv(path)
        return EnvMetadata(
            language="python",
            tool="poetry",
            version=version,
            path=str(venv_path or path),
            size_bytes=self._du(venv_path) if venv_path else self._du(path),
            interpreter_path="python3",
            packages_count=len(self.get_packages(path)),
        )

    def get_packages(self, path: Path) -> list[Package]:
        try:
            r = subprocess.run(
                ["poetry", "show", "--no-dev", "--format", "json"],
                capture_output=True, text=True, timeout=30, cwd=str(path),
            )
            if r.returncode == 0:
                data = json.loads(r.stdout)
                return [
                    Package(name=p["name"], version=p.get("version", "?"))
                    for p in data
                ]
        except Exception:
            pass
        return []

    def freeze(self, path: Path) -> FreezeResult:
        packages = self.get_packages(path)
        raw = "\n".join(
            f"{p.name}=={p.version}"
            for p in sorted(packages, key=lambda x: x.name)
        )
        return FreezeResult(
            raw_content=raw, format="pyproject.toml", packages=packages
        )

    def check_health(self, path: Path) -> HealthResult:
        venv = self._find_venv(path)
        if venv and (venv / "bin" / "python").exists():
            return HealthResult(status="healthy")
        try:
            subprocess.run(
                ["poetry", "--version"], capture_output=True, timeout=10
            )
            return HealthResult(status="healthy")
        except Exception:
            return HealthResult(
                status="broken",
                errors=["poetry not found"],
                suggestions=["Install poetry: pip install poetry"],
            )

    def _read_python_version(self, path: Path) -> str:
        toml = path / "pyproject.toml"
        if toml.exists():
            for line in toml.read_text().splitlines():
                if line.strip().startswith("python"):
                    return line.split("=")[-1].strip().strip('"').strip("'")
        return "unknown"

    def _find_venv(self, path: Path) -> Path | None:
        candidates = [
            path / ".venv",
            path / "venv",
        ]
        for c in candidates:
            if c.exists() and (c / "bin" / "python").exists():
                return c
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
