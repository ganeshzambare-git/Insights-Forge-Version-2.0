'use client';

import React from 'react';
import type { TaskStatus } from '../store/taskStatusStore';
import styles from './TaskProgressMonitorPage.module.css';

const STATUS_CONFIG: Record<TaskStatus, { label: string; color: string; bg: string; icon: string }> = {
  Pending:   { label: 'Pending',   color: '#94a3b8', bg: 'rgba(148,163,184,0.1)', icon: '⏳' },
  Running:   { label: 'Running',   color: '#38bdf8', bg: 'rgba(56,189,248,0.1)',  icon: '⚙️' },
  Completed: { label: 'Completed', color: '#34d399', bg: 'rgba(52,211,153,0.1)',  icon: '✅' },
  Failed:    { label: 'Failed',    color: '#f87171', bg: 'rgba(248,113,113,0.1)', icon: '❌' },
};

interface TaskStatusIndicatorProps {
  status: TaskStatus;
  size?: 'sm' | 'md';
}

export const TaskStatusIndicator: React.FC<TaskStatusIndicatorProps> = ({ status, size = 'md' }) => {
  const cfg = STATUS_CONFIG[status];
  return (
    <span
      className={size === 'sm' ? styles.statusBadgeSm : styles.statusBadge}
      style={{ color: cfg.color, backgroundColor: cfg.bg }}
      role="status"
      aria-label={`Task status: ${cfg.label}`}
    >
      <span aria-hidden="true">{cfg.icon}</span> {cfg.label}
    </span>
  );
};
