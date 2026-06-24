import { useState, useEffect } from 'react';
import { fetchSnapshots, restoreSnapshot, pruneSnapshots } from '../api';
import EmptyState from './EmptyState';
import { createToast } from './Toast';

const RotateCcwIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="1 4 1 10 7 10"/>
    <path d="M3.51 15a9 9 0 1 0 2.13-9.36L1 10"/>
  </svg>
);

const TrashIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="3 6 5 6 21 6"/>
    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
  </svg>
);

const RefreshIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="23 4 23 10 17 10"/>
    <polyline points="1 20 1 14 7 14"/>
    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
  </svg>
);

const ArchiveIcon = () => (
  <svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="21 8 21 21 3 21 3 8"/>
    <rect x="1" y="3" width="22" height="5"/>
    <line x1="10" y1="12" x2="14" y2="12"/>
  </svg>
);

function fmtDate(ts) {
  if (!ts) return '-';
  const d = new Date(ts);
  return d.toLocaleDateString('en-US', {
    month: 'short',
    day: 'numeric',
    year: 'numeric',
    hour: '2-digit',
    minute: '2-digit',
  });
}

export default function SnapshotsView() {
  const [snaps, setSnaps] = useState([]);
  const [loading, setLoading] = useState(true);

  const load = () => {
    setLoading(true);
    fetchSnapshots()
      .then((data) => setSnaps(data.snapshots || []))
      .catch(() => createToast('Failed to load snapshots', 'error'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleRestore = async (snap) => {
    try {
      await restoreSnapshot(snap.id);
      createToast(`Snapshot restored`, 'success');
      load();
    } catch {
      createToast('Restore failed', 'error');
    }
  };

  const handlePrune = async () => {
    try {
      const result = await pruneSnapshots();
      createToast(`Pruned ${result.pruned} old snapshots`, 'success');
      load();
    } catch {
      createToast('Prune failed', 'error');
    }
  };

  const pkgCount = (snap) => {
    try {
      const deps = JSON.parse(snap.frozen_deps || '{}');
      return Array.isArray(deps) ? deps.length : Object.keys(deps).length;
    } catch {
      return 0;
    }
  };

  return (
    <div>
      <div className="toolbar">
        <button className="btn" onClick={load} title="Refresh">
          <RefreshIcon /> Refresh
        </button>
        <button className="btn btn-danger" onClick={handlePrune}>
          <TrashIcon /> Prune Old
        </button>
      </div>

      {loading ? (
        <div>
          {[...Array(5)].map((_, i) => (
            <div key={i} className="skeleton" style={{ height: '72px', marginBottom: 'var(--space-3)', borderRadius: 'var(--radius-md)' }} />
          ))}
        </div>
      ) : snaps.length === 0 ? (
        <EmptyState
          icon={<ArchiveIcon />}
          title="No snapshots yet"
          description="Remove envs with --snapshot to create snapshot backups before deletion."
        />
      ) : (
        <div className="snaps-timeline">
          {snaps.map((snap, i) => (
            <div key={snap.id} className="snap-item">
              <div className="snap-dot" />
              <div className="snap-header">
                <span className="snap-version">v{snap.version}</span>
                <span className="snap-date">{fmtDate(snap.created_at)}</span>
              </div>
              <div className="snap-details">
                <span className="snap-stat">
                  <strong>{snap.language || 'Unknown'}</strong>
                </span>
                <span className="snap-stat">
                  <strong>{pkgCount(snap)}</strong> packages
                </span>
              </div>
              <div className="snap-actions">
                <button
                  className="btn btn-primary"
                  onClick={() => handleRestore(snap)}
                  style={{ padding: '6px 14px', fontSize: 'var(--text-xs)' }}
                >
                  <RotateCcwIcon /> Restore
                </button>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
