"""Environment and project state enums."""

from enum import Enum


class ManagementState(str, Enum):
    """What can I DO with this environment?"""

    CREATING = "creating"
    READY = "ready"
    UPDATING = "updating"
    ERROR = "error"
    SNAPSHOTTED = "snapshotted"
    DELETED = "deleted"
    PURGED = "purged"


class DiscoveryStatus(str, Enum):
    """What do I KNOW about this environment?"""

    UNTRACKED = "untracked"
    TRACKED = "tracked"
    IGNORED = "ignored"
