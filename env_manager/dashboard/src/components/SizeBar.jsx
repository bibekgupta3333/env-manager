function fmtSize(b) {
  if (!b || b === 0) return '0 B';
  if (b >= 1e9) return (b / 1e9).toFixed(1) + ' GB';
  if (b >= 1e6) return (b / 1e6).toFixed(1) + ' MB';
  if (b >= 1e3) return (b / 1e3).toFixed(1) + ' KB';
  return b + ' B';
}

const DEFAULT_MAX = 5 * 1024 * 1024 * 1024;

export default function SizeBar({ bytes, max = DEFAULT_MAX }) {
  const pct = Math.min(100, Math.round((bytes || 0) / max * 100));
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--space-2)' }}>
      <div style={{
        flex: 1,
        height: '4px',
        borderRadius: '2px',
        background: 'var(--gray-5)',
        overflow: 'hidden',
        minWidth: '48px',
      }}>
        <div style={{
          height: '100%',
          borderRadius: '2px',
          background: pct > 80 ? 'var(--amber-9)'
                     : pct > 50 ? 'var(--violet-9)'
                     : 'var(--gray-8)',
          width: pct + '%',
          transition: 'width var(--transition-slow)',
        }} />
      </div>
      <span style={{
        fontSize: 'var(--text-xs)',
        color: 'var(--gray-10)',
        fontFamily: 'var(--font-mono)',
        whiteSpace: 'nowrap',
        minWidth: '52px',
        textAlign: 'right',
      }}>
        {fmtSize(bytes)}
      </span>
    </div>
  );
}
