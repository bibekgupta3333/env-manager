import { createRoot } from 'react-dom/client';
import { useEffect, useState, useCallback } from 'react';

const TOAST_TYPES = {
  success: { bg: 'var(--green-3)', border: 'var(--green-9)', text: 'var(--green-11)', icon: 'check' },
  error:   { bg: 'var(--red-3)',   border: 'var(--red-9)',   text: 'var(--red-11)',   icon: 'alert' },
  info:    { bg: 'var(--violet-3)',border: 'var(--violet-9)',text: 'var(--violet-11)',icon: 'info' },
};

const CheckIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <path d="M22 11.08V12a10 10 0 1 1-5.93-9.14"/>
    <polyline points="22 4 12 14.01 9 11.01"/>
  </svg>
);

const AlertIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <line x1="12" y1="8" x2="12" y2="12"/>
    <line x1="12" y1="16" x2="12.01" y2="16"/>
  </svg>
);

const InfoIcon = () => (
  <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="12" cy="12" r="10"/>
    <line x1="12" y1="16" x2="12" y2="12"/>
    <line x1="12" y1="8" x2="12.01" y2="8"/>
  </svg>
);

const iconMap = { check: CheckIcon, alert: AlertIcon, info: InfoIcon };

function ToastItem({ message, type = 'info', onDone }) {
  const [visible, setVisible] = useState(false);
  useEffect(() => {
    requestAnimationFrame(() => setVisible(true));
    const t = setTimeout(() => {
      setVisible(false);
      setTimeout(onDone, 300);
    }, 3700);
    return () => clearTimeout(t);
  }, [onDone]);

  const t = TOAST_TYPES[type] || TOAST_TYPES.info;
  const Icon = iconMap[t.icon];

  return (
    <div style={{
      background: t.bg,
      border: `1px solid ${t.border}`,
      color: t.text,
      padding: '10px 16px',
      borderRadius: 'var(--radius-md)',
      fontSize: 'var(--text-sm)',
      fontWeight: 500,
      display: 'flex',
      alignItems: 'center',
      gap: 'var(--space-2)',
      boxShadow: 'var(--shadow-lg)',
      pointerEvents: 'auto',
      opacity: visible ? 1 : 0,
      transform: visible ? 'translateY(0) scale(1)' : 'translateY(8px) scale(0.97)',
      transition: 'all var(--transition-slow)',
    }}>
      <Icon />
      {message}
    </div>
  );
}

let _toastContainer = null;
let _toasts = [];
let _setToasts = null;

function ToastContainer() {
  const [toasts, setToasts] = useState([]);
  _setToasts = setToasts;
  _toasts = toasts;

  const remove = useCallback((id) => {
    setToasts(prev => prev.filter(t => t.id !== id));
  }, []);

  if (toasts.length === 0) return null;

  return (
    <div style={{
      position: 'fixed',
      bottom: '24px',
      right: '24px',
      zIndex: 1000,
      display: 'flex',
      flexDirection: 'column',
      gap: 'var(--space-2)',
      pointerEvents: 'none',
    }}>
      {toasts.map(t => (
        <ToastItem key={t.id} message={t.message} type={t.type} onDone={() => remove(t.id)} />
      ))}
    </div>
  );
}

let _id = 0;

export function createToast(message, type = 'info') {
  if (!_toastContainer) {
    const el = document.createElement('div');
    el.id = 'toast-root';
    document.body.appendChild(el);
    const root = createRoot(el);
    root.render(<ToastContainer />);
    _toastContainer = true;
  }

  setTimeout(() => {
    const id = ++_id;
    _setToasts?.(prev => [...prev, { id, message, type }]);
  }, 0);
}
