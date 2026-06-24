import { useState, useEffect, useMemo } from 'react';
import { fetchEnvs } from '../api';
import StatusBadge from './StatusBadge';
import SizeBar from './SizeBar';
import { createToast } from './Toast';

function fmtSize(b) {
  if (!b || b === 0) return '0 B';
  if (b >= 1e9) return (b / 1e9).toFixed(1) + ' GB';
  if (b >= 1e6) return (b / 1e6).toFixed(1) + ' MB';
  if (b >= 1e3) return (b / 1e3).toFixed(1) + ' KB';
  return b + ' B';
}

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

const BoxIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
    <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
    <line x1="12" y1="22.08" x2="12" y2="12"/>
  </svg>
);

const CheckIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
    <polyline points="22 4 12 14.01 9 11.01"/>
  </svg>
);

const CpuIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="4" y="4" width="16" height="16" rx="2" ry="2"/>
    <rect x="9" y="9" width="6" height="6"/>
    <line x1="9" y1="1" x2="9" y2="4"/>
    <line x1="15" y1="1" x2="15" y2="4"/>
    <line x1="9" y1="20" x2="9" y2="23"/>
    <line x1="15" y1="20" x2="15" y2="23"/>
    <line x1="20" y1="9" x2="23" y2="9"/>
    <line x1="20" y1="14" x2="23" y2="14"/>
    <line x1="1" y1="9" x2="4" y2="9"/>
    <line x1="1" y1="14" x2="4" y2="14"/>
  </svg>
);

const HardDriveIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="12" x2="2" y2="12"/>
    <path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>
    <line x1="6" y1="16" x2="6.01" y2="16"/>
    <line x1="10" y1="16" x2="10.01" y2="16"/>
  </svg>
);

function LoadingSkeleton() {
  return (
    <div>
      <div className="summary">
        {[...Array(5)].map((_, i) => (
          <div key={i} className="skeleton skeleton-card" />
        ))}
      </div>
      <div style={{ marginBottom: 'var(--space-8)' }}>
        <div className="skeleton" style={{ height: '24px', width: '220px', marginBottom: 'var(--space-4)' }} />
        <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
          {[...Array(4)].map((_, i) => (
            <div key={i} className="skeleton" style={{ height: '120px', width: '280px', borderRadius: 'var(--radius-md)' }} />
          ))}
        </div>
      </div>
      <div>
        <div className="skeleton" style={{ height: '24px', width: '160px', marginBottom: 'var(--space-4)' }} />
        {[...Array(5)].map((_, i) => (
          <div key={i} className="skeleton skeleton-row" />
        ))}
      </div>
    </div>
  );
}

function countProjectsForRuntime(runtime, projects) {
  return projects.filter((p) =>
    p.language === runtime.language &&
    p.tool === runtime.tool &&
    p.version === runtime.version
  ).length;
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    Promise.all([
      fetchEnvs(null, null, 'runtime'),
      fetchEnvs(null, null, 'project'),
    ])
      .then(([globalData, localData]) => {
        setData({
          runtimes: globalData.environments || [],
          projects: localData.environments || [],
        });
      })
      .catch(() => createToast('Failed to load', 'error'))
      .finally(() => setLoading(false));
  }, []);

  const runtimeGroups = useMemo(() => {
    if (!data) return [];
    const seen = new Map();
    for (const env of data.runtimes) {
      const key = `${env.adapter || 'unknown'}|${env.version || 'unknown'}`;
      if (!seen.has(key)) seen.set(key, env);
    }
    return [...seen.values()];
  }, [data]);

  if (loading) return <LoadingSkeleton />;

  const { runtimes, projects } = data;

  const total = runtimes.length + projects.length;
  const healthy = [...runtimes, ...projects].filter(
    (e) => e.last_health_result === 'healthy'
  ).length;
  const totalSize = [...runtimes, ...projects].reduce(
    (s, e) => s + (e.size_bytes || 0), 0
  );

  const statCards = [
    {
      icon: <BoxIcon />,
      iconBg: 'var(--violet-3)',
      iconColor: 'var(--violet-9)',
      value: total,
      label: 'Total Envs',
    },
    {
      icon: <CpuIcon />,
      iconBg: 'var(--green-3)',
      iconColor: 'var(--green-9)',
      value: runtimes.length,
      label: 'Runtimes',
    },
    {
      icon: <BoxIcon />,
      iconBg: 'var(--violet-3)',
      iconColor: 'var(--violet-9)',
      value: projects.length,
      label: 'Projects',
    },
    {
      icon: <CheckIcon />,
      iconBg: 'var(--green-3)',
      iconColor: 'var(--green-9)',
      value: healthy,
      label: 'Healthy',
    },
    {
      icon: <HardDriveIcon />,
      iconBg: 'var(--amber-3)',
      iconColor: 'var(--amber-9)',
      value: totalSize,
      label: 'Disk Usage',
      isSize: true,
    },
  ];

  return (
    <div>
      <div className="summary">
        {statCards.map((card) => (
          <div key={card.label} className="stat-card">
            <div className="stat-card-header">
              <div className="stat-card-icon" style={{ background: card.iconBg, color: card.iconColor }}>
                {card.icon}
              </div>
              <span className="stat-card-label">{card.label}</span>
            </div>
            <div
              className={`stat-card-value${card.isSize && totalSize >= 1e9 ? ' sm' : ''}`}
              style={!card.isSize ? { color: card.iconColor } : undefined}
            >
              {card.isSize ? fmtSize(card.value) : card.value}
            </div>
          </div>
        ))}
      </div>

      <section style={{ marginBottom: 'var(--space-8)' }}>
        <div style={{ marginBottom: 'var(--space-4)' }}>
          <h2 style={{ fontSize: 'var(--text-xl)', fontWeight: 700, color: 'var(--gray-12)', letterSpacing: '-0.02em' }}>Virtual Environments</h2>
          <p style={{ fontSize: 'var(--text-sm)', color: 'var(--gray-9)', marginTop: 'var(--space-1)' }}>Installed runtimes and version managers</p>
        </div>
        {runtimeGroups.length === 0 ? (
          <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--gray-9)', fontSize: 'var(--text-sm)' }}>
            No virtual environments discovered. Run a scan to find installed runtimes.
          </div>
        ) : (
          <div style={{ display: 'flex', gap: 'var(--space-3)', flexWrap: 'wrap' }}>
            {runtimeGroups.map((env) => {
              const langStyle = getLangStyle(env.language);
              const projectCount = countProjectsForRuntime(env, projects);
              const status = env.last_health_result || 'unchecked';
              return (
                <div key={env.id} className="stat-card" style={{ flex: '1 1 260px', minWidth: '240px', maxWidth: '360px' }}>
                  <div className="stat-card-header">
                    <div
                      className="stat-card-icon"
                      style={{
                        background: langStyle.bg,
                        color: langStyle.color,
                        fontSize: 'var(--text-xs)',
                        fontWeight: 700,
                        textTransform: 'uppercase',
                      }}
                    >
                      {langStyle.label}
                    </div>
                    <span className="stat-card-label">{env.tool || env.adapter} {env.version || ''}</span>
                  </div>
                  <div style={{ display: 'flex', gap: 'var(--space-4)', marginTop: 'var(--space-3)', alignItems: 'center', flexWrap: 'wrap' }}>
                    <div>
                      <div className="stat-card-value" style={{ fontSize: 'var(--text-xl)', fontFamily: 'var(--font-mono)', fontWeight: 700, color: 'var(--gray-12)' }}>
                        {projectCount}
                      </div>
                      <small style={{ color: 'var(--gray-9)', fontSize: 'var(--text-xs)' }}>projects</small>
                    </div>
                    <div style={{ minWidth: '100px' }}>
                      <SizeBar bytes={env.size_bytes} />
                    </div>
                    <StatusBadge status={status} size="sm" />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </section>

      <section>
        <div style={{ marginBottom: 'var(--space-4)' }}>
          <h2 style={{ fontSize: 'var(--text-xl)', fontWeight: 700, color: 'var(--gray-12)', letterSpacing: '-0.02em' }}>Projects</h2>
          <p style={{ fontSize: 'var(--text-sm)', color: 'var(--gray-9)', marginTop: 'var(--space-1)' }}>Your project environments</p>
        </div>
        {projects.length === 0 ? (
          <div style={{ padding: 'var(--space-8)', textAlign: 'center', color: 'var(--gray-9)', fontSize: 'var(--text-sm)' }}>
            No project environments discovered. Run a scan to find environments in your projects.
          </div>
        ) : (
          <div className="table-wrap">
            <table>
              <colgroup>
                <col style={{ width: '22%' }} />
                <col style={{ width: '18%' }} />
                <col style={{ width: '12%' }} />
                <col style={{ width: '12%' }} />
                <col style={{ width: '36%' }} />
              </colgroup>
              <thead>
                <tr>
                  <th>Project Name</th>
                  <th>Runtime</th>
                  <th>Size</th>
                  <th>Health</th>
                  <th>Path</th>
                </tr>
              </thead>
              <tbody>
                {projects.map((env) => {
                  const status = env.last_health_result || 'unchecked';
                  const runtimeLabel = env.language && env.version
                    ? `${env.language} ${env.version}${env.tool ? ` (${env.tool})` : ''}`
                    : '-';
                  return (
                    <tr key={env.id}>
                      <td style={{ fontWeight: 600, color: 'var(--gray-12)' }}>
                        {env.project_name || '-'}
                      </td>
                      <td style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--gray-10)' }}>
                        {runtimeLabel}
                      </td>
                      <td>
                        <SizeBar bytes={env.size_bytes} />
                      </td>
                      <td>
                        <StatusBadge status={status} size="sm" />
                      </td>
                      <td className="path-cell" title={env.path || ''}>
                        {env.path || '-'}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
