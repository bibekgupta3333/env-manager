import { useState } from 'react';
import { fetchEnvs } from '../api';

export default function DoctorView({ showToast }) {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(false);

  const runDoctor = async () => {
    setLoading(true);
    try {
      const data = await fetchEnvs();
      setResults(data.environments || []);
    } catch {
      showToast?.('Doctor check failed');
    } finally {
      setLoading(false);
    }
  };

  const healthy = results ? results.filter((e) => e.last_health_result === 'healthy').length : 0;
  const broken = results ? results.filter((e) => e.last_health_result === 'broken').length : 0;
  const unknown = results ? results.length - healthy - broken : 0;

  return (
    <div>
      <h2>Doctor</h2>
      <div className="toolbar">
        <button className="primary" onClick={runDoctor} disabled={loading}>
          {loading ? 'Running...' : 'Run Doctor (All)'}
        </button>
      </div>

      {loading && <p className="loading">Running health checks...</p>}

      {results && (
        <>
          <div className="summary">
            <div className="card">
              <div className="num" style={{ color: 'var(--green)' }}>{healthy}</div>
              <div className="label">Healthy</div>
            </div>
            <div className="card">
              <div className="num" style={{ color: 'var(--red)' }}>{broken}</div>
              <div className="label">Broken</div>
            </div>
            <div className="card">
              <div className="num" style={{ color: 'var(--dim)' }}>{unknown}</div>
              <div className="label">Unknown</div>
            </div>
          </div>

          {results.length === 0 ? (
            <p className="loading">No environments to check.</p>
          ) : (
            <table>
              <thead>
                <tr>
                  <th>Project</th>
                  <th>Version</th>
                  <th>Status</th>
                </tr>
              </thead>
              <tbody>
                {results.map((env) => {
                  const status = env.last_health_result || 'unchecked';
                  return (
                    <tr key={env.id}>
                      <td>{env.project_name || env.path}</td>
                      <td>{env.language} {env.version}</td>
                      <td>
                        <span className={`badge ${status}`}>
                          {status === 'healthy' ? 'OK' : status === 'broken' ? 'BROKEN' : '-'}
                        </span>
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </>
      )}

      {!loading && !results && (
        <p className="loading">Click "Run Doctor" to check health of all environments.</p>
      )}
    </div>
  );
}
