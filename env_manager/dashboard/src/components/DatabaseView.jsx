import { useState, useEffect } from 'react';
import { fetchDbPath, backupDb, restoreDb, repairDb } from '../api';
import { createToast } from './Toast';

const HardDriveIcon = () => (
  <svg width="18" height="18" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="22" y1="12" x2="2" y2="12"/>
    <path d="M5.45 5.11L2 12v6a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2v-6l-3.45-6.89A2 2 0 0 0 16.76 4H7.24a2 2 0 0 0-1.79 1.11z"/>
    <line x1="6" y1="16" x2="6.01" y2="16"/>
    <line x1="10" y1="16" x2="10.01" y2="16"/>
  </svg>
);

const UploadIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="17 8 12 3 7 8"/>
    <line x1="12" y1="3" x2="12" y2="15"/>
  </svg>
);

const DownloadIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="7 10 12 15 17 10"/>
    <line x1="12" y1="15" x2="12" y2="3"/>
  </svg>
);

const WrenchIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M14.7 6.3a1 1 0 0 0 0 1.4l1.6 1.6a1 1 0 0 0 1.4 0l3.77-3.77a6 6 0 0 1-7.94 7.94l-6.91 6.91a2.12 2.12 0 0 1-3-3l6.91-6.91a6 6 0 0 1 7.94-7.94l-3.76 3.76z"/>
  </svg>
);

const inputStyle = {
  background: 'var(--gray-3)',
  border: '1px solid var(--gray-5)',
  color: 'var(--gray-12)',
  padding: '7px 10px',
  borderRadius: 'var(--radius-sm)',
  fontSize: 'var(--text-sm)',
  outline: 'none',
  width: '100%',
  boxSizing: 'border-box',
  transition: 'border-color var(--transition-fast)',
};

const cardStyle = {
  background: 'var(--gray-2)',
  border: '1px solid var(--gray-5)',
  borderRadius: 'var(--radius-md)',
  padding: 'var(--space-5)',
};

export default function DatabaseView() {
  const [dbPath, setDbPath] = useState(null);
  const [loading, setLoading] = useState(true);
  const [backupPath, setBackupPath] = useState('');
  const [restorePath, setRestorePath] = useState('');
  const [backingUp, setBackingUp] = useState(false);
  const [restoring, setRestoring] = useState(false);
  const [repairing, setRepairing] = useState(false);

  const load = () => {
    setLoading(true);
    fetchDbPath()
      .then((data) => setDbPath(data.path || data.db_path || ''))
      .catch(() => createToast('Failed to load DB path', 'error'))
      .finally(() => setLoading(false));
  };

  useEffect(() => { load(); }, []);

  const handleBackup = async () => {
    setBackingUp(true);
    try {
      const result = await backupDb(backupPath || null);
      createToast(`Backup created: ${result.path || result.backup_path || 'done'}`, 'success');
      setBackupPath('');
    } catch {
      createToast('Backup failed', 'error');
    } finally {
      setBackingUp(false);
    }
  };

  const handleRestore = async () => {
    if (!restorePath) { createToast('Enter a restore path', 'error'); return; }
    setRestoring(true);
    try {
      await restoreDb(restorePath);
      createToast('Database restored', 'success');
      setRestorePath('');
      load();
    } catch {
      createToast('Restore failed', 'error');
    } finally {
      setRestoring(false);
    }
  };

  const handleRepair = async () => {
    setRepairing(true);
    try {
      await repairDb();
      createToast('Database repair complete', 'success');
    } catch {
      createToast('Repair failed', 'error');
    } finally {
      setRepairing(false);
    }
  };

  return (
    <div>
      <div style={{ ...cardStyle, marginBottom: 'var(--space-5)' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)', marginBottom: 'var(--space-3)' }}>
          <HardDriveIcon />
          <h2 style={{ fontSize: 'var(--text-base)', fontWeight: 600, color: 'var(--gray-12)' }}>Database</h2>
        </div>
        <div style={{ fontSize: 'var(--text-sm)', color: 'var(--gray-9)' }}>
          Path:{' '}
          {loading ? (
            <span style={{ color: 'var(--gray-8)' }}>Loading...</span>
          ) : (
            <span style={{ fontFamily: 'var(--font-mono)', color: 'var(--gray-11)', fontSize: 'var(--text-xs)' }}>
              {dbPath || 'Not available'}
            </span>
          )}
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: 'var(--space-4)' }}>
        <div style={cardStyle}>
          <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--gray-12)', marginBottom: 'var(--space-3)' }}>Backup</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <div>
              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--gray-9)', marginBottom: 'var(--space-1)' }}>Destination Path (optional)</div>
              <input style={inputStyle} value={backupPath} onChange={(e) => setBackupPath(e.target.value)} placeholder="/path/to/backup.db" />
            </div>
            <button className="btn btn-primary" onClick={handleBackup} disabled={backingUp}>
              <UploadIcon /> <span>{backingUp ? 'Backing up...' : 'Backup'}</span>
            </button>
          </div>
        </div>

        <div style={cardStyle}>
          <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--gray-12)', marginBottom: 'var(--space-3)' }}>Restore</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <div>
              <div style={{ fontSize: 'var(--text-xs)', color: 'var(--gray-9)', marginBottom: 'var(--space-1)' }}>Backup File Path</div>
              <input style={inputStyle} value={restorePath} onChange={(e) => setRestorePath(e.target.value)} placeholder="/path/to/backup.db" />
            </div>
            <button className="btn btn-danger" onClick={handleRestore} disabled={restoring}>
              <DownloadIcon /> <span>{restoring ? 'Restoring...' : 'Restore'}</span>
            </button>
          </div>
        </div>

        <div style={cardStyle}>
          <h3 style={{ fontSize: 'var(--text-sm)', fontWeight: 600, color: 'var(--gray-12)', marginBottom: 'var(--space-3)' }}>Repair</h3>
          <p style={{ fontSize: 'var(--text-xs)', color: 'var(--gray-9)', marginBottom: 'var(--space-3)', lineHeight: 1.5 }}>
            Attempt to repair database corruption or inconsistencies.
          </p>
          <button className="btn btn-danger" onClick={handleRepair} disabled={repairing}>
            <WrenchIcon /> <span>{repairing ? 'Repairing...' : 'Repair'}</span>
          </button>
        </div>
      </div>
    </div>
  );
}
