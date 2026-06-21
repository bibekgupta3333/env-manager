"""Tests for ProjectRepository."""

from env_manager.storage.database import close_connection, get_connection, init_db
from env_manager.storage.repo_project import ProjectRepository


def test_insert_and_get(db_path):
    init_db(db_path)
    conn = get_connection(db_path)
    repo = ProjectRepository(conn)

    pid = repo.insert(name="myapp", path="/tmp/myapp", tags=["client-a"])
    assert pid > 0

    proj = repo.get_by_id(pid)
    assert proj is not None
    assert proj["name"] == "myapp"
    assert proj["is_pinned"] == 0

    conn.close()
    close_connection(db_path)


def test_get_by_path(db_path):
    init_db(db_path)
    conn = get_connection(db_path)
    repo = ProjectRepository(conn)

    repo.insert(name="a", path="/tmp/a")
    proj = repo.get_by_path("/tmp/a")
    assert proj is not None
    assert proj["name"] == "a"

    assert repo.get_by_path("/nonexistent") is None

    conn.close()
    close_connection(db_path)


def test_get_or_create(db_path):
    init_db(db_path)
    conn = get_connection(db_path)
    repo = ProjectRepository(conn)

    pid1, created1 = repo.get_or_create(name="first", path="/tmp/first")
    assert created1 is True

    pid2, created2 = repo.get_or_create(name="first", path="/tmp/first")
    assert created2 is False
    assert pid1 == pid2

    conn.close()
    close_connection(db_path)


def test_set_pinned(db_path):
    init_db(db_path)
    conn = get_connection(db_path)
    repo = ProjectRepository(conn)

    pid = repo.insert(name="p", path="/tmp/p")
    repo.set_pinned(pid, True)
    proj = repo.get_by_id(pid)
    assert proj["is_pinned"] == 1

    repo.set_pinned(pid, False)
    proj = repo.get_by_id(pid)
    assert proj["is_pinned"] == 0

    conn.close()
    close_connection(db_path)


def test_list_all(db_path):
    init_db(db_path)
    conn = get_connection(db_path)
    repo = ProjectRepository(conn)

    repo.insert(name="b", path="/tmp/b")
    repo.insert(name="a", path="/tmp/a")

    projects = repo.list_all()
    assert len(projects) == 2
    assert projects[0]["name"] == "a"  # alphabetical

    conn.close()
    close_connection(db_path)
