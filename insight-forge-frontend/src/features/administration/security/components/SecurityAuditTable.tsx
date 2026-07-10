'use client';

import React from 'react';
import { useAuditLogs, useAuditTotalRecords, useAuditActions, type AuditLogRecord, type AuditSeverity } from '../store/securityAuditStore';
import styles from './SecurityAuditPage.module.css';

const SEVERITY_STYLE: Record<AuditSeverity, { color: string; bg: string }> = {
  INFO:     { color: '#38bdf8', bg: 'rgba(56,189,248,0.1)' },
  WARNING:  { color: '#f59e0b', bg: 'rgba(245,158,11,0.1)' },
  CRITICAL: { color: '#f87171', bg: 'rgba(248,113,113,0.12)' },
};

export const SecurityAuditTable: React.FC = () => {
  const logs = useAuditLogs();
  const total = useAuditTotalRecords();
  const { selectLog } = useAuditActions();

  if (!logs.length) {
    return (
      <div className={styles.emptyState} role="status">
        No audit records match the selected filters.
      </div>
    );
  }

  return (
    <section className={styles.tableSection} aria-label="Security audit records table">
      <div className={styles.tableHeader}>
        <span className={styles.tableCount}>{total} record{total !== 1 ? 's' : ''}</span>
      </div>
      <div className={styles.tableWrapper} role="region" aria-label="Scrollable audit table" tabIndex={0}>
        <table className={styles.table} aria-label="Security audit log">
          <thead>
            <tr>
              <th scope="col" className={styles.th}>Timestamp</th>
              <th scope="col" className={styles.th}>Event Type</th>
              <th scope="col" className={styles.th}>Severity</th>
              <th scope="col" className={styles.th}>Source IP</th>
              <th scope="col" className={styles.th}>User</th>
              <th scope="col" className={styles.th}>Session Token</th>
              <th scope="col" className={styles.th}>Actions</th>
            </tr>
          </thead>
          <tbody>
            {logs.map((log: AuditLogRecord) => {
              const sev = SEVERITY_STYLE[log.severity];
              return (
                <tr key={log.audit_id} className={styles.tr}>
                  <td className={`${styles.td} ${styles.mono}`}>
                    {new Date(log.timestamp).toLocaleString()}
                  </td>
                  <td className={`${styles.td} ${styles.mono}`}>{log.event_type}</td>
                  <td className={styles.td}>
                    <span
                      className={styles.severityBadge}
                      style={{ color: sev.color, backgroundColor: sev.bg }}
                      aria-label={`Severity: ${log.severity}`}
                    >
                      {log.severity}
                    </span>
                  </td>
                  <td className={`${styles.td} ${styles.mono}`}>{log.source_ip}</td>
                  <td className={styles.td}>{log.user_email}</td>
                  <td className={`${styles.td} ${styles.mono} ${styles.tokenCell}`}>
                    {log.session_token ?? <span className={styles.nullVal}>—</span>}
                  </td>
                  <td className={styles.td}>
                    <button
                      onClick={() => selectLog(log)}
                      className={styles.detailsBtn}
                      aria-label={`View details for audit record ${log.audit_id}`}
                    >
                      Details
                    </button>
                  </td>
                </tr>
              );
            })}
          </tbody>
        </table>
      </div>
    </section>
  );
};
