"""asdf universal version manager adapter."""

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
from env_manager.platform import find_vm_path


class AsdfAdapter(BaseAdapter):
    """Detects asdf-managed runtime versions for any language."""

    name = "asdf.universal"
    display_name = "asdf (Universal)"
    version = "1.0.0"
    env_type = "runtime"

    def find_patterns(self) -> list[str]:
        patterns = ["**/.tool-versions"]
        asdf_root = find_vm_path("asdf") or Path.home() / ".asdf"
        if asdf_root.exists():
            patterns.insert(0, str(asdf_root / "installs"))
        return patterns

    def detect(self, path: Path) -> EnvMetadata | None:
        asdf_root = find_vm_path("asdf") or Path.home() / ".asdf"
        installs = asdf_root / "installs"

        # .tool-versions file → project using asdf
        tv = path / ".tool-versions"
        if tv.exists():
            return self._detect_tool_versions(tv, path)

        # asdf installs directory → installed runtimes
        if installs.exists() and str(path).startswith(str(installs)):
            return self._detect_installed_runtime(path, installs)

        return None

    def _detect_tool_versions(
        self, tv: Path, proj_path: Path
    ) -> EnvMetadata | None:
        try:
            for line in tv.read_text().splitlines():
                line = line.strip()
                if not line or line.startswith("#"):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    lang = parts[0]
                    version = parts[1]
                    return EnvMetadata(
                        language=lang,
                        tool="asdf",
                        version=version,
                        path=str(proj_path),
                        size_bytes=self._du(proj_path),
                        interpreter_path=lang,
                        env_type="project",
                    )
        except (OSError, UnicodeDecodeError):
            pass
        return None

    def _detect_installed_runtime(
        self, path: Path, installs: Path
    ) -> EnvMetadata | None:
        rel = path.relative_to(installs)
        parts = rel.parts
        if len(parts) >= 2:
            lang, version = parts[0], parts[1]
            return EnvMetadata(
                language=lang,
                tool="asdf",
                version=version,
                path=str(path),
                size_bytes=self._du(path),
                interpreter_path=str(path / "bin" / lang),
                env_type="runtime",
            )
        return None

    def inspect(self, path: Path) -> EnvMetadata:
        return EnvMetadata(
            language="unknown",
            tool="asdf",
            version="unknown",
            path=str(path),
            size_bytes=self._du(path),
            interpreter_path="",
            env_type="runtime",
        )

    def get_packages(self, path: Path) -> list[Package]:
        return []

    def freeze(self, path: Path) -> FreezeResult:
        return FreezeResult(
            raw_content="", format=".tool-versions", packages=[]
        )

    def check_health(self, path: Path) -> HealthResult:
        env_info = self.inspect(path)
        interp = env_info.interpreter_path
        if interp and Path(interp).exists() and os.access(interp, os.X_OK):
            return HealthResult(status="healthy")
        return HealthResult(
            status="broken", errors=[f"Interpreter not found: {interp}"]
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
