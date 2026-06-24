import { useState, useEffect } from 'react';
import { triggerDoctor } from '../api';
import StatusBadge from './StatusBadge';
import { createToast } from './Toast';

const HeartIcon = () => (
  <svg width="28" height="28" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M20.84 4.61a5.5 5.5 0 0 0-7.78 0L12 5.67l-1.06-1.06a5.5 5.5 0 0 0-7.78 7.78l1.06 1.06L12 21.23l7.78-7.78 1.06-1.06a5.5 5.5 0 0 0 0-7.78z"/>
  </svg>
);

export default function DoctorView() {
  const [results, setResults] = useState(null);
  const [loading, setLoading] = useState(true);
  const [hasRun, setHasRun] = useState(false);

  const runDoctor = async () => {
    setLoading(true);
    setHasRun(true);
    try {
      const data = await triggerDoctor();
      setResults(data.results || []);
    } catch {
      createToast('Doctor check failed', 'error');
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    runDoctor();
  }, []);
  const healthy = results ? results.filter((e) => e.status === 'healthy').length : 0;
  const broken = results ? results.filter((e) => e.status === 'broken').length : 0;
  const degraded = results ? results.filter((e) => e.status === 'degraded').length : 0;
  const unchecked = results ? results.filter((e) => !e.status || e.status === 'unchecked').length : 0;

  return (
    <div>
      <div className="doctor-hero">
        <div className="doctor-hero-icon">
          <HeartIcon />
        </div>
        <h2>Health Check</h2>
        <p>
          Run a health check across all environments to detect broken dependencies, missing packages, and configuration issues.
        </p>
        <button
          className="btn btn-primary"
          onClick={runDoctor}
          disabled={loading}
          style={{ padding: '10px 28px', fontSize: 'var(--text-base)', marginTop: 'var(--space-2)' }}
        >
          {loading ? (
            <>
              <span style={{
                display: 'inline-block',
                width: '14px',
                height: '14px',
                border: '2px solid rgba(255,255,255,0.3)',
                borderTopColor: '#fff',
                borderRadius: '50%',
                animation: 'spin 0.6s linear infinite',
                marginRight: 'var(--space-2)',
              }} />
              {results ? `Checking ${results.length} environments...` : 'Checking environments...'}
            </>
          ) : (
            <>
              <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round" style={{ marginRight: 'var(--space-2)' }}>
                <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
                <polyline points="22 4 12 14.01 9 11.01"/>
              </svg>
              Run Health Check
            </>
          )}
        </button>
        {loading && (
          <div className="progress-bar" style={{ marginTop: 'var(--space-3)' }}>
            <div className="progress-bar-fill" />
          </div>
        )}
      </div>

      {hasRun && results && (
        <>
          <div className="doctor-summary">
            <div className="doctor-summary-item">
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--green-9)' }} />
              <span className="doctor-summary-count">{healthy}</span>
              <span>healthy</span>
            </div>
            <div className="doctor-summary-item">
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--amber-9)' }} />
              <span className="doctor-summary-count">{degraded}</span>
              <span>degraded</span>
            </div>
            <div className="doctor-summary-item">
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--red-9)' }} />
              <span className="doctor-summary-count">{broken}</span>
              <span>broken</span>
            </div>
            <div className="doctor-summary-item">
              <span style={{ width: '8px', height: '8px', borderRadius: '50%', background: 'var(--gray-8)' }} />
              <span className="doctor-summary-count">{unchecked}</span>
              <span>unchecked</span>
            </div>
          </div>

          <div className="doctor-results">
            {results.map((env) => {
              const status = env.status || 'unchecked';
              const errorMsg = env.errors && env.errors.length > 0 ? env.errors[0] : null;
              return (
                <div key={env.env_id} className="doctor-card">
                  <div className="doctor-card-top">
                    <div className="doctor-card-name">
                      {env.project_name}
                    </div>
                    <StatusBadge status={status} size="sm" />
                  </div>
                  <div className="doctor-card-detail">
                    <span>{env.language} {env.version || ''}</span>
                  </div>
                  {status === 'broken' && errorMsg && (
                    <div className="doctor-card-error">
                      {errorMsg}
                    </div>
                  )}
                  {status === 'broken' && !errorMsg && (
                    <div className="doctor-card-suggestion">
                      Run <code style={{ background: 'var(--green-3)', padding: '1px 4px', borderRadius: '2px' }}>envs doctor --fix</code> to attempt repair
                    </div>
                  )}
                  {status === 'healthy' && (
                    <div className="doctor-card-suggestion">
                      All checks passed
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        </>
      )}

      {!loading && !hasRun && !results && (
        <p style={{ color: 'var(--gray-9)', textAlign: 'center', padding: 'var(--space-12) 0', fontSize: 'var(--text-sm)' }}>
          Click "Run Health Check" to check health of all environments.
        </p>
      )}
    </div>
  );
}
