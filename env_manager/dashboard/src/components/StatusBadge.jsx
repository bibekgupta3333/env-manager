const STATUS_COLORS = {
  healthy:  { dot: 'var(--green-9)',  bg: 'var(--green-3)',  text: 'var(--green-11)' },
  degraded: { dot: 'var(--amber-9)',  bg: 'var(--amber-3)',  text: 'var(--amber-11)' },
  broken:   { dot: 'var(--red-9)',    bg: 'var(--red-3)',    text: 'var(--red-11)' },
  stale:    { dot: 'var(--amber-9)',  bg: 'var(--amber-3)',  text: 'var(--amber-11)' },
  orphaned: { dot: 'var(--red-9)',    bg: 'var(--red-3)',    text: 'var(--red-11)' },
  unchecked:{ dot: 'var(--gray-9)',   bg: 'var(--gray-5)',   text: 'var(--gray-10)' },
  unknown:  { dot: 'var(--gray-9)',   bg: 'var(--gray-5)',   text: 'var(--gray-10)' },
};

export default function StatusBadge({ status = 'unchecked', size = 'md' }) {
  const colors = STATUS_COLORS[status] || STATUS_COLORS.unchecked;
  const isSm = size === 'sm';
  return (
    <span style={{
      display: 'inline-flex',
      alignItems: 'center',
      gap: isSm ? '4px' : '5px',
      padding: isSm ? '1px 7px' : '3px 10px',
      borderRadius: '20px',
      fontSize: isSm ? 'var(--text-xs)' : 'var(--text-xs)',
      fontWeight: 550,
      textTransform: 'capitalize',
      background: colors.bg,
      color: colors.text,
      lineHeight: isSm ? '18px' : '20px',
    }}>
      <span style={{
        width: isSm ? '6px' : '7px',
        height: isSm ? '6px' : '7px',
        borderRadius: '50%',
        background: colors.dot,
        flexShrink: 0,
      }} />
      {status}
    </span>
  );
}
