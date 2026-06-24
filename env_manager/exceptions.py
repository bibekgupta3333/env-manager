"""Exception hierarchy for env-manager."""


class EnvManagerError(Exception):
    """Base exception for all env-manager errors."""


class AdapterError(EnvManagerError):
    """Errors from language adapters (detect, inspect, health, etc.)."""


class StorageError(EnvManagerError):
    """Errors from storage layer (database, filesystem)."""


class ConfigError(EnvManagerError):
    """Errors from configuration."""
