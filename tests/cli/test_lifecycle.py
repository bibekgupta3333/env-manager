"""Integration tests for CLI lifecycle commands using real venvs."""

import json
import sys

import pytest
from typer.testing import CliRunner

from env_manager.cli.main import app
from env_manager.storage.database import init_db


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test_lifecycle.db")


@pytest.fixture
def runner(db_path, monkeypatch):
    """CLI runner with isolated test DB and ENVS_DB_PATH set."""
    init_db(db_path)
    monkeypatch.setenv("ENVS_DB_PATH", db_path)
    return CliRunner()


@pytest.fixture
def created_env(runner, tmp_path):
    """Create a real venv via lifecycle create and return project dir."""
    proj_dir = tmp_path / "proj"
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    result = runner.invoke(
        app,
        [
            "lifecycle",
            "create",
            f"python@{version}",
            str(proj_dir),
            "--confirm",
        ],
    )
    assert result.exit_code == 0, f"create failed: {result.output}"
    return proj_dir


def test_create_confirm(runner, tmp_path):
    """lifecycle create python@3.12 <tmp>/proj --confirm should succeed."""
    proj_dir = tmp_path / "proj2"
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    result = runner.invoke(
        app,
        [
            "lifecycle",
            "create",
            f"python@{version}",
            str(proj_dir),
            "--confirm",
        ],
    )
    assert result.exit_code == 0
    assert "Created:" in result.stdout
    assert (proj_dir / ".venv").exists()


def test_create_dry_run(runner, tmp_path):
    """lifecycle create python@3.12 <tmp>/proj --dry-run shows preview."""
    proj_dir = tmp_path / "proj3"
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    result = runner.invoke(
        app,
        [
            "lifecycle",
            "create",
            f"python@{version}",
            str(proj_dir),
            "--dry-run",
        ],
    )
    assert result.exit_code == 0
    assert "Would create" in result.stdout
    assert not (proj_dir / ".venv").exists()


def test_install_dry_run(runner, created_env):
    """lifecycle install <tmp>/proj httpx --dry-run shows Would install."""
    result = runner.invoke(
        app,
        ["lifecycle", "install", str(created_env), "httpx", "--dry-run"],
    )
    assert result.exit_code == 0
    assert "Would install" in result.stdout


def test_install_confirm(runner, created_env):
    """lifecycle install <tmp>/proj httpx --confirm installs package."""
    result = runner.invoke(
        app,
        ["lifecycle", "install", str(created_env), "httpx", "--confirm"],
    )
    assert result.exit_code == 0
    assert "Installed" in result.stdout


def test_export_spec(runner, created_env):
    """lifecycle export-spec <tmp>/proj outputs JSON with version key."""
    result = runner.invoke(
        app,
        ["lifecycle", "export-spec", str(created_env)],
    )
    assert result.exit_code == 0
    try:
        data = json.loads(result.stdout)
        assert "version" in data
    except json.JSONDecodeError:
        assert "version" in result.stdout


def test_activate(runner, created_env):
    """lifecycle activate <tmp>/proj outputs 'source' in result."""
    result = runner.invoke(
        app,
        ["lifecycle", "activate", str(created_env)],
    )
    assert result.exit_code == 0
    assert "source" in result.stdout


def test_remove_snapshot(runner, created_env):
    """lifecycle remove <tmp>/proj --snapshot --confirm removes env."""
    venv_dir = created_env / ".venv"
    assert venv_dir.exists()

    result = runner.invoke(
        app,
        [
            "lifecycle",
            "remove",
            str(created_env),
            "--snapshot",
            "--confirm",
        ],
    )
    assert (
        result.exit_code == 0
    ), f"stdout={result.stdout} stderr={result.stderr}"
    assert "Removed:" in result.stdout
    assert not venv_dir.exists()


def test_restore(runner, created_env):
    """lifecycle restore <tmp>/proj --confirm restores from snapshot."""
    venv_dir = created_env / ".venv"
    assert venv_dir.exists()

    # First snapshotted-remove
    remove_result = runner.invoke(
        app,
        [
            "lifecycle",
            "remove",
            str(created_env),
            "--snapshot",
            "--confirm",
        ],
    )
    assert remove_result.exit_code == 0
    assert not venv_dir.exists()

    # Then restore
    result = runner.invoke(
        app,
        ["lifecycle", "restore", str(created_env), "--confirm"],
    )
    assert (
        result.exit_code == 0
    ), f"stdout={result.stdout} stderr={result.stderr}"
    assert "Restored:" in result.stdout
    assert venv_dir.exists()
