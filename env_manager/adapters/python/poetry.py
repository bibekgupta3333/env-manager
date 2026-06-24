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
from env_manager.platform import python_bin_dir, python_exe_name


class PythonPoetryAdapter(BaseAdapter):
    name = "python.poetry"
    display_name = "Python (poetry)"
    version = "1.0.0"
    env_type = "project"

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
        except (OSError, UnicodeDecodeError):
            return None

        if not self._is_real_python_project(path):
            return None

        version = self._read_python_version(path)
        venv_path = self._find_venv(path)
        interpreter = "python3"
        if venv_path:
            py = venv_path / python_bin_dir(venv_path) / python_exe_name()
            if py.exists():
                interpreter = str(py)
        return EnvMetadata(
            language="python",
            tool="poetry",
            version=version,
            path=str(venv_path or path),
            size_bytes=self._du(venv_path) if venv_path else self._du(path),
            interpreter_path=interpreter,
        )

    def _is_real_python_project(self, path: Path) -> bool:
        """Check if path is a real Python project (not test/docs)."""
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

        has_source_code = False
        try:
            for entry in path.iterdir():
                if entry.is_file() and entry.suffix == ".py":
                    has_source_code = True
                    break
            if not has_source_code and (path / "src").is_dir():
                for entry in (path / "src").iterdir():
                    if entry.is_file() and entry.suffix == ".py":
                        has_source_code = True
                        break
        except (OSError, PermissionError):
            pass
        if not has_source_code:
            return False

        indicators = 0
        if (path / ".git").exists():
            # .git is a strong indicator: project is under version control
            indicators += 2
        if (path / "tests").is_dir() or (path / "test").is_dir():
            indicators += 1
        if (path / "README.md").exists() or (path / "README.rst").exists():
            indicators += 1
        if (path / "poetry.lock").exists():
            indicators += 1

        return indicators >= 2

    def inspect(self, path: Path) -> EnvMetadata:
        version = self._read_python_version(path)
        venv_path = self._find_venv(path)
        interpreter = "python3"
        if venv_path:
            py = venv_path / python_bin_dir(venv_path) / python_exe_name()
            if py.exists():
                interpreter = str(py)
        return EnvMetadata(
            language="python",
            tool="poetry",
            version=version,
            path=str(venv_path or path),
            size_bytes=self._du(venv_path) if venv_path else self._du(path),
            interpreter_path=interpreter,
            packages_count=len(self.get_packages(path)),
        )

    def get_packages(self, path: Path) -> list[Package]:
        try:
            r = subprocess.run(
                ["poetry", "show", "--no-dev", "--format", "json"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=str(path),
            )
            if r.returncode == 0:
                data = json.loads(r.stdout)
                return [
                    Package(name=p["name"], version=p.get("version", "?"))
                    for p in data
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
            f"{p.name}=={p.version}"
            for p in sorted(packages, key=lambda x: x.name)
        )
        return FreezeResult(
            raw_content=raw, format="requirements.txt", packages=packages
        )

    def check_health(self, path: Path) -> HealthResult:
        venv = self._find_venv(path)
        if venv and (venv / python_bin_dir(venv) / python_exe_name()).exists():
            return HealthResult(status="healthy")
        try:
            subprocess.run(
                ["poetry", "--version"], capture_output=True, timeout=10
            )
            return HealthResult(status="healthy")
        except (
            OSError,
            subprocess.TimeoutExpired,
            subprocess.SubprocessError,
        ):
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
            if (
                c.exists()
                and (c / python_bin_dir(c) / python_exe_name()).exists()
            ):
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
