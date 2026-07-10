'use client';

import React, { useEffect } from 'react';
import {
  useAttendanceIsLoading,
  useAttendanceError,
  useAttendanceActions,
} from '../store/attendanceStore';
import { AttendanceFilterBar } from './AttendanceFilterBar';
import { AttendanceSummary } from './AttendanceSummary';
import { AttendanceChart } from './AttendanceChart';
import styles from './AttendanceAnalyticsPage.module.css';

export const AttendanceAnalyticsPage: React.FC = () => {
  const isLoading = useAttendanceIsLoading();
  const error = useAttendanceError();
  const { fetchAttendanceSummary } = useAttendanceActions();

  useEffect(() => {
    fetchAttendanceSummary();
  }, [fetchAttendanceSummary]);

  return (
    <main className={styles.page}>
      <header className={styles.pageHeader}>
        <div>
          <h1 className={styles.pageTitle}>Attendance Analytics</h1>
          <p className={styles.pageSubtitle}>
            Historical attendance trends and cohort engagement metrics.
          </p>
        </div>
      </header>

      <AttendanceFilterBar />
      <AttendanceSummary />

      <section className={styles.chartSection} aria-label="Attendance trend chart">
        <div className={styles.chartCard}>
          <h2 className={styles.chartTitle}>Monthly Attendance Trend</h2>
          {isLoading && (
            <div className={styles.statusRow} role="status" aria-live="polite">
              <span className={styles.spinner} aria-hidden="true" />
              Loading attendance data…
            </div>
          )}
          {error && !isLoading && (
            <div className={styles.errorBanner} role="alert">
              <strong>Error:</strong> {error}
              <button className={styles.retryBtn} onClick={fetchAttendanceSummary}>Retry</button>
            </div>
          )}
          {!isLoading && !error && <AttendanceChart />}
        </div>
      </section>
    </main>
  );
};
