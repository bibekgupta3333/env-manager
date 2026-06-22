import { useState, useCallback, useEffect } from 'react';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import EnvList from './components/EnvList';
import DoctorView from './components/DoctorView';
import CleanupView from './components/CleanupView';
import SnapshotsView from './components/SnapshotsView';
import { connectWS } from './api';

const TABS = {
  dashboard: Dashboard,
  environments: EnvList,
  doctor: DoctorView,
  cleanup: CleanupView,
  snapshots: SnapshotsView,
};

export default function App() {
  const [activeTab, setActiveTab] = useState('dashboard');
  const [wsStatus, setWsStatus] = useState('connecting');
  const [toast, setToast] = useState(null);

  const showToast = useCallback((msg, dur = 3000) => {
    setToast(msg);
    setTimeout(() => setToast(null), dur);
  }, []);

  const onWsMessage = useCallback((data) => {
    if (data.event === 'scan') {
      showToast('Scan complete — refreshing data');
    }
  }, [showToast]);

  useEffect(() => {
    const ws = connectWS(onWsMessage);
    ws.onopen = () => setWsStatus('connected');
    ws.onclose = () => setWsStatus('disconnected');
    return () => ws.close();
  }, [onWsMessage]);

  const TabComponent = TABS[activeTab] || Dashboard;

  return (
    <>
      <Sidebar activeTab={activeTab} onTabChange={setActiveTab} wsStatus={wsStatus} />
      <main className="main-content">
        <TabComponent showToast={showToast} />
      </main>
      {toast && <div className="toast">{toast}</div>}
    </>
  );
}
