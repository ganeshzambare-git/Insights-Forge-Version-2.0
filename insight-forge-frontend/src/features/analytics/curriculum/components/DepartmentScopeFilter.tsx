'use client';

import React from 'react';
import { useCourseFilters, useCourseActions } from '../store/courseAnalyticsStore';
import styles from './CourseAnalyticsPage.module.css';

const DEPARTMENTS = ['', 'Computer Science', 'Mathematics', 'Engineering'];

export const DepartmentScopeFilter: React.FC = () => {
  const filters = useCourseFilters();
  const { setFilter } = useCourseActions();

  return (
    <div className={styles.filterGroup}>
      <label htmlFor="dept-filter" className={styles.filterLabel}>Department</label>
      <select
        id="dept-filter"
        className={styles.filterSelect}
        value={filters.department}
        onChange={(e) => setFilter('department', e.target.value)}
        aria-label="Filter by department"
      >
        {DEPARTMENTS.map((d) => (
          <option key={d} value={d}>{d || 'All Departments'}</option>
        ))}
      </select>
    </div>
  );
};
