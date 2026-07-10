'use client';

import React, { useEffect } from 'react';
import {
  useDeadLetterLogs,
  useDeadLetterLoading,
  useDeadLetterError,
  useDeadLetterActions,
} from '../store/deadLetterStore';
import styles from './DeadLetterPanel.module.css';

export const DeadLetterPanel: React.FC = () => {
  const logs = useDeadLetterLogs();
  const loading = useDeadLetterLoading();
  const error = useDeadLetterError();
  const { fetchDeadLetterLogs } = useDeadLetterActions();

  useEffect(() => {
    fetchDeadLetterLogs();
  }, [fetchDeadLetterLogs]);

  return (
    <div className={styles.card}>
      <header className={styles.header}>
        <div>
          <h3 className={styles.title}>Dead-Letter Diagnostics Observatory</h3>
          <p className={styles.subtitle}>Review schema mismatches and processing failures from raw CSV streams</p>
        </div>
        <button
          onClick={fetchDeadLetterLogs}
          className={styles.refreshBtn}
          disabled={loading}
          aria-label="Refresh ingestion diagnostics logs"
        >
          {loading ? 'Refreshing...' : '🔄 Refresh Data'}
        </button>
      </header>

      {error && (
        <div className={styles.errorAlert} role="alert">
          <span>⚠️</span> {error}
        </div>
      )}

      {loading && logs.length === 0 ? (
        <div className={styles.loader}>Polling diagnostic records...</div>
      ) : logs.length === 0 ? (
        <div className={styles.emptyState}>
          <span>✓</span> No ingestion failures present. Dead-letter queue is empty.
        </div>
      ) : (
        <div className={styles.tableWrapper}>
          <table className={styles.table}>
            <thead>
              <tr>
                <th style={{ textAlign: 'left' }}>Payload ID</th>
                <th style={{ textAlign: 'left' }}>Error Details</th>
                <th>Timestamp</th>
                <th>Status</th>
              </tr>
            </thead>
            <tbody>
              {logs.map((log) => (
                <tr key={log.payload_id}>
                  <td className={styles.payloadId}>{log.payload_id}</td>
                  <td className={styles.errorDetails}>{log.error_summary}</td>
                  <td className={styles.timestamp}>{new Date(log.timestamp).toLocaleString()}</td>
                  <td>
                    <span className={styles.failedBadge}>{log.status}</span>
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
