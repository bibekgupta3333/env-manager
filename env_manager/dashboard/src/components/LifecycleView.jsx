import { useState } from 'react';
import { triggerScan, createEnv, importSpec, exportSpec, cloneEnv } from '../api';
import { createToast } from './Toast';

const RefreshCwIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <polyline points="23 4 23 10 17 10"/>
    <polyline points="1 20 1 14 7 14"/>
    <path d="M3.51 9a9 9 0 0 1 14.85-3.36L23 10M1 14l4.64 4.36A9 9 0 0 0 20.49 15"/>
  </svg>
);

const PlusIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="12" y1="5" x2="12" y2="19"/>
    <line x1="5" y1="12" x2="19" y2="12"/>
  </svg>
);

const ImportIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="7 10 12 15 17 10"/>
    <line x1="12" y1="15" x2="12" y2="3"/>
  </svg>
);

const ExportIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/>
    <polyline points="17 8 12 3 7 8"/>
    <line x1="12" y1="3" x2="12" y2="15"/>
  </svg>
);

const CopyIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <rect x="9" y="9" width="13" height="13" rx="2" ry="2"/>
    <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"/>
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

const labelStyle = {
  fontSize: 'var(--text-xs)',
  color: 'var(--gray-9)',
  fontWeight: 500,
  marginBottom: 'var(--space-1)',
};

export default function LifecycleView() {
  const [scanning, setScanning] = useState(false);
  const [language, setLanguage] = useState('python');
  const [version, setVersion] = useState('');
  const [tool, setTool] = useState('');
  const [createPath, setCreatePath] = useState('');
  const [targetDir, setTargetDir] = useState('');
  const [importPath, setImportPath] = useState('');
  const [exportPath, setExportPath] = useState('');
  const [cloneSrc, setCloneSrc] = useState('');
  const [cloneDst, setCloneDst] = useState('');
  const [creating, setCreating] = useState(false);
  const [importing, setImporting] = useState(false);
  const [exporting, setExporting] = useState(false);
  const [cloning, setCloning] = useState(false);

  const handleScan = async () => {
    setScanning(true);
    try {
      await triggerScan();
      createToast('Scan triggered successfully', 'success');
    } catch {
      createToast('Scan failed', 'error');
    } finally {
      setScanning(false);
    }
  };

  const handleCreate = async () => {
    setCreating(true);
    try {
      await createEnv({ language, version, tool, path: createPath, target_directory: targetDir });
      createToast('Environment created', 'success');
      setVersion('');
      setTool('');
      setCreatePath('');
      setTargetDir('');
    } catch {
      createToast('Failed to create environment', 'error');
    } finally {
      setCreating(false);
    }
  };

  const handleImport = async () => {
    setImporting(true);
    try {
      await importSpec(importPath);
      createToast('Spec imported', 'success');
      setImportPath('');
    } catch {
      createToast('Failed to import spec', 'error');
    } finally {
      setImporting(false);
    }
  };

  const handleExport = async () => {
    setExporting(true);
    try {
      await exportSpec(exportPath);
      createToast('Spec exported', 'success');
      setExportPath('');
    } catch {
      createToast('Failed to export spec', 'error');
    } finally {
      setExporting(false);
    }
  };

  const handleClone = async () => {
    setCloning(true);
    try {
      await cloneEnv(cloneSrc, cloneDst);
      createToast('Environment cloned', 'success');
      setCloneSrc('');
      setCloneDst('');
    } catch {
      createToast('Failed to clone environment', 'error');
    } finally {
      setCloning(false);
    }
  };

  return (
    <div>
      <div className="toolbar">
        <button className="btn btn-primary" onClick={handleScan} disabled={scanning}>
          <RefreshCwIcon /> <span>{scanning ? 'Scanning...' : 'Scan'}</span>
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(340px, 1fr))', gap: 'var(--space-4)' }}>
        <div style={cardStyle}>
          <h3 style={{ fontSize: 'var(--text-base)', fontWeight: 600, color: 'var(--gray-12)', marginBottom: 'var(--space-4)' }}>
            <PlusIcon /> Create Environment
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <div>
              <div style={labelStyle}>Language</div>
              <select
                value={language}
                onChange={(e) => setLanguage(e.target.value)}
                style={{
                  ...inputStyle,
                  cursor: 'pointer',
                  appearance: 'none',
                  backgroundImage: 'url("data:image/svg+xml,%3Csvg xmlns=\'http://www.w3.org/2000/svg\' width=\'12\' height=\'12\' fill=\'%23707078\'%3E%3Cpath d=\'M3 5l3 3 3-3\'/%3E%3C/svg%3E")',
                  backgroundRepeat: 'no-repeat',
                  backgroundPosition: 'right 10px center',
                }}
              >
                <option value="python">Python</option>
                <option value="node">Node</option>
                <option value="ruby">Ruby</option>
                <option value="go">Go</option>
                <option value="rust">Rust</option>
              </select>
            </div>
            <div>
              <div style={labelStyle}>Version</div>
              <input style={inputStyle} value={version} onChange={(e) => setVersion(e.target.value)} placeholder="e.g. 3.11" />
            </div>
            <div>
              <div style={labelStyle}>Tool</div>
              <input style={inputStyle} value={tool} onChange={(e) => setTool(e.target.value)} placeholder="e.g. venv, pipenv" />
            </div>
            <div>
              <div style={labelStyle}>Path</div>
              <input style={inputStyle} value={createPath} onChange={(e) => setCreatePath(e.target.value)} placeholder="/path/to/project" />
            </div>
            <div>
              <div style={labelStyle}>Target Directory</div>
              <input style={inputStyle} value={targetDir} onChange={(e) => setTargetDir(e.target.value)} placeholder="e.g. .venv" />
            </div>
            <button className="btn btn-primary" onClick={handleCreate} disabled={creating}>
              <PlusIcon /> <span>{creating ? 'Creating...' : 'Create'}</span>
            </button>
          </div>
        </div>

        <div style={cardStyle}>
          <h3 style={{ fontSize: 'var(--text-base)', fontWeight: 600, color: 'var(--gray-12)', marginBottom: 'var(--space-4)' }}>
            <ImportIcon /> Import Spec
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <div>
              <div style={labelStyle}>File Path</div>
              <input style={inputStyle} value={importPath} onChange={(e) => setImportPath(e.target.value)} placeholder="/path/to/spec.yml" />
            </div>
            <button className="btn btn-primary" onClick={handleImport} disabled={importing}>
              <ImportIcon /> <span>{importing ? 'Importing...' : 'Import'}</span>
            </button>
          </div>
        </div>

        <div style={cardStyle}>
          <h3 style={{ fontSize: 'var(--text-base)', fontWeight: 600, color: 'var(--gray-12)', marginBottom: 'var(--space-4)' }}>
            <ExportIcon /> Export Spec
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <div>
              <div style={labelStyle}>Project Path</div>
              <input style={inputStyle} value={exportPath} onChange={(e) => setExportPath(e.target.value)} placeholder="/path/to/project" />
            </div>
            <button className="btn btn-primary" onClick={handleExport} disabled={exporting}>
              <ExportIcon /> <span>{exporting ? 'Exporting...' : 'Export'}</span>
            </button>
          </div>
        </div>

        <div style={cardStyle}>
          <h3 style={{ fontSize: 'var(--text-base)', fontWeight: 600, color: 'var(--gray-12)', marginBottom: 'var(--space-4)' }}>
            <CopyIcon /> Clone
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--space-3)' }}>
            <div>
              <div style={labelStyle}>Source Path</div>
              <input style={inputStyle} value={cloneSrc} onChange={(e) => setCloneSrc(e.target.value)} placeholder="/path/to/source" />
            </div>
            <div>
              <div style={labelStyle}>Destination Path</div>
              <input style={inputStyle} value={cloneDst} onChange={(e) => setCloneDst(e.target.value)} placeholder="/path/to/destination" />
            </div>
            <button className="btn btn-primary" onClick={handleClone} disabled={cloning}>
              <CopyIcon /> <span>{cloning ? 'Cloning...' : 'Clone'}</span>
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
