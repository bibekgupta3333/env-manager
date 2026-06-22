"""Base adapter protocol — all language adapters implement this."""

from __future__ import annotations

from abc import ABC, abstractmethod
from pathlib import Path
from typing import Any

from env_manager.exceptions import AdapterError
from env_manager.models.env import (
    EnvMetadata,
    FreezeResult,
    HealthResult,
    Package,
)


class InspectError(AdapterError):
    """Raised when an adapter cannot inspect an environment."""


class BaseAdapter(ABC):
    """Every language adapter must implement this protocol."""

    name: str = ""
    display_name: str = ""
    version: str = "0.1.0"
    env_type: str = "local"

    @abstractmethod
    def find_patterns(self) -> list[str]:
        """Glob patterns for scanner to find candidate paths."""

    @abstractmethod
    def detect(self, path: Path) -> EnvMetadata | None:
        """Is this path one of our environments? Returns metadata or None."""

    @abstractmethod
    def inspect(self, path: Path) -> EnvMetadata:
        """Full inspection: version, size, packages count."""

    @abstractmethod
    def get_packages(self, path: Path) -> list[Package]:
        """List installed packages with versions."""

    @abstractmethod
    def freeze(self, path: Path) -> FreezeResult:
        """Export lockfile + normalized package list."""

    @abstractmethod
    def check_health(self, path: Path) -> HealthResult:
        """Is this environment functional?"""

    def create(
        self, path: Path, config: dict[str, Any] | None = None
    ) -> EnvMetadata:
        raise NotImplementedError(f"{self.name} does not support create")

    def install(self, path: Path, packages: list[str]) -> None:
        raise NotImplementedError(f"{self.name} does not support install")

    def uninstall(self, path: Path, packages: list[str]) -> None:
        raise NotImplementedError(f"{self.name} does not support uninstall")

    def update(self, path: Path, packages: list[str] | None = None) -> None:
        raise NotImplementedError(f"{self.name} does not support update")

    def delete(self, path: Path) -> None:
        raise NotImplementedError(f"{self.name} does not support delete")

    def clone(self, source: Path, dest: Path) -> EnvMetadata:
        raise NotImplementedError(f"{self.name} does not support clone")
