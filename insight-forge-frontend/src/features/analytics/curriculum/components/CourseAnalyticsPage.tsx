'use client';

import React, { useEffect } from 'react';
import { useCourseIsLoading, useCourseError, useCourseActions } from '../store/courseAnalyticsStore';
import { DepartmentScopeFilter } from './DepartmentScopeFilter';
import { CohortFilter } from './CohortFilter';
import { CoursePerformanceTable } from './CoursePerformanceTable';
import styles from './CourseAnalyticsPage.module.css';

export const CourseAnalyticsPage: React.FC = () => {
  const isLoading = useCourseIsLoading();
  const error = useCourseError();
  const { fetchCourseEvaluation, clearFilters } = useCourseActions();

  useEffect(() => {
    fetchCourseEvaluation();
  }, [fetchCourseEvaluation]);

  const handleApply = () => fetchCourseEvaluation();
  const handleClear = () => { clearFilters(); fetchCourseEvaluation(); };

  return (
    <main className={styles.page}>
      <header className={styles.pageHeader}>
        <div>
          <h1 className={styles.pageTitle}>Course & Curriculum Analytics</h1>
          <p className={styles.pageSubtitle}>
            Department and cohort-level performance evaluation metrics.
          </p>
        </div>
      </header>

      {/* Filter toolbar */}
      <div className={styles.filterBar} role="search" aria-label="Course analytics filters">
        <DepartmentScopeFilter />
        <CohortFilter />
        <div className={styles.filterActions}>
          <button className={styles.applyBtn} onClick={handleApply} aria-label="Apply course filters">
            Apply Filters
          </button>
          <button className={styles.clearBtn} onClick={handleClear} aria-label="Clear course filters">
            Clear
          </button>
        </div>
      </div>

      {/* Status */}
      {isLoading && (
        <div className={styles.statusRow} role="status" aria-live="polite">
          <span className={styles.spinner} aria-hidden="true" />
          Loading course evaluation data…
        </div>
      )}
      {error && !isLoading && (
        <div className={styles.errorBanner} role="alert">
          <strong>Error:</strong> {error}
          <button className={styles.retryBtn} onClick={fetchCourseEvaluation}>Retry</button>
        </div>
      )}

      {/* Table */}
      {!isLoading && !error && <CoursePerformanceTable />}
    </main>
  );
};
