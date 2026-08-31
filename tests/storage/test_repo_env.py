"""Tests for EnvironmentRepository."""

from env_manager.models.states import DiscoveryStatus, ManagementState
from env_manager.storage.database import (
    close_connection,
    get_connection,
    init_db,
)
from env_manager.storage.repo_env import EnvironmentRepository
from env_manager.storage.repo_project import ProjectRepository


def _setup(db_path):
    init_db(db_path)
    conn = get_connection(db_path)
    proj_repo = ProjectRepository(conn)
    pid = proj_repo.insert(name="test-project", path="/tmp/test-project")
    return conn, pid


def test_insert_and_get_env(db_path):
    conn, pid = _setup(db_path)
    repo = EnvironmentRepository(conn)

    env_id = repo.insert(
        project_id=pid,
        adapter="python.venv",
        env_type="project",
        path="/tmp/test-project/.venv",
        language="python",
        version="3.12.1",
        tool="venv",
        size_bytes=245_000_000,
        management_state=ManagementState.READY,
        discovery_status=DiscoveryStatus.TRACKED,
    )
    assert env_id > 0

    env = repo.get_by_id(env_id)
    assert env is not None
    assert env["language"] == "python"
    assert env["version"] == "3.12.1"
    assert env["management_state"] == "ready"
    assert env["project_id"] == pid

    conn.close()
    close_connection(db_path)


def test_list_by_language(db_path):
    conn, pid = _setup(db_path)
    repo = EnvironmentRepository(conn)

    repo.insert(
        project_id=pid,
        adapter="python.venv",
        env_type="project",
        path="/tmp/p1/.venv",
        language="python",
        version="3.12",
    )
    repo.insert(
        project_id=pid,
        adapter="node.nvm",
        env_type="runtime",
        path="/tmp/.nvm/v20",
        language="node",
        version="20.10",
    )

    python_envs = repo.list_by_language("python")
    assert len(python_envs) == 1

    all_envs = repo.list_all()
    assert len(all_envs) == 2

    conn.close()
    close_connection(db_path)


def test_get_by_path(db_path):
    conn, pid = _setup(db_path)
    repo = EnvironmentRepository(conn)

    repo.insert(
        project_id=pid,
        adapter="python.venv",
        env_type="project",
        path="/tmp/specific/.venv",
        language="python",
        version="3.12",
    )

    env = repo.get_by_path("/tmp/specific/.venv")
    assert env is not None
    assert env["language"] == "python"

    assert repo.get_by_path("/nonexistent") is None

    conn.close()
    close_connection(db_path)


def test_update_state(db_path):
    conn, pid = _setup(db_path)
    repo = EnvironmentRepository(conn)

    env_id = repo.insert(
        project_id=pid,
        adapter="python.venv",
        env_type="project",
        path="/tmp/p1/.venv",
        language="python",
        version="3.12",
    )

    repo.update_state(env_id, ManagementState.ERROR)
    env = repo.get_by_id(env_id)
    assert env["management_state"] == "error"

    conn.close()
    close_connection(db_path)


def test_update_discovery_status(db_path):
    conn, pid = _setup(db_path)
    repo = EnvironmentRepository(conn)

    env_id = repo.insert(
        project_id=pid,
        adapter="python.venv",
        env_type="project",
        path="/tmp/p1/.venv",
        language="python",
        version="3.12",
        discovery_status=DiscoveryStatus.UNTRACKED,
    )

    repo.update_discovery_status(env_id, DiscoveryStatus.TRACKED)
    env = repo.get_by_id(env_id)
    assert env["discovery_status"] == "tracked"

    conn.close()
    close_connection(db_path)


def test_touch_and_update_health(db_path):
    conn, pid = _setup(db_path)
    repo = EnvironmentRepository(conn)

    env_id = repo.insert(
        project_id=pid,
        adapter="python.venv",
        env_type="project",
        path="/tmp/p1/.venv",
        language="python",
        version="3.12",
    )

    repo.touch(env_id)
    env = repo.get_by_id(env_id)
    assert env["last_used_at"] is not None

    repo.update_health(env_id, "healthy")
    env = repo.get_by_id(env_id)
    assert env["last_health_result"] == "healthy"
    assert env["last_health_check"] is not None

    conn.close()
    close_connection(db_path)


def test_delete_env(db_path):
    conn, pid = _setup(db_path)
    repo = EnvironmentRepository(conn)

    env_id = repo.insert(
        project_id=pid,
        adapter="python.venv",
        env_type="project",
        path="/tmp/p1/.venv",
        language="python",
        version="3.12",
    )

    repo.delete(env_id)
    assert repo.get_by_id(env_id) is None

    conn.close()
    close_connection(db_path)


def test_set_orphaned(db_path):
    conn, pid = _setup(db_path)
    repo = EnvironmentRepository(conn)

    env_id = repo.insert(
        project_id=pid,
        adapter="python.venv",
        env_type="project",
        path="/tmp/p1/.venv",
        language="python",
        version="3.12",
    )

    repo.set_orphaned(env_id, True)
    env = repo.get_by_id(env_id)
    assert env["is_orphaned"] == 1

    repo.set_orphaned(env_id, False)
    env = repo.get_by_id(env_id)
    assert env["is_orphaned"] == 0

    conn.close()
    close_connection(db_path)
