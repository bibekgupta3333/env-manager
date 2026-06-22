import { useState, useEffect } from 'react';
import { fetchEnvs } from '../api';

function fmtSize(b) {
  if (!b) return '0 B';
  if (b >= 1e9) return (b / 1e9).toFixed(1) + ' GB';
  if (b >= 1e6) return (b / 1e6).toFixed(1) + ' MB';
  if (b >= 1e3) return (b / 1e3).toFixed(1) + ' KB';
  return b + ' B';
}

export default function Dashboard({ showToast }) {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchEnvs()
      .then(setData)
      .catch(() => showToast?.('Failed to load environments'))
      .finally(() => setLoading(false));
  }, []);

  if (loading) return <p className="loading">Loading...</p>;

  const envs = data?.environments || [];
  const total = envs.length;
  const healthy = envs.filter((e) => e.last_health_result === 'healthy').length;
  const broken = envs.filter((e) => e.last_health_result === 'broken').length;
  const totalSize = envs.reduce((s, e) => s + (e.size_bytes || 0), 0);

  return (
    <div>
      <h2>Dashboard</h2>
      <div className="summary">
        <div className="card">
          <div className="num" style={{ color: 'var(--accent)' }}>{total}</div>
          <div className="label">Environments</div>
        </div>
        <div className="card">
          <div className="num" style={{ color: 'var(--green)' }}>{healthy}</div>
          <div className="label">Healthy</div>
        </div>
        <div className="card">
          <div className="num" style={{ color: 'var(--red)' }}>{broken}</div>
          <div className="label">Broken</div>
        </div>
        <div className="card">
          <div className="num" style={{ color: 'var(--dim)' }}>{fmtSize(totalSize)}</div>
          <div className="label">Total Size</div>
        </div>
      </div>
    </div>
  );
}
