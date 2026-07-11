'use client';

import React from 'react';
import { useAttendanceSummary } from '../store/attendanceStore';
import styles from './AttendanceAnalyticsPage.module.css';

export const AttendanceSummary: React.FC = () => {
  const summary = useAttendanceSummary();

  if (!summary) return null;

  const cards = [
    { label: 'Average Rate', value: `${summary.average_attendance_rate.toFixed(1)}%`, icon: '', color: 'var(--brand)' },
    { label: 'Peak Rate',    value: `${summary.peak_attendance_rate.toFixed(1)}%`,    icon: '', color: 'var(--safe)' },
    { label: 'Trough Rate',  value: `${summary.trough_attendance_rate.toFixed(1)}%`,  icon: '', color: 'var(--warn)' },
    { label: 'Months Tracked', value: `${summary.total_months}`,                      icon: '', color: 'var(--violet)' },
  ];

  return (
    <div className={styles.summaryGrid} role="region" aria-label="Attendance KPI summary">
      {cards.map((c) => (
        <div key={c.label} className={styles.summaryCard}>
          <span className={styles.summaryIcon} aria-hidden="true">{c.icon}</span>
          <span className={styles.summaryValue} style={{ color: c.color }}>{c.value}</span>
          <span className={styles.summaryLabel}>{c.label}</span>
        </div>
      ))}
    </div>
  );
};
