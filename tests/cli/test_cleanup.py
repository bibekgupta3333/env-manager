"""Tests for cleanup CLI command."""

import sqlite3
import subprocess
import sys

import pytest
from typer.testing import CliRunner

from env_manager.cli.main import app
from env_manager.storage.database import init_db


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test_cleanup.db")


@pytest.fixture
def runner(db_path, monkeypatch):
    init_db(db_path)
    monkeypatch.setenv("ENVS_DB_PATH", db_path)
    return CliRunner()


class TestCleanup:
    def test_cleanup_dry_run(self, runner, db_path, tmp_path, monkeypatch):
        venv_path = tmp_path / "proj_stale" / ".venv"
        venv_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_path)], check=True
        )

        from env_manager.cli.commands import scan as scan_mod

        monkeypatch.setattr(scan_mod, "DEFAULT_SCAN_PATHS", [str(tmp_path)])
        result = runner.invoke(app, ["scan"])
        assert result.exit_code == 0

        conn = sqlite3.connect(db_path)
        conn.execute(
            "UPDATE environments SET last_used_at = '2020-01-01T00:00:00'"
        )
        conn.commit()
        conn.close()

        result = runner.invoke(app, ["cleanup", "--stale", "365", "--dry-run"])
        assert result.exit_code == 0
        assert "Would" in result.stdout

    def test_cleanup_gc_dry_run(self, runner):
        result = runner.invoke(
            app, ["cleanup", "--dry-run", "gc", "--dry-run"]
        )
        assert result.exit_code == 0
        assert "Would" in result.stdout

    def test_cleanup_compare(self, runner, tmp_path, monkeypatch):
        venv_a = tmp_path / "proj_a" / ".venv"
        venv_a.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_a)], check=True
        )

        venv_b = tmp_path / "proj_b" / ".venv"
        venv_b.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [sys.executable, "-m", "venv", str(venv_b)], check=True
        )

        from env_manager.cli.commands import scan as scan_mod

        monkeypatch.setattr(scan_mod, "DEFAULT_SCAN_PATHS", [str(tmp_path)])
        result = runner.invoke(app, ["scan"])
        assert result.exit_code == 0

        result = runner.invoke(
            app, ["cleanup", "--dry-run", "compare", "proj_a", "proj_b"]
        )
        assert result.exit_code == 0

    def test_cleanup_needs_confirm(self, runner):
        result = runner.invoke(app, ["cleanup", "--stale", "1"])
        assert result.exit_code != 0
