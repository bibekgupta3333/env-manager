import { useState } from 'react';
import StatusBadge from './StatusBadge';
import { createToast } from './Toast';

const CloseIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="6" x2="6" y2="18"/>
    <line x1="6" y1="6" x2="18" y2="18"/>
  </svg>
);

const SearchIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8"/>
    <line x1="21" y1="21" x2="16.65" y2="16.65"/>
  </svg>
);

function fmtSize(b) {
  if (!b) return '0 B';
  if (b >= 1e9) return (b / 1e9).toFixed(1) + ' GB';
  if (b >= 1e6) return (b / 1e6).toFixed(1) + ' MB';
  if (b >= 1e3) return (b / 1e3).toFixed(1) + ' KB';
  return b + ' B';
}

export default function EnvDetail({ env, onClose }) {
  const [tab, setTab] = useState('packages');
  const [pkgFilter, setPkgFilter] = useState('');

  const packages = usePackages(env);

  return (
    <div className="detail-overlay" onClick={onClose}>
      <div className="detail-panel" onClick={(e) => e.stopPropagation()}>
        <div className="detail-header">
          <div>
            <h2>{env.project_name || env.path}</h2>
            <div className="detail-path">{env.path || ''}</div>
          </div>
          <button className="detail-close" onClick={onClose}>
            <CloseIcon />
          </button>
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
                <dt>Packages</dt><dd style={{ fontFamily: 'var(--font-mono)' }}>{env.package_count ?? 'N/A'}</dd>
              </dl>

              {packages.length > 0 && (
                <div style={{ marginTop: 'var(--space-6)' }}>
                  <div style={{ fontSize: 'var(--text-xs)', color: 'var(--gray-9)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 'var(--space-3)' }}>
                    Package list
                  </div>
                  <div style={{ position: 'relative', marginBottom: 'var(--space-3)' }}>
                    <span style={{ position: 'absolute', left: '8px', top: '7px', color: 'var(--gray-9)', display: 'flex', pointerEvents: 'none' }}>
                      <SearchIcon />
                    </span>
                    <input
                      type="text"
                      placeholder="Filter packages..."
                      value={pkgFilter}
                      onChange={(e) => setPkgFilter(e.target.value)}
                      style={{
                        width: '100%',
                        background: 'var(--gray-3)',
                        border: '1px solid var(--gray-5)',
                        color: 'var(--gray-12)',
                        padding: '7px 10px 7px 28px',
                        borderRadius: 'var(--radius-sm)',
                        fontSize: 'var(--text-sm)',
                        outline: 'none',
                        boxSizing: 'border-box',
                      }}
                      onFocus={e => e.currentTarget.style.borderColor = 'var(--violet-9)'}
                      onBlur={e => e.currentTarget.style.borderColor = 'var(--gray-5)'}
                    />
                  </div>
                  <div style={{ maxHeight: '300px', overflow: 'auto' }}>
                    {packages
                      .filter(p => !pkgFilter || p.name.toLowerCase().includes(pkgFilter.toLowerCase()))
                      .map((p, i) => (
                        <div key={i} style={{
                          display: 'flex',
                          justifyContent: 'space-between',
                          alignItems: 'center',
                          padding: 'var(--space-2) var(--space-3)',
                          borderBottom: '1px solid var(--gray-5)',
                          fontSize: 'var(--text-sm)',
                        }}>
                          <span style={{ color: 'var(--gray-12)' }}>{p.name}</span>
                          <span style={{
                            fontFamily: 'var(--font-mono)',
                            fontSize: 'var(--text-xs)',
                            color: 'var(--gray-9)',
                          }}>
                            {p.version || '-'}
                          </span>
                        </div>
                      ))}
                  </div>
                </div>
              )}

              {env.raw_info && (
                <details style={{ marginTop: 'var(--space-4)' }}>
                  <summary style={{ cursor: 'pointer', color: 'var(--gray-9)', fontSize: 'var(--text-xs)', fontWeight: 500 }}>
                    Raw metadata
                  </summary>
                  <pre style={{
                    marginTop: 'var(--space-2)',
                    fontSize: 'var(--text-xs)',
                    color: 'var(--gray-10)',
                    overflow: 'auto',
                    maxHeight: '200px',
                    background: 'var(--gray-3)',
                    padding: 'var(--space-3)',
                    borderRadius: 'var(--radius-sm)',
                    fontFamily: 'var(--font-mono)',
                  }}>
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
                  <StatusBadge status={env.last_health_result || 'unchecked'} />
                </dd>
                <dt>Last checked</dt><dd style={{ fontSize: 'var(--text-sm)', color: 'var(--gray-10)' }}>{env.last_health_at || 'Never'}</dd>
                <dt>Error</dt>
                <dd style={{ fontSize: 'var(--text-xs)', color: 'var(--red-9)' }}>
                  {env.last_health_error || '—'}
                </dd>
              </dl>
            </div>
          )}

          {tab === 'actions' && (
            <div className="detail-actions">
              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--gray-9)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em', marginBottom: 'var(--space-1)' }}>
                Actions
              </div>

              <button className="action-btn" onClick={() => createToast('Install not available via dashboard. Use the CLI.', 'info')}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="12" y1="5" x2="12" y2="19"/>
                  <line x1="5" y1="12" x2="19" y2="12"/>
                </svg>
                <div>
                  <div className="action-label">Install package</div>
                  <div className="action-desc">Add a dependency to this environment</div>
                </div>
              </button>

              <button className="action-btn" onClick={() => createToast('Pin not available via dashboard. Use the CLI.', 'info')}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <path d="M12 2L15.09 8.26 22 9.27 17 14.14 18.18 21.02 12 17.77 5.82 21.02 7 14.14 2 9.27 8.91 8.26 12 2z"/>
                </svg>
                <div>
                  <div className="action-label">Pin environment</div>
                  <div className="action-desc">Protect from automatic cleanup</div>
                </div>
              </button>

              <button className="action-btn danger" onClick={() => createToast('Remove not available via dashboard. Use the CLI.', 'info')}>
                <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <polyline points="3 6 5 6 21 6"/>
                  <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
                  <line x1="10" y1="11" x2="10" y2="17"/>
                  <line x1="14" y1="11" x2="14" y2="17"/>
                </svg>
                <div>
                  <div className="action-label">Remove environment</div>
                  <div className="action-desc">Permanently delete this environment</div>
                </div>
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

function usePackages(env) {
  if (!env || !env.raw_info) return [];
  try {
    const raw = typeof env.raw_info === 'string' ? JSON.parse(env.raw_info) : env.raw_info;
    if (raw.dependencies && typeof raw.dependencies === 'object') {
      return Object.entries(raw.dependencies).map(([name, version]) => ({
        name,
        version: typeof version === 'string' ? version : String(version),
      }));
    }
    return [];
  } catch {
    return [];
  }
}
