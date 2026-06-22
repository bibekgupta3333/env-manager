const API = '/api';

export async function fetchEnvs(language, state) {
  const params = new URLSearchParams();
  if (language) params.set('language', language);
  if (state) params.set('state', state);
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

export function connectWS(onMessage) {
  const proto = location.protocol === 'https:' ? 'wss:' : 'ws:';
  const ws = new WebSocket(`${proto}//${location.host}/ws/events`);
  ws.onmessage = (e) => onMessage(JSON.parse(e.data));
  ws.onclose = () => {
    setTimeout(() => connectWS(onMessage), 5000);
  };
  return ws;
}
