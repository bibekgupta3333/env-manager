import { useState, useEffect } from 'react';
import { fetchConfig, enablePlugin, disablePlugin } from '../api';
import { createToast } from './Toast';

const RefreshIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="23 4 23 10 17 10"/>
    <polyline points="1 20 1 14 7 14"/>
    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
  </svg>
);

const PowerIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M18.36 6.64a9 9 0 1 1-12.73 0"/>
    <line x1="12" y1="2" x2="12" y2="12"/>
  </svg>
);

export default function ConfigView() {
  const [config, setConfig] = useState(null);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    fetchConfig()
      .then((data) => setConfig(data))
      .catch(() => createToast('Failed to load config', 'error'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleToggle = async (name, currentEnabled) => {
    try {
      if (currentEnabled) {
        await disablePlugin(name);
        createToast(`Plugin ${name} disabled`, 'success');
      } else {
        await enablePlugin(name);
        createToast(`Plugin ${name} enabled`, 'success');
      }
      load();
    } catch {
      createToast(`Failed to toggle plugin ${name}`, 'error');
    }
  };

  const adapters = config?.adapter_registry || config?.adapters || [];
  const dbPath = config?.db_path || config?.database?.path || '';

  return (
    <div>
      <div className="toolbar">
        <button className="btn" onClick={load} disabled={loading}>
          <RefreshIcon /> Refresh
        </button>
      </div>

      {loading ? (
        <div>
          {[...Array(5)].map((_, i) => (
            <div key={i} className="skeleton" style={{ height: '36px', marginBottom: '2px', borderRadius: 'var(--radius-sm)' }} />
          ))}
        </div>
      ) : (
        <>
          {dbPath && (
            <div style={{
              background: 'var(--gray-2)',
              border: '1px solid var(--gray-5)',
              borderRadius: 'var(--radius-md)',
              padding: 'var(--space-4) var(--space-5)',
              marginBottom: 'var(--space-5)',
              display: 'flex',
              alignItems: 'center',
              gap: 'var(--space-2)',
              fontSize: 'var(--text-sm)',
            }}>
              <span style={{ color: 'var(--gray-9)', fontWeight: 500 }}>DB Path:</span>
              <span style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--gray-11)' }}>{dbPath}</span>
            </div>
          )}

          {adapters.length > 0 ? (
            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Name</th>
                    <th>Display Name</th>
                    <th>Enabled</th>
                    <th>Action</th>
                  </tr>
                </thead>
                <tbody>
                  {adapters.map((adapter) => {
                    const name = adapter.name || adapter.id || '';
                    const displayName = adapter.display_name || adapter.label || name;
                    const enabled = adapter.enabled !== undefined ? adapter.enabled : adapter.active;
                    return (
                      <tr key={name}>
                        <td style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--gray-11)' }}>{name}</td>
                        <td style={{ color: 'var(--gray-12)', fontWeight: 500 }}>{displayName}</td>
                        <td>
                          <span style={{
                            display: 'inline-flex',
                            alignItems: 'center',
                            gap: 'var(--space-1)',
                            fontSize: 'var(--text-xs)',
                            color: enabled ? 'var(--green-11)' : 'var(--red-9)',
                          }}>
                            <span style={{
                              width: '7px',
                              height: '7px',
                              borderRadius: '50%',
                              background: enabled ? 'var(--green-9)' : 'var(--red-9)',
                              display: 'inline-block',
                            }} />
                            {enabled ? 'Enabled' : 'Disabled'}
                          </span>
                        </td>
                        <td>
                          <button
                            className={`btn ${enabled ? 'btn-danger' : 'btn-primary'}`}
                            onClick={() => handleToggle(name, enabled)}
                            style={{ fontSize: 'var(--text-xs)', padding: '4px 10px' }}
                          >
                            <PowerIcon />
                            <span>{enabled ? 'Disable' : 'Enable'}</span>
                          </button>
                        </td>
                      </tr>
                    );
                  })}
                </tbody>
              </table>
            </div>
          ) : (
            <p style={{ color: 'var(--gray-9)', textAlign: 'center', padding: 'var(--space-12) 0', fontSize: 'var(--text-sm)' }}>
              No adapter registry found in configuration.
            </p>
          )}
        </>
      )}
    </div>
  );
}
