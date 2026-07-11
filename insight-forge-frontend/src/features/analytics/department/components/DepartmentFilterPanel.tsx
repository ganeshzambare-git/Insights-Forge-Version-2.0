'use client';

import React, { useEffect } from 'react';
import {
  useDepartmentScope,
  useDepartmentRecords,
  useDepartmentLoading,
  useDepartmentError,
  useDepartmentTimeoutOccurred,
  useDepartmentActions,
} from '../store/departmentStore';
import styles from './DepartmentFilterPanel.module.css';

export const DepartmentFilterPanel: React.FC = () => {
  const scope = useDepartmentScope();
  const records = useDepartmentRecords();
  const loading = useDepartmentLoading();
  const error = useDepartmentError();
  const timeoutOccurred = useDepartmentTimeoutOccurred();
  const { fetchDepartmentRecords } = useDepartmentActions();

  useEffect(() => {
    fetchDepartmentRecords(scope);
  }, [fetchDepartmentRecords]);

  const handleScopeChange = (e: React.ChangeEvent<HTMLSelectElement>) => {
    fetchDepartmentRecords(e.target.value);
  };

  const handleRetry = () => {
    fetchDepartmentRecords(scope);
  };

  return (
    <div className={styles.container}>
      <header className={styles.filterBar}>
        <div className={styles.selectGroup}>
          <label htmlFor="dept-scope-select" className={styles.label}>
            Select Department Partition:
          </label>
          <select
            id="dept-scope-select"
            value={scope}
            onChange={handleScopeChange}
            className={styles.select}
            disabled={loading}
          >
            <option value="Engineering">Engineering Department</option>
            <option value="Sciences">Sciences Department</option>
            <option value="Humanities">Humanities Department</option>
            <option value="Business">Business Department</option>
            <option value="Arts">Arts Department</option>
            <option value="TimeoutTrigger">TimeoutTrigger (Simulate Timeout)</option>
          </select>
        </div>
      </header>

      {/* Loading Skeleton */}
      {loading && (
        <div className={styles.skeletonContainer}>
          <div className={styles.skeletonRowHeader} />
          <div className={styles.skeletonRow} />
          <div className={styles.skeletonRow} />
          <div className={styles.skeletonRow} />
          <div className={styles.skeletonRow} />
          <div className={styles.skeletonRow} />
        </div>
      )}

      {/* Timeout Alert Screen */}
      {!loading && timeoutOccurred && (
        <div className={styles.timeoutCard}>
          <div className={styles.timeoutIcon}>⏳</div>
          <h3 className={styles.timeoutTitle}>Database Query Timeout</h3>
          <p className={styles.timeoutText}>
            Query execution timeout exceeded (2.5 seconds limit). Please select a narrower institutional scope to refine compute parameters.
          </p>
          <button onClick={handleRetry} className={styles.retryBtn}>
            Retry Request
          </button>
        </div>
      )}

      {/* Error Alert Screen */}
      {!loading && !timeoutOccurred && error && (
        <div className={styles.errorCard}>
          <p>Error contacting gateway logs: {error}</p>
          <button onClick={handleRetry} className={styles.retryBtn}>
            Retry Request
          </button>
        </div>
      )}

      {/* Records Table View */}
      {!loading && !timeoutOccurred && !error && (
        <div className={styles.tableWrapper}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th>Student Identifier</th>
                <th>Academic Department</th>
                <th>GPA</th>
                <th>MFA status</th>
                <th>Risk Matrix</th>
              </tr>
            </thead>
            <tbody>
              {records.map((r) => (
                <tr key={r.id}>
                  <td style={{ fontWeight: 600 }}>{r.name}</td>
                  <td>{r.department}</td>
                  <td>{r.term_gpa.toFixed(2)}</td>
                  <td>
                    <span className={styles.creditsBadge}>{r.term_credits} credits</span>
                  </td>
                  <td>
                    {r.risk_level === 'High' ? (
                      <span className={styles.riskHigh}>High Risk</span>
                    ) : r.risk_level === 'Medium' ? (
                      <span className={styles.riskMedium}>Medium Risk</span>
                    ) : (
                      <span className={styles.riskLow}>Low Risk</span>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
};
