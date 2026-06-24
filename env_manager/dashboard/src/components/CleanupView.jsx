import { useState, useEffect, useRef } from 'react';
import { fetchEnvs, triggerCleanup } from '../api';
import SizeBar from './SizeBar';
import { createToast } from './Toast';

const SearchIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8"/>
    <line x1="21" y1="21" x2="16.65" y2="16.65"/>
  </svg>
);

const TrashIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="3 6 5 6 21 6"/>
    <path d="M19 6v14a2 2 0 0 1-2 2H7a2 2 0 0 1-2-2V6m3 0V4a2 2 0 0 1 2-2h4a2 2 0 0 1 2 2v2"/>
    <line x1="10" y1="11" x2="10" y2="17"/>
    <line x1="14" y1="11" x2="14" y2="17"/>
  </svg>
);

function fmtSize(b) {
  if (!b) return '0 B';
  if (b >= 1e9) return (b / 1e9).toFixed(1) + ' GB';
  if (b >= 1e6) return (b / 1e6).toFixed(1) + ' MB';
  if (b >= 1e3) return (b / 1e3).toFixed(1) + ' KB';
  return b + ' B';
}

export default function CleanupView() {
  const [days, setDays] = useState(60);
  const [candidates, setCandidates] = useState(null);
  const [selected, setSelected] = useState(new Set());
  const [loading, setLoading] = useState(false);
  const listRef = useRef(null);
  const debounceRef = useRef(null);

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
      createToast('Cleanup preview failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    preview();
  }, []);

  useEffect(() => {
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      preview();
    }, 500);
    return () => clearTimeout(debounceRef.current);
  }, [days]);

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

  const handleCleanup = async () => {
    try {
      const result = await triggerCleanup(days, false, false);
      createToast(`Cleaned up ${result.processed} environments — freed ${fmtSize(result.freed_bytes)}`, 'success');
      setCandidates(null);
    } catch {
      createToast('Cleanup failed', 'error');
    }
  };

  const selectedSize = candidates
    ? candidates.filter(e => selected.has(e.id)).reduce((s, e) => s + (e.size_bytes || 0), 0)
    : 0;

  return (
    <div>
      <div className="cleanup-top">
        <div className="cleanup-threshold">
          <span style={{ fontSize: 'var(--text-xs)', color: 'var(--gray-9)', fontWeight: 500, textTransform: 'uppercase', letterSpacing: '0.05em' }}>
            Stale threshold
          </span>
          <input
            type="range"
            min="7"
            max="365"
            value={days}
            onChange={(e) => setDays(Number(e.target.value))}
          />
          <span className="cleanup-threshold-value">{days}d</span>
        </div>
        <button className="btn" onClick={preview} disabled={loading}>
          <SearchIcon /> {loading ? 'Analyzing...' : 'Preview'}
        </button>
      </div>

      {loading && (
        <div>
          {[...Array(6)].map((_, i) => (
            <div key={i} className="skeleton" style={{ height: '44px', marginBottom: '2px', borderRadius: 'var(--radius-sm)' }} />
          ))}
        </div>
      )}

      {candidates && candidates.length === 0 && (
        <div style={{ color: 'var(--green-11)', padding: 'var(--space-8) 0', textAlign: 'center', fontSize: 'var(--text-base)' }}>
          <div style={{ fontSize: 'var(--text-2xl)', marginBottom: 'var(--space-2)' }}>&#10003;</div>
          No stale environments found ({'>'} {days} days unused).
        </div>
      )}

      {candidates && candidates.length > 0 && (
        <>
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--space-2)',
            marginBottom: 'var(--space-4)',
            flexWrap: 'wrap',
          }}>
            <button className="btn" onClick={toggleAll}>
              {selected.size === candidates.length ? 'Deselect All' : 'Select All'}
            </button>
            <span style={{ fontSize: 'var(--text-xs)', color: 'var(--gray-9)' }}>
              {selected.size} of {candidates.length} selected
            </span>
          </div>

          <div ref={listRef}>
            {candidates.map((env, i) => (
              <label
                key={env.id}
                className="cleanup-item"
                style={{ animationDelay: `${i * 40}ms` }}
              >
                <input
                  type="checkbox"
                  checked={selected.has(env.id)}
                  onChange={() => toggle(env.id)}
                />
                <span className="ci-name">{env.project_name || env.path}</span>
                <span className="ci-lang">{env.language || 'unknown'}</span>
                <div style={{ width: '100px', flexShrink: 0 }}>
                  <SizeBar bytes={env.size_bytes} />
                </div>
                <span className="ci-meta">
                  {env.last_used_at
                    ? new Date(env.last_used_at).toLocaleDateString()
                    : 'never'}
                </span>
              </label>
            ))}
          </div>

          <div className="cleanup-footer">
            <div className="cleanup-footer-info">
              <strong>{selected.size} selected</strong> · <strong>{fmtSize(selectedSize)}</strong> reclaimable
            </div>
            <button className="btn btn-danger" onClick={handleCleanup} disabled={selected.size === 0}>
              <TrashIcon /> Clean Up
            </button>
          </div>

          <p style={{ color: 'var(--gray-9)', fontSize: 'var(--text-xs)', marginTop: 'var(--space-3)' }}>
            Cleanup is now available from the dashboard. Use <code style={{ color: 'var(--violet-9)', background: 'var(--violet-3)', padding: '2px 6px', borderRadius: 'var(--radius-xs)' }}>envs cleanup --stale {days} --dry-run</code> in terminal for a full preview.
          </p>
        </>
      )}

      {!loading && !candidates && (
        <p style={{ color: 'var(--gray-9)', textAlign: 'center', padding: 'var(--space-12) 0', fontSize: 'var(--text-sm)' }}>
          Adjust the stale threshold and click "Preview" to see which environments can be cleaned up.
        </p>
      )}
    </div>
  );
}
