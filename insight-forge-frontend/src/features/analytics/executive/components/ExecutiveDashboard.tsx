'use client';

import React, { useEffect, useTransition } from 'react';
import {
  useExecutiveKPIs,
  useExecutiveLoading,
  useExecutiveError,
  useExecutiveDepartments,
  useExecutiveResourceAllocation,
  useExecutiveActions,
} from '../store/executiveStore';
import styles from './ExecutiveDashboard.module.css';

export const ExecutiveDashboard: React.FC = () => {
  const kpis = useExecutiveKPIs();
  const loading = useExecutiveLoading();
  const error = useExecutiveError();
  const departments = useExecutiveDepartments();
  const resources = useExecutiveResourceAllocation();
  const { fetchExecutiveSummary } = useExecutiveActions();

  const [isPending, startTransition] = useTransition();

  useEffect(() => {
    fetchExecutiveSummary();
  }, [fetchExecutiveSummary]);

  const handleRefresh = () => {
    startTransition(async () => {
      await fetchExecutiveSummary();
    });
  };

  if (loading && !kpis) {
    return <div className={styles.loading}>Loading Institutional Executive Analytics...</div>;
  }

  if (error && !kpis) {
    return (
      <div className={styles.errorContainer}>
        <p className={styles.errorText}>⚠️ Failed to load executive metrics: {error}</p>
        <button onClick={handleRefresh} className={styles.retryButton}>
          Retry Query
        </button>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <h2 className={styles.title}>Institutional Analytics Dashboard</h2>
          <p className={styles.subtitle}>Executive summary metrics & cohort distributions (Dean-1 view)</p>
        </div>
        <button 
          onClick={handleRefresh} 
          className={styles.refreshBtn}
          disabled={loading || isPending}
        >
          {loading || isPending ? 'Refreshing...' : '🔄 Refresh Data'}
        </button>
      </header>

      {kpis && (
        <section className={styles.kpiGrid}>
          <div className={styles.kpiCard}>
            <div className={styles.kpiLabel}>Total Student Enrollment</div>
            <div className={styles.kpiValue}>{kpis.total_students.toLocaleString()}</div>
            <div className={styles.kpiMeta}>✓ Audited active accounts</div>
          </div>
          
          <div className={`${styles.kpiCard} ${styles.criticalCard}`}>
            <div className={styles.kpiLabel}>Critical Risk Cases</div>
            <div className={styles.kpiValue}>{kpis.critical_risk}</div>
            <div className={styles.kpiMeta}>🚨 Requires coaching escalation</div>
          </div>

          <div className={styles.kpiCard}>
            <div className={styles.kpiLabel}>Active Interventions</div>
            <div className={styles.kpiValue}>{kpis.active_interventions}</div>
            <div className={styles.kpiMeta}>💼 Cohorts coaching active</div>
          </div>

          <div className={styles.kpiCard}>
            <div className={styles.kpiLabel}>Projected Graduation Rate</div>
            <div className={styles.kpiValue}>{kpis.completion_rate}%</div>
            <div className={styles.kpiMeta}>📈 +1.2% over target line</div>
          </div>
        </section>
      )}

      <div className={styles.dashboardSplit}>
        {/* Department GPA Standings */}
        <section className={styles.card}>
          <h3 className={styles.sectionTitle}>Department Performance Index</h3>
          <div className={styles.tableWrapper}>
            <table className={styles.table}>
              <thead>
                <tr>
                  <th>Department</th>
                  <th>Average Term GPA</th>
                  <th>Student Size</th>
                  <th>Resource Allocation</th>
                </tr>
              </thead>
              <tbody>
                {departments.map((dept) => (
                  <tr key={dept.name}>
                    <td style={{ fontWeight: 700 }}>{dept.name}</td>
                    <td>
                      <span className={styles.gpaBadge}>{dept.gpa.toFixed(2)}</span>
                    </td>
                    <td>{dept.student_count.toLocaleString()}</td>
                    <td>${dept.budget_allocated.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>

        {/* Compute Resource Allocations & SVG Trends */}
        <div className={styles.rightColumn}>
          {resources && (
            <section className={styles.card}>
              <h3 className={styles.sectionTitle}>Compute Cluster Quota Logs</h3>
              <div className={styles.resourceGrid}>
                <div className={styles.resourceItem}>
                  <div className={styles.resourceMeta}>
                    <span>PySpark Cores (Active / Limit)</span>
                    <strong>{resources.pyspark_cores_active} / {resources.pyspark_cores_quota}</strong>
                  </div>
                  <div className={styles.barBg}>
                    <div 
                      className={styles.barFill} 
                      style={{ width: `${(resources.pyspark_cores_active / resources.pyspark_cores_quota) * 100}%` }}
                    />
                  </div>
                </div>

                <div className={styles.resourceItem}>
                  <div className={styles.resourceMeta}>
                    <span>Software Licenses (Allocated)</span>
                    <strong>{resources.software_licenses_active} / {resources.software_licenses_total}</strong>
                  </div>
                  <div className={styles.barBg}>
                    <div 
                      className={styles.barFill} 
                      style={{ width: `${(resources.software_licenses_active / resources.software_licenses_total) * 100}%` }}
                    />
                  </div>
                </div>
              </div>
            </section>
          )}

          <section className={styles.card}>
            <h3 className={styles.sectionTitle}>Risk Escalation Trends (24h)</h3>
            <div className={styles.chartWrapper}>
              <svg viewBox="0 0 400 160" width="100%" height="160px" style={{ overflow: 'visible' }}>
                <defs>
                  <linearGradient id="areaGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="0%" stopColor="#38bdf8" stopOpacity="0.4" />
                    <stop offset="100%" stopColor="#38bdf8" stopOpacity="0" />
                  </linearGradient>
                </defs>
                <line x1="10" y1="20" x2="390" y2="20" stroke="rgba(255,255,255,0.05)" />
                <line x1="10" y1="60" x2="390" y2="60" stroke="rgba(255,255,255,0.05)" />
                <line x1="10" y1="100" x2="390" y2="100" stroke="rgba(255,255,255,0.05)" />
                <line x1="10" y1="140" x2="390" y2="140" stroke="rgba(255,255,255,0.1)" />

                <path
                  d="M 10 120 L 70 100 L 130 130 L 190 70 L 250 85 L 310 40 L 390 55"
                  fill="none"
                  stroke="#38bdf8"
                  strokeWidth="3"
                  strokeLinecap="round"
                />

                <path
                  d="M 10 120 L 70 100 L 130 130 L 190 70 L 250 85 L 310 40 L 390 55 L 390 140 L 10 140 Z"
                  fill="url(#areaGrad)"
                />

                <circle cx="10" cy="120" r="4" fill="#020617" stroke="#38bdf8" strokeWidth="2" />
                <circle cx="70" cy="100" r="4" fill="#020617" stroke="#38bdf8" strokeWidth="2" />
                <circle cx="130" cy="130" r="4" fill="#020617" stroke="#38bdf8" strokeWidth="2" />
                <circle cx="190" cy="70" r="4" fill="#020617" stroke="#38bdf8" strokeWidth="2" />
                <circle cx="250" cy="85" r="4" fill="#020617" stroke="#38bdf8" strokeWidth="2" />
                <circle cx="310" cy="40" r="4" fill="#020617" stroke="#38bdf8" strokeWidth="2" />
                <circle cx="390" cy="55" r="4" fill="#020617" stroke="#38bdf8" strokeWidth="2" />
              </svg>
              <div className={styles.chartLabels}>
                <span>00:00</span>
                <span>06:00</span>
                <span>12:00</span>
                <span>18:00</span>
                <span>24:00</span>
              </div>
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};
