const API = '/api';

export async function fetchEnvs(language, state, envType) {
  const params = new URLSearchParams();
  if (language) params.set('language', language);
  if (state) params.set('state', state);
  if (envType) params.set('env_type', envType);
  const qs = params.toString();
  const url = qs ? `${API}/envs/?${qs}` : `${API}/envs/`;
  const r = await fetch(url);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function fetchEnv(envId) {
  const r = await fetch(`${API}/envs/${envId}`);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function fetchPlugins() {
  const r = await fetch(`${API}/plugins/`);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function fetchSnapshots() {
  const r = await fetch(`${API}/snapshots/`);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function fetchStatus() {
  const r = await fetch(`${API}/status`);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function triggerDoctor() {
  const r = await fetch('/api/doctor/run', { method: 'POST' });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function triggerDoctorFix() {
  const r = await fetch('/api/doctor/fix', { method: 'POST' });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function installPackage(envId, packages) {
  const r = await fetch(`/api/envs/${envId}/install`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ packages }),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function pinEnv(envId) {
  const r = await fetch(`/api/envs/${envId}/pin`, { method: 'POST' });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function unpinEnv(envId) {
  const r = await fetch(`/api/envs/${envId}/unpin`, { method: 'POST' });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function removeEnv(envId, snapshot = false) {
  const r = await fetch(`/api/envs/${envId}/remove`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ snapshot }),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function restoreEnv(envId) {
  const r = await fetch(`/api/envs/${envId}/restore`, { method: 'POST' });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function triggerCleanup(staleDays, orphaned, snapshot) {
  const r = await fetch('/api/cleanup/execute', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ stale_days: staleDays, orphaned, snapshot }),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function triggerGc() {
  const r = await fetch('/api/cleanup/gc', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ dry_run: false }),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function restoreSnapshot(snapshotId) {
  const r = await fetch(`/api/snapshots/${snapshotId}/restore`, { method: 'POST' });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function pruneSnapshots(keep = 5) {
  const r = await fetch('/api/snapshots/prune', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ keep }),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function trackPath(path) {
  const r = await fetch('/api/track', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path }),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function ignorePath(path) {
  const r = await fetch('/api/ignore', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path }),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function triggerScan() {
  const r = await fetch(`${API}/scan`, { method: 'POST' });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function fetchDbPath() {
  const r = await fetch(`${API}/db/path`);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function backupDb(path) {
  const r = await fetch(`${API}/db/backup`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path: path || null }),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function restoreDb(path) {
  const r = await fetch(`${API}/db/restore`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path }),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function repairDb() {
  const r = await fetch(`${API}/db/repair`, { method: 'POST' });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function fetchConfig() {
  const r = await fetch(`${API}/config`);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function fetchVersions() {
  const r = await fetch(`${API}/versions`);
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export function connectWS(onMessage) {
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const ws = new WebSocket(`${proto}//${location.host}/ws/events`);
  ws.onmessage = (e) => onMessage(JSON.parse(e.data));
  return ws;
}

export async function createEnv(body) {
  const r = await fetch(`${API}/envs/`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(body),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function importSpec(path) {
  const r = await fetch(`${API}/specs/import`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path }),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function exportSpec(path) {
  const r = await fetch(`${API}/specs/export`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ path }),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function cloneEnv(src, dest) {
  const r = await fetch(`${API}/envs/clone`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ source: src, destination: dest }),
  });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function enablePlugin(name) {
  const r = await fetch(`${API}/plugins/${name}/enable`, { method: 'POST' });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}

export async function disablePlugin(name) {
  const r = await fetch(`${API}/plugins/${name}/disable`, { method: 'POST' });
  if (!r.ok) throw new Error(`HTTP ${r.status}`);
  return r.json();
}
