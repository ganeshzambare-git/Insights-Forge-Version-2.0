'use client';

import React from 'react';
import { useCourseFilters, useCourseActions } from '../store/courseAnalyticsStore';
import styles from './CourseAnalyticsPage.module.css';

const COHORTS = ['', 'CS-2026', 'MTH-2026', 'ENG-2026'];

export const CohortFilter: React.FC = () => {
  const filters = useCourseFilters();
  const { setFilter } = useCourseActions();

  return (
    <div className={styles.filterGroup}>
      <label htmlFor="cohort-eval-filter" className={styles.filterLabel}>Cohort</label>
      <select
        id="cohort-eval-filter"
        className={styles.filterSelect}
        value={filters.cohortCode}
        onChange={(e) => setFilter('cohortCode', e.target.value)}
        aria-label="Filter by cohort code"
      >
        {COHORTS.map((c) => (
          <option key={c} value={c}>{c || 'All Cohorts'}</option>
        ))}
      </select>
    </div>
  );
};
