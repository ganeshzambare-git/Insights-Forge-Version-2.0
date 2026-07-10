'use client';

import React from 'react';
import { useFinancialSummary } from '../store/resourceAllocationStore';
import styles from './ResourceAllocationPage.module.css';

export const FinancialSummary: React.FC = () => {
  const summary = useFinancialSummary();
  if (!summary) return null;

  const fmt = (v: number) =>
    `$${v.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;

  return (
    <div className={styles.financialSummaryBar} role="region" aria-label="Financial summary strip">
      <div className={styles.summaryItem}>
        <span className={styles.summaryItemLabel}>Fiscal Year</span>
        <span className={styles.summaryItemValue} style={{ color: '#a78bfa' }}>{summary.fiscal_year}</span>
      </div>
      <div className={styles.summaryDivider} aria-hidden="true" />
      <div className={styles.summaryItem}>
        <span className={styles.summaryItemLabel}>Total Allocated</span>
        <span className={styles.summaryItemValue} style={{ color: '#38bdf8' }}>{fmt(summary.total_allocated)}</span>
      </div>
      <div className={styles.summaryDivider} aria-hidden="true" />
      <div className={styles.summaryItem}>
        <span className={styles.summaryItemLabel}>Total Spent</span>
        <span className={styles.summaryItemValue} style={{ color: '#f59e0b' }}>{fmt(summary.total_spent)}</span>
      </div>
      <div className={styles.summaryDivider} aria-hidden="true" />
      <div className={styles.summaryItem}>
        <span className={styles.summaryItemLabel}>Remaining Balance</span>
        <span className={styles.summaryItemValue} style={{ color: '#34d399' }}>{fmt(summary.total_balance)}</span>
      </div>
      <div className={styles.summaryDivider} aria-hidden="true" />
      <div className={styles.summaryItem}>
        <span className={styles.summaryItemLabel}>Overall Utilization</span>
        <span
          className={styles.summaryItemValue}
          style={{ color: summary.overall_utilization_pct > 70 ? '#f87171' : '#34d399' }}
        >
          {summary.overall_utilization_pct.toFixed(2)}%
        </span>
      </div>
    </div>
  );
};
