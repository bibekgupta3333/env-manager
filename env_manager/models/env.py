"""Environment-related data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Package:
    name: str
    version: str


@dataclass
class EnvMetadata:
    language: str
    tool: str
    version: str
    path: str
    size_bytes: int
    interpreter_path: str
    packages_count: int = 0
    env_type: str = "project"


@dataclass
class FreezeResult:
    raw_content: str
    format: str
    packages: list[Package] = field(default_factory=list)


@dataclass
class HealthResult:
    status: str  # "healthy" | "degraded" | "broken"
    checks: list[dict[str, Any]] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
