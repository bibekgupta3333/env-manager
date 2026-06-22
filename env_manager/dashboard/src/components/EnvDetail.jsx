import { useState } from 'react';

function fmtSize(b) {
  if (!b) return '0 B';
  if (b >= 1e9) return (b / 1e9).toFixed(1) + ' GB';
  if (b >= 1e6) return (b / 1e6).toFixed(1) + ' MB';
  if (b >= 1e3) return (b / 1e3).toFixed(1) + ' KB';
  return b + ' B';
}

export default function EnvDetail({ env, onClose, showToast }) {
  const [tab, setTab] = useState('packages');

  const handleAction = (action) => {
    showToast?.(`Action "${action}" not yet available via dashboard. Use the CLI.`);
  };

  return (
    <div className="detail-overlay">
      <div className="detail-header">
        <h3>{env.project_name || env.path}</h3>
        <button onClick={onClose}>&times;</button>
      </div>
      <div className="detail-tabs">
        <button className={tab === 'packages' ? 'active' : ''} onClick={() => setTab('packages')}>
          Packages
        </button>
        <button className={tab === 'health' ? 'active' : ''} onClick={() => setTab('health')}>
          Health
        </button>
        <button className={tab === 'actions' ? 'active' : ''} onClick={() => setTab('actions')}>
          Actions
        </button>
      </div>
      <div className="detail-body">
        {tab === 'packages' && (
          <div>
            <dl>
              <dt>Language</dt><dd>{env.language} {env.version || ''}</dd>
              <dt>Tool</dt><dd>{env.tool || '-'}</dd>
              <dt>Size</dt><dd>{fmtSize(env.size_bytes)}</dd>
              <dt>Path</dt><dd style={{ wordBreak: 'break-all', fontSize: '12px', color: 'var(--dim)' }}>{env.path || '-'}</dd>
              <dt>Packages</dt><dd>{env.package_count ?? 'N/A'}</dd>
            </dl>
            {env.raw_info && (
              <details style={{ marginTop: '12px' }}>
                <summary style={{ cursor: 'pointer', color: 'var(--dim)', fontSize: '12px' }}>
                  Raw metadata
                </summary>
                <pre style={{ marginTop: '8px', fontSize: '11px', color: 'var(--dim)', overflow: 'auto', maxHeight: '200px' }}>
                  {typeof env.raw_info === 'string' ? env.raw_info : JSON.stringify(env.raw_info, null, 2)}
                </pre>
              </details>
            )}
          </div>
        )}

        {tab === 'health' && (
          <div>
            <dl>
              <dt>Status</dt>
              <dd>
                <span className={`badge ${env.last_health_result || 'unchecked'}`}>
                  {env.last_health_result || 'unchecked'}
                </span>
              </dd>
              <dt>Checked</dt><dd>{env.last_health_at || 'never'}</dd>
              <dt>Error</dt><dd style={{ color: 'var(--red)', fontSize: '12px' }}>{env.last_health_error || '-'}</dd>
            </dl>
          </div>
        )}

        {tab === 'actions' && (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
            <button className="primary" style={{ width: '100%', padding: '8px', borderRadius: '6px', background: 'var(--accent)', color: '#fff', border: 'none', cursor: 'pointer' }}
              onClick={() => handleAction('activate')}>
              Activate
            </button>
            <button style={{ width: '100%', padding: '8px', borderRadius: '6px', background: 'var(--surface)', border: '1px solid var(--border)', color: 'var(--text)', cursor: 'pointer' }}
              onClick={() => handleAction('health_check')}>
              Run Health Check
            </button>
            <button className="danger" style={{ width: '100%', padding: '8px', borderRadius: '6px', background: 'transparent', border: '1px solid var(--red)', color: 'var(--red)', cursor: 'pointer' }}
              onClick={() => handleAction('delete')}>
              Delete
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
