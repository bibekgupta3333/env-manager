"""Python conda adapter — detects conda environments."""

from __future__ import annotations

from pathlib import Path

from env_manager.adapters.base import BaseAdapter
from env_manager.models.env import (
    EnvMetadata,
    FreezeResult,
    HealthResult,
    Package,
)
from env_manager.platform import find_vm_path


class PythonCondaAdapter(BaseAdapter):
    name = "python.conda"
    display_name = "Python (conda)"
    version = "1.0.0"
    env_type = "global"

    def find_patterns(self) -> list[str]:
        conda_root = find_vm_path("conda")
        if conda_root and (conda_root / "envs").exists():
            return [str(conda_root / "envs")]
        home = Path.home()
        patterns = []
        conda_dirs = [
            "anaconda3/envs",
            "miniconda3/envs",
            "miniforge3/envs",
            "mambaforge/envs",
        ]
        for p in conda_dirs:
            if (home / p).exists():
                patterns.append(str(home / p))
        return patterns or ["**/conda-meta"]

    def detect(self, path: Path) -> EnvMetadata | None:
        conda_meta = path / "conda-meta"
        if conda_meta.exists() and conda_meta.is_dir():
            version = "unknown"
            history = path / "conda-meta" / "history"
            if history.exists():
                try:
                    for line in history.read_text().splitlines():
                        if "python" in line:
                            parts = line.split()
                            if len(parts) > 1:
                                version = parts[1]
                                break
                except (OSError, UnicodeDecodeError):
                    pass
            return EnvMetadata(
                language="python",
                tool="conda",
                version=version,
                path=str(path),
                size_bytes=self._du(path),
                interpreter_path=str(path / "bin" / "python"),
                env_type="global",
            )
        return None

    def inspect(self, path: Path) -> EnvMetadata:
        return EnvMetadata(
            language="python",
            tool="conda",
            version="unknown",
            path=str(path),
            size_bytes=self._du(path),
            interpreter_path=str(path / "bin" / "python"),
            env_type="global",
        )

    def get_packages(self, path: Path) -> list[Package]:
        return []

    def freeze(self, path: Path) -> FreezeResult:
        return FreezeResult(
            raw_content="", format="environment.yml", packages=[]
        )

    def check_health(self, path: Path) -> HealthResult:
        python_bin = path / "bin" / "python"
        if python_bin.exists():
            return HealthResult(status="healthy")
        return HealthResult(status="broken", errors=["python not found"])

    def _du(self, path: Path) -> int:
        total = 0
        try:
            for f in path.rglob("*"):
                if f.is_file() and not f.is_symlink():
                    total += f.stat().st_size
        except PermissionError:
            pass
        return total
