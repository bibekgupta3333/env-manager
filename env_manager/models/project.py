"""Project-related data models."""

from dataclasses import dataclass, field


@dataclass
class Project:
    name: str
    path: str
    tags: list[str] = field(default_factory=list)
    is_pinned: bool = False
