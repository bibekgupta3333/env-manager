const TABS = [
  { key: 'dashboard', label: 'Dashboard' },
  { key: 'environments', label: 'Environments' },
  { key: 'doctor', label: 'Doctor' },
  { key: 'snapshots', label: 'Snapshots' },
  { key: 'cleanup', label: 'Cleanup' },
];

export default function Sidebar({ activeTab, onTabChange, wsStatus }) {
  return (
    <aside className="sidebar">
      <div className="sidebar-title">env-manager</div>
      <nav>
        {TABS.map((tab) => (
          <button
            key={tab.key}
            className={activeTab === tab.key ? 'active' : ''}
            onClick={() => onTabChange(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </nav>
      <div className={`sidebar-status ${wsStatus}`}>
        {wsStatus === 'connected' ? 'live' : wsStatus === 'connecting' ? 'connecting...' : 'offline'}
      </div>
    </aside>
  );
}
