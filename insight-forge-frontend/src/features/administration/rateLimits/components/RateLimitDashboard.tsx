'use client';

import React, { useEffect, useState } from 'react';
import {
  useRateLimitLogs,
  useRateLimitLoading,
  useRateLimitError,
  useRateLimitTimeRange,
  useRateLimitTenantFilter,
  useRateLimitActions,
} from '../store/rateLimitStore';
import styles from './RateLimitDashboard.module.css';

export const RateLimitDashboard: React.FC = () => {
  const logs = useRateLimitLogs();
  const loading = useRateLimitLoading();
  const error = useRateLimitError();
  const timeRangeMin = useRateLimitTimeRange();
  const tenantFilter = useRateLimitTenantFilter();
  const { fetchRateLimitLogs, setTimeRangeMin, setTenantFilter } = useRateLimitActions();

  const [viewMode, setViewMode] = useState<'timeline' | 'table'>('timeline');

  useEffect(() => {
    fetchRateLimitLogs();
  }, [fetchRateLimitLogs]);

  const uniqueTenants = Array.from(new Set(logs.map((l) => l.tenant_name)));

  const filteredLogs = logs.filter((l) => {
    if (tenantFilter !== 'All' && l.tenant_name !== tenantFilter) {
      return false;
    }

    const logTime = new Date(l.timestamp).getTime();
    const now = Date.now();
    const ageMinutes = (now - logTime) / 60000;
    
    return ageMinutes <= timeRangeMin;
  });

  if (loading && logs.length === 0) {
    return <div className={styles.loading}>Loading Rate Limit Observation Timelines...</div>;
  }

  if (error && logs.length === 0) {
    return (
      <div className={styles.errorContainer}>
        <p className={styles.errorText}>Failed to retrieve telemetry: {error}</p>
        <button onClick={fetchRateLimitLogs} className={styles.retryButton}>
          Retry Connection
        </button>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <h2 className={styles.title}>Tenant Rate Limit Observatory</h2>
          <p className={styles.subtitle}>Track high-density query counts and detect threshold spikes</p>
        </div>

        <div className={styles.toggleContainer}>
          <button 
            onClick={() => setViewMode('timeline')} 
            className={`${styles.toggleBtn} ${viewMode === 'timeline' ? styles.activeToggle : ''}`}
            aria-pressed={viewMode === 'timeline'}
          >
            Timeline Chart
          </button>
          <button 
            onClick={() => setViewMode('table')} 
            className={`${styles.toggleBtn} ${viewMode === 'table' ? styles.activeToggle : ''}`}
            aria-pressed={viewMode === 'table'}
          >
            Violations List
          </button>
        </div>
      </header>

      <section className={styles.controlsSection}>
        <div className={styles.controlGroup}>
          <label htmlFor="tenant-filter-select" className={styles.label}>
            Institutional Tenant Partition:
          </label>
          <select
            id="tenant-filter-select"
            value={tenantFilter}
            onChange={(e) => setTenantFilter(e.target.value)}
            className={styles.select}
          >
            <option value="All">All Tenants</option>
            {uniqueTenants.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </div>

        <div className={styles.controlGroup} style={{ flex: 1 }}>
          <label htmlFor="time-range-slider" className={styles.label}>
            Timeline Window Age: <strong>{timeRangeMin} minutes</strong>
          </label>
          <input
            id="time-range-slider"
            type="range"
            min={5}
            max={60}
            step={5}
            value={timeRangeMin}
            onChange={(e) => setTimeRangeMin(parseInt(e.target.value, 10))}
            className={styles.slider}
            aria-valuemin={5}
            aria-valuemax={60}
            aria-valuenow={timeRangeMin}
          />
        </div>
      </section>

      {filteredLogs.length === 0 ? (
        <div className={styles.emptyState}>
          <h3>No Activity Records Found</h3>
          <p>No transactions match the selected tenant filter or timeline window.</p>
        </div>
      ) : (
        <>
          {viewMode === 'timeline' ? (
            <div className={styles.timelineContainer}>
              <h3 className={styles.sectionTitle}>High-Density Rate Logs</h3>
              <div className={styles.barGrid}>
                {filteredLogs.map((l) => (
                  <div key={l.id} className={styles.barCol}>
                    <div className={styles.barTooltip}>
                      <strong>{l.tenant_name}</strong>
                      <div>Rate: {l.request_rate}/min</div>
                      <div>Time: {new Date(l.timestamp).toLocaleTimeString()}</div>
                    </div>
                    <div className={styles.barWrapper}>
                      <div 
                        className={`${styles.barFill} ${l.is_violation ? styles.barViolation : ''}`} 
                        style={{ height: `${Math.min((l.request_rate / 150) * 100, 100)}%` }}
                      />
                    </div>
                    <span className={styles.barLabel}>
                      {new Date(l.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })}
                    </span>
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className={styles.tableContainer}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th>Tenant Institution</th>
                    <th>Audit Timestamp</th>
                    <th>Query Rate</th>
                    <th>Limit Cap</th>
                    <th>Safety Status</th>
                  </tr>
                </thead>
                <tbody>
                  {filteredLogs.map((l) => (
                    <tr 
                      key={l.id} 
                      className={l.is_violation ? styles.rowViolation : ''}
                    >
                      <td style={{ fontWeight: 600 }}>{l.tenant_name}</td>
                      <td>{new Date(l.timestamp).toLocaleString()}</td>
                      <td>
                        <span style={{ fontWeight: 700, color: l.is_violation ? 'var(--critical)' : 'var(--ink)' }}>
                          {l.request_rate} req/min
                        </span>
                      </td>
                      <td>{l.limit_threshold} req/min</td>
                      <td>
                        {l.is_violation ? (
                          <span className={styles.alertCrimson} role="status">
                            [CRITICAL VIOLATION]
                          </span>
                        ) : (
                          <span className={styles.statusSafe} role="status">
                            Compliant
                          </span>
                        )}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}
    </div>
  );
};
