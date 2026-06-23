import { useState, useCallback, useEffect, useRef } from 'react';
import Sidebar from './components/Sidebar';
import Dashboard from './components/Dashboard';
import EnvList from './components/EnvList';
import DoctorView from './components/DoctorView';
import CleanupView from './components/CleanupView';
import SnapshotsView from './components/SnapshotsView';
import { createToast } from './components/Toast';
import { connectWS } from './api';
import './App.css';

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
  const [collapsed, setCollapsed] = useState(false);
  const [tabSwitching, setTabSwitching] = useState(false);
  const tabTimerRef = useRef(null);

  const onWsMessage = useCallback((data) => {
    if (data.event === 'scan') {
      createToast('Scan complete — refreshing data', 'success');
    }
  }, []);

  const handleTabChange = useCallback((tab) => {
    if (tab === activeTab) return;
    setTabSwitching(true);
    setActiveTab(tab);
  }, [activeTab]);

  useEffect(() => {
    clearTimeout(tabTimerRef.current);
    tabTimerRef.current = setTimeout(() => setTabSwitching(false), 350);
    return () => clearTimeout(tabTimerRef.current);
  }, [activeTab]);

  useEffect(() => {
    const ws = connectWS(onWsMessage);
    ws.onopen = () => setWsStatus('connected');
    ws.onclose = () => setWsStatus('disconnected');
    return () => ws.close();
  }, [onWsMessage]);

  const TabComponent = TABS[activeTab] || Dashboard;

  return (
    <>
      <Sidebar
        activeTab={activeTab}
        onTabChange={handleTabChange}
        wsStatus={wsStatus}
        collapsed={collapsed}
        onToggle={() => setCollapsed(v => !v)}
      />
      <main className={`main-content${collapsed ? ' expanded' : ''}`}>
        <div className="page-wrap">
          <div key={activeTab} className={`page-enter${tabSwitching ? ' page-loading' : ''}`}>
            <TabComponent />
          </div>
        </div>
      </main>
    </>
  );
}
