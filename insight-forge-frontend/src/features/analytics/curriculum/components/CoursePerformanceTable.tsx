'use client';

import React from 'react';
import { useCourseList, useTotalCourses, type CourseEvaluationRecord } from '../store/courseAnalyticsStore';
import styles from './CourseAnalyticsPage.module.css';

const KPI_COLORS: Record<string, string> = {
  'Exceeding': '#34d399',
  'On Track':  '#38bdf8',
  'At Risk':   '#f59e0b',
  'Critical':  '#f87171',
};

const KPI_BG: Record<string, string> = {
  'Exceeding': 'rgba(52, 211, 153, 0.1)',
  'On Track':  'rgba(56, 189, 248, 0.1)',
  'At Risk':   'rgba(245, 158, 11, 0.1)',
  'Critical':  'rgba(248, 113, 113, 0.1)',
};

export const CoursePerformanceTable: React.FC = () => {
  const courses = useCourseList();
  const total = useTotalCourses();

  if (!courses.length) {
    return (
      <div className={styles.emptyState} role="status">
        No course evaluation records match the selected filters.
      </div>
    );
  }

  return (
    <section className={styles.tableSection} aria-label="Course performance table">
      <div className={styles.tableHeader}>
        <span className={styles.tableCount}>{total} Course{total !== 1 ? 's' : ''} found</span>
      </div>
      <div className={styles.tableWrapper} role="region" aria-label="Scrollable course table" tabIndex={0}>
        <table className={styles.table} aria-label="Course evaluation metrics">
          <thead>
            <tr>
              <th scope="col" className={styles.th}>Course ID</th>
              <th scope="col" className={styles.th}>Course Name</th>
              <th scope="col" className={styles.th}>Department</th>
              <th scope="col" className={styles.th}>Cohort</th>
              <th scope="col" className={styles.th}>Avg Score</th>
              <th scope="col" className={styles.th}>Pass Rate</th>
              <th scope="col" className={styles.th}>Enrolment</th>
              <th scope="col" className={styles.th}>Evaluations</th>
              <th scope="col" className={styles.th}>KPI Status</th>
            </tr>
          </thead>
          <tbody>
            {courses.map((course: CourseEvaluationRecord) => (
              <tr key={course.course_id} className={styles.tr}>
                <td className={`${styles.td} ${styles.codeCell}`}>{course.course_id}</td>
                <td className={styles.td}>{course.course_name}</td>
                <td className={styles.td}>{course.department}</td>
                <td className={`${styles.td} ${styles.codeCell}`}>{course.cohort_code}</td>
                <td className={styles.td}>{course.avg_score.toFixed(1)}</td>
                <td className={styles.td}>{course.pass_rate.toFixed(1)}%</td>
                <td className={styles.td}>{course.enrollment}</td>
                <td className={styles.td}>{course.evaluations_submitted}</td>
                <td className={styles.td}>
                  <span
                    className={styles.kpiBadge}
                    style={{
                      color: KPI_COLORS[course.kpi_status] ?? '#94a3b8',
                      backgroundColor: KPI_BG[course.kpi_status] ?? 'rgba(148,163,184,0.1)',
                    }}
                    aria-label={`KPI status: ${course.kpi_status}`}
                  >
                    {course.kpi_status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
};
