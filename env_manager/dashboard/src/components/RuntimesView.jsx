import { useState, useEffect } from 'react';
import { fetchEnvs } from '../api';
import StatusBadge from './StatusBadge';
import SizeBar from './SizeBar';
import { createToast } from './Toast';

const LANG_STYLES = {
  python: { bg: 'var(--violet-3)', color: 'var(--violet-9)', label: 'py' },
  node: { bg: 'var(--green-3)', color: 'var(--green-9)', label: 'js' },
  ruby: { bg: 'var(--red-3)', color: 'var(--red-9)', label: 'rb' },
  go: { bg: 'var(--amber-3)', color: 'var(--amber-9)', label: 'go' },
  rust: { bg: 'var(--amber-3)', color: 'var(--amber-9)', label: 'rs' },
};

const DEFAULT_LANG = { bg: 'var(--gray-5)', color: 'var(--gray-10)', label: '?' };

function getLangStyle(lang) {
  return LANG_STYLES[lang?.toLowerCase()] || DEFAULT_LANG;
}

const RefreshIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="23 4 23 10 17 10"/>
    <polyline points="1 20 1 14 7 14"/>
    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
  </svg>
);

const STATE_LABELS = {
  active: 'Active',
  stale: 'Stale',
  removed: 'Removed',
  ignored: 'Ignored',
  archived: 'Archived',
};

export default function RuntimesView() {
  const [runtimes, setRuntimes] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    fetchEnvs(null, null, 'runtime')
      .then((data) => setRuntimes(data.environments || []))
      .catch(() => createToast('Failed to load runtimes', 'error'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  if (loading) {
    return (
      <div>
        <div style={{ display: 'flex', gap: 'var(--space-2)', marginBottom: 'var(--space-5)' }}>
          <div className="skeleton" style={{ height: '34px', width: '100px', borderRadius: 'var(--radius-sm)' }} />
        </div>
        <div style={{ display: 'flex', gap: 'var(--space-4)', flexWrap: 'wrap' }}>
          {[...Array(6)].map((_, i) => (
            <div key={i} className="skeleton" style={{ height: '180px', width: '320px', borderRadius: 'var(--radius-md)' }} />
          ))}
        </div>
      </div>
    );
  }

  return (
    <div>
      <div className="toolbar">
        <button className="btn" onClick={load} title="Refresh">
          <RefreshIcon />
          Refresh
        </button>
      </div>

      {runtimes.length === 0 ? (
        <div style={{ padding: 'var(--space-10) var(--space-6)', textAlign: 'center' }}>
          <p style={{ color: 'var(--gray-9)', fontSize: 'var(--text-sm)', marginBottom: 'var(--space-3)' }}>
            No virtual environments discovered.
          </p>
          <p style={{ color: 'var(--gray-8)', fontSize: 'var(--text-xs)' }}>
            Run a scan to discover installed language runtimes.
          </p>
        </div>
      ) : (
        <div style={{ display: 'flex', gap: 'var(--space-4)', flexWrap: 'wrap' }}>
          {runtimes.map((env) => {
            const langStyle = getLangStyle(env.language);
            const status = env.last_health_result || 'unchecked';
            const mgmtState = env.management_state || 'unknown';
            const discovery = env.discovery_status || 'unknown';
            return (
              <div
                key={env.id}
                className="stat-card"
                style={{ flex: '1 1 300px', minWidth: '280px', maxWidth: '380px' }}
              >
                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-3)' }}>
                  <div
                    className="stat-card-icon"
                    style={{
                      background: langStyle.bg,
                      color: langStyle.color,
                      fontSize: 'var(--text-xs)',
                      fontWeight: 700,
                      textTransform: 'uppercase',
                      flexShrink: 0,
                    }}
                  >
                    {langStyle.label}
                  </div>
                  <div style={{ minWidth: 0 }}>
                    <div style={{ fontSize: 'var(--text-base)', fontWeight: 600, color: 'var(--gray-12)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                      {env.language || 'unknown'}{env.tool ? ` (${env.tool})` : ''} {env.version || ''}
                    </div>
                    <div className="path-cell" style={{ fontSize: 'var(--text-xs)', marginTop: '2px', maxWidth: '220px' }} title={env.path || ''}>
                      {env.path || '-'}
                    </div>
                  </div>
                </div>

                <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-4)', marginBottom: 'var(--space-3)', flexWrap: 'wrap' }}>
                  <SizeBar bytes={env.size_bytes} />
                  <StatusBadge status={status} size="sm" />
                </div>

                <div style={{ display: 'flex', gap: 'var(--space-2)', flexWrap: 'wrap' }}>
                  <span style={{
                    fontSize: 'var(--text-xs)',
                    padding: '2px 8px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'var(--gray-4)',
                    color: 'var(--gray-10)',
                    fontWeight: 500,
                  }}>
                    {mgmtState}
                  </span>
                  <span style={{
                    fontSize: 'var(--text-xs)',
                    padding: '2px 8px',
                    borderRadius: 'var(--radius-sm)',
                    background: 'var(--gray-4)',
                    color: 'var(--gray-10)',
                    fontWeight: 500,
                  }}>
                    {discovery}
                  </span>
                </div>
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
