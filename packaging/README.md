# Packaging & Distribution

env-manager is distributed through multiple channels:

## pip (PyPI)

```bash
pip install env-manager
```

## Homebrew (macOS)

```bash
brew tap bibekgupta3333/env-manager
brew install env-manager
```

## Direct Binary Download

Pre-built standalone binaries are available on [GitHub Releases](https://github.com/bibekgupta3333/env-manager/releases).

### macOS

```bash
curl -L https://github.com/bibekgupta3333/env-manager/releases/latest/download/envs-macos.tar.gz | tar xz
chmod +x envs
./envs --help
```

### Linux

```bash
curl -L https://github.com/bibekgupta3333/env-manager/releases/latest/download/envs-linux.tar.gz | tar xz
chmod +x envs
./envs --help
```

### Windows

Download `envs-windows.tar.gz` from GitHub Releases, extract it, and add the directory to your PATH.

## Build from Source

```bash
git clone https://github.com/bibekgupta3333/env-manager.git
cd env-manager
pip install -e .
```
