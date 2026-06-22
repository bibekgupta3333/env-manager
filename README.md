# env-manager

Cross-language virtual environment manager. Discover, manage, health-check, snapshot, and clean up environments across Python, Node, Ruby, Go, and Rust — from one CLI and a localhost dashboard.

## Quick Start

```bash
pip install env-manager
envs scan
envs list
```

## Features

- **Scan** — auto-discover all venvs, nvm installs, rbenv versions across your machine
- **Manage** — create, install, update, delete environments for any language
- **Doctor** — health-check every environment; detect broken ones before you need them
- **Snapshot & Restore** — save exact dependency blueprint before deleting; rebuild in seconds
- **Cleanup** — batch-remove stale environments across languages; see what you'd free
- **Dashboard** — visual web UI at http://localhost:9876
- **Plugins** — community adapters for any language (`envs-plugin-java`, etc.)

## Supported Languages

| Language | Tools |
|----------|-------|
| Python | venv, poetry, pipenv, pyenv, conda |
| Node.js | nvm, fnm, volta, n, bun |
| Ruby | rbenv, rvm, chruby, asdf |
| Go | goenv |
| Rust | rustup |

## Supported Version Managers (15 adapters)

| # | Language | Adapter | Type | Detect Pattern |
|---|----------|---------|------|----------------|
| 1 | Python | venv | local | `pyvenv.cfg` |
| 2 | Python | virtualenv | local | `pyvenv.cfg` + orig-prefix |
| 3 | Python | poetry | local | `pyproject.toml` with `[tool.poetry]` |
| 4 | Python | pipenv | local | `Pipfile` |
| 5 | Python | pyenv | global | `~/.pyenv/versions/*` |
| 6 | Python | conda | global | `~/anaconda3/envs/*` |
| 7 | Node.js | nvm | global | `~/.nvm/versions/node/*` |
| 8 | Node.js | fnm | global | `~/.fnm/node-versions/*` |
| 9 | Node.js | volta | global | `~/.volta/tools/image/node/*` |
| 10 | Node.js | n | global | `/usr/local/n/versions/node/*` |
| 11 | Node.js | bun | global | `~/.bun/install/` |
| 12 | Ruby | rbenv | global | `~/.rbenv/versions/*` |
| 13 | Ruby | rvm | global | `~/.rvm/rubies/*` |
| 14 | Go | goenv | global | `~/.goenv/versions/*` |
| 15 | Universal | asdf | global | `~/.asdf/installs/*` |

Note: Rust (rustup) is supported via the adapter layer but tracks toolchains rather than per-project environments.

## CLI Reference

```bash
envs scan                          # discover all environments
envs list                          # list tracked environments
envs list --by-project --stale     # group and filter
envs info <project>                # detailed view
envs versions [--lang python]      # show available language runtimes
envs doctor --all                  # health check everything
envs lifecycle create python@3.12  # create new env
envs lifecycle install <p> flask   # install packages
envs lifecycle remove <p> --snapshot --confirm  # safe delete
envs lifecycle restore <p> --confirm            # rebuild from snapshot
envs cleanup --stale 60 --dry-run  # preview cleanup
envs cleanup compare <a> <b>       # diff two environments
eval "$(envs lifecycle activate <p>)"  # activate in shell
envs pin <project>                 # favorite, safe from cleanup
envs unpin <project>               # unfavorite
envs track <path>                  # manually register path
envs ignore <path>                 # exclude path from tracking
envs db backup/restore/path/repair # database management
envs hook --install/--uninstall    # shell integration
```

## Development

```bash
git clone https://github.com/bibekgupta3333/env-manager.git
cd env-manager
bash scripts/dev-setup.sh
make check
```

## License

MIT
