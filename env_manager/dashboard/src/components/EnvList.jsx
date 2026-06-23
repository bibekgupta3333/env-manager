import { useState, useEffect, useMemo } from 'react';
import { fetchEnvs } from '../api';
import EnvDetail from './EnvDetail';
import StatusBadge from './StatusBadge';
import SizeBar from './SizeBar';
import EmptyState from './EmptyState';
import SearchInput from './SearchInput';
import { createToast } from './Toast';

const RefreshIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="23 4 23 10 17 10"/>
    <polyline points="1 20 1 14 7 14"/>
    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
  </svg>
);

const SearchIconSvg = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8"/>
    <line x1="21" y1="21" x2="16.65" y2="16.65"/>
  </svg>
);

export default function EnvList() {
  const [envs, setEnvs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [langFilter, setLangFilter] = useState('');
  const [selectedEnv, setSelectedEnv] = useState(null);

  const load = () => {
    setLoading(true);
    fetchEnvs()
      .then((data) => setEnvs(data.environments || []))
      .catch(() => createToast('Failed to load environments', 'error'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const languages = useMemo(() => {
    return [...new Set(envs.map((e) => e.language).filter(Boolean))].sort();
  }, [envs]);

  const filtered = useMemo(() => {
    let list = [...envs];
    if (search) {
      const q = search.toLowerCase();
      list = list.filter(
        (e) =>
          (e.project_name || '').toLowerCase().includes(q) ||
          (e.path || '').toLowerCase().includes(q),
      );
    }
    if (langFilter) {
      list = list.filter((e) => e.language === langFilter);
    }
    return list;
  }, [envs, search, langFilter]);

  return (
    <div>
      <div className="toolbar">
        <div style={{ width: '240px' }}>
          <SearchInput
            value={search}
            onChange={setSearch}
            placeholder="Search projects..."
          />
        </div>
        <select value={langFilter} onChange={(e) => setLangFilter(e.target.value)}>
          <option value="">All languages</option>
          {languages.map((l) => (
            <option key={l} value={l}>{l}</option>
          ))}
        </select>
        <button className="btn" onClick={load} title="Refresh">
          <RefreshIcon />
          Refresh
        </button>
      </div>

      {loading ? (
        <div>
          {[...Array(8)].map((_, i) => (
            <div key={i} className="skeleton" style={{ height: '40px', marginBottom: '2px', borderRadius: 'var(--radius-sm)' }} />
          ))}
        </div>
      ) : filtered.length === 0 ? (
        <EmptyState
          icon={<SearchIconSvg />}
          title="No environments found"
          description="Run envs scan to discover environments in your projects."
          action={envs.length === 0 ? undefined : { label: 'Clear filters', onClick: () => { setSearch(''); setLangFilter(''); } }}
        />
      ) : (
        <div className="table-wrap">
          <table>
            <colgroup>
              <col style={{ width: '20%' }} />
              <col style={{ width: '12%' }} />
              <col style={{ width: '10%' }} />
              <col style={{ width: '12%' }} />
              <col style={{ width: '10%' }} />
              <col style={{ width: '36%' }} />
            </colgroup>
            <thead>
              <tr>
                <th>Project</th>
                <th>Version</th>
                <th>Tool</th>
                <th>Size</th>
                <th>Health</th>
                <th>Path</th>
              </tr>
            </thead>
            <tbody>
              {filtered.map((env) => {
                const status = env.last_health_result || 'unchecked';
                return (
                  <tr
                    key={env.id}
                    className="clickable"
                    onClick={() => setSelectedEnv(env)}
                  >
                    <td style={{ fontWeight: 600, color: 'var(--gray-12)' }}>
                      {env.project_name || '-'}
                    </td>
                    <td style={{ fontFamily: 'var(--font-mono)', fontSize: 'var(--text-xs)', color: 'var(--gray-10)' }}>
                      {env.version || '-'}
                    </td>
                    <td style={{ fontSize: 'var(--text-xs)', color: 'var(--gray-10)', textTransform: 'capitalize' }}>
                      {env.tool || '-'}
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

      {selectedEnv && (
        <EnvDetail env={selectedEnv} onClose={() => setSelectedEnv(null)} />
      )}
    </div>
  );
}
