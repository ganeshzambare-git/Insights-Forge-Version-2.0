'use client';

import { motion, useReducedMotion } from 'framer-motion';

export type Bar = { label: string; value: number; sub?: string };

type BarChartProps = {
  data: Bar[];
  color?: string;
  unit?: string;
  animateOnMount?: boolean;
  ariaLabel?: string;
};

// Horizontal bars that grow from the left with a staggered reveal.
// Horizontal keeps long category labels readable — the common product case.
export function BarChart({ data, color = 'var(--c-primary)', unit = '', animateOnMount, ariaLabel }: BarChartProps) {
  const reduce = useReducedMotion();
  const max = Math.max(...data.map((d) => d.value), 1);

  return (
    <div role="img" aria-label={ariaLabel || 'Bar chart'} style={{ display: 'grid', gap: 14 }}>
      {data.map((d, i) => {
        const pct = Math.max(2, (d.value / max) * 100);
        return (
          <div key={d.label + i} style={{ display: 'grid', gap: 6 }}>
            <div
              style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'baseline',
                gap: 12,
                fontSize: 'var(--text-body-sm)',
              }}
            >
              <span style={{ color: 'var(--graphite)', fontWeight: 500 }}>{d.label}</span>
              <span style={{ color: 'var(--slate)', fontVariantNumeric: 'tabular-nums' }}>
                {d.value.toLocaleString()}
                {unit}
                {d.sub ? <span style={{ color: 'var(--stone)' }}> · {d.sub}</span> : null}
              </span>
            </div>
            <div
              style={{
                height: 10,
                borderRadius: 999,
                background: 'var(--paper)',
                overflow: 'hidden',
              }}
            >
              <motion.div
                style={{ height: '100%', borderRadius: 999, background: color, transformOrigin: 'left' }}
                initial={reduce ? { width: `${pct}%` } : { width: 0 }}
                {...(animateOnMount
                  ? { animate: { width: `${pct}%` } }
                  : { whileInView: { width: `${pct}%` }, viewport: { once: true } })}
                transition={{ duration: 0.9, delay: 0.08 * i, ease: [0.22, 1, 0.36, 1] }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
