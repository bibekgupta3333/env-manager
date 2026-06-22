import { useState, useEffect, useMemo } from 'react';
import { fetchEnvs } from '../api';
import EnvDetail from './EnvDetail';

function fmtSize(b) {
  if (!b) return '0 B';
  if (b >= 1e9) return (b / 1e9).toFixed(1) + ' GB';
  if (b >= 1e6) return (b / 1e6).toFixed(1) + ' MB';
  if (b >= 1e3) return (b / 1e3).toFixed(1) + ' KB';
  return b + ' B';
}

function trunc(s, len) {
  if (!s) return '-';
  return s.length > len ? s.slice(0, len) + '...' : s;
}

export default function EnvList({ showToast }) {
  const [envs, setEnvs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [langFilter, setLangFilter] = useState('');
  const [sortKey, setSortKey] = useState('project_name');
  const [sortDir, setSortDir] = useState('asc');
  const [selectedEnv, setSelectedEnv] = useState(null);

  const load = () => {
    setLoading(true);
    fetchEnvs()
      .then((data) => setEnvs(data.environments || []))
      .catch(() => showToast?.('Failed to load environments'))
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
    list.sort((a, b) => {
      const va = a[sortKey] ?? '';
      const vb = b[sortKey] ?? '';
      const cmp = String(va).localeCompare(String(vb));
      return sortDir === 'asc' ? cmp : -cmp;
    });
    return list;
  }, [envs, search, langFilter, sortKey, sortDir]);

  const handleHeaderClick = (key) => {
    if (sortKey === key) {
      setSortDir((d) => (d === 'asc' ? 'desc' : 'asc'));
    } else {
      setSortKey(key);
      setSortDir('asc');
    }
  };

  return (
    <div>
      <h2>Environments</h2>
      <div className="toolbar">
        <input
          type="text"
          placeholder="Search..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
        />
        <select value={langFilter} onChange={(e) => setLangFilter(e.target.value)}>
          <option value="">All languages</option>
          {languages.map((l) => (
            <option key={l} value={l}>{l}</option>
          ))}
        </select>
        <button onClick={load}>Refresh</button>
      </div>

      {loading ? (
        <p className="loading">Loading...</p>
      ) : filtered.length === 0 ? (
        <p className="loading">No environments found. Run `envs scan` first.</p>
      ) : (
        <table>
          <thead>
            <tr>
              <th onClick={() => handleHeaderClick('project_name')} style={{ cursor: 'pointer' }}>
                Project {sortKey === 'project_name' ? (sortDir === 'asc' ? '^' : 'v') : ''}
              </th>
              <th onClick={() => handleHeaderClick('language')} style={{ cursor: 'pointer' }}>
                Version {sortKey === 'language' ? (sortDir === 'asc' ? '^' : 'v') : ''}
              </th>
              <th>Tool</th>
              <th onClick={() => handleHeaderClick('size_bytes')} style={{ cursor: 'pointer' }}>
                Size {sortKey === 'size_bytes' ? (sortDir === 'asc' ? '^' : 'v') : ''}
              </th>
              <th>Health</th>
              <th>Path</th>
            </tr>
          </thead>
          <tbody>
            {filtered.map((env) => (
              <tr
                key={env.id}
                className="clickable"
                onClick={() => setSelectedEnv(env)}
              >
                <td style={{ color: 'var(--accent)' }}>{env.project_name || '-'}</td>
                <td>{env.language} {env.version || ''}</td>
                <td>{env.tool || '-'}</td>
                <td>{fmtSize(env.size_bytes)}</td>
                <td>
                  <span className={`badge ${env.last_health_result || 'unchecked'}`}>
                    {env.last_health_result || 'unchecked'}
                  </span>
                </td>
                <td style={{ color: 'var(--dim)', fontSize: '11px' }}>
                  {trunc(env.path, 40)}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      {selectedEnv && (
        <EnvDetail env={selectedEnv} onClose={() => setSelectedEnv(null)} showToast={showToast} />
      )}
    </div>
  );
}
