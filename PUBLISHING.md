# Publishing Guide

## Branch Strategy

```
main  — stable releases (tags trigger publish)
dev   — release candidates (builds artifacts, no publish)
```

Workflow: `feature branch → PR to dev → test → merge to dev → test → merge to main → tag → publish`

## Publishing a Release

### 1. Bump version

```bash
git checkout dev
git pull
make bump-patch    # 0.1.0 → 0.1.1
# or: make bump-minor  (0.1.0 → 0.2.0)
# or: make bump-major  (0.1.0 → 1.0.0)
```

This auto-updates `pyproject.toml` and `env_manager/__init__.py`, commits, and tags.

### 2. Merge to main

```bash
git checkout main
git merge dev
git push origin main --tags
```

### 3. Release triggers automatically

Pushing a `v*` tag to main triggers `.github/workflows/release.yml`:
- Builds and publishes to **PyPI** via OIDC trusted publishing
- Builds **standalone binaries** for Linux, macOS, Windows
- Creates **GitHub Release** with auto-generated changelog and attached binaries

## PyPI Setup (one-time)

Go to https://pypi.org/manage/project/env-manager/settings/publishing/ and add:

- **Owner**: your GitHub username
- **Repository**: bibekgupta3333/env-manager
- **Workflow**: release.yml
- **Environment**: pypi

This uses OIDC trusted publishing — no API tokens needed.

## GitHub Environments

Go to Settings → Environments → create `pypi` environment with:
- Required reviewers: none (or add if desired)
- Deployment branches: `main`

## Installation After Publishing

```bash
pip install env-manager              # from PyPI
# or download binary from GitHub Releases
curl -L https://github.com/bibekgupta3333/env-manager/releases/latest/download/envs-macos.tar.gz | tar xz
./envs --help
```

## CI Pipeline Summary

| Event | CI | Build | Publish |
|-------|:--:|:-----:|:-------:|
| PR to dev/main | lint + typecheck + test (3 OS × 3 Python) | — | — |
| Push to dev | lint + typecheck + test | binary artifact (3 OS) | — |
| Push to main | lint + typecheck + test | binary artifact (3 OS) | — |
| Tag v* on main | — | — | PyPI + GitHub Release + binaries |

## Release Drafter

Merged PRs to main auto-generate a draft release in GitHub Releases with categorized changelog. Labels like `feature`, `fix`, `chore` categorize entries.
