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

## CLI Reference

```bash
envs scan                          # discover all environments
envs list                          # list tracked environments
envs list --by-project --stale     # group and filter
envs info <project>                # detailed view
envs doctor --all                  # health check everything
envs lifecycle create python@3.12  # create new env
envs lifecycle install <p> flask   # install packages
envs lifecycle remove <p> --snapshot --confirm  # safe delete
envs lifecycle restore <p> --confirm            # rebuild from snapshot
envs cleanup --stale 60 --dry-run  # preview cleanup
eval "$(envs lifecycle activate <p>)"  # activate in shell
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
