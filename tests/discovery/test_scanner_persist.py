"""Tests for scanner persistence."""

from env_manager.adapters.base import BaseAdapter
from env_manager.discovery.scanner import Scanner
from env_manager.models.env import EnvMetadata, FreezeResult, HealthResult


class FakePersistAdapter(BaseAdapter):
    name = "test.persist"
    display_name = "Test Persist"
    version = "0.1"
    env_type = "project"

    def find_patterns(self):
        return ["**/.test-env"]

    def detect(self, path):
        if (path / ".test-env").exists():
            return EnvMetadata(
                language="test",
                tool="persist",
                version="1.0",
                path=str(path),
                size_bytes=42_000,
                interpreter_path="/bin/test",
            )
        return None

    def inspect(self, path):
        return EnvMetadata(
            language="test",
            tool="persist",
            version="1.0",
            path=str(path),
            size_bytes=42_000,
            interpreter_path="/bin/test",
            packages_count=0,
        )

    def get_packages(self, path):
        return []

    def freeze(self, path):
        return FreezeResult(raw_content="", format="test.lock", packages=[])

    def check_health(self, path):
        return HealthResult(status="healthy")


def test_scanner_persists_to_db(tmp_path, db_connection):
    proj = tmp_path / "test-proj"
    proj.mkdir()
    (proj / ".test-env").touch()

    scanner = Scanner(db_connection, adapters=[FakePersistAdapter()])
    results = scanner.scan(str(tmp_path), depth=3)
    assert len(results) == 1

    # Verify it was persisted
    from env_manager.storage.repo_env import EnvironmentRepository
    from env_manager.storage.repo_project import ProjectRepository

    env_repo = EnvironmentRepository(db_connection)
    proj_repo = ProjectRepository(db_connection)

    # Check project was created (name is the parent directory)
    projects = proj_repo.list_all()
    assert len(projects) == 1

    # Check env was created
    all_envs = env_repo.list_all()
    assert len(all_envs) == 1
    assert all_envs[0]["language"] == "test"
    assert all_envs[0]["management_state"] == "ready"


def test_scanner_duplicate_doesnt_create(tmp_path, db_connection):
    proj = tmp_path / "test-proj"
    proj.mkdir()
    (proj / ".test-env").touch()

    scanner = Scanner(db_connection, adapters=[FakePersistAdapter()])
    scanner.scan(str(tmp_path), depth=3)

    # Second scan
    scanner.scan(str(tmp_path), depth=3)

    from env_manager.storage.repo_env import EnvironmentRepository

    env_repo = EnvironmentRepository(db_connection)
    all_envs = env_repo.list_all()
    assert len(all_envs) == 1  # No duplicates


def test_scanner_idempotent_scan(tmp_path, db_connection):
    proj = tmp_path / "idem-proj"
    proj.mkdir()
    (proj / ".test-env").touch()

    scanner = Scanner(db_connection, adapters=[FakePersistAdapter()])
    r1 = scanner.scan(str(tmp_path), depth=3)
    r2 = scanner.scan(str(tmp_path), depth=3)
    assert len(r1) == 1
    assert len(r2) == 1
