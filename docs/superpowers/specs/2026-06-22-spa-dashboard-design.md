# SPA Dashboard — UX Design

## User Journey

```
FIRST VISIT                    DAILY USE                     CLEANUP SESSION
────────────                   ─────────                     ───────────────
"0 environments"               "47 envs, 32 GB"             "12 stale, 8.4 GB"
[Scan Now] button              [Filter: python ▾]           [Select all ▢]
    │                              │                            │
    ▼                              ▼                            ▼
Scanning progress bar          Env table loads              Checkboxes appear
  47 found!                    Click row → detail           Preview: "Free 8.4 GB"
    │                              │                            │
    ▼                              ▼                            ▼
Table populates                Packages tab                 [Clean Up] → confirm
Summary cards update           Health badge                 Done! Freed 8.4 GB
```

## Layout

```
┌──────────────────────────────────────────────────────────────┐
│  env-manager  [Sidebar toggle]              ○ live  ☰ menu   │
├──────────┬───────────────────────────────────────────────────┤
│          │                                                   │
│ Dashboard│  ┌──────┐ ┌──────┐ ┌──────┐ ┌──────┐           │
│ 📊       │  │  47  │ │  38  │ │  3   │ │32 GB │           │
│          │  │ envs │ │healthy│ │broken│ │ total│           │
│ Envs     │  └──────┘ └──────┘ └──────┘ └──────┘           │
│ 📦       │                                                   │
│          │  [Search...] [Python ▾] [Sort: Size ▾] [Scan]   │
│ Doctor   │                                                   │
│ 🩺       │  ┌─────────────────────────────────────────────┐ │
│          │  │ myapp-api     python 3.12   520 MB  healthy  │ │
│ Cleanup  │  │ frontend      node   20     890 MB  healthy  │ │
│ 🧹       │  │ old-scraper   python 3.8    980 MB  broken ✗ │ │
│          │  │ data-pipeline python 3.11  2.1 GB  degraded ⚠│ │
│ Snapshots│  └─────────────────────────────────────────────┘ │
│ 💾       │                                                   │
│          │  Detail panel (slides in from right):            │
│ Settings │  ┌─────────────────────────────────────────┐     │
│ ⚙        │  │ myapp-api  ★ pin                        │     │
│          │  │ python 3.12  |  venv  |  520 MB         │     │
└──────────┘  │ Path: ~/projects/myapp-api/.venv         │     │
              │ ─────────────────────────────────────── │     │
              │ [Packages] [Health] [Snapshots] [Actions]│     │
              │                                          │     │
              │ requests==2.31.0    flask==3.0.0         │     │
              │ numpy==1.26.0       pandas==2.1.0        │     │
              │ ...                                      │     │
              └──────────────────────────────────────────┘     │
└──────────────────────────────────────────────────────────────┘
```

## Component Tree

```
App
├── Sidebar
│   ├── Dashboard (summary cards)
│   ├── Environments (table + detail)
│   ├── Doctor (health check runner)
│   ├── Cleanup (stale/orphaned manager)
│   ├── Snapshots (list + restore)
│   └── Settings (plugins, config)
│
├── Header
│   ├── ConnectionStatus (live/offline dot)
│   └── ScanButton (triggers background scan)
│
└── Main Content Area
    ├── SummaryCards (env count, healthy, broken, size)
    ├── EnvTable (searchable, filterable, sortable)
    │   └── EnvRow (click → open detail)
    ├── DetailPanel (slide-in from right)
    │   ├── PackagesTab
    │   ├── HealthTab
    │   ├── SnapshotsTab
    │   └── ActionsTab (install, remove, restore, pin)
    ├── DoctorView (run checks, show results)
    ├── CleanupView (candidate list, preview, confirm)
    ├── SnapshotView (list, restore button)
    └── SettingsView (plugins toggle, scan paths)
```

## Key Interactions

| User wants to | How |
|---------------|-----|
| See what envs exist | Dashboard → scroll/search table |
| Find broken envs | Doctor tab → run check → red rows |
| Free disk space | Cleanup tab → select candidates → preview → confirm |
| Restore old project | Snapshots tab → find → click Restore |
| Create new env | Sidebar → + New Env button → form |
| Install packages | Click env → Actions tab → type package → Install |
| See what changed | Click env → Snapshots tab → compare versions |
| Pin important project | Click env → ★ button |

## Tech Stack

- React 18 + Vite (fast dev, tree-shaken prod build)
- No router needed (single page with tabs)
- Fetch API for REST calls to daemon
- WebSocket for live status updates
- CSS modules or Tailwind for styling
- Build output: static files served by FastAPI
