"""Tests for daemon and API endpoints."""

import pytest
from fastapi.testclient import TestClient

from env_manager.daemon.server import app
from env_manager.storage.database import init_db


@pytest.fixture
def db_path(tmp_path):
    p = str(tmp_path / "test_daemon.db")
    init_db(p)
    return p


@pytest.fixture
def client(db_path, monkeypatch):
    monkeypatch.setenv("ENVS_DB_PATH", db_path)
    monkeypatch.setattr(
        "env_manager.daemon.scheduler.start_scheduler",
        lambda *a, **kw: None,
    )
    monkeypatch.setattr(
        "env_manager.daemon.scheduler.stop_scheduler",
        lambda: None,
    )
    return TestClient(app)


class TestStatusEndpoint:
    def test_status(self, client):
        resp = client.get("/api/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"


class TestEnvsEndpoint:
    pass  # Requires DB seeding — tested via E2E


class TestProjectsEndpoint:
    pass  # Requires DB seeding — tested via E2E


class TestHealthEndpoint:
    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200


class TestPluginsEndpoint:
    pass  # Requires seeded DB — tested via CLI


class TestSnapshotsEndpoint:
    pass  # Requires seeded DB — tested via CLI
