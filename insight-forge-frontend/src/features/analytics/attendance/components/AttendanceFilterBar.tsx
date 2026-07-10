'use client';

import React from 'react';
import { useAttendanceFilters, useAttendanceActions } from '../store/attendanceStore';
import styles from './AttendanceAnalyticsPage.module.css';

const SEMESTERS = ['', 'Spring 2026', 'Summer 2026', 'Fall 2026'];
const COHORTS = ['', 'CS-2026', 'MTH-2026', 'ENG-2026'];

export const AttendanceFilterBar: React.FC = () => {
  const filters = useAttendanceFilters();
  const { setFilter, clearFilters, fetchAttendanceSummary } = useAttendanceActions();

  const handleChange = (key: 'semester' | 'cohortCode', value: string) => {
    setFilter(key, value);
  };

  const handleApply = () => {
    fetchAttendanceSummary();
  };

  return (
    <div className={styles.filterBar} role="search" aria-label="Attendance filters">
      <div className={styles.filterGroup}>
        <label htmlFor="semester-filter" className={styles.filterLabel}>Semester</label>
        <select
          id="semester-filter"
          className={styles.filterSelect}
          value={filters.semester}
          onChange={(e) => handleChange('semester', e.target.value)}
          aria-label="Filter by semester"
        >
          {SEMESTERS.map((s) => (
            <option key={s} value={s}>{s || 'All Semesters'}</option>
          ))}
        </select>
      </div>

      <div className={styles.filterGroup}>
        <label htmlFor="cohort-filter" className={styles.filterLabel}>Cohort</label>
        <select
          id="cohort-filter"
          className={styles.filterSelect}
          value={filters.cohortCode}
          onChange={(e) => handleChange('cohortCode', e.target.value)}
          aria-label="Filter by cohort"
        >
          {COHORTS.map((c) => (
            <option key={c} value={c}>{c || 'All Cohorts'}</option>
          ))}
        </select>
      </div>

      <div className={styles.filterActions}>
        <button
          onClick={handleApply}
          className={styles.applyBtn}
          aria-label="Apply attendance filters"
        >
          Apply Filters
        </button>
        <button
          onClick={() => { clearFilters(); fetchAttendanceSummary(); }}
          className={styles.clearBtn}
          aria-label="Clear all filters"
        >
          Clear
        </button>
      </div>
    </div>
  );
};
