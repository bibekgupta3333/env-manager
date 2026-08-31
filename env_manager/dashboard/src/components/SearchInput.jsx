const SearchIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <circle cx="11" cy="11" r="8"/>
    <line x1="21" y1="21" x2="16.65" y2="16.65"/>
  </svg>
);

const CloseIcon = () => (
  <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
    <line x1="18" y1="6" x2="6" y2="18"/>
    <line x1="6" y1="6" x2="18" y2="18"/>
  </svg>
);

export default function SearchInput({ value, onChange, placeholder = 'Search...' }) {
  return (
    <div style={{ position: 'relative', display: 'flex', alignItems: 'center' }}>
      <span style={{
        position: 'absolute',
        left: '10px',
        color: 'var(--gray-9)',
        display: 'flex',
        pointerEvents: 'none',
      }}>
        <SearchIcon />
      </span>
      <input
        type="text"
        placeholder={placeholder}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        style={{
          background: 'var(--gray-3)',
          border: '1px solid var(--gray-5)',
          color: 'var(--gray-12)',
          padding: '7px 32px 7px 32px',
          borderRadius: 'var(--radius-sm)',
          fontSize: 'var(--text-sm)',
          outline: 'none',
          width: '100%',
          boxSizing: 'border-box',
          transition: 'border-color var(--transition-fast)',
        }}
        onFocus={e => e.currentTarget.style.borderColor = 'var(--violet-9)'}
        onBlur={e => e.currentTarget.style.borderColor = 'var(--gray-5)'}
      />
      {value && (
        <button
          onClick={() => onChange('')}
          style={{
            position: 'absolute',
            right: '6px',
            background: 'none',
            border: 'none',
            color: 'var(--gray-8)',
            cursor: 'pointer',
            display: 'flex',
            padding: '2px',
            borderRadius: 'var(--radius-xs)',
          }}
          onMouseEnter={e => e.currentTarget.style.color = 'var(--gray-11)'}
          onMouseLeave={e => e.currentTarget.style.color = 'var(--gray-8)'}
        >
          <CloseIcon />
        </button>
      )}
    </div>
  );
}
