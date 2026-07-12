'use client';

import { motion, useReducedMotion } from 'framer-motion';
import type { MetricRange } from '@/lib/derive';

// Displays each metric on a horizontal range with its average highlighted.
export function MetricRanges({ data, animateOnMount }: { data: MetricRange[]; animateOnMount?: boolean }) {
  const reduce = useReducedMotion();

  return (
    <div style={{ display: 'grid', gap: 18 }}>
      {data.map((m, i) => {

        // Calculate the total range and average marker position.
        const span = m.max - m.min || 1;
        const avgPct = ((m.avg - m.min) / span) * 100;

        return (
          <div key={m.label + i} style={{ display: 'grid', gap: 8 }}>

            {/* Metric title and average value */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 12 }}>
              <span style={{ fontWeight: 500, fontSize: 'var(--text-body-sm)', color: 'var(--graphite)' }}>{m.label}</span>
              <span style={{ fontSize: 'var(--text-caption)', color: 'var(--action-blue-ink)', fontVariantNumeric: 'tabular-nums' }}>
                avg {m.avg.toLocaleString()}
              </span>
            </div>

            {/* Horizontal benchmark track */}
            <div style={{ position: 'relative', height: 8, borderRadius: 999, background: 'var(--paper)' }}>

              {/* Animated range bar */}
              <motion.div
                style={{ position: 'absolute', inset: 0, borderRadius: 999, background: 'var(--silver)', transformOrigin: 'left' }}
                initial={reduce ? { scaleX: 1 } : { scaleX: 0 }}
                {...(animateOnMount
                  ? { animate: { scaleX: 1 } }
                  : { whileInView: { scaleX: 1 }, viewport: { once: true } })}
                transition={{ duration: 0.7, delay: 0.05 * i, ease: [0.22, 1, 0.36, 1] }}
              />

              {/* Animated marker showing the average position */}
              <motion.div
                style={{
                  position: 'absolute',
                  top: -3,
                  width: 14,
                  height: 14,
                  marginLeft: -7,
                  borderRadius: '50%',
                  background: 'var(--action-blue)',
                  border: '2px solid var(--white)',
                  boxShadow: 'var(--shadow-card)',
                }}
                initial={reduce ? { left: `${avgPct}%`, opacity: 1 } : { left: '0%', opacity: 0 }}
                {...(animateOnMount
                  ? { animate: { left: `${avgPct}%`, opacity: 1 } }
                  : { whileInView: { left: `${avgPct}%`, opacity: 1 }, viewport: { once: true } })}
                transition={{ duration: 0.8, delay: 0.05 * i + 0.15, ease: [0.22, 1, 0.36, 1] }}
              />
            </div>

            {/* Lowest and highest benchmark values */}
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 'var(--text-caption)', color: 'var(--slate)', fontVariantNumeric: 'tabular-nums' }}>
              <span>Lowest {m.min.toLocaleString()}</span>
              <span>Highest {m.max.toLocaleString()}</span>
            </div>

          </div>
        );
      })}
    </div>
  );
}
