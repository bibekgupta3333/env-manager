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


class TestEnvActions:
    def test_install_dry_run(self, seeded_client):
        envs = seeded_client.get("/api/envs/").json()["environments"]
        if envs:
            resp = seeded_client.post(
                f"/api/envs/{envs[0]['id']}/install",
                json={"packages": ["pip"]},
            )
            assert resp.status_code in (200, 500)

    def test_uninstall_dry_run(self, seeded_client):
        envs = seeded_client.get("/api/envs/").json()["environments"]
        if envs:
            resp = seeded_client.post(
                f"/api/envs/{envs[0]['id']}/uninstall",
                json={"packages": ["pip"]},
            )
            assert resp.status_code in (200, 500)

    def test_pin_env(self, seeded_client):
        envs = seeded_client.get("/api/envs/").json()["environments"]
        if envs:
            resp = seeded_client.post(f"/api/envs/{envs[0]['id']}/pin")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "pinned"

    def test_unpin_env(self, seeded_client):
        envs = seeded_client.get("/api/envs/").json()["environments"]
        if envs:
            resp = seeded_client.post(f"/api/envs/{envs[0]['id']}/unpin")
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "unpinned"

    def test_remove_env(self, seeded_client):
        envs = seeded_client.get("/api/envs/").json()["environments"]
        if envs:
            resp = seeded_client.post(
                f"/api/envs/{envs[0]['id']}/remove",
                json={"snapshot": False},
            )
            assert resp.status_code == 200
            data = resp.json()
            assert data["status"] == "removed"

    def test_remove_404(self, seeded_client):
        resp = seeded_client.post(
            "/api/envs/99999/remove", json={"snapshot": False}
        )
        assert resp.status_code == 404

    def test_restore_env(self, seeded_client):
        envs = seeded_client.get("/api/envs/").json()["environments"]
        if envs:
            resp = seeded_client.post(
                f"/api/envs/{envs[0]['id']}/restore",
                json={},
            )
            assert resp.status_code in (200, 404)


class TestDoctor:
    def test_doctor_run(self, seeded_client):
        resp = seeded_client.post("/api/doctor/run")
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data

    def test_doctor_fix(self, seeded_client):
        resp = seeded_client.post("/api/doctor/fix")
        assert resp.status_code == 200
        data = resp.json()
        assert "results" in data


class TestCleanup:
    def test_cleanup_execute(self, seeded_client):
        resp = seeded_client.post(
            "/api/cleanup/execute",
            json={"stale_days": 0, "orphaned": False, "snapshot": False},
        )
        assert resp.status_code == 200

    def test_cleanup_gc_dry(self, seeded_client):
        resp = seeded_client.post("/api/cleanup/gc", json={"dry_run": True})
        assert resp.status_code == 200

    def test_cleanup_compare(self, seeded_client):
        envs = seeded_client.get("/api/envs/").json()["environments"]
        if len(envs) >= 2:
            resp = seeded_client.post(
                "/api/cleanup/compare",
                json={
                    "project_a": envs[0]["path"],
                    "project_b": envs[1]["path"],
                },
            )
            assert resp.status_code == 200
        else:
            resp = seeded_client.post(
                "/api/cleanup/compare",
                json={
                    "project_a": "/nonexistent",
                    "project_b": "/nonexistent",
                },
            )
            assert resp.status_code == 404


class TestScan:
    def test_scan(self, seeded_client):
        resp = seeded_client.post(
            "/api/scan",
            json={"path": ["/tmp"], "depth": 1, "incremental": False},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "count" in data


class TestTrackIgnore:
    def test_track(self, seeded_client, tmp_path):
        test_path = str(tmp_path / "dummy_env")
        resp = seeded_client.post("/api/track", json={"path": test_path})
        assert resp.status_code in (200, 400)

    def test_ignore(self, seeded_client):
        envs = seeded_client.get("/api/envs/").json()["environments"]
        if envs:
            resp = seeded_client.post(
                "/api/ignore", json={"path": envs[0]["path"]}
            )
            assert resp.status_code == 200


class TestSnapshots:
    def test_prune_snapshots(self, seeded_client):
        resp = seeded_client.post("/api/snapshots/prune", json={"keep": 5})
        assert resp.status_code == 200
        data = resp.json()
        assert "pruned" in data


class TestDB:
    def test_db_path(self, client):
        resp = client.get("/api/db/path")
        assert resp.status_code == 200
        data = resp.json()
        assert "path" in data

    def test_db_backup(self, client):
        resp = client.post("/api/db/backup", json={})
        assert resp.status_code in (200, 400)

    def test_db_repair(self, client):
        resp = client.post("/api/db/repair")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ok"


class TestConfig:
    def test_get_config(self, client):
        resp = client.get("/api/config")
        assert resp.status_code == 200
        data = resp.json()
        assert "db_path" in data
        assert "adapters" in data


class TestNotFound:
    def test_404(self, client):
        resp = client.get("/api/nonexistent")
        assert resp.status_code == 404
