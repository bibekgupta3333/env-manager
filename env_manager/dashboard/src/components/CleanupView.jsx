import { useState } from 'react';
import { fetchEnvs } from '../api';

function fmtSize(b) {
  if (!b) return '0 B';
  if (b >= 1e9) return (b / 1e9).toFixed(1) + ' GB';
  if (b >= 1e6) return (b / 1e6).toFixed(1) + ' MB';
  if (b >= 1e3) return (b / 1e3).toFixed(1) + ' KB';
  return b + ' B';
}

export default function CleanupView({ showToast }) {
  const [days, setDays] = useState(60);
  const [includeOrphaned, setIncludeOrphaned] = useState(false);
  const [includeSnapshot, setIncludeSnapshot] = useState(true);
  const [candidates, setCandidates] = useState(null);
  const [selected, setSelected] = useState(new Set());
  const [loading, setLoading] = useState(false);

  const preview = async () => {
    setLoading(true);
    try {
      const data = await fetchEnvs();
      const cutoff = Date.now() - days * 86400000;
      const stale = (data.environments || []).filter((e) => {
        if (!e.last_used_at) return true;
        return new Date(e.last_used_at).getTime() < cutoff;
      });
      setCandidates(stale);
      setSelected(new Set());
    } catch {
      showToast?.('Cleanup preview failed');
    } finally {
      setLoading(false);
    }
  };

  const toggle = (id) => {
    setSelected((prev) => {
      const next = new Set(prev);
      if (next.has(id)) next.delete(id);
      else next.add(id);
      return next;
    });
  };

  const toggleAll = () => {
    if (candidates && selected.size === candidates.length) {
      setSelected(new Set());
    } else {
      setSelected(new Set(candidates?.map((e) => e.id) || []));
    }
  };

  const execute = () => {
    const cmd = `envs cleanup --stale ${days} --confirm${includeSnapshot ? ' --snapshot' : ''}${includeOrphaned ? ' --orphaned' : ''}`;
    showToast?.(`Use CLI: ${cmd}`);
  };

  const totalSize = candidates
    ? candidates.reduce((s, e) => s + (e.size_bytes || 0), 0)
    : 0;

  return (
    <div>
      <h2>Cleanup</h2>
      <div className="toolbar">
        <label>Stale days:</label>
        <input
          type="number"
          value={days}
          onChange={(e) => setDays(Number(e.target.value))}
          style={{ width: '70px' }}
        />
        <label>
          <input
            type="checkbox"
            checked={includeOrphaned}
            onChange={(e) => setIncludeOrphaned(e.target.checked)}
          />
          Orphaned
        </label>
        <label>
          <input
            type="checkbox"
            checked={includeSnapshot}
            onChange={(e) => setIncludeSnapshot(e.target.checked)}
          />
          Snapshot
        </label>
        <button onClick={preview} disabled={loading}>
          {loading ? 'Analyzing...' : 'Preview (dry-run)'}
        </button>
        {candidates && candidates.length > 0 && (
          <button className="danger" onClick={execute}>
            Execute Cleanup
          </button>
        )}
      </div>

      {loading && <p className="loading">Analyzing...</p>}

      {candidates && candidates.length === 0 && (
        <p style={{ color: 'var(--green)' }}>
          No stale environments found (unused &gt; {days} days).
        </p>
      )}

      {candidates && candidates.length > 0 && (
        <>
          <p style={{ color: 'var(--red)', marginBottom: '12px' }}>
            {candidates.length} environments stale (&gt;{days} days).
            Would free <strong>{fmtSize(totalSize)}</strong>.
          </p>

          <div className="toolbar">
            <button onClick={toggleAll}>
              {selected.size === candidates.length ? 'Deselect All' : 'Select All'}
            </button>
          </div>

          <div className="cleanup-list">
            {candidates.map((env) => (
              <label key={env.id} className="cleanup-item">
                <input
                  type="checkbox"
                  checked={selected.has(env.id)}
                  onChange={() => toggle(env.id)}
                />
                <span className="name">{env.project_name || env.path}</span>
                <span className="meta">{env.language}</span>
                <span className="meta">{fmtSize(env.size_bytes)}</span>
                <span className="meta">
                  {env.last_used_at
                    ? new Date(env.last_used_at).toLocaleDateString()
                    : 'never'}
                </span>
              </label>
            ))}
          </div>

          <p style={{ color: 'var(--dim)', fontSize: '12px' }}>
            Run <code>envs cleanup --stale {days} --dry-run</code> in terminal for full preview.
          </p>
        </>
      )}

      {!loading && !candidates && (
        <p className="loading">Click "Preview" to see what would be cleaned up.</p>
      )}
    </div>
  );
}
