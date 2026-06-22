"""Tests for cross-platform utilities."""

import sys
from pathlib import Path

from env_manager.platform import (
    app_data_dir,
    default_db_path,
    find_vm_path,
    get_activate_cmd,
    is_linux,
    is_macos,
    is_windows,
    python_bin_dir,
    python_exe_name,
    system_excludes,
    version_manager_paths,
)


class TestPlatformDetection:
    def test_is_windows(self):
        assert isinstance(is_windows(), bool)

    def test_is_macos(self):
        assert isinstance(is_macos(), bool)

    def test_is_linux(self):
        assert isinstance(is_linux(), bool)

    def test_exactly_one_platform(self):
        results = [is_windows(), is_macos(), is_linux()]
        assert sum(results) == 1


class TestPythonBin:
    def test_python_exe_name(self):
        name = python_exe_name()
        assert name in ("python", "python.exe")

    def test_python_bin_dir(self):
        d = python_bin_dir(Path("/tmp/venv"))
        assert d in ("bin", "Scripts")


class TestAppDataDir:
    def test_returns_path(self):
        d = app_data_dir()
        assert isinstance(d, Path)
        assert "env-manager" in str(d)

    def test_default_db_path(self):
        p = default_db_path()
        assert p.endswith("envs.db")


class TestSystemExcludes:
    def test_returns_list(self):
        excl = system_excludes()
        assert isinstance(excl, list)
        assert len(excl) > 0

    def test_contains_common(self):
        excl = system_excludes()
        assert "/proc" in excl
        assert "/sys" in excl
        assert "/dev" in excl


class TestVersionManagerPaths:
    def test_returns_dict(self):
        paths = version_manager_paths()
        assert isinstance(paths, dict)
        assert "nvm" in paths
        assert "pyenv" in paths

    def test_all_vms_present(self):
        paths = version_manager_paths()
        expected = [
            "nvm", "fnm", "volta", "pyenv", "rbenv",
            "rvm", "conda", "rustup", "goenv",
        ]
        for vm in expected:
            assert vm in paths, f"{vm} missing from version_manager_paths"

    def test_paths_are_strings(self):
        paths = version_manager_paths()
        for vm, candidates in paths.items():
            for c in candidates:
                assert isinstance(c, str) or c == "", f"{vm}: {c}"


class TestFindVmPath:
    def test_returns_none_for_nonexistent(self):
        result = find_vm_path("nvm", "nonexistent", "path", "xyz")
        assert result is None

    def test_returns_path_for_existing(self, tmp_path):
        # Create a fake nvm install
        nvm_dir = tmp_path / ".nvm" / "versions" / "node" / "v20.0.0"
        nvm_dir.mkdir(parents=True)

        # Monkey-patch version_manager_paths for this test
        import env_manager.platform as plat
        original = plat.version_manager_paths
        plat.version_manager_paths = lambda: {
            "nvm": [str(tmp_path / ".nvm")]
        }
        try:
            result = find_vm_path("nvm", "versions", "node", "v20.0.0")
            assert result is not None
            assert result.exists()
        finally:
            plat.version_manager_paths = original


class TestActivateCmd:
    def test_python_venv_activate(self, tmp_path):
        venv = tmp_path / ".venv"
        venv.mkdir()
        bin_dir = venv / "bin"
        bin_dir.mkdir()
        (bin_dir / "activate").touch()

        cmd = get_activate_cmd(venv, "python")
        assert cmd is not None
        assert "activate" in cmd

    def test_activate_returns_none_for_missing(self, tmp_path):
        cmd = get_activate_cmd(tmp_path / "nonexistent", "python")
        assert cmd is None

    def test_node_activate(self, tmp_path):
        proj = tmp_path / "node-proj"
        proj.mkdir()
        bin_dir = proj / "bin"
        bin_dir.mkdir()

        cmd = get_activate_cmd(proj, "node")
        if sys.platform == "win32":
            assert cmd is not None
        else:
            assert cmd is not None
            assert "PATH" in cmd

    def test_unknown_language(self, tmp_path):
        cmd = get_activate_cmd(tmp_path, "erlang")
        assert cmd is None
