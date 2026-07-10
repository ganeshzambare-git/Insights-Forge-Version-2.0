'use client';

import React, { useEffect } from 'react';
import { useAuditIsLoading, useAuditError, useAuditTotalRecords, useAuditActions } from '../store/securityAuditStore';
import { SecurityFilterToolbar } from './SecurityFilterToolbar';
import { SecurityAuditTable } from './SecurityAuditTable';
import { AuditDetailsDrawer } from './AuditDetailsDrawer';
import styles from './SecurityAuditPage.module.css';

export const SecurityAuditPage: React.FC = () => {
  const isLoading = useAuditIsLoading();
  const error = useAuditError();
  const total = useAuditTotalRecords();
  const { fetchAuditLogs } = useAuditActions();

  useEffect(() => {
    fetchAuditLogs();
  }, [fetchAuditLogs]);

  return (
    <main className={styles.page}>
      <header className={styles.pageHeader}>
        <div>
          <h1 className={styles.pageTitle}>Security Audit Log</h1>
          <p className={styles.pageSubtitle}>
            Administrative view of platform security events, access records, and operational anomalies.
          </p>
        </div>
        {!isLoading && total > 0 && (
          <div className={styles.recordCount} aria-live="polite">
            {total} records
          </div>
        )}
      </header>

      <SecurityFilterToolbar />

      {isLoading && (
        <div className={styles.statusRow} role="status" aria-live="polite">
          <span className={styles.spinner} aria-hidden="true" />
          Loading security audit records…
        </div>
      )}

      {error && !isLoading && (
        <div className={styles.errorBanner} role="alert">
          <strong>Error:</strong> {error}
          <button className={styles.retryBtn} onClick={fetchAuditLogs}>Retry</button>
        </div>
      )}

      {!isLoading && !error && <SecurityAuditTable />}

      <AuditDetailsDrawer />
    </main>
  );
};
