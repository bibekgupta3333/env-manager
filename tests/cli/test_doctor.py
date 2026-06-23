"""Tests for doctor CLI command."""

import subprocess

import pytest
from typer.testing import CliRunner

from env_manager.cli.main import app
from env_manager.storage.database import init_db


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test_doctor.db")


@pytest.fixture
def runner(db_path, monkeypatch):
    init_db(db_path)
    monkeypatch.setenv("ENVS_DB_PATH", db_path)
    return CliRunner()


class TestDoctor:
    def test_doctor_all_on_empty_db(self, runner):
        result = runner.invoke(app, ["doctor", "--all"])
        assert result.exit_code == 0
        assert (
            "No environments" in result.stdout
            or "no environments" in result.stdout
        )

    def test_doctor_detects_broken_env(self, runner, tmp_path, monkeypatch):
        venv_path = tmp_path / "proj_broken" / ".venv"
        venv_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["python3", "-m", "venv", str(venv_path)], check=True)

        from env_manager.cli.commands import scan as scan_mod

        monkeypatch.setattr(scan_mod, "DEFAULT_SCAN_PATHS", [str(tmp_path)])
        result = runner.invoke(app, ["scan"])
        assert result.exit_code == 0

        python_bin = venv_path / "bin" / "python"
        python_bin.unlink()

        result = runner.invoke(app, ["doctor", "--all"])
        assert result.exit_code == 0
        assert "broken" in result.stdout

    def test_doctor_detects_healthy_env(self, runner, tmp_path, monkeypatch):
        venv_path = tmp_path / "proj_healthy" / ".venv"
        venv_path.parent.mkdir(parents=True, exist_ok=True)
        subprocess.run(["python3", "-m", "venv", str(venv_path)], check=True)

        from env_manager.cli.commands import scan as scan_mod

        monkeypatch.setattr(scan_mod, "DEFAULT_SCAN_PATHS", [str(tmp_path)])
        result = runner.invoke(app, ["scan"])
        assert result.exit_code == 0

        result = runner.invoke(app, ["doctor", "--all"])
        assert result.exit_code == 0
        assert "healthy" in result.stdout
