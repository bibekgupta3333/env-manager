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
    env_type = "local"

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
                if "uv" in content.lower():
                    is_uv = True
            except Exception:
                pass

        if not is_uv and not (ver_file.exists() and venv_dir.exists()):
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
            size_bytes=self._du(venv_dir)
            if venv_dir.exists()
            else self._du(path),
            interpreter_path="python3",
        )

    def inspect(self, path: Path) -> EnvMetadata:
        venv = path if path.name == ".venv" else path / ".venv"
        return EnvMetadata(
            language="python",
            tool="uv",
            version=self._read_venv_version(venv)
            if venv.exists()
            else "unknown",
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
        return HealthResult(status="healthy")

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
