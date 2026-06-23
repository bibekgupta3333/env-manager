const GridIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="7" height="7" rx="1"/>
    <rect x="14" y="3" width="7" height="7" rx="1"/>
    <rect x="3" y="14" width="7" height="7" rx="1"/>
    <rect x="14" y="14" width="7" height="7" rx="1"/>
  </svg>
);

const BoxIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
    <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
    <line x1="12" y1="22.08" x2="12" y2="12"/>
  </svg>
);

const HeartIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
  </svg>
);

const ArchiveIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="21 8 21 21 3 21 3 8"/>
    <rect x="1" y="3" width="22" height="5"/>
    <line x1="10" y1="12" x2="14" y2="12"/>
  </svg>
);

const BroomIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21.5 2.5l-7 7-3-3 7-7"/>
    <path d="M14.5 9.5l-12 12"/>
    <path d="M2.5 21.5l5-5"/>
    <path d="M3 17l2 2"/>
    <line x1="9" y1="15" x2="15" y2="9"/>
  </svg>
);

const LogoIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polygon points="12 2 22 8.5 22 15.5 12 22 2 15.5 2 8.5 12 2"/>
    <line x1="12" y1="22" x2="12" y2="15.5"/>
    <polyline points="22 8.5 12 15.5 2 8.5"/>
  </svg>
);

const CollapseIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="3" y="3" width="18" height="18" rx="2" ry="2"/>
    <line x1="9" y1="3" x2="9" y2="21"/>
    <line x1="3" y1="9" x2="21" y2="9"/>
  </svg>
);

const TABS = [
  { key: 'dashboard', label: 'Dashboard', Icon: GridIcon },
  { key: 'environments', label: 'Environments', Icon: BoxIcon },
  { key: 'doctor', label: 'Doctor', Icon: HeartIcon },
  { key: 'snapshots', label: 'Snapshots', Icon: ArchiveIcon },
  { key: 'cleanup', label: 'Cleanup', Icon: BroomIcon },
];

const STATUS_LABELS = {
  connected: 'Connected',
  connecting: 'Connecting...',
  disconnected: 'Offline',
};

export default function Sidebar({ activeTab, onTabChange, wsStatus, collapsed, onToggle }) {
  return (
    <aside className={`sidebar${collapsed ? ' collapsed' : ''}`}>
      <div className="sidebar-brand">
        <span className="sidebar-logo"><LogoIcon /></span>
        <span className="sidebar-logo-text">env-manager</span>
        <button className="sidebar-toggle" onClick={onToggle} title={collapsed ? 'Expand' : 'Collapse'}>
          <CollapseIcon />
        </button>
      </div>
      <nav>
        {TABS.map(({ key, label, Icon }) => (
          <button
            key={key}
            className={activeTab === key ? 'active' : ''}
            onClick={() => onTabChange(key)}
            title={label}
          >
            <Icon />
            <span className="nav-label">{label}</span>
          </button>
        ))}
      </nav>
      <div className="sidebar-footer">
        <div className="sidebar-status">
          <span className={`status-dot ${wsStatus}`} />
          <span className="sidebar-status-text">{STATUS_LABELS[wsStatus] || wsStatus}</span>
        </div>
        <div className="sidebar-version">v1.0.0</div>
      </div>
    </aside>
  );
}
