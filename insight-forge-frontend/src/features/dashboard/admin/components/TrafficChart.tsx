'use client';

import React, { useState } from 'react';
import { TrafficPoint } from '../store/dashboardStore';

interface TrafficChartProps {
  data: TrafficPoint[];
}

export const TrafficChart: React.FC<TrafficChartProps> = ({ data }) => {
  const [hoveredIdx, setHoveredIdx] = useState<number | null>(null);

  if (!data || data.length === 0) return null;

  const svgWidth = 1000;
  const svgHeight = 320;
  const paddingLeft = 60;
  const paddingRight = 30;
  const paddingTop = 40;
  const paddingBottom = 40;

  const chartWidth = svgWidth - paddingLeft - paddingRight;
  const chartHeight = svgHeight - paddingTop - paddingBottom;

  const maxRequests = Math.max(...data.map(d => d.requests), 100);

  const points = data.map((d, index) => {
    const x = paddingLeft + (index / (data.length - 1)) * chartWidth;
    const y = svgHeight - paddingBottom - (d.requests / maxRequests) * chartHeight;
    return { x, y, item: d };
  });

  const strokePath = points.map((p, i) => `${i === 0 ? 'M' : 'L'} ${p.x} ${p.y}`).join(' ');
  const fillPath = `${strokePath} L ${points[points.length - 1].x} ${svgHeight - paddingBottom} L ${points[0].x} ${svgHeight - paddingBottom} Z`;

  const yGridLines = [0.25, 0.5, 0.75, 1];

  return (
    <div style={{ width: '100%', position: 'relative' }}>
      <svg viewBox={`0 0 ${svgWidth} ${svgHeight}`} width="100%" height="auto" style={{ overflow: 'visible' }}>
        <defs>
          <linearGradient id="areaGradient" x1="0" y1="0" x2="0" y2="1">
            <stop offset="0%" stopColor="var(--violet)" stopOpacity="0.4" />
            <stop offset="100%" stopColor="var(--violet)" stopOpacity="0.0" />
          </linearGradient>
        </defs>

        {/* Y Gridlines & labels */}
        {yGridLines.map((ratio, idx) => {
          const y = svgHeight - paddingBottom - ratio * chartHeight;
          const labelVal = Math.round(ratio * maxRequests);
          return (
            <g key={idx}>
              <line 
                x1={paddingLeft} 
                y1={y} 
                x2={svgWidth - paddingRight} 
                y2={y} 
                stroke="var(--border)" 
                strokeDasharray="4"
              />
              <text 
                x={paddingLeft - 12} 
                y={y + 4} 
                fill="var(--faint)" 
                fontSize="11px" 
                textAnchor="end"
              >
                {labelVal}
              </text>
            </g>
          );
        })}

        {/* Bottom base boundary line */}
        <line 
          x1={paddingLeft} 
          y1={svgHeight - paddingBottom} 
          x2={svgWidth - paddingRight} 
          y2={svgHeight - paddingBottom} 
          stroke="var(--border-strong)"
        />

        {/* X hour ticks */}
        {points.map((p, idx) => {
          if (idx % 4 !== 0 && idx !== points.length - 1) return null;
          return (
            <text 
              key={idx}
              x={p.x} 
              y={svgHeight - paddingBottom + 20} 
              fill="var(--faint)" 
              fontSize="11px" 
              textAnchor="middle"
            >
              {p.item.time}
            </text>
          );
        })}

        {/* Area fill path */}
        <path d={fillPath} fill="url(#areaGradient)" />

        {/* Area border line */}
        <path d={strokePath} fill="none" stroke="var(--violet)" strokeWidth="3" />

        {/* Active crosshair projection */}
        {hoveredIdx !== null && (
          <>
            <line 
              x1={points[hoveredIdx].x} 
              y1={paddingTop} 
              x2={points[hoveredIdx].x} 
              y2={svgHeight - paddingBottom} 
              stroke="rgba(99, 102, 241, 0.3)" 
              strokeWidth="2"
              strokeDasharray="2"
            />
            <circle 
              cx={points[hoveredIdx].x} 
              cy={points[hoveredIdx].y} 
              r="6" 
              fill="var(--violet)" 
              stroke="var(--ink)" 
              strokeWidth="2" 
            />
          </>
        )}

        {/* Interactive column listener zones */}
        {points.map((p, idx) => {
          const colWidth = chartWidth / (data.length - 1);
          return (
            <rect
              key={idx}
              x={p.x - colWidth / 2}
              y={paddingTop}
              width={colWidth}
              height={chartHeight}
              fill="transparent"
              style={{ cursor: 'pointer' }}
              onMouseEnter={() => setHoveredIdx(idx)}
              onMouseLeave={() => setHoveredIdx(null)}
            />
          );
        })}
      </svg>

      {/* Floating tooltip block */}
      {hoveredIdx !== null && (
        <div style={{
          position: 'absolute',
          left: `${(points[hoveredIdx].x / svgWidth) * 100}%`,
          top: `${(points[hoveredIdx].y / svgHeight) * 75}%`,
          transform: 'translate(-50%, -110%)',
          backgroundColor: 'var(--surface-2)',
          border: '1px solid var(--border-strong)',
          borderRadius: '0.375rem',
          padding: '0.5rem 0.75rem',
          pointerEvents: 'none',
          boxShadow: '0 4px 12px rgba(0,0,0,0.5)',
          zIndex: 10,
          whiteSpace: 'nowrap',
        }}>
          <div style={{ fontSize: '11px', color: 'var(--muted)', marginBottom: '2px' }}>
            Time: {points[hoveredIdx].item.time}
          </div>
          <div style={{ fontSize: '13px', fontWeight: 600, color: 'var(--brand)' }}>
            Requests: {points[hoveredIdx].item.requests.toLocaleString()}
          </div>
        </div>
      )}
    </div>
  );
};
