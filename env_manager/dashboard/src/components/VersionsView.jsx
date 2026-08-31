import { useState, useEffect } from 'react';
import { fetchConfig } from '../api';
import { createToast } from './Toast';

const RefreshIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="23 4 23 10 17 10"/>
    <polyline points="1 20 1 14 7 14"/>
    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
  </svg>
);

const LANGUAGE_LABELS = {
  python: 'Python',
  node: 'Node.js',
  ruby: 'Ruby',
  go: 'Go',
  rust: 'Rust',
};

const LANGUAGE_COLORS = {
  python: 'var(--blue-9, #3b82f6)',
  node: 'var(--green-9, #42d392)',
  ruby: 'var(--red-9, #ff4d6a)',
  go: 'var(--amber-9, #ffb224)',
  rust: 'var(--violet-9, #7c6ff7)',
};

function groupByLanguage(adapters) {
  const groups = {};
  for (const a of adapters) {
    const name = a.name || a.id || '';
    const parts = name.split('.');
    const lang = parts.length > 1 ? parts[0] : 'other';
    if (!groups[lang]) groups[lang] = [];
    groups[lang].push(a);
  }
  return groups;
}

export default function VersionsView() {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    fetchConfig()
      .then((data) => setConfig(data))
      .catch(() => createToast('Failed to load versions', 'error'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const adapters = config?.adapter_registry || config?.adapters || [];
  const groups = groupByLanguage(adapters);
  const versionManagers = config?.version_managers || config?.managers || [];

  return (
    <div>
      <div className="toolbar">
        <button className="btn" onClick={load} disabled={loading}>
          <RefreshIcon /> Refresh
        </button>
      </div>

      {loading ? (
        <div>
          {[...Array(4)].map((_, i) => (
            <div key={i} className="skeleton" style={{ height: '80px', marginBottom: 'var(--space-3)', borderRadius: 'var(--radius-md)' }} />
          ))}
        </div>
      ) : (
        <>
          {versionManagers.length > 0 && (
            <div style={{
              background: 'var(--gray-2)',
              border: '1px solid var(--gray-5)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-4) var(--space-5)',
              marginBottom: 'var(--space-5)',
            }}>
              <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--gray-12)', marginBottom: 'var(--space-3)' }}>
                Version Managers Installed
              </h3>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
                {versionManagers.map((mgr) => {
                  const name = typeof mgr === 'string' ? mgr : mgr.name;
                  const version = typeof mgr === 'string' ? '' : mgr.version || '';
                  return (
                    <span key={name} style={{
                      background: 'var(--violet-3)',
                      color: 'var(--violet-11)',
                      padding: '4px 10px',
                      borderRadius: 'var(--radius-sm)',
                      fontSize: 'var(--text-xs)',
                      fontFamily: 'var(--font-mono)',
                    }}>
                      {name}{version ? ` ${version}` : ''}
                    </span>
                  );
                })}
              </div>
            </div>
          )}

          {Object.keys(groups).length === 0 ? (
            <p style={{ color: 'var(--gray-9)', textAlign: 'center', padding: 'var(--space-12) 0', fontSize: 'var(--text-sm)' }}>
              No version data available.
            </p>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-4)' }}>
              {Object.entries(groups).map(([lang, items]) => {
                const label = LANGUAGE_LABELS[lang] || lang.charAt(0).toUpperCase() + lang.slice(1);
                const color = LANGUAGE_COLORS[lang] || 'var(--gray-9)';
                const enabled = items.filter((a) => a.enabled !== false);
                const disabled = items.filter((a) => a.enabled === false);
                return (
                  <div key={lang} style={{
                    background: 'var(--gray-2)',
                    border: '1px solid var(--gray-5)',
                    borderRadius: 'var(--radius-md)',
                    padding: 'var(--space-5)',
                  }}>
                    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-3)', marginBottom: 'var(--space-3)' }}>
                      <span style={{
                        width: '10px',
                        height: '10px',
                        borderRadius: '50%',
                        background: color,
                        display: 'inline-block',
                      }} />
                      <h3 style={{ fontSize: 'var(--text-base)', fontWeight: 600, color: 'var(--gray-12)' }}>{label}</h3>
                      <span style={{ fontSize: 'var(--text-xs)', color: 'var(--gray-9)' }}>
                        {enabled.length} adapter{enabled.length !== 1 ? 's' : ''} active
                      </span>
                    </div>
                    <div style={{ display: 'flex', flexWrap: 'wrap', gap: 'var(--space-2)' }}>
                      {items.map((item) => {
                        const name = item.name || item.id || '';
                        const displayName = item.display_name || item.label || name;
                        const isEnabled = item.enabled !== false;
                        const ver = item.version || item.installed_version || '';
                        return (
                          <div key={name} style={{
                            background: isEnabled ? 'var(--gray-3)' : 'var(--gray-4)',
                            border: '1px solid var(--gray-5)',
                            borderRadius: 'var(--radius-sm)',
                            padding: 'var(--space-2) var(--space-3)',
                            opacity: isEnabled ? 1 : 0.5,
                          }}>
                            <div style={{ fontSize: 'var(--text-sm)', fontWeight: 500, color: 'var(--gray-12)' }}>{displayName}</div>
                            {ver && (
                              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--gray-9)', fontFamily: 'var(--font-mono)' }}>{ver}</div>
                            )}
                            <div style={{ fontSize: 'var(--text-xs)', color: isEnabled ? 'var(--green-11)' : 'var(--red-9)', marginTop: '2px' }}>
                              {isEnabled ? 'Active' : 'Disabled'}
                            </div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                );
              })}
            </div>
          )}
        </>
      )}
    </div>
  );
}
