"""Tests for state enums and data models."""

from env_manager.models.env import (
    EnvMetadata,
    FreezeResult,
    HealthResult,
    Package,
)
from env_manager.models.project import Project
from env_manager.models.states import DiscoveryStatus, ManagementState


class TestManagementState:
    def test_values(self):
        assert ManagementState.CREATING.value == "creating"
        assert ManagementState.READY.value == "ready"
        assert ManagementState.UPDATING.value == "updating"
        assert ManagementState.ERROR.value == "error"
        assert ManagementState.SNAPSHOTTED.value == "snapshotted"
        assert ManagementState.DELETED.value == "deleted"
        assert ManagementState.PURGED.value == "purged"

    def test_restorable_states(self):
        restorable = {ManagementState.SNAPSHOTTED}
        assert ManagementState.READY not in restorable
        assert ManagementState.PURGED not in restorable

    def test_from_string(self):
        assert ManagementState("ready") == ManagementState.READY
        assert ManagementState("snapshotted") == ManagementState.SNAPSHOTTED


class TestDiscoveryStatus:
    def test_values(self):
        assert DiscoveryStatus.UNTRACKED.value == "untracked"
        assert DiscoveryStatus.TRACKED.value == "tracked"
        assert DiscoveryStatus.IGNORED.value == "ignored"

    def test_untracked_is_default(self):
        assert DiscoveryStatus.UNTRACKED != DiscoveryStatus.TRACKED


class TestEnvMetadata:
    def test_creation(self):
        meta = EnvMetadata(
            language="python",
            tool="venv",
            version="3.12.1",
            path="/home/user/projects/myapp/.venv",
            size_bytes=245_000_000,
            interpreter_path="/usr/bin/python3.12",
            packages_count=23,
        )
        assert meta.language == "python"
        assert meta.tool == "venv"
        assert meta.size_bytes == 245_000_000
        assert meta.env_type == "project"

    def test_default_env_type(self):
        meta = EnvMetadata(
            language="python",
            tool="venv",
            version="3.9",
            path="/tmp/.venv",
            size_bytes=0,
            interpreter_path="/bin/python",
        )
        assert meta.env_type == "project"

    def test_runtime_env_type(self):
        meta = EnvMetadata(
            language="node",
            tool="nvm",
            version="20.10.0",
            path="/home/user/.nvm/versions/node/v20.10.0",
            size_bytes=150_000_000,
            interpreter_path="/home/user/.nvm/versions/node/v20.10.0/bin/node",
            env_type="runtime",
        )
        assert meta.env_type == "runtime"


class TestPackage:
    def test_creation(self):
        pkg = Package(name="requests", version="2.31.0")
        assert pkg.name == "requests"
        assert pkg.version == "2.31.0"

    def test_equality(self):
        p1 = Package(name="a", version="1.0")
        p2 = Package(name="a", version="1.0")
        p3 = Package(name="a", version="2.0")
        assert p1 == p2
        assert p1 != p3


class TestFreezeResult:
    def test_creation(self):
        result = FreezeResult(
            raw_content="requests==2.31.0\n",
            format="requirements.txt",
            packages=[Package("requests", "2.31.0")],
        )
        assert result.format == "requirements.txt"
        assert len(result.packages) == 1


class TestHealthResult:
    def test_healthy(self):
        result = HealthResult(status="healthy")
        assert result.status == "healthy"
        assert len(result.errors) == 0

    def test_broken(self):
        result = HealthResult(
            status="broken",
            errors=["python binary missing"],
            suggestions=["Recreate environment"],
        )
        assert result.status == "broken"
        assert len(result.errors) == 1
        assert len(result.suggestions) == 1


class TestProject:
    def test_creation(self):
        proj = Project(name="myapp", path="/tmp/myapp", tags=["client-a"])
        assert proj.name == "myapp"
        assert proj.tags == ["client-a"]
        assert not proj.is_pinned

    def test_pinned(self):
        proj = Project(name="pinned", path="/tmp/p", is_pinned=True)
        assert proj.is_pinned
