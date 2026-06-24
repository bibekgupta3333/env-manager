"""Tests for SnapshotRepository."""

from env_manager.storage.database import (
    close_connection,
    get_connection,
    init_db,
)
from env_manager.storage.repo_env import EnvironmentRepository
from env_manager.storage.repo_project import ProjectRepository
from env_manager.storage.repo_snapshot import SnapshotRepository


def _setup(db_path):
    init_db(db_path)
    conn = get_connection(db_path)
    proj_repo = ProjectRepository(conn)
    env_repo = EnvironmentRepository(conn)
    pid = proj_repo.insert(name="test", path="/tmp/test")
    eid = env_repo.insert(
        project_id=pid,
        adapter="python.venv",
        env_type="project",
        path="/tmp/test/.venv",
        language="python",
        version="3.12",
    )
    return conn, eid


def test_insert_and_retrieve(db_path):
    conn, eid = _setup(db_path)
    repo = SnapshotRepository(conn)

    snap_id, version = repo.insert(eid, frozen_deps={"requests": "2.31.0"})
    assert snap_id > 0
    assert version == 1

    snap = repo.get_latest(eid)
    assert snap is not None
    assert snap["version"] == 1

    conn.close()
    close_connection(db_path)


def test_version_increments(db_path):
    conn, eid = _setup(db_path)
    repo = SnapshotRepository(conn)

    _, v1 = repo.insert(eid, frozen_deps={"a": "1.0"})
    _, v2 = repo.insert(eid, frozen_deps={"a": "2.0"})
    _, v3 = repo.insert(eid, frozen_deps={"a": "3.0"})

    assert v1 == 1
    assert v2 == 2
    assert v3 == 3

    latest = repo.get_latest(eid)
    assert latest is not None

    conn.close()
    close_connection(db_path)


def test_get_by_version(db_path):
    conn, eid = _setup(db_path)
    repo = SnapshotRepository(conn)

    repo.insert(eid, frozen_deps={"v": "1"})
    repo.insert(eid, frozen_deps={"v": "2"})

    snap = repo.get_by_env_and_version(eid, 1)
    assert snap is not None

    conn.close()
    close_connection(db_path)


def test_list_by_env(db_path):
    conn, eid = _setup(db_path)
    repo = SnapshotRepository(conn)

    repo.insert(eid, frozen_deps={"v": "1"})
    repo.insert(eid, frozen_deps={"v": "2"})

    snapshots = repo.list_by_env(eid)
    assert len(snapshots) == 2
    assert snapshots[0]["version"] == 2  # newest first

    conn.close()
    close_connection(db_path)


def test_prune(db_path):
    conn, eid = _setup(db_path)
    repo = SnapshotRepository(conn)

    for i in range(10):
        repo.insert(eid, frozen_deps={"v": str(i)})

    repo.prune(eid, keep=3)
    snapshots = repo.list_by_env(eid)
    assert len(snapshots) == 3
    assert snapshots[0]["version"] == 10

    conn.close()
    close_connection(db_path)
