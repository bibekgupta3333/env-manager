"""Python uv adapter — detects uv-managed virtual environments."""

from __future__ import annotations

from pathlib import Path

from env_manager.adapters.base import BaseAdapter
from env_manager.models.env import (
    EnvMetadata,
    FreezeResult,
    HealthResult,
    Package,
)


class PythonUvAdapter(BaseAdapter):
    name = "python.uv"
    display_name = "Python (uv)"
    version = "1.0.0"
    env_type = "project"

    def find_patterns(self) -> list[str]:
        return ["**/pyproject.toml", "**/.python-version"]

    def detect(self, path: Path) -> EnvMetadata | None:
        # uv projects: pyproject.toml OR .python-version + .venv
        toml = path / "pyproject.toml"
        ver_file = path / ".python-version"
        venv_dir = path / ".venv"

        is_uv = False
        if toml.exists():
            try:
                content = toml.read_text()
                if "[tool.uv]" in content:
                    is_uv = True
            except (OSError, UnicodeDecodeError):
                pass

        if not is_uv:
            return None

        if not self._is_real_python_project(path):
            return None

        version = "unknown"
        if ver_file.exists():
            version = ver_file.read_text().strip()
        elif venv_dir.exists():
            version = self._read_venv_version(venv_dir)

        return EnvMetadata(
            language="python",
            tool="uv",
            version=version,
            path=str(venv_dir if venv_dir.exists() else path),
            size_bytes=(
                self._du(venv_dir) if venv_dir.exists() else self._du(path)
            ),
            interpreter_path="python3",
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

        return indicators >= 2

    def inspect(self, path: Path) -> EnvMetadata:
        venv = path if path.name == ".venv" else path / ".venv"
        return EnvMetadata(
            language="python",
            tool="uv",
            version=(
                self._read_venv_version(venv) if venv.exists() else "unknown"
            ),
            path=str(venv if venv.exists() else path),
            size_bytes=self._du(venv) if venv.exists() else self._du(path),
            interpreter_path="python3",
        )

    def get_packages(self, path: Path) -> list[Package]:
        return []

    def freeze(self, path: Path) -> FreezeResult:
        return FreezeResult(
            raw_content="", format="pyproject.toml", packages=[]
        )

    def check_health(self, path: Path) -> HealthResult:
        venv = path if path.name == ".venv" else path / ".venv"
        if venv.exists() and (venv / "bin" / "python").exists():
            return HealthResult(status="healthy")
        return HealthResult(
            status="broken",
            errors=[".venv not found or missing python binary"],
        )

    def _read_venv_version(self, venv: Path) -> str:
        cfg = venv / "pyvenv.cfg"
        if cfg.exists():
            for line in cfg.read_text().splitlines():
                if line.strip().startswith("version"):
                    return line.split("=")[-1].strip()
        return "unknown"

    def _du(self, path: Path) -> int:
        total = 0
        try:
            for f in path.rglob("*"):
                if f.is_file() and not f.is_symlink():
                    total += f.stat().st_size
        except PermissionError:
            pass
        return total
