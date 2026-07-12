'use client';

import { motion, useReducedMotion } from 'framer-motion';
import { useId } from 'react';

export type Point = { label: string; value: number };

type LineChartProps = {
  data: Point[];
  height?: number;
  color?: string;
  animateOnMount?: boolean;
  ariaLabel?: string;
};

const W = 640;
const PAD_X = 12;
const PAD_TOP = 16;
const PAD_BOTTOM = 26;

export function LineChart({
  data,
  height = 240,
  color = 'var(--c-primary)',
  animateOnMount,
  ariaLabel,
}: LineChartProps) {
  const reduce = useReducedMotion();
  const clipId = useId();

  const values = data.map((d) => d.value);
  const dataMin = Math.min(...values);
  const dataMax = Math.max(...values);
  // Pad around the actual range so real variation is visible (not squashed to a 0 baseline).
  const pad = (dataMax - dataMin) * 0.18 || Math.max(Math.abs(dataMax) * 0.1, 1);
  const min = dataMin - pad;
  const max = dataMax + pad;
  const range = max - min || 1;
  const innerH = height - PAD_TOP - PAD_BOTTOM;
  const stepX = data.length > 1 ? (W - PAD_X * 2) / (data.length - 1) : 0;

  const pts = data.map((d, i) => {
    const x = PAD_X + i * stepX;
    const y = PAD_TOP + innerH - ((d.value - min) / range) * innerH;
    return [x, y] as const;
  });

  const linePath = pts.map(([x, y], i) => `${i === 0 ? 'M' : 'L'}${x.toFixed(1)} ${y.toFixed(1)}`).join(' ');
  const areaPath = `${linePath} L${pts[pts.length - 1][0].toFixed(1)} ${PAD_TOP + innerH} L${pts[0][0].toFixed(1)} ${PAD_TOP + innerH} Z`;

  const gridY = [0, 0.5, 1].map((t) => PAD_TOP + innerH * t);
  const labelEvery = Math.ceil(data.length / 6);

  return (
    <svg
      viewBox={`0 0 ${W} ${height}`}
      width="100%"
      role="img"
      aria-label={ariaLabel || 'Line chart'}
      style={{ display: 'block' }}
    >
      <defs>
        <clipPath id={clipId}>
          <rect x="0" y="0" width={W} height={PAD_TOP + innerH} />
        </clipPath>
      </defs>

      {gridY.map((y, i) => (
        <line
          key={i}
          x1={PAD_X}
          x2={W - PAD_X}
          y1={y}
          y2={y}
          stroke="var(--silver)"
          strokeWidth="1"
          strokeDasharray={i === gridY.length - 1 ? '0' : '3 5'}
        />
      ))}

      <motion.path
        d={areaPath}
        fill={color}
        clipPath={`url(#${clipId})`}
        initial={reduce ? { opacity: 0.08 } : { opacity: 0 }}
        {...(animateOnMount
          ? { animate: { opacity: 0.08 } }
          : { whileInView: { opacity: 0.08 }, viewport: { once: true } })}
        transition={{ duration: 0.8, delay: 0.2 }}
      />

      <motion.path
        d={linePath}
        fill="none"
        stroke={color}
        strokeWidth="2.5"
        strokeLinecap="round"
        strokeLinejoin="round"
        initial={reduce ? { pathLength: 1 } : { pathLength: 0 }}
        {...(animateOnMount
          ? { animate: { pathLength: 1 } }
          : { whileInView: { pathLength: 1 }, viewport: { once: true } })}
        transition={{ duration: 1.1, ease: [0.22, 1, 0.36, 1] }}
      />

      {pts.map(([x, y], i) => (
        <motion.circle
          key={i}
          cx={x}
          cy={y}
          r="3"
          fill="var(--white)"
          stroke={color}
          strokeWidth="2"
          initial={reduce ? { opacity: 1 } : { opacity: 0, scale: 0 }}
          {...(animateOnMount
            ? { animate: { opacity: 1, scale: 1 } }
            : { whileInView: { opacity: 1, scale: 1 }, viewport: { once: true } })}
          transition={{ duration: 0.3, delay: 0.6 + i * (0.5 / pts.length) }}
          style={{ transformOrigin: `${x}px ${y}px` }}
        />
      ))}

      {data.map((d, i) =>
        i % labelEvery === 0 ? (
          <text
            key={i}
            x={pts[i][0]}
            y={height - 8}
            textAnchor="middle"
            fontSize="11"
            fill="var(--slate)"
            fontFamily="var(--font-body)"
          >
            {d.label}
          </text>
        ) : null,
      )}
    </svg>
  );
}
