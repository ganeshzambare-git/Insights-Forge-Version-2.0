'use client';

import React from 'react';
import { useAuditFilters, useAuditActions } from '../store/securityAuditStore';
import styles from './SecurityAuditPage.module.css';

const EVENT_TYPES = ['', 'LOGIN_SUCCESS', 'LOGIN_FAILED', 'PRIVILEGE_ESCALATION_ATTEMPT', 'DATA_EXPORT', 'MFA_BYPASS_ATTEMPT', 'API_KEY_ROTATION'];
const SEVERITIES = ['', 'INFO', 'WARNING', 'CRITICAL'];

export const SecurityFilterToolbar: React.FC = () => {
  const filters = useAuditFilters();
  const { setFilter, clearFilters, fetchAuditLogs } = useAuditActions();

  const handleApply = () => fetchAuditLogs();
  const handleClear = () => { clearFilters(); fetchAuditLogs(); };

  return (
    <div className={styles.filterBar} role="search" aria-label="Security audit filters">
      <div className={styles.filterGroup}>
        <label htmlFor="event-type-filter" className={styles.filterLabel}>Event Type</label>
        <select
          id="event-type-filter"
          className={styles.filterSelect}
          value={filters.eventType}
          onChange={(e) => setFilter('eventType', e.target.value)}
        >
          {EVENT_TYPES.map((t) => <option key={t} value={t}>{t || 'All Event Types'}</option>)}
        </select>
      </div>

      <div className={styles.filterGroup}>
        <label htmlFor="severity-filter" className={styles.filterLabel}>Severity</label>
        <select
          id="severity-filter"
          className={styles.filterSelect}
          value={filters.severity}
          onChange={(e) => setFilter('severity', e.target.value)}
        >
          {SEVERITIES.map((s) => <option key={s} value={s}>{s || 'All Severities'}</option>)}
        </select>
      </div>

      <div className={styles.filterGroup}>
        <label htmlFor="ip-filter" className={styles.filterLabel}>Source IP</label>
        <input
          id="ip-filter"
          type="text"
          className={styles.filterInput}
          value={filters.sourceIp}
          onChange={(e) => setFilter('sourceIp', e.target.value)}
          placeholder="e.g. 192.168.1.42"
          aria-label="Filter by source IP address"
        />
      </div>

      <div className={styles.filterActions}>
        <button className={styles.applyBtn} onClick={handleApply} aria-label="Apply audit filters">Apply</button>
        <button className={styles.clearBtn} onClick={handleClear} aria-label="Clear audit filters">Clear</button>
      </div>
    </div>
  );
};
