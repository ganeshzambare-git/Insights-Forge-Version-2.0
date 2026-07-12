'use client';

import { motion, useReducedMotion } from 'framer-motion';
import type { Point } from './LineChart';

type HistogramProps = {
  data: Point[];
  color?: string;
  height?: number;
  animateOnMount?: boolean;
  ariaLabel?: string;
};

// Vertical distribution bars that grow up from the baseline, with a light stagger.
export function Histogram({ data, color = 'var(--c-primary)', height = 150, animateOnMount, ariaLabel }: HistogramProps) {
  const reduce = useReducedMotion();
  const max = Math.max(...data.map((d) => d.value), 1);
  const labelEvery = Math.ceil(data.length / 8);

  return (
    <div role="img" aria-label={ariaLabel || 'Distribution histogram'}>
      <div style={{ display: 'flex', alignItems: 'flex-end', gap: 4, height }}>
        {data.map((d, i) => (
          <div key={i} style={{ flex: 1, height: '100%', display: 'flex', alignItems: 'flex-end' }} title={`${d.label}: ${d.value}`}>
            <motion.div
              style={{ width: '100%', background: color, borderRadius: '4px 4px 0 0', minHeight: 2 }}
              initial={reduce ? { height: `${(d.value / max) * 100}%` } : { height: 0 }}
              {...(animateOnMount
                ? { animate: { height: `${(d.value / max) * 100}%` } }
                : { whileInView: { height: `${(d.value / max) * 100}%` }, viewport: { once: true } })}
              transition={{ duration: 0.7, delay: 0.03 * i, ease: [0.22, 1, 0.36, 1] }}
            />
          </div>
        ))}
      </div>
      <div style={{ display: 'flex', gap: 4, marginTop: 6 }}>
        {data.map((d, i) => (
          <div key={i} style={{ flex: 1, textAlign: 'center', fontSize: 10, color: 'var(--slate)', fontVariantNumeric: 'tabular-nums' }}>
            {i % labelEvery === 0 ? d.label : ''}
          </div>
        ))}
      </div>
    </div>
  );
}
