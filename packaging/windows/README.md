# Windows Installer

## Prerequisites

- [NSIS](https://nsis.sourceforge.io/Download) (Nullsoft Scriptable Install System)
- The `EnvVarUpdate` plugin (bundled with NSIS, or install from `nsis-plugin-envarupdate`)
- `envs.exe` built via PyInstaller (run `make binary` on Windows, or download from a GitHub release)

## Build

```bash
# Copy the PyInstaller-built binary into this directory
copy dist\envs-dist\envs.exe packaging\windows\

# Build the installer
makensis packaging\windows\envs.nsi
```

Output: `envs-setup.exe`

## Manual Installation

If you prefer to install manually without the NSIS installer:

```powershell
# Download and extract
tar -xzf envs-windows.tar.gz
mkdir "$env:LOCALAPPDATA\env-manager"
move envs.exe "$env:LOCALAPPDATA\env-manager\"

# Add to user PATH
[Environment]::SetEnvironmentVariable(
    "Path",
    "$env:Path;$env:LOCALAPPDATA\env-manager",
    "User"
)
```

After a new terminal session, `envs` will be available on your PATH.

## CI Integration

The GitHub Actions release workflow (`.github/workflows/release.yml`) builds the
NSIS installer automatically when a `v*` tag is pushed. The resulting
`envs-setup.exe` is attached to the GitHub release.
