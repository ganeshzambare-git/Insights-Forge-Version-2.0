'use client';

import { motion, useReducedMotion } from 'framer-motion';

export type Slice = { label: string; value: number; color: string };

type DonutChartProps = {
  data: Slice[];
  size?: number;
  thickness?: number;
  centerLabel?: string;
  centerValue?: string;
  showLegend?: boolean;
  animateOnMount?: boolean;
  ariaLabel?: string;
};

// Donut chart with animated SVG segments.
export function DonutChart({
  data,
  size = 200,
  thickness = 22,
  centerLabel,
  centerValue,
  showLegend = true,
  animateOnMount,
  ariaLabel,
}: DonutChartProps) {
  const reduce = useReducedMotion();

  // Calculate total value and SVG dimensions.
  const total = data.reduce((s, d) => s + d.value, 0) || 1;
  const r = (size - thickness) / 2;
  const c = 2 * Math.PI * r;
  const cx = size / 2;

  // Convert each data item into a drawable donut segment.
  let offset = 0;
  const segments = data.map((d) => {
    const frac = d.value / total;
    const seg = { ...d, frac, dash: frac * c, gapStart: offset * c };
    offset += frac;
    return seg;
  });

  return (
    <div style={{ display: 'flex', gap: 22, alignItems: 'center', flexWrap: 'wrap' }}>
      <svg width={size} height={size} viewBox={`0 0 ${size} ${size}`} role="img" aria-label={ariaLabel || 'Donut chart'}>

        {/* Background ring */}
        <circle cx={cx} cy={cx} r={r} fill="none" stroke="var(--paper)" strokeWidth={thickness} />

        {/* Rotate chart so drawing starts from the top */}
        <g transform={`rotate(-90 ${cx} ${cx})`}>
          {segments.map((s, i) => (
            <motion.circle
              key={s.label + i}
              cx={cx}
              cy={cx}
              r={r}
              fill="none"
              stroke={s.color}
              strokeWidth={thickness}
              strokeLinecap="butt"
              strokeDasharray={`${s.dash} ${c - s.dash}`}
              initial={reduce ? { strokeDashoffset: -s.gapStart } : { strokeDashoffset: -s.gapStart + s.dash }}
              {...(animateOnMount
                ? { animate: { strokeDashoffset: -s.gapStart } }
                : { whileInView: { strokeDashoffset: -s.gapStart }, viewport: { once: true } })}
              transition={{ duration: 0.85, delay: 0.1 * i, ease: [0.22, 1, 0.36, 1] }}
            />
          ))}
        </g>

        {/* Optional center text */}
        {(centerValue || centerLabel) && (
          <>
            <text x={cx} y={cx - 2} textAnchor="middle" fontSize="26" fontFamily="var(--font-display)" fontWeight="600" fill="var(--graphite)">
              {centerValue}
            </text>
            <text x={cx} y={cx + 18} textAnchor="middle" fontSize="12" fill="var(--slate)" fontFamily="var(--font-body)">
              {centerLabel}
            </text>
          </>
        )}
      </svg>

      {/* Optional legend with percentage values */}
      {showLegend && (
      <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'grid', gap: 10, minWidth: 140 }}>
        {segments.map((s, i) => (
          <li key={s.label + i} style={{ display: 'flex', alignItems: 'center', gap: 10, fontSize: 'var(--text-body-sm)' }}>
            <span style={{ width: 10, height: 10, borderRadius: 3, background: s.color, flexShrink: 0 }} />
            <span style={{ color: 'var(--graphite)', fontWeight: 500 }}>{s.label}</span>
            <span style={{ marginLeft: 'auto', color: 'var(--slate)', fontVariantNumeric: 'tabular-nums' }}>
              {/* Display percentage contribution of each slice */}
              {Math.round(s.frac * 100)}%
            </span>
          </li>
        ))}
      </ul>
      )}
    </div>
  );
}
