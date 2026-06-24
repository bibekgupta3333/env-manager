export default function EmptyState({ icon, title, description, action }) {
  return (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      alignItems: 'center',
      justifyContent: 'center',
      padding: 'var(--space-12) var(--space-6)',
      textAlign: 'center',
      gap: 'var(--space-3)',
    }}>
      {icon && (
        <div style={{
          width: '48px',
          height: '48px',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          borderRadius: '50%',
          background: 'var(--gray-4)',
          color: 'var(--gray-9)',
        }}>
          {icon}
        </div>
      )}
      {title && (
        <div style={{
          fontSize: 'var(--text-base)',
          fontWeight: 600,
          color: 'var(--gray-11)',
        }}>
          {title}
        </div>
      )}
      {description && (
        <div style={{
          fontSize: 'var(--text-sm)',
          color: 'var(--gray-9)',
          maxWidth: '360px',
          lineHeight: 1.5,
        }}>
          {description}
        </div>
      )}
      {action && (
        <button
          onClick={action.onClick}
          style={{
            marginTop: 'var(--space-2)',
            background: 'var(--violet-9)',
            color: '#fff',
            border: 'none',
            padding: '8px 18px',
            borderRadius: 'var(--radius-sm)',
            fontSize: 'var(--text-sm)',
            fontWeight: 500,
            cursor: 'pointer',
            transition: 'background var(--transition-fast)',
          }}
          onMouseEnter={e => e.currentTarget.style.background = 'var(--violet-10)'}
          onMouseLeave={e => e.currentTarget.style.background = 'var(--violet-9)'}
        >
          {action.label}
        </button>
      )}
    </div>
  );
}
