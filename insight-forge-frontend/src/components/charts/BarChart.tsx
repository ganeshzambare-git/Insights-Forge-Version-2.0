'use client';

// Framer Motion is used for smooth bar animations.
// useReducedMotion respects accessibility settings for users who prefer less animation.
import { motion, useReducedMotion } from 'framer-motion';

// Represents a single bar item.
export type Bar = { label: string; value: number; sub?: string };

// Props accepted by the BarChart component.
type BarChartProps = {
  data: Bar[];
  color?: string;
  unit?: string;
  animateOnMount?: boolean;
  ariaLabel?: string;
};

// Horizontal bars that grow from the left with a staggered reveal.
// Horizontal layout keeps long category labels readable.
export function BarChart({ data, color = 'var(--c-primary)', unit = '', animateOnMount, ariaLabel }: BarChartProps) {

  // Disable animations if the user has enabled "Reduce Motion"
  // in their operating system accessibility settings.
  const reduce = useReducedMotion();

  // Find the largest value.
  // Used to normalize every bar width into a percentage.
  const max = Math.max(...data.map((d) => d.value), 1);

  return (
    <div role="img" aria-label={ariaLabel || 'Bar chart'} style={{ display: 'grid', gap: 14 }}>
      {data.map((d, i) => {

        // Convert the current value into a percentage
        // while keeping a minimum visible width of 2%.
        const pct = Math.max(2, (d.value / max) * 100);

        return (
          <div key={d.label + i} style={{ display: 'grid', gap: 6 }}>

            {/* Bar label and corresponding value */}
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

              {/* Display formatted value with optional unit and subtitle */}
              <span style={{ color: 'var(--slate)', fontVariantNumeric: 'tabular-nums' }}>
                {d.value.toLocaleString()}
                {unit}
                {d.sub ? <span style={{ color: 'var(--stone)' }}> · {d.sub}</span> : null}
              </span>
            </div>

            {/* Background track of the progress bar */}
            <div
              style={{
                height: 10,
                borderRadius: 999,
                background: 'var(--paper)',
                overflow: 'hidden',
              }}
            >

              {/* Animated foreground bar */}
              <motion.div
                style={{
                  height: '100%',
                  borderRadius: 999,
                  background: color,
                  transformOrigin: 'left',
                }}

                // Show full width immediately if animations are disabled.
                // Otherwise start from 0 width for animation.
                initial={reduce ? { width: `${pct}%` } : { width: 0 }}

                // Animate either on component mount
                // or when the chart enters the viewport.
                {...(animateOnMount
                  ? { animate: { width: `${pct}%` } }
                  : { whileInView: { width: `${pct}%` }, viewport: { once: true } })}

                // Slight delay creates a staggered loading effect.
                transition={{
                  duration: 0.9,
                  delay: 0.08 * i,
                  ease: [0.22, 1, 0.36, 1],
                }}
              />
            </div>
          </div>
        );
      })}
    </div>
  );
}
