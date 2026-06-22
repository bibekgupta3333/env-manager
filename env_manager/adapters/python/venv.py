"""Python venv adapter — detects, inspects, manages virtual environments."""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

from env_manager.adapters.base import BaseAdapter
from env_manager.exceptions import AdapterError  # noqa: F401
from env_manager.models.env import (
    EnvMetadata,
    FreezeResult,
    HealthResult,
    Package,
)


class PythonVenvAdapter(BaseAdapter):
    name = "python.venv"
    display_name = "Python (venv)"
    version = "1.0.0"
    env_type = "local"

    def find_patterns(self) -> list[str]:
        return ["**/pyvenv.cfg"]

    def detect(self, path: Path) -> EnvMetadata | None:
        cfg = path / "pyvenv.cfg"
        if not cfg.exists():
            return None
        return EnvMetadata(
            language="python",
            tool="venv",
            version=self._read_version(path),
            path=str(path),
            size_bytes=self._du(path),
            interpreter_path=str(self._python_bin(path)),
        )

    def inspect(self, path: Path) -> EnvMetadata:
        return EnvMetadata(
            language="python",
            tool="venv",
            version=self._read_version(path),
            path=str(path),
            size_bytes=self._du(path),
            interpreter_path=str(self._python_bin(path)),
            packages_count=len(self.get_packages(path)),
        )

    def get_packages(self, path: Path) -> list[Package]:
        try:
            result = subprocess.run(
                [
                    str(self._python_bin(path)),
                    "-m",
                    "pip",
                    "list",
                    "--format",
                    "json",
                ],
                capture_output=True,
                text=True,
                timeout=30,
            )
            if result.returncode != 0:
                return []
            data = json.loads(result.stdout)
            return [
                Package(name=p["name"], version=p["version"]) for p in data
            ]
        except (subprocess.TimeoutExpired, Exception):
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
        checks: list[dict[str, Any]] = []
        errors: list[str] = []
        suggestions: list[str] = []

        py_bin = self._python_bin(path)
        if not py_bin.exists():
            errors.append(f"Python binary not found: {py_bin}")
            return HealthResult(
                status="broken",
                checks=checks,
                errors=errors,
                suggestions=[
                    "Recreate environment with envs lifecycle restore"
                ],
            )

        try:
            r = subprocess.run(
                [str(py_bin), "--version"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            checks.append(
                {"name": "python_binary", "passed": r.returncode == 0}
            )
            if r.returncode != 0:
                errors.append(f"python --version failed: {r.stderr}")
        except (subprocess.TimeoutExpired, subprocess.SubprocessError,
                OSError) as e:
            checks.append({"name": "python_binary", "passed": False})
            errors.append(str(e))

        try:
            r = subprocess.run(
                [str(py_bin), "-c", "import json; print('ok')"],
                capture_output=True,
                text=True,
                timeout=10,
            )
            checks.append({"name": "import_test", "passed": r.returncode == 0})
            if r.returncode != 0:
                errors.append(f"Import test failed: {r.stderr}")
        except (subprocess.TimeoutExpired, subprocess.SubprocessError,
                OSError) as e:
            checks.append({"name": "import_test", "passed": False})
            errors.append(str(e))

        status = "healthy" if len(errors) == 0 else "broken"
        return HealthResult(
            status=status,
            checks=checks,
            errors=errors,
            suggestions=suggestions,
        )

    def create(
        self, path: Path, config: dict[str, Any] | None = None
    ) -> EnvMetadata:
        version = (config or {}).get("version", "")
        # Try exact version first, then major.minor, then default python3
        candidates = []
        if version:
            candidates.append(f"python{version}")
            parts = version.split(".")
            if len(parts) >= 2:
                candidates.append(f"python{parts[0]}.{parts[1]}")
        candidates.append("python3")

        for python_bin in candidates:
            try:
                subprocess.run(
                    [python_bin, "-m", "venv", str(path)],
                    check=True,
                    capture_output=True,
                    text=True,
                    timeout=60,
                )
                break
            except (subprocess.CalledProcessError, FileNotFoundError):
                continue
        else:
            raise AdapterError(
                f"cannot create venv: no python binary "
                f"(tried {', '.join(candidates)})"
            )
        return self.inspect(path)

    def install(self, path: Path, packages: list[str]) -> None:
        pip_bin = str(self._python_bin(path).parent / "pip")
        try:
            subprocess.run(
                [pip_bin, "install"] + list(packages),
                check=True,
                capture_output=True,
                text=True,
                timeout=120,
            )
        except subprocess.CalledProcessError:
            subprocess.run(
                [str(self._python_bin(path)), "-m", "pip", "install"]
                + list(packages),
                check=True,
                capture_output=True,
                text=True,
                timeout=120,
            )

    def _read_version(self, path: Path) -> str:
        cfg = path / "pyvenv.cfg"
        if cfg.exists():
            for line in cfg.read_text().splitlines():
                if line.startswith("version"):
                    return line.split("=")[-1].strip()
        return "unknown"

    def _python_bin(self, path: Path) -> Path:
        if sys.platform == "win32":
            return path / "Scripts" / "python.exe"
        return path / "bin" / "python"

    def _du(self, path: Path) -> int:
        total = 0
        try:
            for f in path.rglob("*"):
                if f.is_file() and not f.is_symlink():
                    total += f.stat().st_size
        except PermissionError:
            pass
        return total
