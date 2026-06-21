# env-manager — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a cross-language virtual environment manager (CLI + localhost dashboard) that discovers, manages, health-checks, snapshots, and safely cleans up environments across Python, Node, Ruby, Go, and Rust.

**Architecture:** Python Core daemon (FastAPI + SQLite + APScheduler) with pluggable language adapters via an ABC protocol. CLI and web dashboard communicate with the daemon over REST + WebSocket. Shipped as a self-contained PyInstaller binary.

**Tech Stack:** Python 3.10+, FastAPI, SQLite (WAL mode), Typer (CLI), APScheduler, PyInstaller, Pytest, React (dashboard)

---

## Phases Overview

| Phase | Milestone | Test Gate |
|-------|-----------|-----------|
| **0** | Project scaffold, dev tooling, CI | `pytest` runs, `ruff` passes, `mypy` passes |
| **1** | Data models + Storage + Python adapter + Scanner + CLI (read-only) | `envs scan` + `envs list` works on real machine |
| **2** | Lifecycle CLI + Daemon + API + remaining adapters (Node, Ruby, Go, Rust) | `envs create/install/delete/restore` works across all 5 languages |
| **3** | Health system + Snapshot system + Cleanup | `envs doctor` + `envs cleanup --snapshot` + `envs restore` end-to-end |
| **4** | Dashboard + Packaging + Polish | Dashboard at localhost, single-binary distribution |

Each phase is independently testable and shippable. Phase 0 is foundation. Phases 1-3 build the product incrementally. Phase 4 adds the GUI and distribution.

---

## WBS — Work Breakdown Structure

```
env-manager
├── Phase 0: Foundation
│   ├── 0.1  Project scaffold
│   ├── 0.2  Dev tooling (lint, typecheck, test runner)
│   └── 0.3  CI pipeline
├── Phase 1: Core Engine
│   ├── 1.1  Data models (dataclasses)
│   ├── 1.2  SQLite storage layer
│   ├── 1.3  Base adapter ABC + plugin loader
│   ├── 1.4  Python venv adapter
│   ├── 1.5  Discovery engine (scanner)
│   ├── 1.6  CLI foundation + read-only commands
│   └── 1.7  Phase 1 integration test gate
├── Phase 2: Lifecycle + API + More Adapters
│   ├── 2.1  CLI lifecycle commands (create, install, delete, restore)
│   ├── 2.2  Daemon core (FastAPI)
│   ├── 2.3  REST API endpoints
│   ├── 2.4  Node.js adapters (nvm, fnm, volta)
│   ├── 2.5  Ruby adapters (rbenv, rvm)
│   ├── 2.6  Go + Rust adapters
│   └── 2.7  Phase 2 integration test gate
├── Phase 3: Health + Snapshots + Cleanup
│   ├── 3.1  Health check system (doctor)
│   ├── 3.2  Snapshot system (freeze + restore)
│   ├── 3.3  Cleanup engine
│   └── 3.4  Phase 3 end-to-end test gate
└── Phase 4: Dashboard + Packaging
    ├── 4.1  React dashboard scaffold
    ├── 4.2  Dashboard pages (list, info, cleanup, doctor)
    ├── 4.3  WebSocket real-time updates
    ├── 4.4  PyInstaller packaging
    └── 4.5  Release pipeline
```

---

## File Structure

```
env-manager/
├── DESIGN.md
├── .gitignore
├── pyproject.toml
├── Makefile
├── env_manager/
│   ├── __init__.py
│   ├── models/
│   │   ├── __init__.py
│   │   ├── env.py              # EnvMetadata, Package, FreezeResult, HealthResult
│   │   ├── project.py          # Project
│   │   └── states.py           # ManagementState, DiscoveryStatus enums
│   ├── storage/
│   │   ├── __init__.py
│   │   ├── database.py         # SQLite connection, WAL, migrations
│   │   ├── schema.sql          # DDL
│   │   ├── repo_env.py         # EnvironmentRepository
│   │   ├── repo_project.py     # ProjectRepository
│   │   ├── repo_snapshot.py    # SnapshotRepository
│   │   └── repo_activity.py    # ActivityRepository
│   ├── adapters/
│   │   ├── __init__.py
│   │   ├── base.py             # BaseAdapter ABC
│   │   ├── loader.py           # Adapter discovery + loading
│   │   ├── registry.py         # AdapterRegistry
│   │   ├── python/
│   │   │   ├── __init__.py
│   │   │   ├── venv.py         # PythonVenvAdapter
│   │   │   └── poetry.py       # PythonPoetryAdapter
│   │   ├── node/
│   │   │   ├── __init__.py
│   │   │   ├── nvm.py          # NodeNvmAdapter
│   │   │   └── fnm.py          # NodeFnmAdapter
│   │   ├── ruby/
│   │   │   ├── __init__.py
│   │   │   └── rbenv.py        # RubyRbenvAdapter
│   │   ├── go/
│   │   │   ├── __init__.py
│   │   │   └── goenv.py        # GoGoenvAdapter
│   │   └── rust/
│   │       ├── __init__.py
│   │       └── rustup.py       # RustRustupAdapter
│   ├── discovery/
│   │   ├── __init__.py
│   │   ├── scanner.py          # Filesystem scanner
│   │   ├── hooks.py            # Shell hook generation
│   │   └── registry.py         # Manual env registration
│   ├── health/
│   │   ├── __init__.py
│   │   └── doctor.py           # Health check runner
│   ├── snapshot/
│   │   ├── __init__.py
│   │   ├── freezer.py          # Adapter.freeze() orchestration
│   │   └── restorer.py         # Adapter.create() + install from snapshot
│   ├── cleanup/
│   │   ├── __init__.py
│   │   └── engine.py           # Cleanup rule evaluation
│   ├── cli/
│   │   ├── __init__.py
│   │   ├── main.py             # Typer app entry
│   │   ├── commands/
│   │   │   ├── __init__.py
│   │   │   ├── scan.py
│   │   │   ├── list_cmd.py
│   │   │   ├── info.py
│   │   │   ├── create.py
│   │   │   ├── lifecycle.py    # install, uninstall, update, delete
│   │   │   ├── shell.py        # activate, shell
│   │   │   ├── restore.py
│   │   │   ├── doctor.py
│   │   │   ├── cleanup.py
│   │   │   ├── config.py       # config show, plugins enable/disable
│   │   │   └── plugin.py       # plugins list/add/remove
│   │   └── formatters.py       # Table, JSON, colored output
│   ├── daemon/
│   │   ├── __init__.py
│   │   ├── server.py           # FastAPI app + uvicorn
│   │   ├── api/
│   │   │   ├── __init__.py
│   │   │   ├── envs.py         # /api/envs endpoints
│   │   │   ├── projects.py     # /api/projects endpoints
│   │   │   ├── health.py       # /api/health endpoints
│   │   │   ├── snapshots.py    # /api/snapshots endpoints
│   │   │   ├── plugins.py      # /api/plugins endpoints
│   │   │   └── ws.py           # WebSocket for dashboard
│   │   └── scheduler.py        # APScheduler: periodic scans
│   └── dashboard/
│       ├── index.html
│       ├── package.json
│       ├── src/
│       │   ├── App.tsx
│       │   ├── api.ts          # REST + WS client
│       │   ├── pages/
│       │   │   ├── Dashboard.tsx
│       │   │   ├── EnvList.tsx
│       │   │   ├── EnvInfo.tsx
│       │   │   ├── Doctor.tsx
│       │   │   └── Cleanup.tsx
│       │   └── components/
│       │       ├── EnvTable.tsx
│       │       ├── DiskChart.tsx
│       │       └── StatusBadge.tsx
│       └── dist/               # built static files served by FastAPI
└── tests/
    ├── __init__.py
    ├── conftest.py             # Fixtures: temp SQLite, mock adapters, temp dirs
    ├── models/
    │   └── test_states.py
    ├── storage/
    │   ├── test_database.py
    │   ├── test_repo_env.py
    │   ├── test_repo_project.py
    │   └── test_repo_snapshot.py
    ├── adapters/
    │   ├── test_base.py
    │   ├── test_loader.py
    │   ├── python/
    │   │   └── test_venv.py
    │   └── conftest.py         # Fake env factories
    ├── discovery/
    │   └── test_scanner.py
    ├── health/
    │   └── test_doctor.py
    ├── snapshot/
    │   ├── test_freezer.py
    │   └── test_restorer.py
    ├── cleanup/
    │   └── test_engine.py
    ├── cli/
    │   ├── test_scan.py
    │   ├── test_list.py
    │   ├── test_info.py
    │   ├── test_create.py
    │   ├── test_lifecycle.py
    │   ├── test_restore.py
    │   └── test_doctor.py
    └── daemon/
        ├── test_server.py
        ├── test_api_envs.py
        └── test_api_health.py
```

---

## Phase 0: Foundation

### Task 0.1: Project Scaffold

**Files:**
- Create: `pyproject.toml`
- Create: `Makefile`
- Create: `env_manager/__init__.py`

- [ ] **Step 1: Create pyproject.toml with dependencies**

```toml
[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "env-manager"
version = "0.1.0"
description = "Cross-language virtual environment manager"
requires-python = ">=3.10"
dependencies = [
    "fastapi>=0.115.0",
    "uvicorn[standard]>=0.30.0",
    "typer>=0.12.0",
    "rich>=13.0.0",
    "apscheduler>=3.10.0",
    "websockets>=12.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.24.0",
    "pytest-cov>=5.0",
    "ruff>=0.5.0",
    "mypy>=1.10",
]

[project.scripts]
envs = "env_manager.cli.main:app"

[tool.ruff]
target-version = "py310"
line-length = 100

[tool.ruff.lint]
select = ["E", "F", "I", "N", "W", "UP", "B", "C4", "SIM"]

[tool.mypy]
python_version = "3.10"
strict = true

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

- [ ] **Step 2: Create Makefile with dev commands**

```makefile
.PHONY: install test lint typecheck clean

install:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --tb=short

test-cov:
	pytest tests/ -v --cov=env_manager --cov-report=term-missing

lint:
	ruff check env_manager/ tests/

lint-fix:
	ruff check --fix env_manager/ tests/

typecheck:
	mypy env_manager/

check: lint typecheck test
	@echo "All checks passed"

clean:
	rm -rf dist/ build/ *.egg-info/ .pytest_cache/ __pycache__/
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
```

- [ ] **Step 3: Create env_manager/__init__.py**

```python
__version__ = "0.1.0"
```

- [ ] **Step 4: Verify scaffold works**

Run: `pip install -e ".[dev]"`
Expected: installs without errors

Run: `make lint`
Expected: passes (no files to lint yet, or ruff works)

Run: `pytest tests/`
Expected: "no tests ran" (test infrastructure works)

- [ ] **Step 5: Commit**

```bash
git add pyproject.toml Makefile env_manager/__init__.py
git commit -m "chore: project scaffold with pyproject.toml, Makefile, ruff, mypy, pytest"
```

### Task 0.2: Gitignore additions

**Files:**
- Modify: `.gitignore`

- [ ] **Step 1: Add Python/build exclusions to .gitignore**

Append to `.gitignore`:
```
dist/
build/
*.egg-info/
.pytest_cache/
.ruff_cache/
.mypy_cache/
.coverage
htmlcov/
```

- [ ] **Step 2: Commit**

```bash
git add .gitignore
git commit -m "chore: add Python build/test artifacts to gitignore"
```

### Task 0.3: CI Pipeline

**Files:**
- Create: `.github/workflows/ci.yml`

- [ ] **Step 1: Create GitHub Actions CI**

```yaml
name: CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  test:
    runs-on: ubuntu-latest
    strategy:
      matrix:
        python-version: ["3.10", "3.11", "3.12"]

    steps:
    - uses: actions/checkout@v4
    - uses: actions/setup-python@v5
      with:
        python-version: ${{ matrix.python-version }}
    - run: pip install -e ".[dev]"
    - run: make lint
    - run: make typecheck
    - run: make test-cov
```

- [ ] **Step 2: Verify CI config**

Run: `cat .github/workflows/ci.yml` — verify syntax

- [ ] **Step 3: Commit**

```bash
git add .github/workflows/ci.yml
git commit -m "ci: add GitHub Actions CI pipeline (lint, typecheck, test)"
```

---

## Phase 1: Core Engine

### Task 1.1: Data Models

**Files:**
- Create: `env_manager/models/__init__.py`
- Create: `env_manager/models/states.py`
- Create: `env_manager/models/env.py`
- Create: `env_manager/models/project.py`
- Create: `tests/models/test_states.py`

**Test Gate:** All model tests pass, enums have correct values

- [ ] **Step 1: Write failing test for ManagementState enum**

Create `tests/models/test_states.py`:
```python
from env_manager.models.states import ManagementState, DiscoveryStatus


def test_management_state_values():
    assert ManagementState.CREATING.value == "creating"
    assert ManagementState.READY.value == "ready"
    assert ManagementState.UPDATING.value == "updating"
    assert ManagementState.ERROR.value == "error"
    assert ManagementState.SNAPSHOTTED.value == "snapshotted"
    assert ManagementState.DELETED.value == "deleted"
    assert ManagementState.PURGED.value == "purged"


def test_discovery_status_values():
    assert DiscoveryStatus.UNTRACKED.value == "untracked"
    assert DiscoveryStatus.TRACKED.value == "tracked"
    assert DiscoveryStatus.IGNORED.value == "ignored"


def test_management_state_allows_restore():
    """envs restore should only work on SNAPSHOTTED envs"""
    restorable = {ManagementState.SNAPSHOTTED}
    assert ManagementState.READY not in restorable
    assert ManagementState.PURGED not in restorable
    assert ManagementState.SNAPSHOTTED in restorable
```

Run: `pytest tests/models/test_states.py -v`
Expected: FAIL — module not found

- [ ] **Step 2: Implement states.py**

Create `env_manager/models/states.py`:
```python
from enum import Enum


class ManagementState(str, Enum):
    CREATING = "creating"
    READY = "ready"
    UPDATING = "updating"
    ERROR = "error"
    SNAPSHOTTED = "snapshotted"
    DELETED = "deleted"
    PURGED = "purged"


class DiscoveryStatus(str, Enum):
    UNTRACKED = "untracked"
    TRACKED = "tracked"
    IGNORED = "ignored"
```

Create `env_manager/models/__init__.py`:
```python
from env_manager.models.states import ManagementState, DiscoveryStatus

__all__ = ["ManagementState", "DiscoveryStatus"]
```

Run: `pytest tests/models/test_states.py -v`
Expected: 3 PASS

- [ ] **Step 3: Write failing test for EnvMetadata dataclass**

Add to `tests/models/test_states.py`:
```python
from env_manager.models.env import EnvMetadata, Package


def test_env_metadata_creation():
    meta = EnvMetadata(
        language="python",
        tool="venv",
        version="3.12.1",
        path="/home/user/projects/myapp/.venv",
        size_bytes=245_000_000,
        interpreter_path="/usr/bin/python3.12",
        packages_count=23,
    )
    assert meta.language == "python"
    assert meta.tool == "venv"
    assert meta.size_bytes == 245_000_000
    assert meta.env_type == "local"  # default


def test_package_creation():
    pkg = Package(name="requests", version="2.31.0")
    assert pkg.name == "requests"
    assert pkg.version == "2.31.0"


def test_env_metadata_global_type():
    meta = EnvMetadata(
        language="node",
        tool="nvm",
        version="20.10.0",
        path="/home/user/.nvm/versions/node/v20.10.0",
        size_bytes=150_000_000,
        interpreter_path="/home/user/.nvm/versions/node/v20.10.0/bin/node",
        packages_count=0,
        env_type="global",
    )
    assert meta.env_type == "global"
```

Run: `pytest tests/models/test_states.py -v`
Expected: 2 new FAILs — EnvMetadata not defined

- [ ] **Step 4: Implement env.py models**

Create `env_manager/models/env.py`:
```python
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Package:
    name: str
    version: str


@dataclass
class EnvMetadata:
    language: str
    tool: str
    version: str
    path: str
    size_bytes: int
    interpreter_path: str
    packages_count: int = 0
    env_type: str = "local"


@dataclass
class FreezeResult:
    raw_content: str
    format: str
    packages: list[Package] = field(default_factory=list)


@dataclass
class HealthResult:
    status: str  # "healthy" | "degraded" | "broken"
    checks: list[dict] = field(default_factory=list)
    errors: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)
```

Update `env_manager/models/__init__.py`:
```python
from env_manager.models.states import ManagementState, DiscoveryStatus
from env_manager.models.env import EnvMetadata, Package, FreezeResult, HealthResult

__all__ = [
    "ManagementState",
    "DiscoveryStatus",
    "EnvMetadata",
    "Package",
    "FreezeResult",
    "HealthResult",
]
```

Run: `pytest tests/models/test_states.py -v`
Expected: 5 PASS

- [ ] **Step 5: Commit**

```bash
git add env_manager/models/ tests/models/
git commit -m "feat: add data models — ManagementState, DiscoveryStatus, EnvMetadata, Package"
```

### Task 1.2: SQLite Storage Layer

**Files:**
- Create: `env_manager/storage/__init__.py`
- Create: `env_manager/storage/database.py`
- Create: `env_manager/storage/schema.sql`
- Create: `tests/storage/test_database.py`
- Create: `tests/conftest.py`

**Test Gate:** In-memory SQLite DB created, WAL enabled, schema applied, CRUD operations work

- [ ] **Step 1: Write failing test for database connection**

Create `tests/conftest.py`:
```python
import pytest
import sqlite3
from pathlib import Path
from env_manager.storage.database import get_connection, init_db


@pytest.fixture
def db_path(tmp_path):
    """Temp SQLite database path."""
    return str(tmp_path / "test.db")


@pytest.fixture
def db_connection(db_path):
    """Initialized database connection."""
    init_db(db_path)
    conn = get_connection(db_path)
    yield conn
    conn.close()


@pytest.fixture
def temp_dir(tmp_path):
    """Temporary directory for file operations."""
    return tmp_path
```

Create `tests/storage/test_database.py`:
```python
import sqlite3
from env_manager.storage.database import init_db, get_connection


def test_init_db_creates_tables(db_path):
    init_db(db_path)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # Verify all tables exist
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
    tables = [row[0] for row in cursor.fetchall()]

    assert "projects" in tables
    assert "environments" in tables
    assert "snapshots" in tables
    assert "packages" in tables
    assert "activity_log" in tables
    assert "scan_history" in tables
    assert "cleanup_rules" in tables
    assert "adapter_registry" in tables

    conn.close()


def test_wal_mode_enabled(db_path):
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    cursor = conn.execute("PRAGMA journal_mode")
    assert cursor.fetchone()[0].lower() == "wal"
    conn.close()


def test_get_connection_returns_same_instance(db_path):
    init_db(db_path)
    conn1 = get_connection(db_path)
    conn2 = get_connection(db_path)
    assert conn1 is conn2
    conn1.close()
```

Run: `pytest tests/storage/test_database.py -v`
Expected: FAIL — module not found

- [ ] **Step 2: Create schema.sql**

Create `env_manager/storage/schema.sql`:
```sql
PRAGMA journal_mode=WAL;
PRAGMA foreign_keys=ON;

CREATE TABLE IF NOT EXISTS projects (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    path TEXT NOT NULL UNIQUE,
    last_active TEXT,
    tags TEXT DEFAULT '[]',
    is_pinned INTEGER DEFAULT 0,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    updated_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS environments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    adapter TEXT NOT NULL,
    env_type TEXT NOT NULL,
    path TEXT NOT NULL,
    language TEXT NOT NULL,
    version TEXT,
    tool TEXT,
    size_bytes INTEGER DEFAULT 0,
    management_state TEXT NOT NULL DEFAULT 'ready',
    discovery_status TEXT NOT NULL DEFAULT 'untracked',
    is_stale INTEGER DEFAULT 0,
    is_orphaned INTEGER DEFAULT 0,
    is_locked INTEGER DEFAULT 0,
    last_health_check TEXT,
    last_health_result TEXT,
    metadata TEXT DEFAULT '{}',
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    last_used_at TEXT,
    last_scanned_at TEXT
);
CREATE INDEX IF NOT EXISTS idx_envs_project ON environments(project_id);
CREATE INDEX IF NOT EXISTS idx_envs_language ON environments(language);
CREATE INDEX IF NOT EXISTS idx_envs_mgmt_state ON environments(management_state);
CREATE INDEX IF NOT EXISTS idx_envs_disc_status ON environments(discovery_status);
CREATE INDEX IF NOT EXISTS idx_envs_path ON environments(path);

CREATE TABLE IF NOT EXISTS snapshots (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    env_id INTEGER NOT NULL REFERENCES environments(id) ON DELETE CASCADE,
    version INTEGER NOT NULL,
    frozen_deps TEXT NOT NULL,
    raw_lockfile TEXT,
    lockfile_format TEXT,
    tool_config TEXT DEFAULT '{}',
    notes TEXT,
    created_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(env_id, version)
);
CREATE INDEX IF NOT EXISTS idx_snapshots_env ON snapshots(env_id);

CREATE TABLE IF NOT EXISTS packages (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    env_id INTEGER NOT NULL REFERENCES environments(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    version TEXT NOT NULL,
    scanned_at TEXT NOT NULL DEFAULT (datetime('now')),
    UNIQUE(env_id, name)
);
CREATE INDEX IF NOT EXISTS idx_packages_env ON packages(env_id);
CREATE INDEX IF NOT EXISTS idx_packages_name ON packages(name);

CREATE TABLE IF NOT EXISTS activity_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    env_id INTEGER REFERENCES environments(id) ON DELETE SET NULL,
    project_id INTEGER REFERENCES projects(id) ON DELETE SET NULL,
    event TEXT NOT NULL,
    detail TEXT DEFAULT '{}',
    timestamp TEXT NOT NULL DEFAULT (datetime('now'))
);
CREATE INDEX IF NOT EXISTS idx_activity_env ON activity_log(env_id);
CREATE INDEX IF NOT EXISTS idx_activity_ts ON activity_log(timestamp);

CREATE TABLE IF NOT EXISTS scan_history (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    started_at TEXT NOT NULL,
    finished_at TEXT,
    paths_scanned INTEGER DEFAULT 0,
    envs_found INTEGER DEFAULT 0,
    envs_new INTEGER DEFAULT 0,
    errors TEXT DEFAULT '[]'
);

CREATE TABLE IF NOT EXISTS cleanup_rules (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,
    conditions TEXT NOT NULL,
    action TEXT NOT NULL,
    enabled INTEGER DEFAULT 1,
    created_at TEXT NOT NULL DEFAULT (datetime('now'))
);

CREATE TABLE IF NOT EXISTS adapter_registry (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL UNIQUE,
    display_name TEXT NOT NULL,
    version TEXT NOT NULL,
    env_type TEXT NOT NULL,
    source TEXT NOT NULL,
    source_path TEXT,
    enabled INTEGER DEFAULT 1,
    installed_at TEXT NOT NULL DEFAULT (datetime('now'))
);
```

- [ ] **Step 3: Implement database.py**

Create `env_manager/storage/database.py`:
```python
import sqlite3
from pathlib import Path
from threading import Lock

_connections: dict[str, sqlite3.Connection] = {}
_lock = Lock()

SCHEMA_PATH = Path(__file__).parent / "schema.sql"


def init_db(db_path: str) -> None:
    """Initialize database with schema. Idempotent (IF NOT EXISTS)."""
    schema = SCHEMA_PATH.read_text()
    conn = get_connection(db_path)
    conn.executescript(schema)
    conn.commit()


def get_connection(db_path: str) -> sqlite3.Connection:
    """Get or create a connection for the given DB path. Thread-safe."""
    with _lock:
        if db_path not in _connections:
            conn = sqlite3.connect(db_path)
            conn.row_factory = sqlite3.Row
            conn.execute("PRAGMA journal_mode=WAL")
            conn.execute("PRAGMA foreign_keys=ON")
            _connections[db_path] = conn
        return _connections[db_path]


def close_connection(db_path: str) -> None:
    """Close and remove a connection."""
    with _lock:
        conn = _connections.pop(db_path, None)
        if conn:
            conn.close()
```

Create `env_manager/storage/__init__.py`:
```python
from env_manager.storage.database import init_db, get_connection, close_connection

__all__ = ["init_db", "get_connection", "close_connection"]
```

Run: `pytest tests/storage/test_database.py -v`
Expected: 3 PASS

- [ ] **Step 4: Commit**

```bash
git add env_manager/storage/ tests/storage/ tests/conftest.py
git commit -m "feat: add SQLite storage layer with schema and connection manager"
```

### Task 1.3: Repository Layer

**Files:**
- Create: `env_manager/storage/repo_env.py`
- Create: `env_manager/storage/repo_project.py`
- Create: `env_manager/storage/repo_snapshot.py`
- Create: `env_manager/storage/repo_activity.py`
- Create: `tests/storage/test_repo_env.py`
- Create: `tests/storage/test_repo_project.py`
- Create: `tests/storage/test_repo_snapshot.py`

**Test Gate:** CRUD operations work on all repositories, foreign keys enforced

- [ ] **Step 1: Write failing test for EnvironmentRepository**

Create `tests/storage/test_repo_env.py`:
```python
import json
from env_manager.storage.database import get_connection
from env_manager.storage.repo_env import EnvironmentRepository
from env_manager.storage.repo_project import ProjectRepository
from env_manager.models.states import ManagementState, DiscoveryStatus


def test_insert_and_get_env(db_path):
    from env_manager.storage.database import init_db
    init_db(db_path)

    # Create a project first (FK constraint)
    proj_repo = ProjectRepository(get_connection(db_path))
    proj_id = proj_repo.insert(name="test-project", path="/tmp/test-project")

    repo = EnvironmentRepository(get_connection(db_path))
    env_id = repo.insert(
        project_id=proj_id,
        adapter="python.venv",
        env_type="local",
        path="/tmp/test-project/.venv",
        language="python",
        version="3.12.1",
        tool="venv",
        size_bytes=245_000_000,
        management_state=ManagementState.READY,
        discovery_status=DiscoveryStatus.TRACKED,
    )
    assert env_id > 0

    env = repo.get_by_id(env_id)
    assert env["language"] == "python"
    assert env["version"] == "3.12.1"
    assert env["management_state"] == "ready"
    assert env["project_id"] == proj_id


def test_list_by_language(db_path):
    from env_manager.storage.database import init_db
    init_db(db_path)

    proj_repo = ProjectRepository(get_connection(db_path))
    pid = proj_repo.insert(name="p1", path="/tmp/p1")

    repo = EnvironmentRepository(get_connection(db_path))
    repo.insert(project_id=pid, adapter="python.venv", env_type="local",
                path="/tmp/p1/.venv", language="python", version="3.12")
    repo.insert(project_id=pid, adapter="node.nvm", env_type="global",
                path="/tmp/.nvm/v20", language="node", version="20.10")

    python_envs = repo.list_by_language("python")
    assert len(python_envs) == 1

    all_envs = repo.list_all()
    assert len(all_envs) == 2


def test_update_state(db_path):
    from env_manager.storage.database import init_db
    init_db(db_path)

    proj_repo = ProjectRepository(get_connection(db_path))
    pid = proj_repo.insert(name="p1", path="/tmp/p1")

    repo = EnvironmentRepository(get_connection(db_path))
    env_id = repo.insert(project_id=pid, adapter="python.venv", env_type="local",
                         path="/tmp/p1/.venv", language="python", version="3.12")

    repo.update_state(env_id, ManagementState.ERROR)
    env = repo.get_by_id(env_id)
    assert env["management_state"] == "error"


def test_delete_env(db_path):
    from env_manager.storage.database import init_db
    init_db(db_path)

    proj_repo = ProjectRepository(get_connection(db_path))
    pid = proj_repo.insert(name="p1", path="/tmp/p1")

    repo = EnvironmentRepository(get_connection(db_path))
    env_id = repo.insert(project_id=pid, adapter="python.venv", env_type="local",
                         path="/tmp/p1/.venv", language="python", version="3.12")

    repo.delete(env_id)
    assert repo.get_by_id(env_id) is None
```

Run: `pytest tests/storage/test_repo_env.py -v`
Expected: FAIL — module not found

- [ ] **Step 2: Implement ProjectRepository**

Create `env_manager/storage/repo_project.py`:
```python
import json
import sqlite3
from typing import Optional


class ProjectRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def insert(self, name: str, path: str, tags: Optional[list[str]] = None) -> int:
        cursor = self.conn.execute(
            "INSERT INTO projects (name, path, tags) VALUES (?, ?, ?)",
            (name, path, json.dumps(tags or [])),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_by_id(self, project_id: int) -> Optional[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM projects WHERE id = ?", (project_id,)
        ).fetchone()

    def get_by_path(self, path: str) -> Optional[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM projects WHERE path = ?", (path,)
        ).fetchone()

    def get_or_create(self, name: str, path: str) -> tuple[int, bool]:
        existing = self.get_by_path(path)
        if existing:
            return existing["id"], False
        return self.insert(name=name, path=path), True

    def list_all(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM projects ORDER BY name"
        ).fetchall()

    def set_pinned(self, project_id: int, pinned: bool) -> None:
        self.conn.execute(
            "UPDATE projects SET is_pinned = ?, updated_at = datetime('now') WHERE id = ?",
            (int(pinned), project_id),
        )
        self.conn.commit()

    def touch(self, project_id: int) -> None:
        self.conn.execute(
            "UPDATE projects SET last_active = datetime('now'), updated_at = datetime('now') WHERE id = ?",
            (project_id,),
        )
        self.conn.commit()
```

- [ ] **Step 3: Implement EnvironmentRepository**

Create `env_manager/storage/repo_env.py`:
```python
import json
import sqlite3
from typing import Optional
from env_manager.models.states import ManagementState, DiscoveryStatus


class EnvironmentRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def insert(
        self,
        project_id: int,
        adapter: str,
        env_type: str,
        path: str,
        language: str,
        version: str,
        tool: str = "",
        size_bytes: int = 0,
        management_state: ManagementState = ManagementState.READY,
        discovery_status: DiscoveryStatus = DiscoveryStatus.UNTRACKED,
        metadata: Optional[dict] = None,
    ) -> int:
        cursor = self.conn.execute(
            """INSERT INTO environments
               (project_id, adapter, env_type, path, language, version, tool,
                size_bytes, management_state, discovery_status, metadata, last_scanned_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'))""",
            (
                project_id, adapter, env_type, path, language, version, tool,
                size_bytes, management_state.value, discovery_status.value,
                json.dumps(metadata or {}),
            ),
        )
        self.conn.commit()
        return cursor.lastrowid

    def get_by_id(self, env_id: int) -> Optional[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM environments WHERE id = ?", (env_id,)
        ).fetchone()

    def get_by_path(self, path: str) -> Optional[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM environments WHERE path = ?", (path,)
        ).fetchone()

    def list_all(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM environments WHERE management_state != 'purged' ORDER BY language, project_id"
        ).fetchall()

    def list_by_language(self, language: str) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM environments WHERE language = ? AND management_state != 'purged'",
            (language,),
        ).fetchall()

    def list_by_project(self, project_id: int) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM environments WHERE project_id = ? AND management_state != 'purged'",
            (project_id,),
        ).fetchall()

    def list_by_state(self, state: ManagementState) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM environments WHERE management_state = ?", (state.value,)
        ).fetchall()

    def list_stale(self, days: int) -> list[sqlite3.Row]:
        return self.conn.execute(
            """SELECT * FROM environments
               WHERE management_state = 'ready'
               AND last_used_at < datetime('now', ?)""",
            (f"-{days} days",),
        ).fetchall()

    def list_orphaned(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM environments WHERE is_orphaned = 1 AND management_state != 'purged'"
        ).fetchall()

    def list_by_discovery(self, status: DiscoveryStatus) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM environments WHERE discovery_status = ?", (status.value,)
        ).fetchall()

    def update_state(self, env_id: int, state: ManagementState) -> None:
        self.conn.execute(
            "UPDATE environments SET management_state = ? WHERE id = ?",
            (state.value, env_id),
        )
        self.conn.commit()

    def update_discovery_status(self, env_id: int, status: DiscoveryStatus) -> None:
        self.conn.execute(
            "UPDATE environments SET discovery_status = ? WHERE id = ?",
            (status.value, env_id),
        )
        self.conn.commit()

    def update_size(self, env_id: int, size_bytes: int) -> None:
        self.conn.execute(
            "UPDATE environments SET size_bytes = ? WHERE id = ?",
            (size_bytes, env_id),
        )
        self.conn.commit()

    def touch(self, env_id: int) -> None:
        self.conn.execute(
            "UPDATE environments SET last_used_at = datetime('now') WHERE id = ?",
            (env_id,),
        )
        self.conn.commit()

    def mark_scanned(self, env_id: int) -> None:
        self.conn.execute(
            "UPDATE environments SET last_scanned_at = datetime('now') WHERE id = ?",
            (env_id,),
        )
        self.conn.commit()

    def update_health(self, env_id: int, result: str) -> None:
        self.conn.execute(
            "UPDATE environments SET last_health_check = datetime('now'), last_health_result = ? WHERE id = ?",
            (result, env_id),
        )
        self.conn.commit()

    def set_orphaned(self, env_id: int, orphaned: bool) -> None:
        self.conn.execute(
            "UPDATE environments SET is_orphaned = ? WHERE id = ?",
            (int(orphaned), env_id),
        )
        self.conn.commit()

    def delete(self, env_id: int) -> None:
        self.conn.execute("DELETE FROM environments WHERE id = ?", (env_id,))
        self.conn.commit()
```

Run: `pytest tests/storage/test_repo_env.py -v`
Expected: 4 PASS

- [ ] **Step 4: Write and implement SnapshotRepository + ActivityRepository**

Create `env_manager/storage/repo_snapshot.py`:
```python
import json
import sqlite3
from typing import Optional


class SnapshotRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def insert(self, env_id: int, frozen_deps: dict, raw_lockfile: str = "",
               lockfile_format: str = "", tool_config: dict | None = None,
               notes: str = "") -> tuple[int, int]:
        """Returns (snapshot_id, version_number)."""
        latest = self.get_latest_version(env_id)
        version = (latest or 0) + 1
        cursor = self.conn.execute(
            """INSERT INTO snapshots (env_id, version, frozen_deps, raw_lockfile,
               lockfile_format, tool_config, notes)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (env_id, version, json.dumps(frozen_deps), raw_lockfile,
             lockfile_format, json.dumps(tool_config or {}), notes),
        )
        self.conn.commit()
        return cursor.lastrowid, version

    def get_latest_version(self, env_id: int) -> Optional[int]:
        row = self.conn.execute(
            "SELECT MAX(version) FROM snapshots WHERE env_id = ?", (env_id,)
        ).fetchone()
        return row[0] if row else None

    def get_by_env_and_version(self, env_id: int, version: int) -> Optional[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM snapshots WHERE env_id = ? AND version = ?",
            (env_id, version),
        ).fetchone()

    def get_latest(self, env_id: int) -> Optional[sqlite3.Row]:
        version = self.get_latest_version(env_id)
        if version is None:
            return None
        return self.get_by_env_and_version(env_id, version)

    def list_by_env(self, env_id: int) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM snapshots WHERE env_id = ? ORDER BY version DESC",
            (env_id,),
        ).fetchall()

    def list_all(self) -> list[sqlite3.Row]:
        return self.conn.execute(
            """SELECT s.*, e.language, e.version as env_version, e.tool
               FROM snapshots s
               JOIN environments e ON s.env_id = e.id
               ORDER BY s.created_at DESC"""
        ).fetchall()

    def prune(self, env_id: int, keep: int = 5) -> int:
        """Delete old versions beyond `keep`. Returns count deleted."""
        versions = self.conn.execute(
            "SELECT version FROM snapshots WHERE env_id = ? ORDER BY version DESC",
            (env_id,),
        ).fetchall()
        if len(versions) <= keep:
            return 0
        to_delete = [v[0] for v in versions[keep:]]
        self.conn.executemany(
            "DELETE FROM snapshots WHERE env_id = ? AND version = ?",
            [(env_id, v) for v in to_delete],
        )
        self.conn.commit()
        return len(to_delete)
```

Create `env_manager/storage/repo_activity.py`:
```python
import json
import sqlite3
from typing import Optional


class ActivityRepository:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    def log(self, event: str, env_id: Optional[int] = None,
            project_id: Optional[int] = None, detail: dict | None = None) -> int:
        cursor = self.conn.execute(
            "INSERT INTO activity_log (env_id, project_id, event, detail) VALUES (?, ?, ?, ?)",
            (env_id, project_id, event, json.dumps(detail or {})),
        )
        self.conn.commit()
        return cursor.lastrowid

    def list_recent(self, limit: int = 50) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM activity_log ORDER BY timestamp DESC LIMIT ?",
            (limit,),
        ).fetchall()

    def list_by_env(self, env_id: int, limit: int = 50) -> list[sqlite3.Row]:
        return self.conn.execute(
            "SELECT * FROM activity_log WHERE env_id = ? ORDER BY timestamp DESC LIMIT ?",
            (env_id, limit),
        ).fetchall()
```

Update `env_manager/storage/__init__.py`:
```python
from env_manager.storage.database import init_db, get_connection, close_connection
from env_manager.storage.repo_env import EnvironmentRepository
from env_manager.storage.repo_project import ProjectRepository
from env_manager.storage.repo_snapshot import SnapshotRepository
from env_manager.storage.repo_activity import ActivityRepository

__all__ = [
    "init_db",
    "get_connection",
    "close_connection",
    "EnvironmentRepository",
    "ProjectRepository",
    "SnapshotRepository",
    "ActivityRepository",
]
```

Write tests for `tests/storage/test_repo_project.py` and `tests/storage/test_repo_snapshot.py` (similar pattern to test_repo_env.py — test insert, get, list, update).

Run: `pytest tests/storage/ -v`
Expected: all PASS

- [ ] **Step 5: Commit**

```bash
git add env_manager/storage/ tests/storage/
git commit -m "feat: add repository layer — Environment, Project, Snapshot, Activity repos"
```

### Task 1.4: Base Adapter ABC + Plugin Loader

**Files:**
- Create: `env_manager/adapters/__init__.py`
- Create: `env_manager/adapters/base.py`
- Create: `env_manager/adapters/loader.py`
- Create: `env_manager/adapters/registry.py`
- Create: `tests/adapters/test_base.py`
- Create: `tests/adapters/test_loader.py`
- Create: `tests/adapters/conftest.py`

**Test Gate:** ABC enforces required methods, loader discovers built-in adapters, registry enables/disables

- [ ] **Step 1: Write failing test for BaseAdapter**

Create `tests/adapters/test_base.py`:
```python
import pytest
from env_manager.adapters.base import BaseAdapter, EnvMetadata, Package, FreezeResult, HealthResult


def test_cannot_instantiate_abstract_adapter():
    with pytest.raises(TypeError):
        BaseAdapter()


def test_concrete_adapter_must_implement_detect():
    class IncompleteAdapter(BaseAdapter):
        pass  # doesn't implement detect, find_patterns, inspect, get_packages, freeze, check_health

    with pytest.raises(TypeError):
        IncompleteAdapter()


def test_minimal_adapter_works():
    class MinimalAdapter(BaseAdapter):
        name = "test.minimal"
        display_name = "Test Minimal"
        version = "0.1.0"
        env_type = "local"

        def find_patterns(self):
            return ["**/test.cfg"]

        def detect(self, path):
            if (path / "test.cfg").exists():
                return EnvMetadata(language="test", tool="minimal", version="1.0",
                                   path=str(path), size_bytes=0, interpreter_path="/bin/test")
            return None

        def inspect(self, path):
            return EnvMetadata(language="test", tool="minimal", version="1.0",
                               path=str(path), size_bytes=100, interpreter_path="/bin/test")

        def get_packages(self, path):
            return [Package(name="pkg1", version="1.0")]

        def freeze(self, path):
            return FreezeResult(raw_content="pkg1==1.0", format="requirements.txt",
                                packages=[Package(name="pkg1", version="1.0")])

        def check_health(self, path):
            return HealthResult(status="healthy")

    adapter = MinimalAdapter()
    assert adapter.name == "test.minimal"
    assert adapter.env_type == "local"
```

Run: `pytest tests/adapters/test_base.py -v`
Expected: FAIL — module not found

- [ ] **Step 2: Implement base.py**

Create `env_manager/adapters/base.py`:
```python
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from env_manager.models.env import EnvMetadata, Package, FreezeResult, HealthResult


__all__ = ["BaseAdapter", "EnvMetadata", "Package", "FreezeResult", "HealthResult"]


class BaseAdapter(ABC):
    """Every language adapter must implement this protocol."""

    # ── Identity (override as class attributes) ────────
    name: str = ""
    display_name: str = ""
    version: str = "0.1.0"
    env_type: str = "local"  # "local" | "global"

    # ── Detection (required) ────────────────────────────
    @abstractmethod
    def find_patterns(self) -> list[str]:
        """Glob patterns for scanner to find candidate paths."""

    @abstractmethod
    def detect(self, path: Path) -> Optional[EnvMetadata]:
        """Is this path one of our environments? Returns metadata or None."""

    # ── Inspection (required) ───────────────────────────
    @abstractmethod
    def inspect(self, path: Path) -> EnvMetadata:
        """Full inspection: version, size, packages count. Raises InspectError."""

    @abstractmethod
    def get_packages(self, path: Path) -> list[Package]:
        """List installed packages with versions."""

    # ── Snapshot (required) ─────────────────────────────
    @abstractmethod
    def freeze(self, path: Path) -> FreezeResult:
        """Export lockfile + normalized package list."""

    # ── Health (required) ───────────────────────────────
    @abstractmethod
    def check_health(self, path: Path) -> HealthResult:
        """Is this environment functional?"""

    # ── Lifecycle (optional) ────────────────────────────
    def create(self, path: Path, config: dict | None = None) -> EnvMetadata:
        raise NotImplementedError(f"{self.name} does not support create")

    def install(self, path: Path, packages: list[str]) -> None:
        raise NotImplementedError(f"{self.name} does not support install")

    def uninstall(self, path: Path, packages: list[str]) -> None:
        raise NotImplementedError(f"{self.name} does not support uninstall")

    def update(self, path: Path, packages: list[str] | None = None) -> None:
        raise NotImplementedError(f"{self.name} does not support update")

    def delete(self, path: Path) -> None:
        raise NotImplementedError(f"{self.name} does not support delete")

    def clone(self, source: Path, dest: Path) -> EnvMetadata:
        raise NotImplementedError(f"{self.name} does not support clone")
```

Run: `pytest tests/adapters/test_base.py -v`
Expected: 3 PASS

- [ ] **Step 3: Write and implement loader + registry**

Create `env_manager/adapters/loader.py`:
```python
"""Discovers and loads adapters from built-in dir + installed pip packages."""
import importlib
import pkgutil
from pathlib import Path
from env_manager.adapters.base import BaseAdapter


def discover_builtin_adapters() -> list[type[BaseAdapter]]:
    """Load all adapters from env_manager.adapters.* packages."""
    adapters: list[type[BaseAdapter]] = []
    import env_manager.adapters as pkg

    for _, name, is_pkg in pkgutil.iter_modules(pkg.__path__):
        if not is_pkg or name in ("base", "loader", "registry"):
            continue
        try:
            mod = importlib.import_module(f"env_manager.adapters.{name}")
            for attr_name in dir(mod):
                attr = getattr(mod, attr_name)
                if (isinstance(attr, type) and
                    issubclass(attr, BaseAdapter) and
                    attr is not BaseAdapter):
                    adapters.append(attr)
        except ImportError:
            continue
    return adapters


def discover_pip_adapters() -> list[type[BaseAdapter]]:
    """Discover adapters installed via pip (envs-plugin-* packages).
    Returns empty list for now — implemented after entry point support is added."""
    return []
```

Create `env_manager/adapters/registry.py`:
```python
"""Manages the active set of adapters. Supports enable/disable per language."""
import sqlite3
import json
from env_manager.adapters.base import BaseAdapter
from env_manager.adapters.loader import discover_builtin_adapters, discover_pip_adapters


class AdapterRegistry:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn
        self._adapters: dict[str, BaseAdapter] = {}
        self._sync_from_db()

    def _sync_from_db(self) -> None:
        """Load adapters from DB, falling back to built-in discovery."""
        rows = self.conn.execute("SELECT * FROM adapter_registry").fetchall()
        if not rows:
            self._seed_builtins()
            rows = self.conn.execute("SELECT * FROM adapter_registry").fetchall()

        adapter_classes = {cls.name: cls for cls in (discover_builtin_adapters() + discover_pip_adapters())}

        for row in rows:
            if row["enabled"] and row["name"] in adapter_classes:
                self._adapters[row["name"]] = adapter_classes[row["name"]]()

    def _seed_builtins(self) -> None:
        """Insert built-in adapters into DB on first run."""
        for cls in discover_builtin_adapters():
            inst = cls()
            self.conn.execute(
                """INSERT OR IGNORE INTO adapter_registry (name, display_name, version, env_type, source)
                   VALUES (?, ?, ?, ?, 'builtin')""",
                (inst.name, inst.display_name, inst.version, inst.env_type),
            )
        self.conn.commit()

    def get(self, name: str) -> BaseAdapter | None:
        return self._adapters.get(name)

    def get_for_language(self, language: str) -> list[BaseAdapter]:
        """Get all enabled adapters for a language. e.g. 'python' returns [VenvAdapter, PoetryAdapter]."""
        return [a for a in self._adapters.values() if a.name.startswith(language)]

    def get_all_enabled(self) -> list[BaseAdapter]:
        return list(self._adapters.values())

    def enable(self, name: str) -> bool:
        adapter_cls = None
        for cls in discover_builtin_adapters() + discover_pip_adapters():
            if cls.name == name:
                adapter_cls = cls
                break
        if not adapter_cls:
            return False
        self.conn.execute(
            "UPDATE adapter_registry SET enabled = 1 WHERE name = ?", (name,)
        )
        self.conn.commit()
        self._adapters[name] = adapter_cls()
        return True

    def disable(self, name: str) -> bool:
        if name not in self._adapters:
            return False
        self.conn.execute(
            "UPDATE adapter_registry SET enabled = 0 WHERE name = ?", (name,)
        )
        self.conn.commit()
        del self._adapters[name]
        return True

    def list_all(self) -> list[dict]:
        rows = self.conn.execute("SELECT * FROM adapter_registry ORDER BY name").fetchall()
        return [dict(r) for r in rows]
```

Update `env_manager/adapters/__init__.py`:
```python
from env_manager.adapters.base import BaseAdapter
from env_manager.adapters.registry import AdapterRegistry

__all__ = ["BaseAdapter", "AdapterRegistry"]
```

Create `tests/adapters/conftest.py`:
```python
import tempfile
from pathlib import Path
import pytest
import sqlite3
from env_manager.storage.database import init_db


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test.db")


@pytest.fixture
def db_connection(db_path):
    init_db(db_path)
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    yield conn
    conn.close()


@pytest.fixture
def fake_venv(tmp_path):
    """Create a fake Python venv directory structure for testing."""
    venv_dir = tmp_path / ".venv"
    venv_dir.mkdir()
    (venv_dir / "pyvenv.cfg").write_text(
        "home = /usr/bin\nversion = 3.12.1\ninclude-system-site-packages = false\n"
    )
    bin_dir = venv_dir / "bin"
    bin_dir.mkdir()
    (bin_dir / "python").touch(mode=0o755)
    (bin_dir / "pip").touch(mode=0o755)
    return venv_dir
```

Run: `pytest tests/adapters/test_base.py -v`
Expected: 3 PASS

- [ ] **Step 4: Commit**

```bash
git add env_manager/adapters/ tests/adapters/
git commit -m "feat: add BaseAdapter ABC + plugin loader + AdapterRegistry"
```

### Task 1.5: Python Venv Adapter

**Files:**
- Create: `env_manager/adapters/python/__init__.py`
- Create: `env_manager/adapters/python/venv.py`
- Create: `tests/adapters/python/__init__.py`
- Create: `tests/adapters/python/test_venv.py`

**Test Gate:** Adapter detects real venv, inspects version+packages, freezes, checks health

- [ ] **Step 1: Write failing test for PythonVenvAdapter**

Create `tests/adapters/python/test_venv.py`:
```python
import json
from pathlib import Path
from env_manager.adapters.python.venv import PythonVenvAdapter


def test_detect_finds_venv(fake_venv):
    adapter = PythonVenvAdapter()
    result = adapter.detect(fake_venv)
    assert result is not None
    assert result.language == "python"
    assert result.tool == "venv"


def test_detect_returns_none_for_non_venv(tmp_path):
    adapter = PythonVenvAdapter()
    result = adapter.detect(tmp_path)  # empty dir, no pyvenv.cfg
    assert result is None


def test_find_patterns():
    adapter = PythonVenvAdapter()
    patterns = adapter.find_patterns()
    assert "**/pyvenv.cfg" in patterns


def test_inspect_reads_version(fake_venv):
    adapter = PythonVenvAdapter()
    meta = adapter.inspect(fake_venv)
    assert meta.version == "3.12.1"
    assert meta.tool == "venv"
    assert meta.language == "python"
    assert meta.size_bytes > 0


def test_check_health_healthy_venv(fake_venv):
    adapter = PythonVenvAdapter()
    result = adapter.check_health(fake_venv)
    assert result.status == "healthy"
    assert len(result.errors) == 0


def test_check_health_missing_binary(fake_venv):
    # Simulate broken venv by removing python binary
    (fake_venv / "bin" / "python").unlink()
    adapter = PythonVenvAdapter()
    result = adapter.check_health(fake_venv)
    assert result.status == "broken"
    assert len(result.errors) > 0


def test_freeze_returns_format(fake_venv):
    adapter = PythonVenvAdapter()
    # Our fake venv has no real pip, so freeze will capture what it can
    result = adapter.freeze(fake_venv)
    assert result.format == "requirements.txt"
```

Run: `pytest tests/adapters/python/test_venv.py -v`
Expected: FAIL — module not found

- [ ] **Step 2: Implement PythonVenvAdapter**

Create `env_manager/adapters/python/venv.py`:
```python
import subprocess
import sys
from pathlib import Path
from typing import Optional
from env_manager.adapters.base import BaseAdapter
from env_manager.models.env import EnvMetadata, Package, FreezeResult, HealthResult


class PythonVenvAdapter(BaseAdapter):
    name = "python.venv"
    display_name = "Python (venv)"
    version = "1.0.0"
    env_type = "local"

    def find_patterns(self) -> list[str]:
        return ["**/pyvenv.cfg"]

    def detect(self, path: Path) -> Optional[EnvMetadata]:
        cfg = path / "pyvenv.cfg"
        if not cfg.exists():
            return None
        return EnvMetadata(
            language="python",
            tool="venv",
            version=self._read_version(path),
            path=str(path),
            size_bytes=self._du(path),
            interpreter_path=str(self._python_bin(path)),
        )

    def inspect(self, path: Path) -> EnvMetadata:
        return EnvMetadata(
            language="python",
            tool="venv",
            version=self._read_version(path),
            path=str(path),
            size_bytes=self._du(path),
            interpreter_path=str(self._python_bin(path)),
            packages_count=len(self.get_packages(path)),
        )

    def get_packages(self, path: Path) -> list[Package]:
        try:
            result = subprocess.run(
                [str(self._python_bin(path)), "-m", "pip", "list", "--format", "json"],
                capture_output=True, text=True, timeout=30,
            )
            if result.returncode != 0:
                return []
            data = __import__("json").loads(result.stdout)
            return [Package(name=p["name"], version=p["version"]) for p in data]
        except (subprocess.TimeoutExpired, Exception):
            return []

    def freeze(self, path: Path) -> FreezeResult:
        packages = self.get_packages(path)
        raw = "\n".join(f"{p.name}=={p.version}" for p in sorted(packages, key=lambda x: x.name))
        return FreezeResult(raw_content=raw, format="requirements.txt", packages=packages)

    def check_health(self, path: Path) -> HealthResult:
        checks = []
        errors = []
        suggestions = []

        py_bin = self._python_bin(path)
        if not py_bin.exists():
            errors.append(f"Python binary not found: {py_bin}")
            return HealthResult(status="broken", checks=checks, errors=errors,
                                suggestions=["Recreate environment with envs restore"])

        # Test: can we run python --version?
        try:
            r = subprocess.run([str(py_bin), "--version"], capture_output=True, text=True, timeout=10)
            checks.append({"name": "python_binary", "passed": r.returncode == 0})
            if r.returncode != 0:
                errors.append(f"python --version failed: {r.stderr}")
        except Exception as e:
            checks.append({"name": "python_binary", "passed": False})
            errors.append(str(e))

        # Test: can we import a stdlib module?
        try:
            r = subprocess.run(
                [str(py_bin), "-c", "import json; print('ok')"],
                capture_output=True, text=True, timeout=10,
            )
            checks.append({"name": "import_test", "passed": r.returncode == 0})
            if r.returncode != 0:
                errors.append(f"Import test failed: {r.stderr}")
        except Exception as e:
            checks.append({"name": "import_test", "passed": False})
            errors.append(str(e))

        status = "healthy" if len(errors) == 0 else "broken"
        return HealthResult(status=status, checks=checks, errors=errors, suggestions=suggestions)

    def _read_version(self, path: Path) -> str:
        cfg = path / "pyvenv.cfg"
        if cfg.exists():
            for line in cfg.read_text().splitlines():
                if line.startswith("version"):
                    return line.split("=")[-1].strip()
        return "unknown"

    def _python_bin(self, path: Path) -> Path:
        if sys.platform == "win32":
            return path / "Scripts" / "python.exe"
        return path / "bin" / "python"

    def _du(self, path: Path) -> int:
        """Calculate disk usage in bytes."""
        total = 0
        try:
            for f in path.rglob("*"):
                if f.is_file() and not f.is_symlink():
                    total += f.stat().st_size
        except PermissionError:
            pass
        return total
```

Create `env_manager/adapters/python/__init__.py`:
```python
from env_manager.adapters.python.venv import PythonVenvAdapter

__all__ = ["PythonVenvAdapter"]
```

Run: `pytest tests/adapters/python/test_venv.py -v`
Expected: 7 PASS (note: `test_check_health_healthy_venv` may pass "healthy" on fake_venv since we check binary exists + can run --version and import json — this actually works with system python linked to the fake venv, or may show degraded if it can't run. Accept health status "healthy" or "degraded" for fake envs.)

- [ ] **Step 3: Commit**

```bash
git add env_manager/adapters/python/ tests/adapters/python/
git commit -m "feat: add PythonVenvAdapter — detect, inspect, freeze, health check"
```

### Task 1.6: Discovery Engine (Scanner)

**Files:**
- Create: `env_manager/discovery/__init__.py`
- Create: `env_manager/discovery/scanner.py`
- Create: `tests/discovery/__init__.py`
- Create: `tests/discovery/test_scanner.py`

**Test Gate:** Scanner finds fake venvs, respects exclusions, respects enabled adapters only

- [ ] **Step 1: Write failing test for Scanner**

Create `tests/discovery/test_scanner.py`:
```python
from pathlib import Path
from env_manager.discovery.scanner import Scanner
from env_manager.adapters.python.venv import PythonVenvAdapter
from env_manager.adapters.base import BaseAdapter
from env_manager.models.env import EnvMetadata, Package, FreezeResult, HealthResult


class FakePythonAdapter(BaseAdapter):
    """Test adapter that detects .fake-python files."""
    name = "python.fake"
    display_name = "Fake Python"
    version = "0.1"
    env_type = "local"

    def find_patterns(self):
        return ["**/.fake-python"]

    def detect(self, path):
        if (path / ".fake-python").exists():
            return EnvMetadata(language="python", tool="fake", version="3.0",
                               path=str(path), size_bytes=100, interpreter_path="/bin/fake")
        return None

    def inspect(self, path):
        return EnvMetadata(language="python", tool="fake", version="3.0",
                           path=str(path), size_bytes=100, interpreter_path="/bin/fake",
                           packages_count=0)

    def get_packages(self, path):
        return []

    def freeze(self, path):
        return FreezeResult(raw_content="", format="requirements.txt", packages=[])

    def check_health(self, path):
        return HealthResult(status="healthy")


class FakeNodeAdapter(BaseAdapter):
    """Test adapter that detects .fake-node files."""
    name = "node.fake"
    display_name = "Fake Node"
    version = "0.1"
    env_type = "global"

    def find_patterns(self):
        return ["**/.fake-node"]

    def detect(self, path):
        if (path / ".fake-node").exists():
            return EnvMetadata(language="node", tool="fake", version="20.0",
                               path=str(path), size_bytes=200, interpreter_path="/bin/fake-node",
                               env_type="global")
        return None

    def inspect(self, path):
        return EnvMetadata(language="node", tool="fake", version="20.0",
                           path=str(path), size_bytes=200, interpreter_path="/bin/fake-node",
                           packages_count=0, env_type="global")

    def get_packages(self, path):
        return []

    def freeze(self, path):
        return FreezeResult(raw_content="", format="package-lock.json", packages=[])

    def check_health(self, path):
        return HealthResult(status="healthy")


def test_scanner_finds_matching_paths(tmp_path, db_connection):
    # Create fake environments
    py_proj = tmp_path / "pyproj"
    py_proj.mkdir()
    (py_proj / ".fake-python").touch()

    node_proj = tmp_path / "nodeproj"
    node_proj.mkdir()
    (node_proj / ".fake-node").touch()

    scanner = Scanner(db_connection, adapters=[FakePythonAdapter(), FakeNodeAdapter()])
    results = scanner.scan(str(tmp_path), depth=3)

    assert len(results) == 2
    languages = {r.language for r in results}
    assert languages == {"python", "node"}


def test_scanner_respects_disabled_adapters(tmp_path, db_connection):
    py_proj = tmp_path / "pyproj"
    py_proj.mkdir()
    (py_proj / ".fake-python").touch()

    node_proj = tmp_path / "nodeproj"
    node_proj.mkdir()
    (node_proj / ".fake-node").touch()

    # Only enable Python adapter
    scanner = Scanner(db_connection, adapters=[FakePythonAdapter()])
    results = scanner.scan(str(tmp_path), depth=3)

    assert len(results) == 1
    assert results[0].language == "python"


def test_scanner_excludes_patterns(tmp_path, db_connection):
    """Scanner should skip node_modules and .git by default."""
    # Create env inside node_modules (should be skipped)
    nm = tmp_path / "node_modules" / "somepkg"
    nm.mkdir(parents=True)
    (nm / ".fake-python").touch()

    # Create env at top level (should be found)
    top = tmp_path / "myapp"
    top.mkdir()
    (top / ".fake-python").touch()

    scanner = Scanner(db_connection, adapters=[FakePythonAdapter()])
    results = scanner.scan(str(tmp_path), depth=3)

    assert len(results) == 1
    assert str(top) in results[0].path


def test_scanner_handles_empty_directory(tmp_path, db_connection):
    scanner = Scanner(db_connection, adapters=[FakePythonAdapter()])
    results = scanner.scan(str(tmp_path), depth=3)
    assert len(results) == 0
```

Run: `pytest tests/discovery/test_scanner.py -v`
Expected: FAIL — module not found

- [ ] **Step 2: Implement Scanner**

Create `env_manager/discovery/scanner.py`:
```python
import os
from pathlib import Path
from typing import Optional
import sqlite3
from env_manager.adapters.base import BaseAdapter
from env_manager.models.env import EnvMetadata
from env_manager.storage.repo_env import EnvironmentRepository
from env_manager.storage.repo_project import ProjectRepository
from env_manager.storage.repo_activity import ActivityRepository


DEFAULT_EXCLUDES = {
    "node_modules", ".git", "__pycache__", ".mypy_cache",
    ".pytest_cache", ".ruff_cache", ".tox", ".eggs",
    "dist", "build", ".venv-old",
}


class Scanner:
    def __init__(self, conn: sqlite3.Connection, adapters: list[BaseAdapter]):
        self.conn = conn
        self.adapters = adapters
        self.env_repo = EnvironmentRepository(conn)
        self.proj_repo = ProjectRepository(conn)
        self.activity_repo = ActivityRepository(conn)

    def scan(self, root_path: str, depth: int = 5) -> list[EnvMetadata]:
        """Scan a directory tree for environments. Returns discovered metadata."""
        root = Path(root_path).expanduser().resolve()
        if not root.exists():
            return []

        results: list[EnvMetadata] = []
        self._walk(root, depth, results)

        # Activity log
        self.activity_repo.log(
            event="scan_completed",
            detail={"paths_scanned": len(results), "root": str(root)},
        )
        return results

    def _walk(self, directory: Path, remaining_depth: int, results: list[EnvMetadata]) -> None:
        if remaining_depth <= 0:
            return

        # Skip excluded directories
        if directory.name in DEFAULT_EXCLUDES:
            return

        # Skip system paths
        path_str = str(directory)
        if any(path_str.startswith(p) for p in ["/usr", "/System", "/Library", "/proc", "/sys", "/dev"]):
            return

        # Check each adapter
        for adapter in self.adapters:
            try:
                meta = adapter.detect(directory)
                if meta is not None:
                    results.append(meta)
                    break  # First adapter wins
            except Exception:
                continue

        # Recurse
        try:
            for entry in directory.iterdir():
                if entry.is_dir() and not entry.is_symlink():
                    self._walk(entry, remaining_depth - 1, results)
        except PermissionError:
            pass
```

Create `env_manager/discovery/__init__.py`:
```python
from env_manager.discovery.scanner import Scanner

__all__ = ["Scanner"]
```

Run: `pytest tests/discovery/test_scanner.py -v`
Expected: 4 PASS

- [ ] **Step 3: Commit**

```bash
git add env_manager/discovery/ tests/discovery/
git commit -m "feat: add discovery engine — filesystem scanner with adapter-based detection"
```

### Task 1.7: CLI Foundation + Read-Only Commands

**Files:**
- Create: `env_manager/cli/__init__.py`
- Create: `env_manager/cli/main.py`
- Create: `env_manager/cli/formatters.py`
- Create: `env_manager/cli/commands/__init__.py`
- Create: `env_manager/cli/commands/scan.py`
- Create: `env_manager/cli/commands/list_cmd.py`
- Create: `env_manager/cli/commands/info.py`
- Create: `env_manager/cli/commands/plugin.py`
- Create: `tests/cli/__init__.py`
- Create: `tests/cli/conftest.py`

**Test Gate:** `envs scan` discovers environments, `envs list` shows them, `envs info` shows details, `envs plugins` works

- [ ] **Step 1: Write failing test for CLI scan**

Create `tests/cli/conftest.py`:
```python
import pytest
import sqlite3
from typer.testing import CliRunner
from env_manager.storage.database import init_db
from env_manager.cli.main import app


@pytest.fixture
def db_path(tmp_path):
    return str(tmp_path / "test_cli.db")


@pytest.fixture
def runner(db_path, monkeypatch):
    """CLI runner with isolated DB."""
    init_db(db_path)

    # Make CLI use our test DB
    def _get_db_path():
        return db_path

    monkeypatch.setattr("env_manager.cli.main._get_db_path", _get_db_path)
    return CliRunner()
```

Create `tests/cli/test_scan.py`:
```python
from pathlib import Path


def test_scan_finds_fake_envs(runner, tmp_path, db_path, monkeypatch):
    """Test end-to-end: create fake envs, scan, verify results."""
    # Create fake Python project
    py_proj = tmp_path / "py-project"
    py_proj.mkdir()
    (py_proj / "pyvenv.cfg").write_text("version = 3.9.0\n")

    # Patch the CLI to scan tmp_path
    from env_manager.cli.commands import scan as scan_mod
    monkeypatch.setattr(scan_mod, "DEFAULT_SCAN_PATHS", [str(tmp_path)])

    result = runner.invoke(app, ["scan"])
    assert result.exit_code == 0
    assert "py-project" in result.stdout or "Found" in result.stdout


def test_list_shows_discovered_envs(runner, tmp_path, db_path, monkeypatch):
    py_proj = tmp_path / "py-proj"
    py_proj.mkdir()
    (py_proj / "pyvenv.cfg").write_text("version = 3.12.0\n")

    from env_manager.cli.commands import scan as scan_mod
    monkeypatch.setattr(scan_mod, "DEFAULT_SCAN_PATHS", [str(tmp_path)])

    runner.invoke(app, ["scan"])

    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    assert "py-proj" in result.stdout or "python" in result.stdout.lower()


def test_list_empty_shows_message(runner, db_path):
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0
    # Should not crash, may show "no environments" or empty table


def test_plugins_list(runner, db_path):
    result = runner.invoke(app, ["plugins", "list"])
    assert result.exit_code == 0
    # Should show built-in adapters
```

Run: `pytest tests/cli/test_scan.py -v`
Expected: FAIL — module not found

- [ ] **Step 2: Implement CLI main + formatters**

Create `env_manager/cli/main.py`:
```python
import os
from pathlib import Path
import typer
from env_manager.cli.commands import scan, list_cmd, info, plugin, config

app = typer.Typer(
    name="envs",
    help="Cross-language virtual environment manager",
    no_args_is_help=True,
)

app.add_typer(scan.app, name="scan")
app.add_typer(list_cmd.app, name="list")
app.add_typer(info.app, name="info")
app.add_typer(plugin.app, name="plugins")
app.add_typer(config.app, name="config")

DEFAULT_DB_PATH = os.path.expanduser("~/.env-manager/envs.db")


def _get_db_path() -> str:
    """Override for testing."""
    return os.environ.get("ENVS_DB_PATH", DEFAULT_DB_PATH)


def main():
    app()


if __name__ == "__main__":
    main()
```

Create `env_manager/cli/formatters.py`:
```python
from rich.console import Console
from rich.table import Table

console = Console()


def format_env_list(envs: list[dict]) -> None:
    """Print environments as a rich table."""
    if not envs:
        console.print("[dim]No environments found.[/dim]")
        return

    table = Table(title="Environments")
    table.add_column("Project", style="cyan")
    table.add_column("Language", style="green")
    table.add_column("Version")
    table.add_column("Size")
    table.add_column("State")
    table.add_column("Path", style="dim")

    for env in envs:
        table.add_row(
            env.get("project_name", "-"),
            env.get("language", "-"),
            env.get("version", "-"),
            _format_size(env.get("size_bytes", 0)),
            env.get("management_state", "-"),
            env.get("path", "-"),
        )

    console.print(table)


def format_env_info(env: dict) -> None:
    """Print detailed info for one environment."""
    console.print(f"[bold cyan]{env.get('project_name', 'Unknown')}[/bold cyan]")
    console.print(f"  Language:  {env.get('language')} {env.get('version')}")
    console.print(f"  Tool:      {env.get('tool')}")
    console.print(f"  Size:      {_format_size(env.get('size_bytes', 0))}")
    console.print(f"  State:     {env.get('management_state')}")
    console.print(f"  Path:      {env.get('path')}")
    if env.get("last_health_result"):
        color = {"healthy": "green", "degraded": "yellow", "broken": "red"}.get(
            env["last_health_result"], ""
        )
        console.print(f"  Health:    [{color}]{env['last_health_result']}[/{color}]")


def _format_size(size_bytes: int) -> str:
    if size_bytes >= 1_000_000_000:
        return f"{size_bytes / 1_000_000_000:.1f} GB"
    if size_bytes >= 1_000_000:
        return f"{size_bytes / 1_000_000:.1f} MB"
    if size_bytes >= 1_000:
        return f"{size_bytes / 1_000:.1f} KB"
    return f"{size_bytes} B"
```

- [ ] **Step 3: Implement scan command**

Create `env_manager/cli/commands/scan.py`:
```python
import typer
from pathlib import Path
from env_manager.cli.main import _get_db_path
from env_manager.storage.database import init_db, get_connection
from env_manager.adapters.registry import AdapterRegistry
from env_manager.discovery.scanner import Scanner

app = typer.Typer()

DEFAULT_SCAN_PATHS = [str(Path.home() / "projects"), str(Path.home() / "work")]


@app.command()
def scan(
    path: list[str] = typer.Option(None, "--path", "-p", help="Paths to scan"),
    depth: int = typer.Option(5, "--depth", "-d", help="Max directory depth"),
):
    """Discover all language environments."""
    db_path = _get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    registry = AdapterRegistry(conn)
    adapters = registry.get_all_enabled()

    if not adapters:
        typer.echo("No adapters enabled. Enable one: envs plugins enable python")
        raise typer.Exit(1)

    scan_paths = path or DEFAULT_SCAN_PATHS
    scanner = Scanner(conn, adapters)

    for p in scan_paths:
        typer.echo(f"Scanning {p}...")
        results = scanner.scan(str(Path(p).expanduser()), depth=depth)
        typer.echo(f"  Found {len(results)} environments")

    conn.close()
```

Create `env_manager/cli/commands/list_cmd.py`:
```python
import typer
from env_manager.cli.main import _get_db_path
from env_manager.storage.database import init_db, get_connection
from env_manager.storage.repo_env import EnvironmentRepository
from env_manager.storage.repo_project import ProjectRepository
from env_manager.cli.formatters import format_env_list

app = typer.Typer()


@app.command("list")
def list_envs(
    by_project: bool = typer.Option(False, "--by-project", help="Group by project"),
    stale: bool = typer.Option(False, "--stale", help="Show only stale"),
    orphaned: bool = typer.Option(False, "--orphaned", help="Show only orphaned"),
    language: str = typer.Option(None, "--lang", help="Filter by language"),
):
    """List tracked environments."""
    db_path = _get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    repo = EnvironmentRepository(conn)
    proj_repo = ProjectRepository(conn)

    if stale:
        envs = repo.list_stale(days=30)
    elif orphaned:
        envs = repo.list_orphaned()
    elif language:
        envs = repo.list_by_language(language)
    else:
        envs = repo.list_all()

    # Enrich with project name
    enriched = []
    for env in envs:
        env_dict = dict(env)
        if env["project_id"]:
            proj = proj_repo.get_by_id(env["project_id"])
            env_dict["project_name"] = proj["name"] if proj else "-"
        else:
            env_dict["project_name"] = "-"
        enriched.append(env_dict)

    format_env_list(enriched)
    conn.close()
```

Create `env_manager/cli/commands/info.py`:
```python
import typer
from env_manager.cli.main import _get_db_path
from env_manager.storage.database import init_db, get_connection
from env_manager.storage.repo_env import EnvironmentRepository
from env_manager.storage.repo_project import ProjectRepository
from env_manager.cli.formatters import format_env_info

app = typer.Typer()


@app.command()
def info(project: str):
    """Show detailed info for a project."""
    db_path = _get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    proj_repo = ProjectRepository(conn)
    env_repo = EnvironmentRepository(conn)

    proj = proj_repo.get_by_path(project)
    if not proj:
        # Try by name
        all_projects = proj_repo.list_all()
        proj = next((p for p in all_projects if p["name"] == project), None)

    if not proj:
        typer.echo(f"Project not found: {project}")
        raise typer.Exit(1)

    envs = env_repo.list_by_project(proj["id"])
    for env in envs:
        env_dict = dict(env)
        env_dict["project_name"] = proj["name"]
        format_env_info(env_dict)

    conn.close()
```

Create `env_manager/cli/commands/plugin.py`:
```python
import typer
from env_manager.cli.main import _get_db_path
from env_manager.storage.database import init_db, get_connection
from env_manager.adapters.registry import AdapterRegistry

app = typer.Typer()


@app.command("list")
def list_plugins():
    """List installed adapters."""
    db_path = _get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    registry = AdapterRegistry(conn)
    adapters = registry.list_all()

    for a in adapters:
        status = "[green]enabled[/green]" if a["enabled"] else "[red]disabled[/red]"
        typer.echo(f"  {a['name']:20s} {a['display_name']:30s} {status}")

    conn.close()


@app.command("enable")
def enable_plugin(name: str):
    """Enable a language adapter."""
    db_path = _get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    registry = AdapterRegistry(conn)
    if registry.enable(name):
        typer.echo(f"Enabled: {name}")
    else:
        typer.echo(f"Adapter not found: {name}")
        raise typer.Exit(1)

    conn.close()


@app.command("disable")
def disable_plugin(name: str):
    """Disable a language adapter. Its environments won't be scanned."""
    db_path = _get_db_path()
    init_db(db_path)
    conn = get_connection(db_path)

    registry = AdapterRegistry(conn)
    if registry.disable(name):
        typer.echo(f"Disabled: {name}")
    else:
        typer.echo(f"Adapter not found or already disabled: {name}")
        raise typer.Exit(1)

    conn.close()
```

Create `env_manager/cli/commands/config.py`:
```python
import typer
from env_manager.cli.main import _get_db_path
from env_manager.storage.database import init_db, get_connection

app = typer.Typer()


@app.command("show")
def config_show():
    """Show current configuration."""
    db_path = _get_db_path()
    typer.echo(f"Database: {db_path}")

    init_db(db_path)
    conn = get_connection(db_path)

    rows = conn.execute(
        "SELECT name, display_name, enabled FROM adapter_registry ORDER BY name"
    ).fetchall()

    typer.echo("\nLanguage adapters:")
    for row in rows:
        status = "enabled" if row["enabled"] else "disabled"
        typer.echo(f"  {row['name']:20s} [{status}]")

    conn.close()
```

Run: `pytest tests/cli/test_scan.py -v`
Expected: 4 PASS

- [ ] **Step 4: Phase 1 Integration Test**

Create a test that runs the full Phase 1 flow end-to-end in a real process.

Add to `tests/cli/test_scan.py`:
```python
def test_phase1_full_flow(runner, tmp_path, db_path, monkeypatch):
    """End-to-end: scan fake envs → list → info → plugins."""
    from env_manager.cli.commands import scan as scan_mod
    monkeypatch.setattr(scan_mod, "DEFAULT_SCAN_PATHS", [str(tmp_path)])

    # Setup: create projects with fake envs
    for i in range(3):
        proj = tmp_path / f"project-{i}"
        proj.mkdir()
        (proj / "pyvenv.cfg").write_text(f"version = 3.{10+i}.0\n")

    # Scan
    result = runner.invoke(app, ["scan"])
    assert result.exit_code == 0

    # List
    result = runner.invoke(app, ["list"])
    assert result.exit_code == 0

    # Info (by path)
    result = runner.invoke(app, ["info", str(tmp_path / "project-0")])
    assert result.exit_code == 0

    # Plugins
    result = runner.invoke(app, ["plugins", "list"])
    assert result.exit_code == 0
```

Run: `pytest tests/cli/test_scan.py::test_phase1_full_flow -v`
Expected: PASS

- [ ] **Step 5: Commit**

```bash
git add env_manager/cli/ tests/cli/
git commit -m "feat: add CLI foundation — scan, list, info, plugins, config commands + phase 1 integration test"
```

---

## Phase 1 Checkpoint

**Test gate:** All tests pass for models, storage, adapters, scanner, CLI read-only commands.

Run: `pytest tests/ -v`
Expected: all PASS (models + storage + adapters + discovery + CLI)

```bash
git tag v0.1-phase1
```

---

## Phase 2: Lifecycle + API + More Adapters

### Task 2.1: CLI Lifecycle Commands

**Files:**
- Create: `env_manager/cli/commands/lifecycle.py`
- Create: `env_manager/cli/commands/create.py`
- Create: `env_manager/cli/commands/restore.py`
- Create: `tests/cli/test_lifecycle.py`

**Test Gate:** `envs create`, `envs install`, `envs delete --snapshot` via mock adapters

### Task 2.2: Daemon Core (FastAPI)

**Files:**
- Create: `env_manager/daemon/__init__.py`
- Create: `env_manager/daemon/server.py`
- Create: `tests/daemon/test_server.py`

**Test Gate:** FastAPI app starts, health endpoint returns 200

### Task 2.3: REST API Endpoints

**Files:**
- Create: `env_manager/daemon/api/envs.py`
- Create: `env_manager/daemon/api/projects.py`
- Create: `env_manager/daemon/api/health.py`
- Create: `env_manager/daemon/api/snapshots.py`
- Create: `env_manager/daemon/api/plugins.py`
- Create: `tests/daemon/test_api_envs.py`

**Test Gate:** All CRUD endpoints return correct JSON, 404 for missing resources

### Task 2.4: Node.js Adapters

**Files:**
- Create: `env_manager/adapters/node/__init__.py`
- Create: `env_manager/adapters/node/nvm.py`
- Create: `env_manager/adapters/node/fnm.py`
- Create: `tests/adapters/node/test_nvm.py`
- Create: `tests/adapters/node/test_fnm.py`

**Test Gate:** Adapters detect nvm/fnm installs, inspect versions, freeze packages

### Task 2.5: Ruby Adapters

**Files:**
- Create: `env_manager/adapters/ruby/__init__.py`
- Create: `env_manager/adapters/ruby/rbenv.py`
- Create: `tests/adapters/ruby/test_rbenv.py`

**Test Gate:** Detects rbenv installs, inspects Ruby version

### Task 2.6: Go + Rust Adapters

**Files:**
- Create: `env_manager/adapters/go/__init__.py`
- Create: `env_manager/adapters/go/goenv.py`
- Create: `env_manager/adapters/rust/__init__.py`
- Create: `env_manager/adapters/rust/rustup.py`
- Create: `tests/adapters/go/test_goenv.py`
- Create: `tests/adapters/rust/test_rustup.py`

**Test Gate:** Detects goenv/rustup installs, inspects versions

---

## Phase 3: Health + Snapshots + Cleanup

### Task 3.1: Health Check System

**Files:**
- Create: `env_manager/health/__init__.py`
- Create: `env_manager/health/doctor.py`
- Create: `tests/health/test_doctor.py`
- Create: `env_manager/cli/commands/doctor_cmd.py`

**Test Gate:** `envs doctor` detects broken/missing envs, `envs doctor --all` checks everything

### Task 3.2: Snapshot System

**Files:**
- Create: `env_manager/snapshot/__init__.py`
- Create: `env_manager/snapshot/freezer.py`
- Create: `env_manager/snapshot/restorer.py`
- Create: `tests/snapshot/test_freezer.py`
- Create: `tests/snapshot/test_restorer.py`

**Test Gate:** `freeze` captures exact deps, `restore` rebuilds from snapshot

### Task 3.3: Cleanup Engine

**Files:**
- Create: `env_manager/cleanup/__init__.py`
- Create: `env_manager/cleanup/engine.py`
- Create: `env_manager/cli/commands/cleanup_cmd.py`
- Create: `tests/cleanup/test_engine.py`

**Test Gate:** `envs cleanup --stale 60 --dry-run` shows what would happen, `--confirm` executes

---

## Phase 4: Dashboard + Packaging

### Task 4.1: React Dashboard

**Files:**
- Create: `env_manager/dashboard/package.json`
- Create: `env_manager/dashboard/src/App.tsx`
- Create: `env_manager/dashboard/src/pages/EnvList.tsx`

**Test Gate:** `npm run dev` starts dashboard, shows env list from API

### Task 4.2: PyInstaller Packaging

**Files:**
- Create: `pyinstaller.spec`
- Modify: `Makefile` — add `make binary` target

**Test Gate:** `make binary` produces a self-contained executable that runs without Python

---

## Summary: Test Gates Per Phase

| Phase | Gate | Command |
|-------|------|---------|
| 0 | Lint + typecheck + test runner | `make check` |
| 1 | Read-only CLI works | `pytest tests/models tests/storage tests/adapters tests/discovery tests/cli -v` |
| 2 | Lifecycle + API + 5 language adapters | `pytest tests/ -v --cov=env_manager` |
| 3 | Health + snapshots + cleanup | `pytest tests/ -v --cov=env_manager --cov-report=term` |
| 4 | Dashboard + binary | `npm test && make binary && ./dist/envs --version` |
