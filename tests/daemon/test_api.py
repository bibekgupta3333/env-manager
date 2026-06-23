"""Tests for daemon and API endpoints.

Requires FastAPI + httpx. Skipped if not installed.
"""

import subprocess
import sys

import pytest

try:
    from fastapi.testclient import TestClient

    from env_manager.daemon.server import app
except ImportError:
    pytest.skip("fastapi or httpx not installed", allow_module_level=True)

from env_manager.storage.database import (
    close_connection,
    get_connection,
    init_db,
)


@pytest.fixture
def db_path(tmp_path):
    p = str(tmp_path / "test_daemon.db")
    init_db(p)
    return p


@pytest.fixture
def client(db_path, monkeypatch):
    monkeypatch.setenv("ENVS_DB_PATH", db_path)
    monkeypatch.setattr(
        "env_manager.daemon.server.start_scheduler",
        lambda *a, **kw: None,
    )
    monkeypatch.setattr(
        "env_manager.daemon.server.stop_scheduler",
        lambda: None,
    )
    return TestClient(app)


@pytest.fixture
def seeded_client(tmp_path, monkeypatch):
    db = str(tmp_path / "test.db")
    init_db(db)
    monkeypatch.setenv("ENVS_DB_PATH", db)
    monkeypatch.setattr(
        "env_manager.daemon.server.start_scheduler",
        lambda *a, **kw: None,
    )
    monkeypatch.setattr(
        "env_manager.daemon.server.stop_scheduler",
        lambda: None,
    )

    # Create a real venv and scan
    proj = tmp_path / "test-proj"
    proj.mkdir()
    subprocess.run(
        [sys.executable, "-m", "venv", str(proj / ".venv")],
        capture_output=True,
    )

    from env_manager.adapters.registry import AdapterRegistry
    from env_manager.discovery.scanner import Scanner

    conn = get_connection(db)
    registry = AdapterRegistry(conn)
    scanner = Scanner(conn, registry.get_all_enabled())
    scanner.scan(str(tmp_path), depth=3)
    close_connection(db)

    return TestClient(app)


class TestStatusEndpoint:
    def test_status(self, client):
        resp = client.get("/api/status")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"


class TestHealthEndpoint:
    def test_health(self, client):
        resp = client.get("/api/health")
        assert resp.status_code == 200


class TestEnvsList:
    def test_envs_list(self, seeded_client):
        resp = seeded_client.get("/api/envs/")
        assert resp.status_code == 200
        data = resp.json()
        assert "environments" in data

    def test_envs_list_by_language(self, seeded_client):
        resp = seeded_client.get("/api/envs/?language=python")
        assert resp.status_code == 200
        data = resp.json()
        assert "environments" in data
        for env in data["environments"]:
            assert env["language"] == "python"


class TestProjectsList:
    def test_projects_list(self, seeded_client):
        resp = seeded_client.get("/api/projects/")
        assert resp.status_code == 200
        data = resp.json()
        assert "projects" in data


class TestDashboard:
    def test_dashboard_serves(self, client):
        resp = client.get("/")
        assert resp.status_code == 200
        from env_manager.daemon.server import DASHBOARD_DIR
        if DASHBOARD_DIR.exists():
            assert "env-manager" in resp.text.lower()
        else:
            data = resp.json()
            assert data.get("message") == "Dashboard not available"


class TestNotFound:
    def test_404(self, client):
        resp = client.get("/api/nonexistent")
        assert resp.status_code == 404
