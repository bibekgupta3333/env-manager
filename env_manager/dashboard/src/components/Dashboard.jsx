import { useState, useEffect } from 'react';
import { fetchEnvs } from '../api';
import { createToast } from './Toast';

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

const AlertIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <line x1="12" y1="8" x2="12" y2="12"/>
    <line x1="12" y1="16" x2="12.01" y2="16"/>
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

function fmtSize(b) {
  if (!b) return '0 B';
  if (b >= 1e9) return (b / 1e9).toFixed(1) + ' GB';
  if (b >= 1e6) return (b / 1e6).toFixed(1) + ' MB';
  if (b >= 1e3) return (b / 1e3).toFixed(1) + ' KB';
  return b + ' B';
}

export default function Dashboard() {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchEnvs()
      .then(setData)
      .catch(() => createToast('Failed to load environments', 'error'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) {
    return (
      <div>
        <div className="summary">
          {[...Array(4)].map((_, i) => (
            <div key={i} className="skeleton skeleton-card" />
          ))}
        </div>
        {[...Array(6)].map((_, i) => (
          <div key={i} className="skeleton skeleton-row" />
        ))}
      </div>
    );
  }

  const envs = data?.environments || [];
  const total = envs.length;
  const healthy = envs.filter((e) => e.last_health_result === 'healthy').length;
  const broken = envs.filter((e) => e.last_health_result === 'broken').length;
  const totalSize = envs.reduce((s, e) => s + (e.size_bytes || 0), 0);

  const cards = [
    {
      icon: <BoxIcon />,
      iconBg: 'var(--violet-3)',
      iconColor: 'var(--violet-9)',
      value: total,
      label: 'Total',
      color: 'var(--violet-9)',
      hoverColor: 'var(--violet-9)',
    },
    {
      icon: <CheckIcon />,
      iconBg: 'var(--green-3)',
      iconColor: 'var(--green-9)',
      value: healthy,
      label: 'Healthy',
      color: 'var(--green-9)',
      hoverColor: 'var(--green-9)',
    },
    {
      icon: <AlertIcon />,
      iconBg: 'var(--red-3)',
      iconColor: 'var(--red-9)',
      value: broken,
      label: 'Broken',
      color: 'var(--red-9)',
      hoverColor: 'var(--red-9)',
    },
    {
      icon: <HardDriveIcon />,
      iconBg: 'var(--amber-3)',
      iconColor: 'var(--amber-9)',
      value: totalSize,
      label: 'Disk Usage',
      color: 'var(--amber-9)',
      hoverColor: 'var(--amber-9)',
      isSize: true,
    },
  ];

  return (
    <div>
      <div className="summary">
        {cards.map((card) => (
          <div
            key={card.label}
            className="stat-card"
            onMouseEnter={e => e.currentTarget.style.borderColor = card.hoverColor}
            onMouseLeave={e => e.currentTarget.style.borderColor = ''}
          >
            <div className="stat-card-header">
              <div className="stat-card-icon" style={{ background: card.iconBg, color: card.iconColor }}>
                {card.icon}
              </div>
              <span className="stat-card-label">{card.label}</span>
            </div>
            <div
              className={`stat-card-value${card.isSize && totalSize >= 1e9 ? ' sm' : ''}`}
              style={{ color: card.color }}
            >
              {card.isSize ? fmtSize(card.value) : card.value}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
