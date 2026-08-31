"""Typed dicts for environment and project row data."""

from typing import TypedDict


class EnvRowDict(TypedDict, total=False):
    """Dictionary representation of an environment database row."""

    id: int
    project_id: int | None
    adapter: str
    env_type: str
    path: str
    language: str
    version: str
    tool: str
    size_bytes: int
    management_state: str
    discovery_status: str
    is_orphaned: int
    last_used_at: str | None
    last_scanned_at: str | None
    last_health_check: str | None
    last_health_result: str | None
    metadata: str | None
    created_at: str | None
    updated_at: str | None
    project_name: str
    is_pinned: bool


class ProjectRowDict(TypedDict, total=False):
    """Dictionary representation of a project database row."""

    id: int
    name: str
    path: str
    tags: str | None
    is_pinned: int
    last_active: str | None
    created_at: str | None
    updated_at: str | None


class AdapterRowDict(TypedDict, total=False):
    """Dictionary representation of an adapter registry row."""

    name: str
    display_name: str
    enabled: int
    version: str
    env_type: str
    source: str
