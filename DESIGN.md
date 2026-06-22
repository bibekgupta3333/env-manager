# env-manager — Design Specification

## What Problems Are We Solving?

Six concrete problems every developer with 50+ projects faces:

### 1. You don't know what environments exist on your machine

**Before:** 100+ Python venvs, 50+ node_modules, 20+ Ruby gemsets scattered across `~/projects/`, `~/work/`, `~/experiments/`, `~/Downloads/`. You've forgotten half of them. A `find / -name pyvenv.cfg` returns 300 results.

**After:** `envs scan` finds everything. `envs list --by-project` shows all envs grouped by project with language, version, size, and last-used date.

### 2. Environments silently break

**Before:** You `cd` into a 6-month-old project, activate the venv, and get `python: command not found` or `ImportError: libcrypto.so.1.1: cannot open`. You have no idea why. You spend 2 hours debugging.

**After:** `envs doctor` checks every environment: is the binary present? Can it import? Are C extensions compatible? Flags problems BEFORE you need the env.

### 3. You can't safely free disk space

**Before:** You run `du -sh ~/projects/*/.venv` and see 47 GB. But you're afraid to delete anything. "What if I need this venv next month?" So you buy a bigger SSD instead.

**After:** `envs cleanup --stale 60 --snapshot` saves the exact dependency lockfile, deletes the environment, frees the space. `envs restore myproject` rebuilds it in seconds. Delete with confidence.

### 4. No single tool works across languages

**Before:** `pip list` for Python. `npm list -g --depth=0` for Node. `gem list` for Ruby. `rustup show` for Rust. Four different commands, four different formats, zero unified view.

**After:** `envs list` shows everything. `envs install myproject flask` works whether it's pip, npm, gem, or cargo underneath.

### 5. Orphaned environments waste space forever

**Before:** You delete a project directory but forget the `.venv` inside it. The venv sits there forever — 245 MB of nothing. Multiply by 20 deleted projects. That's 5 GB of digital trash you'll never find.

**After:** `envs list --orphaned` finds them instantly. `envs cleanup --orphaned` removes them. The scanner detects when a project directory no longer exists.

### 6. No project-level visibility

**Before:** A project might have a Python 3.11 venv, a Python 3.12 venv, and a node_modules. Three separate environments, three separate tools to check. You don't know the project uses 2.1 GB total.

**After:** `envs info myproject` shows all environments for that project, total disk usage, health status, last activity — in one view.

---

**In one sentence:** env-manager gives you visibility, safety, and control over every language environment on your machine — across all projects, all languages, at any scale.

---

---

**In one sentence:** env-manager gives you visibility, safety, and control over every language environment on your machine — across all projects, all languages, at any scale, via CLI and a localhost dashboard.

---

## Feature Set

| # | Feature | Description |
|---|---------|-------------|
| 1 | **Cross-language (opt-in per language)** | Track Python, Node, Ruby, Go, Rust — or just one. Disable what you don't need. Lighter footprint. |
| 2 | **Auto-discovery** | Scan filesystem for existing environments (venv, nvm, rbenv, etc.) |
| 3 | **Create environments** | `envs create python@3.12` — one command across all languages |
| 4 | **Install/manage deps** | `envs install project flask` — delegates to pip/npm/gem/cargo |
| 5 | **Health checks** | `envs doctor` — detect broken envs before you need them |
| 6 | **Snapshot before delete** | `envs cleanup --snapshot` — save lockfile, free disk, restore later |
| 7 | **Restore from snapshot** | `envs restore project` — rebuild exact env in seconds |
| 8 | **Batch cleanup** | `envs cleanup --stale 60` — remove all stale envs across languages |
| 9 | **Project-centric view** | `envs list --by-project` — see all envs grouped by project |
| 10 | **Disk usage tracking** | Track size per environment, project, language. Show what to reclaim. |
| 11 | **Localhost dashboard** | Visual web UI at localhost — browse, filter, batch-manage 1000+ envs |
| 12 | **Plugin architecture** | `pip install envs-plugin-java` — community adapters for any language |
| 13 | **Zero dependencies** | Self-contained binary. No Python/Docker/Nix required to run. |
| 14 | **Language version listing** | `envs versions` — show all available language runtimes and versions |

---

## Architecture Overview

```
┌──────────────────────────────────────────────────────────────────┐
│                       USER INTERFACES                             │
├──────────────────────────────────────────────────────────────────┤
│                                                                   │
│   CLI (envs)                          Web Dashboard              │
│   ─────────────────                   ──────────────              │
│   envs list --stale                   localhost:9xxx              │
│   envs create python@3.12             React SPA served by API     │
│   envs doctor --all                                                │
│   envs cleanup --snapshot                                          │
│                                                                   │
│   ───────────────┬──────────────────────┬────────────────────     │
│                  │  HTTP REST + WS      │                         │
└──────────────────┼──────────────────────┼─────────────────────────┘
                   │                      │
                   ▼                      ▼
┌──────────────────────────────────────────────────────────────────┐
│                      DAEMON CORE (Python / FastAPI)               │
│                                                                    │
│  ┌──────────┐  ┌───────────┐  ┌──────────┐  ┌───────────────┐   │
│  │ REST API │  │ WebSocket │  │Dashboard │  │   Scheduler   │   │
│  │  Server  │  │  Server   │  │  Static  │  │  (APScheduler)│   │
│  └──────────┘  └───────────┘  └──────────┘  └───────────────┘   │
│  ┌─────────────────┐  ┌────────────────┐  ┌──────────────────┐  │
│  │  Adapter Manager │  │ Discovery Eng  │  │  Health Monitor  │  │
│  │  (plugin load)   │  │ (scan+reg+hook)│  │  (doctor checks) │  │
│  └────────┬────────┘  └───────┬────────┘  └──────────────────┘  │
└───────────┼───────────────────┼──────────────────────────────────┘
            │                   │
            ▼                   ▼
┌───────────────────────┐  ┌───────────────────────────────────────┐
│   Language Adapters   │  │          STORAGE (SQLite + WAL)        │
├───────────────────────┤  ├───────────────────────────────────────┤
│ 🐍 Python             │  │  projects         │  activity_log      │
│  · venv               │  │  environments     │  cleanup_rules     │
│  · virtualenv         │  │  snapshots        │  scan_history      │
│  · poetry / pipenv    │  │  packages         │  adapter_registry  │
│  · pyenv / conda      │  │                                       │
│                        │  └───────────────────────────────────────┘
│ 💚 Node.js             │
│  · nvm / fnm / volta  │
│  · n / bun            │
│                        │
│ ♦ Ruby                 │
│  · rbenv / rvm        │
│  · chruby / asdf      │
│                        │
│ 🔷 Go                  │
│  · goenv / g          │
│                        │
│ ⚙ Rust                 │
│  · rustup / cargo     │
│                        │
│ 📦 Community Plugins   │
│  · pip install         │
│    envs-plugin-java    │
└───────────────────────┘

┌──────────────────────────────────────────────────────────────────┐
│                    DISCOVERY ENGINE (3 modes)                     │
├──────────────────┬───────────────────┬────────────────────────────┤
│   Active Scan    │  Passive Register │     Shell Hooks (opt-in)   │
│   (periodic)     │  (envs track /)   │     (eval cd hook)         │
│                  │                   │                             │
│  Smart scoping:  │  User explicitly  │  Bash/Zsh/Fish hooks       │
│  excludes /usr,  │  registers a path │  POST activity to daemon   │
│  /System,        │                   │  Never auto-modifies rc    │
│  node_modules    │                   │  files                     │
└──────────────────┴───────────────────┴────────────────────────────┘
```

### Data Flow

```
CLI command → HTTP Request → Daemon REST API
                               ├── Read/Write SQLite
                               ├── Route to Adapter Manager
                               │     └── Call adapter.detect/inspect/install/freeze(...)
                               └── Return JSON response

Shell hook → POST to Daemon API → Store activity in SQLite

Scanner (scheduled) → Walk filesystem → adapter.detect(path) → SQLite
```

---

## Two-Dimension State Model

Environments have **two independent dimensions** — what you can DO and what you KNOW.

### Dimension 1: Management State

```
CREATING ──▶ READY ──▶ UPDATING ──▶ READY
               │                        ▲
               │                        │  envs restore (rebuilds from snapshot)
               ▼                        │
             ERROR ──── fix ────────────┘
               │
               │  envs delete (no snapshot)    envs delete --snapshot
               ▼                               ▼
            DELETED ──▶ PURGED          SNAPSHOTTED ──▶ PURGED
          (soft-deleted,              (deleted from disk,
           no blueprint)               blueprint in DB)
```

| State | Meaning |
|-------|---------|
| `creating` | Environment is being created (`envs create`) |
| `ready` | Healthy and usable |
| `updating` | Packages or version being modified |
| `error` | Corrupted, missing binary, or broken — needs attention |
| `snapshotted` | Deleted from disk but blueprint saved; restorable |
| `deleted` | Soft-deleted, still in DB, recoverable |
| `purged` | Permanently removed from disk and DB |

### Dimension 2: Discovery Status

| Status | Meaning |
|--------|---------|
| `untracked` | Found by scanner but not yet tracked |
| `tracked` | Actively monitored |
| `ignored` | User explicitly excluded (`envs ignore`) |

### Computed Booleans (not states)

| Flag | Condition |
|------|-----------|
| `is_stale` | `last_used_at > threshold_days` |
| `is_orphaned` | Project directory no longer exists on disk |
| `is_locked` | Process holds file handle (transient) |
| `is_pinned` | User favorited this project (`envs pin`) |

### Health Status (timestamped, not static)

```
last_health_check_at: 2026-06-21T14:30:00Z  (or NULL if never checked)
last_health_result: "healthy" | "degraded" | "broken"
```

Any command reading health must check if `last_health_check_at` is older than 24 hours and warn: "Health check is N hours old. Run `envs doctor` to refresh."

---

## Adapter Protocol

Every language adapter implements this interface. Community plugins via `pip install envs-plugin-*`.

```python
class BaseAdapter(ABC):
    """Every language adapter must implement this protocol."""

    # ── Identity ──────────────────────────────────
    name: str                    # "python.venv"
    display_name: str            # "Python (venv)"
    version: str                 # "1.0.0"
    env_type: Literal["local", "global"]  # local=project dir, global=system install

    # ── Detection (required) ──────────────────────
    @abstractmethod
    def detect(self, path: Path) -> Optional[EnvMetadata]:
        """Is this path one of our environments? Returns metadata or None."""

    @abstractmethod
    def find_patterns(self) -> list[str]:
        """Glob patterns for scanner. e.g. ['**/pyvenv.cfg', '**/.python-version']"""

    # ── Inspection (required) ─────────────────────
    @abstractmethod
    def inspect(self, path: Path) -> EnvMetadata:
        """Full inspection: version, size, interpreter path. Raises InspectError."""

    @abstractmethod
    def get_packages(self, path: Path) -> list[Package]:
        """List installed packages with versions."""

    # ── Snapshot (required) ───────────────────────
    @abstractmethod
    def freeze(self, path: Path) -> FreezeResult:
        """Returns: (a) raw lockfile content, (b) tool-specific format,
        (c) normalized package list for cross-language display."""

    # ── Health (required) ─────────────────────────
    @abstractmethod
    def check_health(self, path: Path) -> HealthResult:
        """Is the environment functional? Can it import packages?"""

    # ── Lifecycle (optional) ──────────────────────
    def create(self, path: Path, config: CreateConfig) -> EnvMetadata: ...
    def install(self, path: Path, packages: list[str]) -> Result: ...
    def uninstall(self, path: Path, packages: list[str]) -> Result: ...
    def update(self, path: Path, packages: list[str]) -> Result: ...
    def delete(self, path: Path) -> Result: ...
    def clone(self, path: Path, dest: Path) -> EnvMetadata: ...

    # ── Export/Import (optional) ──────────────────
    def export_env(self, path: Path, dest: Path) -> Result: ...
    def import_env(self, spec_path: Path, dest: Path) -> Result: ...


@dataclass
class EnvMetadata:
    language: str          # "python"
    tool: str              # "venv"
    env_type: str          # "local" | "global"
    version: str           # "3.12.1"
    path: str
    size_bytes: int
    interpreter_path: str  # "/usr/bin/python3.12"
    packages_count: int

@dataclass
class FreezeResult:
    raw_content: str                        # actual lockfile text
    format: str                             # "requirements.txt" | "package-lock.json" | "Gemfile.lock"
    packages: list[Package]                 # normalized for cross-language display

@dataclass
class HealthResult:
    status: Literal["healthy", "degraded", "broken"]
    checks: list[dict]      # [{"name": "python_binary", "passed": True}, ...]
    errors: list[str]       # ["Missing /bin/python", "numpy import failed"]
    suggestions: list[str]  # ["Restore from snapshot", "Reinstall with Python 3.12"]
```

### Built-in Adapters (15 tools)

| Language | Adapter | env_type | detect pattern |
|----------|---------|----------|----------------|
| Python | venv | local | `pyvenv.cfg` |
| Python | virtualenv | local | `pyvenv.cfg` + orig-prefix |
| Python | poetry | local | `pyproject.toml` with `[tool.poetry]` |
| Python | pipenv | local | `Pipfile` |
| Python | pyenv | global | `~/.pyenv/versions/*` |
| Python | conda | global | `~/anaconda3/envs/*` |
| Node | nvm | global | `~/.nvm/versions/node/*` |
| Node | fnm | global | `~/.fnm/node-versions/*` |
| Node | volta | global | `~/.volta/tools/image/node/*` |
| Node | n | global | `/usr/local/n/versions/node/*` |
| Node | bun | global | `~/.bun/install/` |
| Ruby | rbenv | global | `~/.rbenv/versions/*` |
| Ruby | rvm | global | `~/.rvm/rubies/*` |
| Go | goenv | global | `~/.goenv/versions/*` |
| Rust | rustup | global | `~/.rustup/toolchains/*` |
| Universal | asdf | global | `~/.asdf/installs/*` |

---

## SQLite Schema

```sql
-- Projects (the user's mental model — "my projects")
CREATE TABLE projects (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,                    -- "myapp-api"
    path        TEXT NOT NULL UNIQUE,             -- /home/user/projects/myapp-api
    last_active TEXT,                             -- ISO 8601
    tags        TEXT DEFAULT '[]',                -- JSON array: ["client-a", "production"]
    is_pinned   INTEGER DEFAULT 0,                -- 0/1
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Environments (one project can have multiple envs — e.g., py3.11 + py3.12)
CREATE TABLE environments (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id          INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    adapter             TEXT NOT NULL,             -- "python.venv"
    env_type            TEXT NOT NULL,             -- "local" | "global"
    path                TEXT NOT NULL,             -- /home/user/.../.venv
    language            TEXT NOT NULL,             -- "python"
    version             TEXT,                      -- "3.12.1"
    tool                TEXT,                      -- "venv"
    size_bytes          INTEGER DEFAULT 0,
    management_state    TEXT NOT NULL DEFAULT 'ready',  -- creating|ready|updating|error|snapshotted|deleted|purged
    discovery_status    TEXT NOT NULL DEFAULT 'untracked', -- untracked|tracked|ignored
    is_stale            INTEGER DEFAULT 0,         -- computed
    is_orphaned         INTEGER DEFAULT 0,         -- computed
    is_locked           INTEGER DEFAULT 0,         -- transient
    last_health_check   TEXT,                      -- ISO 8601, NULL if never checked
    last_health_result  TEXT,                      -- healthy|degraded|broken
    metadata            TEXT DEFAULT '{}',         -- JSON: interpreter path, packages count, etc.
    created_at          TEXT NOT NULL DEFAULT (datetime('now')),
    last_used_at        TEXT,
    last_scanned_at     TEXT
);
CREATE INDEX idx_envs_project ON environments(project_id);
CREATE INDEX idx_envs_language ON environments(language);
CREATE INDEX idx_envs_mgmt_state ON environments(management_state);
CREATE INDEX idx_envs_disc_status ON environments(discovery_status);

-- Snapshots (append-only, versioned)
CREATE TABLE snapshots (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    env_id      INTEGER NOT NULL REFERENCES environments(id) ON DELETE CASCADE,
    version     INTEGER NOT NULL,                 -- 1, 2, 3... per env
    frozen_deps TEXT NOT NULL,                    -- JSON: {"requests":"2.31.0",...}
    raw_lockfile TEXT,                            -- actual requirements.txt content
    lockfile_format TEXT,                         -- "requirements.txt" | "package-lock.json"
    tool_config TEXT DEFAULT '{}',                -- JSON: {"create_cmd":"python3.12 -m venv"}
    notes       TEXT,                             -- user-added note
    created_at  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(env_id, version)
);
CREATE INDEX idx_snapshots_env ON snapshots(env_id);

-- Packages (per-environment package list)
CREATE TABLE packages (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    env_id      INTEGER NOT NULL REFERENCES environments(id) ON DELETE CASCADE,
    name        TEXT NOT NULL,
    version     TEXT NOT NULL,
    scanned_at  TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(env_id, name)
);
CREATE INDEX idx_packages_env ON packages(env_id);
CREATE INDEX idx_packages_name ON packages(name);

-- Activity log (audit trail)
CREATE TABLE activity_log (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    env_id      INTEGER REFERENCES environments(id) ON DELETE SET NULL,
    project_id  INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    event       TEXT NOT NULL,                    -- created|activated|installed|deleted|restored|scanned|...
    detail      TEXT DEFAULT '{}',                -- JSON
    timestamp   TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX idx_activity_env ON activity_log(env_id);
CREATE INDEX idx_activity_ts ON activity_log(timestamp);

-- Scan history (track scanner runs)
CREATE TABLE scan_history (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at  TEXT NOT NULL,
    finished_at TEXT,
    paths_scanned INTEGER DEFAULT 0,
    envs_found  INTEGER DEFAULT 0,
    envs_new    INTEGER DEFAULT 0,
    errors      TEXT DEFAULT '[]'                 -- JSON array of error strings
);

-- Cleanup rules (user-defined)
CREATE TABLE cleanup_rules (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL,
    conditions  TEXT NOT NULL,                    -- JSON: {"stale_days": 60, "min_size_mb": 200}
    action      TEXT NOT NULL,                    -- "snapshot" | "delete" | "ignore"
    enabled     INTEGER DEFAULT 1,
    created_at  TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Adapter registry (installed adapters)
CREATE TABLE adapter_registry (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    name        TEXT NOT NULL UNIQUE,             -- "python.venv"
    display_name TEXT NOT NULL,
    version     TEXT NOT NULL,
    env_type    TEXT NOT NULL,                    -- "local" | "global"
    source      TEXT NOT NULL,                    -- "builtin" | "pip" | "manual"
    source_path TEXT,                             -- path for manual installs
    enabled     INTEGER DEFAULT 1,
    installed_at TEXT NOT NULL DEFAULT (datetime('now'))
);

-- Enable WAL mode for concurrent reads+writes
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;
```

---

## CLI Command Reference (v0.1)

### Global Flags

| Flag | Description |
|------|-------------|
| `--dry-run` | Simulate. Show what would happen. No changes. |
| `--confirm` | Required for destructive operations. |
| `--json` | Output as JSON (for scripting). |

### Discovery Commands

```
envs scan [--path /home/user] [--depth 3]
    Discover all environments. Only uses enabled language adapters.
    Excludes /usr, /System, node_modules, .git by default.
    Track only Python? Disable other adapters first: envs plugins disable node ruby go rust

envs list [--by-project] [--stale] [--orphaned] [--broken] [--lang python] [--size-gt 500M]
    List tracked environments with filtering.

envs list --snapshots
    List all available snapshots (deleted environments with saved blueprints).

envs info <project>
    Detailed view: version, size, packages count, last used, health, snapshots.

envs versions [--lang python]
    Show available language runtimes and versions across all adapters.

envs track <path>
    Register a path for tracking.

envs ignore <path>
    Exclude a path from all tracking.
```

### Lifecycle Commands

```
envs create <lang@version> [path] [--tool venv|poetry|fnm|...]
    Create a new environment. If path omitted, creates .venv in current directory.
    If path is a project directory, creates .venv inside it.

envs shell <project>
    Spawn a subshell with the environment activated.

# Activation in current shell (eval pattern):
eval "$(envs activate <project>)"

envs install <project> <packages...> [--dry-run] [--confirm]
    Install packages. Dry-run shows what would be installed with versions.

envs uninstall <project> <packages...> [--dry-run] [--confirm]

envs update <project> [--all] [--dry-run] [--confirm]
    Update packages to latest versions.

envs delete <project> [--snapshot] [--dry-run] [--confirm]
    Remove environment. --snapshot saves blueprint first.

envs restore <project> [--snapshot N]
    Rebuild environment from snapshot. --snapshot N picks a specific version.

envs clone <src> <dst>
    Clone environment to a new path.

envs export <project> [--output file.json]
    Export environment blueprint as portable JSON.

envs import <spec.json>
    Create environment from an exported spec.
```

### Health & Safety Commands

```
envs doctor [project] [--all] [--fix]
    Health check. --all checks every tracked environment. --fix attempts auto-repair.

envs diff <project-a> <project-b>
    Compare package versions between two environments.

envs pin <project>
envs unpin <project>
    Favorite/unfavorite. Pinned projects are never cleanup candidates.

envs cleanup [--stale N] [--orphaned] [--snapshot] [--dry-run] [--confirm]
    Batch cleanup of stale/orphaned environments.

envs cleanup compare <project-a> <project-b>
    Diff two environments (alias for envs diff).

envs gc [--dry-run] [--confirm]
    Full garbage collection. Purges all soft-deleted environments.

envs snapshots list [project]
    List all snapshots or filter by project.

envs snapshots prune [project] [--keep N]
    Delete old snapshot versions. Default: keep 5 most recent per environment.

envs db backup [--path]
    Backup SQLite database to safe location.

envs db restore [--path]
    Restore database from backup file.

envs db path
    Show the database file path.

envs db repair
    Check and repair database integrity.

envs hook --install
envs hook --uninstall
    Install/uninstall shell integration (bash/zsh/fish) for automatic environment tracking.
```

### Plugin & Language Config Commands

```
envs plugins list
    Show all adapters with enabled/disabled status, language, and source.

envs plugins enable <name>       # envs plugins enable node
envs plugins disable <name>      # envs plugins disable ruby
    Enable or disable a language adapter. Disabled adapters are skipped during scan
    and don't appear in listings. Reduces scan time and DB size.

envs plugins add <path>
    Register a custom adapter.

envs plugins remove <name>
    Remove an adapter and all its tracked environments.

envs config show
    Show current configuration: enabled languages, scan paths, cleanup thresholds.
```

---

## Full Workflow Example

### Scenario: Developer with 118 Python projects, 47.3 GB

```
$ envs scan

Scanning /home/user/projects... (excludes: node_modules, .git, /usr, /System)
  Found: 143 Python environments across 118 projects
  Found: 67 Node environments across 52 projects
  Found: 12 Ruby environments across 8 projects
  Inspecting environments...

  [████████████████████████████████████████] 100%  222/222 inspected

  ✓ 218 healthy   |   3 broken   |   1 corrupted
  ⓘ Total disk: 47.3 GB across 178 projects


$ envs list --by-project

PROJECT                LANG     VERSION    SIZE      LAST USED    HEALTH
───────────────────────────────────────────────────────────────────────────
client-acme-api        python   3.12.1     890 MB    2 hrs ago    healthy
client-acme-worker     python   3.11.4     420 MB    2 hrs ago    healthy
client-beta-dashboard  python   3.10.8     1.2 GB    1 day ago    healthy
personal-blog          python   3.9.13     230 MB    3 days ago   healthy
experiment-transformers python  3.11.0     4.8 GB    2 weeks ago  degraded ⚠
oss-contrib-lib        python   3.12.0     150 MB    1 month ago  healthy
old-scraper-2022       python   3.8.5      980 MB    8 months ago broken ✗
legacy-etl-pipeline    python   3.7.2      2.1 GB    1 year ago   corrupted ✗
temp-plot-test         python   3.11.4      45 MB    5 months ago healthy
  ...
───────────────────────────────────────────────────────────────────────────
TOTAL: 118 projects | 143 environments | 47.3 GB


$ envs doctor old-scraper-2022

  old-scraper-2022  python 3.8.5 (venv)  980 MB
  ══════════════════════════════════════════════
  ✗ Python binary: missing (.venv/bin/python not found)
  ✗ pip: not found
  ✗ Import check: cannot verify
  ✗ 23 packages in snapshot, 0 installed
  ⓘ Cause: Python 3.8 uninstalled from system. Env is unrecoverable.
  ⓘ Snapshot exists. Run: envs restore old-scraper-2022 --python 3.12


$ envs create python@3.12

  --dry-run: Create Python 3.12.1 venv at /home/user/projects/new-client-api/.venv

$ envs create python@3.12 --confirm

  Creating Python 3.12.1 environment (venv)...
  ✓ Created: /home/user/projects/new-client-api/.venv
  ✓ Python 3.12.1 | pip 24.0 | 0 packages | 28 MB


$ envs install new-client-api fastapi uvicorn pydantic httpx --dry-run

  Would install 4 packages:
    fastapi==0.115.0  (+12 MB)
    uvicorn==0.30.0   (+8 MB)
    pydantic==2.9.0   (+15 MB)
    httpx==0.27.0     (+10 MB)
  ─────────────────────
  Estimated total: +45 MB (73 MB after install)

$ envs install new-client-api fastapi uvicorn pydantic httpx --confirm

  Installing 4 packages...
  ✓ fastapi-0.115.0
  ✓ uvicorn-0.30.0
  ✓ pydantic-2.9.0
  ✓ httpx-0.27.0
  ⓘ Auto-snapshot saved (v1): 4 packages, 73 MB


$ eval "$(envs activate new-client-api)"

  Activated: new-client-api (python 3.12.1, 4 packages)
  (.venv) $ python -c "import fastapi; print('ok')"
  ok
  (.venv) $ exit


$ envs pin client-acme-api
  ✓ Pinned: client-acme-api (safe from cleanup)

$ envs pin client-acme-worker
  ✓ Pinned: client-acme-worker (safe from cleanup)


$ envs cleanup --stale 60 --dry-run

  Would process 31 environments across 28 projects:
  ══════════════════════════════════════════════════════
  28 stale (unused > 60 days)
   3 orphaned (project directory deleted)

  Breakdown by action:
    22 would be snapshotted & removed    (12.1 GB freed)
     6 would be removed (no snapshot)    (3.2 GB freed)
     3 skipped — pinned

  ─────────────────────────────────────────────────────
  Would free: 15.3 GB across 28 environments
  Run with --confirm to execute.


$ envs cleanup --stale 60 --confirm --snapshot

  [████████████████████████████████████████] 100%  28/28 processed

  ✓ 22 environments snapshotted & removed (v1 snapshots saved)
  ✓ 6 environments removed (no snapshot)
  ⚠ 3 skipped — pinned

  Freed: 15.3 GB
  Snapshots saved: 22 (restorable anytime)


  ... months later ...


$ envs list --snapshots

  SNAPSHOTS (22 available):
  ══════════════════════════════════════════════
  client-xmas-campaign    python 3.11.2    23 pkgs   340 MB    Dec 2025
  experiment-llm          python 3.11.0    47 pkgs   4.8 GB    Jan 2026
  tax-automation          python 3.10.8    12 pkgs   180 MB    Mar 2026
  ...

$ envs restore client-xmas-campaign --dry-run

  Snapshot v1: python 3.11.2, 23 packages, created Dec 2025
  Would create venv and install 23 packages (~340 MB)

$ envs restore client-xmas-campaign --confirm

  Creating Python 3.11.2 environment (venv)...
  Installing 23 packages from snapshot...
  ✓ requests-2.31.0
  ✓ pandas-2.1.0
  ✓ matplotlib-3.8.0
  ... (23/23)
  ✓ Restored in 18.3s | 340 MB

$ eval "$(envs activate client-xmas-campaign)"
  Activated: client-xmas-campaign (python 3.11.2, 23 packages)


$ envs diff client-xmas-campaign client-acme-api

  client-xmas-campaign (3.11.2) ←→ client-acme-api (3.12.1)
  ═══════════════════════════════════════════════════════
  Python version:  3.11.2           → 3.12.1      ↑
  Packages:        23               → 47           ↑
  ───────────────────────────────────────────────────────
  Only in xmas:    matplotlib-3.8.0, seaborn-0.13.0
  Only in acme:    fastapi-0.115.0, pydantic-2.9.0, sqlalchemy-2.0.0
  Different ver:   requests-2.28.0  → requests-2.31.0  ↑
                   pandas-1.5.0     → pandas-2.1.0     ↑


$ envs db backup
  ✓ Database backed up to: ~/.env-manager/backups/envs-2026-06-21.db


$ envs gc --dry-run
  Would purge 6 soft-deleted environments (3.2 GB)

$ envs gc --confirm
  ✓ Purged 6 environments. Freed 3.2 GB.
```

---

## Deployment & Distribution

| Method | Command | Target |
|--------|---------|--------|
| Self-contained binary | Download from GitHub Releases | All platforms (no Python required) |
| pip install | `pip install env-manager` | Python developers |
| brew install | `brew install env-manager` | macOS |
| cargo install | `cargo install env-manager` (future, if Rust rewrite) | Rust developers |

### Daemon Lifecycle

```
┌─────────────────────────────────────────────────────────┐
│                    DAEMON LIFECYCLE                      │
│                                                          │
│  envs daemon start                                       │
│       │                                                  │
│       ▼                                                  │
│  ┌─────────┐    any CLI command      ┌──────────────┐   │
│  │  IDLE   │────────────────────────▶│  PROCESSING  │   │
│  │         │◀───────────────────────│              │   │
│  └────┬────┘    response returned    └──────────────┘   │
│       │                                                  │
│       │ 15 min no activity                               │
│       ▼                                                  │
│  ┌─────────┐                                             │
│  │  STOP   │  auto-shutdown                              │
│  └─────────┘                                             │
│                                                          │
│  Also starts on-demand via:                              │
│    - Socket activation (macOS launchd / Linux systemd)   │
│    - First CLI command auto-starts daemon                │
│    - envs daemon status → check if running               │
└─────────────────────────────────────────────────────────┘
```

---

## v0.1 vs v0.2 Scope

### v0.1 (MVP)

- CLI + web dashboard (localhost React SPA)
- Scan, list, info, track, ignore
- Create, shell, install, uninstall, update, delete, restore, clone
- Doctor, cleanup, gc, diff, pin/unpin
- `envs versions`, `envs db backup/restore/path/repair`, `envs hook`, `envs cleanup compare`
- Snapshot + restore (versioned, append-only)
- 5 built-in adapters (Python, Node, Ruby, Go, Rust — 15 tools)
- Community plugin support (`pip install envs-plugin-*`)
- `--dry-run` / `--confirm` on all mutating commands
- SQLite + WAL mode
- Ship as self-contained binary + pip install

### v0.2 (Planned)

- `envs security-audit` — CVE scanning across environments
- `envs install --all-projects` — batch install package across environments
- `envs link` — project dependency relationships (monorepo)
- `envs template` — pre-defined scaffolding
- `envs snapshots diff` — compare two snapshots of same project
- Snapshot sharing (export to portable format for colleagues)
- Full disaster recovery (auto-rebuild from filesystem)

---

## Architecture Diagrams

### 1. Publishing Pipeline

```
                         PUBLISHING PIPELINE
                         ═══════════════════

  ┌─────────────────────────────────────────────────────────────────────┐
  │                         DEVELOPMENT FLOW                             │
  │                                                                      │
  │  feature/xyz ──▶ PR ──▶ dev ──▶ PR ──▶ main                        │
  │                     │              │                                 │
  │                     ▼              ▼                                 │
  │               CI: test only   CI: test + build                       │
  │               (3 OS × 3 Py)   (3 OS × 3 Py + binary artifact)       │
  │                                                                      │
  └─────────────────────────────────────────────────────────────────────┘
                                     │
                                     │ git tag v0.2.0
                                     ▼
  ┌─────────────────────────────────────────────────────────────────────┐
  │                         RELEASE PIPELINE                             │
  │                                                                      │
  │  Tag push (v*)                                                       │
  │       │                                                              │
  │       ├──▶ 1. Build sdist + wheel                                   │
  │       │       └──▶ Publish to PyPI (OIDC trusted publishing)        │
  │       │              └──▶ pip install env-manager                   │
  │       │                                                              │
  │       ├──▶ 2. Build PyInstaller binaries                            │
  │       │       ├──▶ ubuntu-latest → envs-linux.tar.gz                │
  │       │       ├──▶ macos-latest   → envs-macos.tar.gz               │
  │       │       └──▶ windows-latest → envs-windows.tar.gz             │
  │       │                                                              │
  │       └──▶ 3. Create GitHub Release                                 │
  │               ├──▶ Changelog from git log (since prev tag)          │
  │               ├──▶ Attach all 3 platform binaries                   │
  │               └──▶ Mark as pre-release if rc/beta/alpha in tag      │
  │                                                                      │
  └─────────────────────────────────────────────────────────────────────┘

  RELEASE DRAFTER (runs on every push to main):
  ┌─────────────────────────────────────────────────────────────────────┐
  │  Merged PRs ──▶ Categorize by label ──▶ Draft release notes        │
  │                                                                      │
  │  feature  → "🚀 Features"                                           │
  │  fix/bug  → "🐛 Bug Fixes"                                          │
  │  chore/ci → "🧰 Maintenance"                                        │
  │  deps     → "📦 Dependencies"                                       │
  └─────────────────────────────────────────────────────────────────────┘

  VERSION BUMP:
  ┌─────────────────────────────────────────────────────────────────────┐
  │  make bump-patch  → 0.1.0 → 0.1.1  (auto-commit + tag)            │
  │  make bump-minor  → 0.1.0 → 0.2.0                                  │
  │  make bump-major  → 0.1.0 → 1.0.0                                  │
  │                                                                      │
  │  Updates: pyproject.toml + env_manager/__init__.py                  │
  └─────────────────────────────────────────────────────────────────────┘
```

### 2. Use Case Flows

#### Use Case A: First-Time User — Discover What's on My Machine

```
  USER ACTION                    SYSTEM ACTION                    STATE
  ────────────                   ──────────────                   ─────
                                  
  $ envs scan                    loads all enabled adapters
       │                         walks filesystem
       │                         adapter.detect() on each dir
       │                         ─────────────────────────
       ▼                         stores in SQLite:
  Found 47 envs (32 GB)          · 47 environments
                                 · 32 projects
                                 · 4 languages
                                 
  $ envs list --by-project       reads from SQLite
       │                         enriches with project names
       ▼                         
  ┌─────────────────────────────────────────────────────────────┐
  │ Project          Lang    Version   Size    Last Used  Health│
  │ myapp-api        python  3.12.1    520 MB  2 hrs ago  ✓     │
  │ myapp-frontend   node    20.10.0   890 MB  1 day ago  ✓     │
  │ old-scraper      python  3.8.5     980 MB  8 mo ago   ✗     │
  │ ...                                                        │
  └─────────────────────────────────────────────────────────────┘
  
  $ envs doctor old-scraper       adapter.check_health()
       │                          · python binary missing
       ▼                          · env is unrecoverable
  ✗ old-scraper: broken
    → has snapshot, run: envs lifecycle restore old-scraper
```

#### Use Case B: Daily Workflow — Create, Use, Save

```
  $ cd ~/projects/new-api
  
  $ envs lifecycle create python@3.12 --confirm
       │                          adapter.create()
       │                          python3.12 -m venv .venv
       ▼                          stores in SQLite
  Created: /home/user/projects/new-api/.venv
  
  $ envs lifecycle install new-api fastapi uvicorn --dry-run
       │                          adapter.install() not called
       ▼                          shows: would install 2 packages
  Would install: fastapi==0.115.0, uvicorn==0.30.0
  
  $ envs lifecycle install new-api fastapi uvicorn --confirm
       │                          adapter.install(["fastapi","uvicorn"])
       ▼                          pip install fastapi uvicorn
  Installed 2 packages
  
  $ eval "$(envs lifecycle activate new-api)"
       │                          prints: source /path/to/.venv/bin/activate
       ▼                          shell evaluates, env is active
  (new-api) $ python -c "import fastapi; print('ok')"
  ok
```

#### Use Case C: Clean Up at Scale — Free Space, Stay Safe

```
  $ envs list --stale --orphaned
       │                          SQL: stale > 30 days OR is_orphaned
       ▼                          
  23 environments flagged (8.4 GB)
  
  $ envs cleanup --stale 60 --snapshot --dry-run
       │                          evaluates cleanup rules
       │                          skips: pinned projects
       │                          skips: locked (process holds file)
       ▼
  Would snapshot + remove 18 environments
  Would free: 6.2 GB
  3 skipped — pinned
  
  $ envs cleanup --stale 60 --snapshot --confirm
       │                          for each env:
       │                          1. adapter.freeze() → snapshot
       │                          2. store snapshot in SQLite (v1, v2...)
       │                          3. rmtree() the directory
       │                          4. update_state() → SNAPSHOTTED
       │                          5. activity_log: "cleaned_up"
       ▼
  Removed 18 envs. Freed 6.2 GB.
  Snapshots saved: 18 (restorable)
  
  ... 3 months later, need old-scraper again ...
  
  $ envs snapshots
       │
       ▼
  v1  python  23 pkgs  old-scraper  2026-03-15
  
  $ envs lifecycle restore old-scraper --confirm
       │                          1. read snapshot from SQLite
       │                          2. adapter.create() → new venv
       │                          3. adapter.install(frozen_deps)
       │                          4. update_state() → READY
       ▼
  Restored: old-scraper (23 packages, 18.3s)
  
  $ eval "$(envs lifecycle activate old-scraper)"
  (old-scraper) $ # back in business
```

#### Use Case D: Dashboard — Visual Browsing at Scale

```
  BROWSER                          DAEMON                         DB
  ───────                          ──────                         ──
  
  open http://localhost:9876
       │
       │  GET /                     FileResponse(index.html)
       ▼                           ────────────────────────
  Dashboard loads (SPA)
       │
       │  GET /api/envs             EnvironmentRepository.list_all()
       ▼                           ───────────────────────────────
  Envs tab: 47 envs, 32 GB
  4 summary cards
  searchable/filterable table
       │
       │  GET /api/plugins          AdapterRegistry.list_all()
       ▼                           ────────────────────────────
  Plugins: 6 adapters shown
       │
       │  WS /ws/events             connect
       ▼                           ───────
  Status: live                     push events on scan/cleanup
```

### 3. Data Flow — Key Operations

#### Scan → Persist

```
  CLI: envs scan --path ~/projects
       │
       ▼
  Scanner._walk(root, depth)
       │
       │  for each directory:
       │    for each adapter:
       │      adapter.detect(dir)
       │
       │  returns: [EnvMetadata, EnvMetadata, ...]
       │
       ▼
  Scanner._persist(meta)
       │
       ├──▶ ProjectRepository.get_or_create()
       │       └──▶ INSERT INTO projects
       │
       ├──▶ EnvironmentRepository.get_by_path()
       │       └──▶ EXISTS? → mark_scanned() + update_size()
       │
       └──▶ EnvironmentRepository.insert()
               └──▶ INSERT INTO environments
                    INSERT INTO packages (per env)
                    ActivityRepository.log("discovered")
```

#### Snapshot → Delete → Restore

```
  DELETE WITH SNAPSHOT:
  
  envs lifecycle remove myproject --snapshot --confirm
       │
       ├──▶ 1. adapter.freeze(path)
       │       └──▶ pip freeze / npm list / gem list
       │           returns: FreezeResult(raw_content, format, packages)
       │
       ├──▶ 2. SnapshotRepository.insert()
       │       └──▶ INSERT INTO snapshots (env_id, version, frozen_deps, ...)
       │           version = auto-incremented (1, 2, 3...)
       │
       ├──▶ 3. EnvironmentRepository.update_state(SNAPSHOTTED)
       │
       ├──▶ 4. shutil.rmtree(env_path)
       │
       └──▶ 5. ActivityRepository.log("removed")
  
  
  RESTORE:
  
  envs lifecycle restore myproject --confirm
       │
       ├──▶ 1. SnapshotRepository.list_all()
       │       └──▶ find matching env by path/name/project
       │
       ├──▶ 2. adapter.create(env_path, {version})
       │       └──▶ python3 -m venv /path/to/.venv
       │
       ├──▶ 3. adapter.install(env_path, frozen_deps.keys())
       │       └──▶ pip install requests flask ...
       │
       ├──▶ 4. EnvironmentRepository.update_state(READY)
       │
       └──▶ 5. ActivityRepository.log("restored")
```

### 4. Component Interaction Map

```
  ┌──────────┐     ┌──────────┐     ┌──────────────┐
  │   CLI    │────▶│  Daemon  │────▶│   Storage    │
  │ (typer)  │     │ (FastAPI)│     │  (SQLite)    │
  └──────────┘     └──────────┘     └──────────────┘
       │                │                   │
       │                │                   │
       ▼                ▼                   ▼
  ┌──────────┐     ┌──────────┐     ┌──────────────┐
  │ stdout   │     │Dashboard │     │   Models     │
  │ (rich)   │     │ (HTML)   │     │(dataclasses) │
  └──────────┘     └──────────┘     └──────────────┘
                         │
  ┌──────────────────────┼──────────────────────┐
  │                 Adapter Layer                │
  │  ┌────────┐ ┌────────┐ ┌────────┐ ┌───────┐│
  │  │ Python │ │  Node  │ │  Ruby  │ │  Go   ││
  │  │ ·venv  │ │ ·nvm   │ │ ·rbenv │ │·goenv ││
  │  │ ·poetry│ │ ·fnm   │ └────────┘ └───────┘│
  │  └────────┘ └────────┘         ┌──────────┐ │
  │                    ┌────────┐  │  Rust    │ │
  │                    │Community│  │ ·rustup  │ │
  │                    │Plugins  │  └──────────┘ │
  │                    └────────┘                │
  └──────────────────────────────────────────────┘
```

---

## Design Decisions Log

| Decision | Rationale |
|----------|-----------|
| Python Core (not Go/Rust) | Target audience already writes Python. Plugin contributions frictionless. |
| Self-contained binary (PyInstaller) | Non-Python devs must not need Python installed. Adoption risk. |
| Two-dimension state model | Management and discovery are independent concerns. Single-axis caused impossible combinations. |
| Snapshots append-only + versioned | Users need history. Overwriting snapshots silently loses data. Max N versions configurable. |
| eval activate pattern | Process can't modify parent shell. `eval "$(envs activate)"` is the standard unix compromise (conda does this). |
| CLI + Dashboard parity | Both CLI and web dashboard are first-class. CLI for automation, dashboard for visual browsing at scale. |
| Health status timestamped not static | Stored "healthy" is a lie after 24 hours. Timestamp forces freshness check. |
| Shell hooks opt-in only | Auto-modifying rc files creates trust-destroying bugs. Print the line, user opts in. |
| WAL mode on SQLite | One PRAGMA converts single-writer to concurrent reads+writes. No reason not to. |
| Smart scan exclusions | Walking /usr finds 10,000 false positives. Exclude known system paths by default. |
| Per-language tracking | Users choose which languages to track. Disable Node adapter = no .nvmrc scanning. Reduces scan time, DB size, and noise. |

---

## Critical Review — Known Gaps & Mitigations

Self-assessment of what's missing, what's risky, and what's planned.

### Fixed Before Shipping (v0.1)

| # | Gap | Fix Applied |
|---|-----|-------------|
| 1 | Release workflow had no test gate — broken tag could ship to PyPI | Added `test` job as `needs` dependency before `pypi` publish. Tagged commit must pass lint + typecheck + pytest before publishing. |
| 2 | Activate prints raw eval output — confusing to new users | Terminal detection: if stdout is a TTY, print "Run: eval \"\$(envs lifecycle activate <p>)\"" instead of raw output. |
| 3 | Scanner didn't persist to DB — scan results lost between runs | `Scanner._persist()` now inserts/updates environments into SQLite on every scan. |

### Accepted Gaps (v0.2+)

| # | Gap | Risk | Mitigation |
|---|-----|------|------------|
| 1 | **No pre-release staging** — binary built on dev branch isn't tested before merge to main | Broken binary could ship if dev build passes but binary fails | Add canary test in v0.2: download artifact, smoke-test on each OS |
| 2 | **No Homebrew tap** — macOS users expect `brew install env-manager` | Adoption friction for macOS-only devs | v0.2: create homebrew formula in separate tap repo |
| 3 | **No Windows installer** — just a .tar.gz | Windows users don't know how to use .tar.gz | v0.2: build .msi or .exe installer with NSIS/WiX |
| 4 | **Scan is always full** — no incremental mode | 1000+ env scan takes minutes every time | v0.2: scan only dirs with mtime changes since last scan |
| 5 | **No cross-machine sync** — snapshots live in local SQLite | Lose snapshot history when switching machines | v0.2: `envs db push/pull` to git-based backup |
| 6 | **Activate doesn't work in all shells** — needs `eval` wrapper in bash/zsh | User runs `envs lifecycle activate` directly, sees raw source command | Clear TTY detection + documentation |
| 7 | **Dashboard is HTML-only** — no React/Vue build step, inline JS | Harder to maintain, no component framework | v0.2: migrate to Vite + React; keep serving as static files |

### Architecture Risks

| Risk | Likelihood | Impact | Mitigation |
|------|:----------:|:------:|------------|
| SQLite corruption on crash during write | Low | High — lose all env metadata | WAL mode + `envs db backup` + auto-rebuild from filesystem (v0.2) |
| Adapter subprocess hangs (pip install timeout) | Medium | Low — CLI blocks | All subprocess calls have 30-120s timeout |
| Scanner hits permission errors in system dirs | High | Low — noisy but safe | Smart exclusions skip /usr, /System, /proc |
| Shell hook breaks user's .bashrc | Low | High — trust destroyed forever | Hooks are **opt-in only**; never auto-modify rc files |

### What We Chose NOT To Build

| Feature | Why Not |
|---------|---------|
| Docker-based isolation | Different paradigm; env-manager is lightweight local-first. Use Docker if you need containers. |
| Cloud-hosted dashboard | Privacy risk; all data stays local. Dashboard is localhost-only. |
| Auto-commit/push of snapshots | Breaks user autonomy; snapshots are local by design. Manual `envs db backup` for portability. |
| GUI desktop app | Unnecessary; CLI + localhost dashboard covers all use cases. Electron would bloat the binary 10x. |
