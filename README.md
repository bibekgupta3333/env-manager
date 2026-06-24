# env-manager

Cross-language virtual environment manager — CLI + localhost dashboard. Discover, manage, health-check, snapshot, and clean up environments across Python, Node, Ruby, Go, and Rust.

[![CI](https://github.com/bibekgupta3333/env-manager/actions/workflows/ci.yml/badge.svg)](https://github.com/bibekgupta3333/env-manager/actions/workflows/ci.yml)
[![PyPI](https://img.shields.io/pypi/v/env-manager)](https://pypi.org/project/env-manager/)

---

## Install

```bash
pip install env-manager
```

Or via Homebrew, direct binary download, or from source — see [packaging/README.md](packaging/README.md).

```bash
brew tap bibekgupta3333/env-manager && brew install env-manager
```

## Quick Start

```bash
envs scan                          # discover all environments on your machine
envs list --by-project             # see everything grouped
envs doctor --all                  # health check every environment
```

## Dashboard

```bash
make run-daemon                    # starts at http://localhost:9876
```

Dark-themed React SPA with sidebar navigation, summary cards, filterable environment table with size bars, health check runner, cleanup flow with dry-run preview, and snapshot management with restore.

## Full CLI Reference

```bash
# Discovery
envs scan [--path /path] [--depth N] [--incremental]
envs list [--by-project] [--stale] [--orphaned] [--lang python] [--limit N] [--json]
envs info <project> [--json]
envs versions [--lang python]
envs track <path>
envs ignore <path>

# Lifecycle
envs lifecycle create python@3.12 [path] [--confirm]
envs lifecycle install <project> <packages...> [--confirm]
envs lifecycle uninstall <project> <packages...> [--confirm]
envs lifecycle remove <project> [--snapshot] [--confirm]
envs lifecycle restore <project> [--snapshot N] [--confirm]
envs lifecycle export-spec <project> [-o file.json]
envs lifecycle import-spec <file.json> [path] [--confirm]
envs lifecycle activate <project>     # use: eval "$(envs lifecycle activate <p>)"

# Health & Cleanup
envs doctor [--all] [--fix]
envs cleanup [--stale N] [--orphaned] [--snapshot] [--dry-run|--confirm]
envs cleanup compare <project-a> <project-b>
envs cleanup gc [--dry-run|--confirm]

# Favorites
envs pin <project>
envs unpin <project>

# Database
envs db backup [--path /backup/file]
envs db restore <backup> --confirm
envs db path
envs db repair

# Shell Integration
envs hook --install
envs hook --uninstall

# Plugins
envs plugins list
envs plugins enable <name>
envs plugins disable <name>

# Config
envs config show
```

## Supported Languages

| Language | Adapters | Count |
|----------|----------|:-----:|
| Python | venv, poetry, uv, pipenv, pyenv, conda | 6 |
| Node.js | nvm, fnm, volta, n | 4 |
| Ruby | rbenv, rvm | 2 |
| Go | goenv | 1 |
| Rust | rustup | 1 |
| Universal | asdf | 1 |

All 15 adapters auto-detect environments from their native files — `.nvmrc`, `Pipfile`, `pyproject.toml`, `.tool-versions`, etc. Disable any with `envs plugins disable <name>`.

## Features

### Discovery & Visibility
- **Cross-language scan** — one command finds Python venvs, Node nvm/fnm installs, Ruby rbenv versions, Go/Rust toolchains, asdf-managed runtimes
- **15 built-in adapters** — auto-detect environments from native files (`.nvmrc`, `Pipfile`, `pyproject.toml`, `.tool-versions`, etc.)
- **Incremental scan** — `--incremental` skips directories unchanged since last scan
- **Per-language control** — disable adapters you don't use; reduces scan time and noise
- **Manual registration** — `envs track <path>` and `envs ignore <path>` for explicit control
- **Grouped listing** — `envs list --by-project` with pin ★ indicators
- **Search & filter** — `--lang python`, `--stale`, `--orphaned`, `--limit N`, `--offset M`
- **Scriptable output** — `--json` flag on list and info commands
- **Version overview** — `envs versions` shows installed runtimes across pyenv, nvm, fnm, rbenv, rvm, asdf

### Environment Management
- **Create** — `envs lifecycle create python@3.12` works across all languages
- **Install/Uninstall packages** — delegates to pip, npm, gem, cargo per adapter
- **Update** — bulk update all or specific packages
- **Clone** — duplicate an environment to a new path
- **Export/Import** — portable JSON blueprints for sharing or backup
- **Shell activation** — `eval "$(envs lifecycle activate <project>)"` pattern
- **Subshell** — `envs lifecycle shell <project>` spawns a shell with env active

### Health & Safety
- **Health checks** — `envs doctor` detects broken envs (missing binaries, import failures, segfaults)
- **Auto-fix suggestions** — doctor recommends restore paths for broken envs
- **Safe cleanup** — snapshot exact dependency blueprint before deleting; restore in seconds
- **Versioned snapshots** — append-only history (v1, v2, v3...), prunable
- **Batch cleanup** — `envs cleanup --stale 60 --snapshot` across all languages
- **Pin protection** — `envs pin` projects are never cleanup candidates
- **Garbage collection** — `envs cleanup gc` purges soft-deleted environments
- **Environment diff** — `envs cleanup compare A B` shows package differences
- **Dry-run everywhere** — `--dry-run` / `--confirm` on all destructive commands

### Dashboard
- **React SPA** — dark-themed, collapsible sidebar, keyboard-navigable
- **Summary cards** — total environments, healthy, broken, disk usage
- **Environment table** — searchable, filterable, with size bar visualization and status badges
- **Detail panel** — slide-in with packages, health, and actions tabs
- **Doctor view** — auto-runs health checks with progress indicator
- **Cleanup flow** — auto-preview candidates, checkbox selection, size savings preview
- **Snapshots view** — restore or prune from web UI
- **Real-time** — WebSocket connection status indicator
- **Toast notifications** — success, error, info with auto-dismiss

### Platform & Distribution
- **macOS, Linux, Windows** — correct paths, version manager locations, system exclusions per OS
- **pip install** — `pip install env-manager`
- **Homebrew** — `brew tap bibekgupta3333/env-manager && brew install env-manager`
- **Standalone binary** — PyInstaller builds for all 3 OSes via GitHub Releases
- **Windows installer** — NSIS `.exe` with PATH integration, Start Menu, uninstaller
- **Zero dependencies** — single binary, no Python required to run

### Developer Experience
- **Shell hooks** — opt-in auto-detection on `cd` (bash, zsh, fish, PowerShell, CMD)
- **Database management** — `envs db backup/restore/path/repair` commands
- **Plugin architecture** — community adapters via `pip install envs-plugin-*`
- **PEP 8 compliant** — 79-char line length, ruff + flake8 + mypy strict
- **144 tests** — 135 Python + 9 React, CI on 3 OS × 3 Python versions
- **Publishing pipeline** — `make bump-patch` → tag → PyPI OIDC + GitHub Release + binaries

## Development

```bash
git clone https://github.com/bibekgupta3333/env-manager.git
cd env-manager
bash scripts/dev-setup.sh

make check        # lint + flake8 + shellcheck + typecheck + test
make test         # pytest only
make format       # black --line-length=79
make run-daemon   # dashboard at http://localhost:9876
make binary       # PyInstaller single executable
```

## Architecture

```
CLI (envs) ──┐                       ┌── Adapter Manager ── 15 adapters
             ├── HTTP ──▶ Daemon ────┤
Dashboard ───┘                       ├── Discovery Engine (scan + hooks)
                                     └── Storage (SQLite + WAL)
```

Full architecture, state model, adapter protocol, and data flow in [DESIGN.md](DESIGN.md).

## License

MIT
