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
    project_id INTEGER REFERENCES projects(id) ON DELETE CASCADE,
    adapter TEXT NOT NULL,
    env_type TEXT NOT NULL,
    path TEXT NOT NULL UNIQUE,
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
CREATE INDEX IF NOT EXISTS idx_activity_event ON activity_log(event);

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

CREATE TABLE IF NOT EXISTS _schema_version (
    version INTEGER PRIMARY KEY,
    applied_at TEXT NOT NULL DEFAULT (datetime('now'))
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
