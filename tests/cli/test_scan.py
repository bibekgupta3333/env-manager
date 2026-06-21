"""Tests for CLI commands using typer CliRunner."""

import pytest
from typer.testing import CliRunner

from env_manager.cli.main import app
from env_manager.storage.database import init_db


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test_cli.db")


@pytest.fixture
def runner(db_path, monkeypatch):
    """CLI runner with isolated test DB and ENVS_DB_PATH set."""
    init_db(db_path)
    monkeypatch.setenv("ENVS_DB_PATH", db_path)
    return CliRunner()


def test_scan_finds_fake_envs(runner, tmp_path, monkeypatch):
    py_proj = tmp_path / "py-project"
    py_proj.mkdir()
    (py_proj / "pyvenv.cfg").write_text("version = 3.9.0\n")

    from env_manager.cli.commands import scan as scan_mod
    monkeypatch.setattr(scan_mod, "DEFAULT_SCAN_PATHS", [str(tmp_path)])

    result = runner.invoke(app, ["scan"])
    assert result.exit_code == 0


def test_list_after_scan(runner, tmp_path, monkeypatch):
    py_proj = tmp_path / "py-proj"
    py_proj.mkdir()
    (py_proj / "pyvenv.cfg").write_text("version = 3.12.0\n")

    from env_manager.cli.commands import scan as scan_mod
    monkeypatch.setattr(scan_mod, "DEFAULT_SCAN_PATHS", [str(tmp_path)])

    runner.invoke(app, ["scan"])

    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0


def test_list_empty(runner):
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0


def test_plugins_list(runner):
    result = runner.invoke(app, ["plugins", "list"])
    assert result.exit_code == 0


def test_config_show(runner):
    result = runner.invoke(app, ["config", "show"])
    assert result.exit_code == 0
