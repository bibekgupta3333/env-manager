import { useState, useEffect } from 'react';
import { fetchSnapshots } from '../api';

export default function SnapshotsView({ showToast }) {
  const [snaps, setSnaps] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    fetchSnapshots()
      .then((data) => setSnaps(data.snapshots || []))
      .catch(() => showToast?.('Failed to load snapshots'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleRestore = (snap) => {
    showToast?.(`Snapshot restore not yet available via dashboard. Use: envs snapshots restore ${snap.id}`);
  };

  const handlePrune = () => {
    showToast?.('Use: envs snapshots prune --confirm');
  };

  const pkgCount = (snap) => {
    try {
      return JSON.parse(snap.frozen_deps || '{}').length;
    } catch {
      return 0;
    }
  };

  return (
    <div>
      <h2>Snapshots</h2>
      <div className="toolbar">
        <button onClick={load}>Refresh</button>
        <button className="danger" onClick={handlePrune}>Prune Old</button>
      </div>

      {loading ? (
        <p className="loading">Loading...</p>
      ) : snaps.length === 0 ? (
        <p className="loading">No snapshots available.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th>Version</th>
              <th>Language</th>
              <th>Packages</th>
              <th>Created</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {snaps.map((snap) => (
              <tr key={snap.id}>
                <td>v{snap.version}</td>
                <td>{snap.language || '-'}</td>
                <td>{pkgCount(snap)} pkgs</td>
                <td style={{ color: 'var(--dim)' }}>{snap.created_at}</td>
                <td>
                  <button
                    onClick={() => handleRestore(snap)}
                    style={{
                      background: 'var(--accent)',
                      color: '#fff',
                      border: 'none',
                      padding: '4px 10px',
                      borderRadius: '4px',
                      fontSize: '12px',
                      cursor: 'pointer',
                    }}
                  >
                    Restore
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
