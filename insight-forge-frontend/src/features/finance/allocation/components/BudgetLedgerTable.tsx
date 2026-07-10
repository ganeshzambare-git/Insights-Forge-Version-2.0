'use client';

import React from 'react';
import { useBudgetLedger, type BudgetLedgerEntry } from '../store/resourceAllocationStore';
import styles from './ResourceAllocationPage.module.css';

function UtilizationBar({ pct }: { pct: number }) {
  const capped = Math.min(100, Math.max(0, pct));
  const color = capped > 70 ? '#f87171' : capped > 45 ? '#f59e0b' : '#34d399';
  return (
    <div className={styles.utilBar} aria-label={`${capped.toFixed(1)}% utilization`}>
      <div className={styles.utilBarFill} style={{ width: `${capped}%`, backgroundColor: color }} />
      <span className={styles.utilBarLabel}>{capped.toFixed(1)}%</span>
    </div>
  );
}

export const BudgetLedgerTable: React.FC = () => {
  const ledger = useBudgetLedger();

  if (!ledger.length) {
    return (
      <div className={styles.emptyState} role="status">
        No budget allocations match the selected dimension filter.
      </div>
    );
  }

  return (
    <section className={styles.tableSection} aria-label="Budget ledger table">
      <h2 className={styles.sectionTitle}>Budget Ledger</h2>
      <div className={styles.tableWrapper} role="region" aria-label="Scrollable budget ledger" tabIndex={0}>
        <table className={styles.table} aria-label="Budget allocation records">
          <thead>
            <tr>
              <th scope="col" className={styles.th}>Category</th>
              <th scope="col" className={styles.th}>Description</th>
              <th scope="col" className={styles.th}>Dimension</th>
              <th scope="col" className={styles.th}>Allocated</th>
              <th scope="col" className={styles.th}>Balance</th>
              <th scope="col" className={styles.th}>Fiscal Year</th>
              <th scope="col" className={styles.th}>Utilization</th>
            </tr>
          </thead>
          <tbody>
            {ledger.map((entry: BudgetLedgerEntry) => (
              <tr key={entry.allocation_id} className={styles.tr}>
                <td className={styles.td}><strong>{entry.category}</strong></td>
                <td className={styles.td}>{entry.description}</td>
                <td className={`${styles.td} ${styles.codeCell}`}>{entry.dimension}</td>
                <td className={styles.td}>${entry.allocated_budget.toLocaleString('en-US', { minimumFractionDigits: 2 })}</td>
                <td className={styles.td} style={{ color: '#34d399' }}>
                  ${entry.current_balance.toLocaleString('en-US', { minimumFractionDigits: 2 })}
                </td>
                <td className={styles.td}>{entry.fiscal_year}</td>
                <td className={styles.td}>
                  <UtilizationBar pct={entry.utilization_pct} />
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
};
