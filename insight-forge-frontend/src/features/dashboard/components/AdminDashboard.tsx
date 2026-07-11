'use client';

import React, { useEffect } from 'react';
import {
  useDashboardMetrics,
  useDashboardLoading,
  useDashboardError,
  useDashboardActions,
} from '../store/dashboardStore';
import { TrafficChart } from './TrafficChart';
import styles from './AdminDashboard.module.css';

export const AdminDashboard: React.FC = () => {
  const metrics = useDashboardMetrics();
  const loading = useDashboardLoading();
  const error = useDashboardError();
  const { fetchMetrics } = useDashboardActions();

  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  const handleRetry = () => {
    fetchMetrics();
  };

  if (loading && !metrics) {
    return (
      <div className={styles.container}>
        <div className={styles.header}>
          <div className={styles.skeletonHeader} />
        </div>
        <div className={styles.grid}>
          <div className={`${styles.card} ${styles.skeletonCard}`} />
          <div className={`${styles.card} ${styles.skeletonCard}`} />
          <div className={`${styles.card} ${styles.skeletonCard}`} />
        </div>
      </div>
    );
  }

  if (error && !metrics) {
    return (
      <div className={styles.container}>
        <div className={styles.errorCard}>
          <span className={styles.errorIcon}></span>
          <h3>Observability Fetch Failure</h3>
          <p>{error}</p>
          <button onClick={handleRetry} className={styles.retryButton}>
            Retry Connection
          </button>
        </div>
      </div>
    );
  }

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <h2 className={styles.dashboardTitle}>Cluster Observation Panel</h2>
          <p className={styles.dashboardSubtitle}>Real-time monitoring of SaaS metrics and compute engine resources</p>
        </div>
        <div className={styles.actionsContainer}>
          {metrics && (
            <span className={styles.lastUpdated}>
              Last updated: {new Date(metrics.last_updated).toLocaleTimeString()}
            </span>
          )}
          <button onClick={fetchMetrics} className={styles.refreshButton} disabled={loading}>
            {loading ? 'Refreshing...' : 'Force Refresh'}
          </button>
        </div>
      </header>

      {metrics && (
        <>
          <div className={styles.grid}>
            {/* Card 1: Server Health */}
            <div className={styles.card}>
              <div className={styles.cardHeader}>
                <h3 className={styles.cardTitle}>Server Health</h3>
                <span className={`${styles.badge} ${styles.badgeHealthy}`}>
                  {metrics.server_health.status}
                </span>
              </div>
              <div className={styles.metricRow}>
                <span className={styles.metricLabel}>CPU Utilization</span>
                <span className={styles.metricValue}>{metrics.server_health.cpu_utilization}%</span>
              </div>
              <div className={styles.progressBarBg}>
                <div 
                  className={styles.progressBarFill} 
                  style={{ width: `${metrics.server_health.cpu_utilization}%`, backgroundColor: 'var(--brand)' }}
                />
              </div>
              <div className={styles.metricRow}>
                <span className={styles.metricLabel}>Memory Utilization</span>
                <span className={styles.metricValue}>{metrics.server_health.ram_utilization}%</span>
              </div>
              <div className={styles.progressBarBg}>
                <div 
                  className={styles.progressBarFill} 
                  style={{ width: `${metrics.server_health.ram_utilization}%`, backgroundColor: 'var(--violet)' }}
                />
              </div>
              <div className={styles.metricRow} style={{ marginTop: '1rem' }}>
                <span className={styles.metricLabel}>Active DB Connections</span>
                <span className={styles.metricValue} style={{ color: 'var(--brand-ink)' }}>{metrics.server_health.db_connection_pool}</span>
              </div>
            </div>

            {/* Card 2: PySpark Compute Load */}
            <div className={styles.card}>
              <div className={styles.cardHeader}>
                <h3 className={styles.cardTitle}>PySpark Compute Engine</h3>
                <span className={`${styles.badge} ${metrics.pyspark_load.status === 'Idle' ? styles.badgeIdle : styles.badgeProcessing}`}>
                  {metrics.pyspark_load.status}
                </span>
              </div>
              <div className={styles.metricRow}>
                <span className={styles.metricLabel}>Compute Core Load</span>
                <span className={styles.metricValue}>{metrics.pyspark_load.load_percentage}%</span>
              </div>
              <div className={styles.progressBarBg}>
                <div 
                  className={styles.progressBarFill} 
                  style={{ width: `${metrics.pyspark_load.load_percentage}%`, backgroundColor: 'var(--violet)' }}
                />
              </div>
              <div className={styles.metricRow} style={{ marginTop: '1.5rem' }}>
                <span className={styles.metricLabel}>Active Job Queue Size</span>
                <span className={styles.metricValue} style={{ color: 'var(--violet)' }}>{metrics.pyspark_load.queue_size} jobs</span>
              </div>
              <p className={styles.metaHelpText}>Governs dataset partition isolation and risk classification triggers.</p>
            </div>

            {/* Card 3: Inbound Traffic */}
            <div className={styles.card}>
              <div className={styles.cardHeader}>
                <h3 className={styles.cardTitle}>Inbound Traffic</h3>
                <span className={styles.trafficPulse}>Live</span>
              </div>
              <div className={styles.bigMetric}>
                <div className={styles.bigValue}>{metrics.inbound_traffic.current_rate_per_sec}</div>
                <div className={styles.bigLabel}>requests / sec</div>
              </div>
              <div className={styles.metricRow} style={{ borderTop: '1px solid var(--border)', paddingTop: '1rem', marginTop: '1rem' }}>
                <span className={styles.metricLabel}>Total Requests (24h)</span>
                <span className={styles.metricValue} style={{ color: 'var(--safe)' }}>{metrics.inbound_traffic.total_requests_24h.toLocaleString()}</span>
              </div>
            </div>
          </div>

          <div className={styles.chartContainer}>
            <h3 className={styles.chartTitle}>Inbound Request Volume (Past 24 Hours)</h3>
            <TrafficChart data={metrics.inbound_traffic.history_24h} />
          </div>
        </>
      )}
    </div>
  );
};
