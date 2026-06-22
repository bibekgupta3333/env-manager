"""Cross-platform utilities — paths, binaries, and shell helpers per OS."""

import os
import sys
from pathlib import Path


def is_windows() -> bool:
    return sys.platform == "win32"


def is_macos() -> bool:
    return sys.platform == "darwin"


def is_linux() -> bool:
    return sys.platform.startswith("linux")


def home_dir() -> Path:
    """User home directory, cross-platform."""
    return Path.home()


def app_data_dir() -> Path:
    """Platform-appropriate app data directory for env-manager."""
    if is_windows():
        base = os.environ.get(
            "APPDATA",
            str(Path.home() / "AppData" / "Roaming"),
        )
        return Path(base) / "env-manager"
    if is_macos():
        return Path.home() / "Library" / "Application Support" / "env-manager"
    # Linux: XDG_DATA_HOME or ~/.local/share
    xdg = os.environ.get("XDG_DATA_HOME", "")
    if xdg:
        return Path(xdg) / "env-manager"
    return Path.home() / ".local" / "share" / "env-manager"


def default_db_path() -> str:
    return str(app_data_dir() / "envs.db")


def python_bin_dir(venv_path: Path) -> str:
    """Path to the bin/Scripts directory inside a venv."""
    if is_windows():
        return "Scripts"
    return "bin"


def python_exe_name() -> str:
    """Python executable name for current platform."""
    if is_windows():
        return "python.exe"
    return "python"


def pip_exe_name() -> str:
    """pip executable name for current platform."""
    if is_windows():
        return "pip.exe"
    return "pip"


def node_exe_name() -> str:
    """Node executable name for current platform."""
    if is_windows():
        return "node.exe"
    return "node"


def get_activate_cmd(venv_path: Path, language: str) -> str | None:
    """Return shell activation command for a given language/env."""
    if language == "python":
        if is_windows():
            activate_bat = venv_path / "Scripts" / "activate.bat"
            if activate_bat.exists():
                return str(activate_bat)
            ps1 = venv_path / "Scripts" / "Activate.ps1"
            if ps1.exists():
                return str(ps1)
            return None
        activate_sh = venv_path / "bin" / "activate"
        if activate_sh.exists():
            return f"source {activate_sh}"
        return None
    if language == "node":
        bin_dir = venv_path / python_bin_dir(venv_path)
        if bin_dir.exists():
            if is_windows():
                return str(bin_dir)
            return f"export PATH='{bin_dir}:$PATH'"
    return None


def system_excludes() -> list[str]:
    """Paths to skip during scanning, per platform."""
    common = ["/proc", "/sys", "/dev"]
    if is_macos():
        return common + [
            "/System",
            "/Library/Developer",
            "/Library/Apple",
            "/opt/homebrew/Cellar",
            "/opt/homebrew/Library",
            "/usr/local/Cellar",
            "/usr/local/Homebrew",
            "/Applications/Xcode.app",
        ]
    if is_linux():
        return common + [
            "/usr/lib",
            "/usr/share",
            "/usr/include",
            "/usr/src",
            "/boot",
            "/etc",
            "/lost+found",
            "/snap",
            "/var",
            "/run",
            "/tmp/.X11-unix",
            "/home/linuxbrew/.linuxbrew/Cellar",
        ]
    if is_windows():
        return [
            "C:\\Windows",
            "C:\\Program Files",
            "C:\\Program Files (x86)",
            "C:\\ProgramData",
            "C:\\$Recycle.Bin",
            "C:\\System Volume Information",
        ]
    return common


def version_manager_paths() -> dict[str, list[str]]:
    """Known version manager install paths per platform."""
    home = str(home_dir())
    if is_windows():
        roaming = os.environ.get(
            "APPDATA",
            str(Path.home() / "AppData" / "Roaming"),
        )
        appdata = roaming
        local_appdata = os.environ.get(
            "LOCALAPPDATA",
            str(Path.home() / "AppData" / "Local"),
        )
        return {
            "nvm": [f"{appdata}\\nvm", f"{local_appdata}\\nvm"],
            "fnm": [f"{appdata}\\fnm", f"{local_appdata}\\fnm"],
            "volta": [f"{appdata}\\Volta", f"{local_appdata}\\Volta"],
            "pyenv": [f"{home}\\.pyenv"],
            "rbenv": [],  # Not available on Windows natively
            "rvm": [],  # Not available on Windows natively
            "conda": [
                f"{home}\\anaconda3",
                f"{home}\\miniconda3",
                f"{home}\\miniforge3",
            ],
            "rustup": [f"{home}\\.rustup"],
        }
    # Unix (macOS + Linux)
    linuxbrew = "/home/linuxbrew/.linuxbrew" if is_linux() else None
    paths = {
        "nvm": [f"{home}/.nvm"],
        "fnm": [f"{home}/.fnm", f"{home}/.local/share/fnm"],
        "volta": [f"{home}/.volta"],
        "pyenv": [f"{home}/.pyenv"],
        "rbenv": [f"{home}/.rbenv"],
        "rvm": [f"{home}/.rvm"],
        "conda": [
            f"{home}/anaconda3",
            f"{home}/miniconda3",
            f"{home}/miniforge3",
            f"{home}/mambaforge",
        ],
        "rustup": [f"{home}/.rustup"],
        "goenv": [f"{home}/.goenv"],
    }
    if linuxbrew:
        for key in paths:
            paths[key].append(
                paths[key][0].replace(home, linuxbrew)
                if paths[key]
                else ""
            )
    return paths


def find_vm_path(vm_name: str, *subpath: str) -> Path | None:
    """Find a version manager install path on any platform.

    Example: find_vm_path("nvm") → ~/.nvm or %APPDATA%/nvm
    """
    paths = version_manager_paths()
    candidates = paths.get(vm_name, [])
    for base in candidates:
        full = Path(base, *subpath)
        if full.exists():
            return full
    return None
