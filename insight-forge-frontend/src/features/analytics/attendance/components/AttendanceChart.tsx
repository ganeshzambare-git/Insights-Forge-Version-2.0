'use client';

import React, { useMemo } from 'react';
import { useAttendanceTrend } from '../store/attendanceStore';

const CHART_WIDTH = 680;
const CHART_HEIGHT = 220;
const PADDING = { top: 24, right: 24, bottom: 40, left: 52 };

export const AttendanceChart: React.FC = () => {
  const trend = useAttendanceTrend();

  const { points, pathD, areaD, minVal, maxVal, yTicks } = useMemo(() => {
    if (!trend.length) return { points: [], pathD: '', areaD: '', minVal: 0, maxVal: 100, yTicks: [] };

    const values = trend.map((t) => t.attendance_rate);
    const rawMin = Math.min(...values);
    const rawMax = Math.max(...values);
    const minVal = Math.max(0, Math.floor(rawMin / 10) * 10 - 10);
    const maxVal = Math.min(100, Math.ceil(rawMax / 10) * 10 + 5);
    const range = maxVal - minVal || 1;

    const plotW = CHART_WIDTH - PADDING.left - PADDING.right;
    const plotH = CHART_HEIGHT - PADDING.top - PADDING.bottom;

    const points = trend.map((t, i) => ({
      x: PADDING.left + (i / Math.max(trend.length - 1, 1)) * plotW,
      y: PADDING.top + plotH - ((t.attendance_rate - minVal) / range) * plotH,
      label: t.month,
      rate: t.attendance_rate,
    }));

    const lineCoords = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x.toFixed(1)},${p.y.toFixed(1)}`).join(' ');
    const areaCoords = [
      `M ${points[0].x.toFixed(1)},${(PADDING.top + plotH).toFixed(1)}`,
      ...points.map((p) => `L ${p.x.toFixed(1)},${p.y.toFixed(1)}`),
      `L ${points[points.length - 1].x.toFixed(1)},${(PADDING.top + plotH).toFixed(1)}`,
      'Z',
    ].join(' ');

    const yTicks = [0, 0.25, 0.5, 0.75, 1].map((f) => ({
      value: Math.round(minVal + f * range),
      y: PADDING.top + plotH - f * plotH,
    }));

    return { points, pathD: lineCoords, areaD: areaCoords, minVal, maxVal, yTicks };
  }, [trend]);

  if (!trend.length) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', height: 220, color: 'var(--faint)', fontSize: '0.9rem' }}>
        No attendance trend data for the selected filters.
      </div>
    );
  }

  return (
    <figure role="img" aria-label="Attendance trend area chart" style={{ margin: 0 }}>
      <svg
        viewBox={`0 0 ${CHART_WIDTH} ${CHART_HEIGHT}`}
        width="100%"
        height={CHART_HEIGHT}
        aria-hidden="true"
        style={{ overflow: 'visible' }}
      >
        <defs>
          <linearGradient id="attendGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--brand)" stopOpacity="0.35" />
            <stop offset="100%" stopColor="var(--brand)" stopOpacity="0.02" />
          </linearGradient>
        </defs>

        {/* Y-axis grid lines */}
        {yTicks.map((tick) => (
          <g key={tick.value}>
            <line
              x1={PADDING.left}
              y1={tick.y}
              x2={CHART_WIDTH - PADDING.right}
              y2={tick.y}
              stroke="var(--border)"
              strokeWidth="1"
            />
            <text x={PADDING.left - 8} y={tick.y + 4} textAnchor="end" fontSize="11" fill="var(--faint)">
              {tick.value}%
            </text>
          </g>
        ))}

        {/* X-axis labels */}
        {points.map((p) => (
          <text key={p.label} x={p.x} y={CHART_HEIGHT - 8} textAnchor="middle" fontSize="11" fill="var(--faint)">
            {p.label}
          </text>
        ))}

        {/* Area fill */}
        <path d={areaD} fill="url(#attendGrad)" />

        {/* Line stroke */}
        <path d={pathD} fill="none" stroke="var(--brand)" strokeWidth="2.5" strokeLinejoin="round" strokeLinecap="round" />

        {/* Data points with tooltips */}
        {points.map((p) => (
          <g key={`pt-${p.label}`}>
            <circle cx={p.x} cy={p.y} r={5} fill="var(--ink)" stroke="var(--brand)" strokeWidth="2" />
            <title>{`${p.label}: ${p.rate.toFixed(1)}%`}</title>
          </g>
        ))}
      </svg>

      {/* Legend */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem', marginTop: '0.75rem', paddingLeft: `${PADDING.left}px` }}>
        <span style={{ display: 'inline-block', width: 28, height: 3, backgroundColor: 'var(--brand)', borderRadius: 2 }} />
        <span style={{ color: 'var(--muted)', fontSize: '0.8rem' }}>Monthly Attendance Rate (%)</span>
      </div>
      <figcaption style={{ position: 'absolute', left: '-9999px' }}>
        Monthly attendance trend showing rates from {trend[0]?.month} to {trend[trend.length - 1]?.month}.
      </figcaption>
    </figure>
  );
};
