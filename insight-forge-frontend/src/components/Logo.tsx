type LogoProps = { showText?: boolean; onDark?: boolean };

// Monochrome mark: three ascending bars (the "forge" turning data into signal).
export function Logo({ showText = true, onDark = false }: LogoProps) {
  const bar = onDark ? 'var(--white)' : 'var(--graphite)';
  const text = onDark ? 'var(--white)' : 'var(--graphite)';
  return (
    <span style={{ display: 'inline-flex', alignItems: 'center', gap: 9 }}>
      <svg width="26" height="26" viewBox="0 0 26 26" aria-hidden="true">
        <rect x="2" y="15" width="5" height="9" rx="1.5" fill={bar} />
        <rect x="10.5" y="9" width="5" height="15" rx="1.5" fill={bar} />
        <rect x="19" y="3" width="5" height="21" rx="1.5" fill="var(--action-blue)" />
      </svg>
      {showText && (
        <span
          style={{
            fontFamily: 'var(--font-display)',
            fontWeight: 600,
            fontSize: 17,
            letterSpacing: '-0.02em',
            color: text,
          }}
        >
          Insight&nbsp;Forge
        </span>
      )}
    </span>
  );
}
