'use client';

import React, { useEffect } from 'react';
import {
  useStudentSelectedTerm,
  useStudentLoading,
  useStudentError,
  useStudentGpa,
  useStudentAttendanceRate,
  useStudentLedgerEmpty,
  useStudentRecords,
  useStudentAttendanceHistory,
  useStudentStudyModules,
  useStudentGpaHistory,
  useCohortGpaHistory,
  useStudentActions,
} from '../store/studentStore';
import styles from './StudentDashboard.module.css';

export const StudentDashboard: React.FC = () => {
  const selectedTerm = useStudentSelectedTerm();
  const loading = useStudentLoading();
  const error = useStudentError();
  const gpa = useStudentGpa();
  const attendanceRate = useStudentAttendanceRate();
  const ledgerEmpty = useStudentLedgerEmpty();
  const records = useStudentRecords();
  const attendanceHistory = useStudentAttendanceHistory();
  const studyModules = useStudentStudyModules();
  const studentGpaHistory = useStudentGpaHistory();
  const cohortGpaHistory = useCohortGpaHistory();
  const { setSelectedTerm, fetchStudentDashboardData } = useStudentActions();

  useEffect(() => {
    fetchStudentDashboardData();
  }, [fetchStudentDashboardData]);

  const terms = ['Fall 2026', 'Spring 2026', 'EmptyTerm'];

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <div>
          <h1 className={styles.title}>Learner Analytics Canvas</h1>
          <p className={styles.subtitle}>Review your term GPAs, attendances, and cohort comparisons (Student-1 & Student-2 views)</p>
        </div>

        <div className={styles.termTabs} role="tablist" aria-label="Academic Term Selector">
          {terms.map((term) => (
            <button
              key={term}
              role="tab"
              aria-selected={selectedTerm === term}
              className={`${styles.termTab} ${selectedTerm === term ? styles.activeTab : ''}`}
              onClick={() => setSelectedTerm(term)}
            >
              {term === 'EmptyTerm' ? 'Empty Ledger Term' : term}
            </button>
          ))}
        </div>
      </header>

      {error && (
        <div className={styles.errorAlert} role="alert">
          <span></span> {error}
        </div>
      )}

      {loading && <div className={styles.loader}>Synchronizing term records...</div>}

      <div className={styles.dashboardGrid}>
        <div className={styles.leftCol}>
          <section className={styles.cardsGrid}>
            <div className={styles.statCard}>
              <h3>Cumulative GPA</h3>
              <div className={styles.statVal} style={{ fontFamily: 'monospace' }}>
                {ledgerEmpty ? '0.00' : gpa.toFixed(2)}
              </div>
              <p className={styles.statMeta}>Target: 4.00 max</p>
            </div>
            <div className={styles.statCard}>
              <h3>Attendance Rate</h3>
              <div className={styles.statVal} style={{ fontFamily: 'monospace' }}>
                {attendanceRate}%
              </div>
              <p className={styles.statMeta}>Threshold: 90% min</p>
            </div>
          </section>

          <section className={styles.sectionCard}>
            <h2 className={styles.sectionTitle}>Grade Ledger Records</h2>
            {ledgerEmpty ? (
              <div className={styles.emptyLedgerCard} role="status">
                <p>Grade ledger is empty. Normalization metrics will display once term evaluations begin.</p>
              </div>
            ) : (
              <div className={styles.tableWrapper}>
                <table className={styles.table}>
                  <thead>
                    <tr>
                      <th style={{ textAlign: 'left' }}>Subject</th>
                      <th>Grade</th>
                      <th>Score</th>
                    </tr>
                  </thead>
                  <tbody>
                    {records.map((r, i) => (
                      <tr key={i}>
                        <td style={{ textAlign: 'left', fontWeight: 600 }}>{r.subject}</td>
                        <td style={{ fontFamily: 'monospace', fontWeight: 700, color: 'var(--safe)' }}>{r.grade}</td>
                        <td style={{ fontFamily: 'monospace' }}>{r.score}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            )}
          </section>

          <section className={styles.sectionCard}>
            <h2 className={styles.sectionTitle}>Recent Attendance Logs</h2>
            <div className={styles.tableWrapper}>
              <table className={styles.table}>
                <thead>
                  <tr>
                    <th style={{ textAlign: 'left' }}>Date</th>
                    <th>Status</th>
                  </tr>
                </thead>
                <tbody>
                  {attendanceHistory.map((item, i) => (
                    <tr key={i}>
                      <td style={{ textAlign: 'left', fontFamily: 'monospace' }}>{item.date}</td>
                      <td style={{ fontWeight: 700 }}>
                        <span className={item.status === 'Present' ? styles.presentBadge : styles.absentBadge}>
                          {item.status}
                        </span>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
        </div>

        <div className={styles.rightCol}>
          <section className={styles.chartContainerCard}>
            <h2 className={styles.chartCardTitle}>Performance Distribution Comparison</h2>
            <p className={styles.chartCardSubtitle}>Personal GPA trends compared with aggregate cohort averages</p>

            <div className={styles.chartPlaceholderWrapper}>
              {studentGpaHistory.length > 0 && cohortGpaHistory.length > 0 ? (
                <svg viewBox="0 0 420 220" width="100%" height="220px" style={{ overflow: 'visible' }}>
                  <defs>
                    <linearGradient id="personalCurveGrad" x1="0" y1="0" x2="0" y2="1">
                      <stop offset="0%" stopColor="var(--violet)" stopOpacity="0.15" />
                      <stop offset="100%" stopColor="var(--violet)" stopOpacity="0" />
                    </linearGradient>
                  </defs>

                  <line x1="20" y1="30" x2="400" y2="30" stroke="var(--ink)" strokeWidth="1" />
                  <line x1="20" y1="80" x2="400" y2="80" stroke="var(--ink)" strokeWidth="1" />
                  <line x1="20" y1="130" x2="400" y2="130" stroke="var(--ink)" strokeWidth="1" />
                  <line x1="20" y1="180" x2="400" y2="180" stroke="var(--ink-soft)" strokeWidth="1.5" />

                  <path
                    d={`M 20 ${180 - (cohortGpaHistory[0].val - 1) * 50} 
                       L 146 ${180 - (cohortGpaHistory[1].val - 1) * 50} 
                       L 272 ${180 - (cohortGpaHistory[2].val - 1) * 50} 
                       L 400 ${180 - (cohortGpaHistory[3].val - 1) * 50}`}
                    fill="none"
                    stroke="var(--safe)"
                    strokeWidth="2.5"
                    strokeDasharray="4 4"
                  />

                  <path
                    d={`M 20 ${180 - (studentGpaHistory[0].val - 1) * 50} 
                       L 146 ${180 - (studentGpaHistory[1].val - 1) * 50} 
                       L 272 ${180 - (studentGpaHistory[2].val - 1) * 50} 
                       L 400 ${180 - (studentGpaHistory[3].val - 1) * 50}`}
                    fill="none"
                    stroke="var(--violet)"
                    strokeWidth="3.5"
                    strokeLinecap="round"
                  />

                  <path
                    d={`M 20 ${180 - (studentGpaHistory[0].val - 1) * 50} 
                       L 146 ${180 - (studentGpaHistory[1].val - 1) * 50} 
                       L 272 ${180 - (studentGpaHistory[2].val - 1) * 50} 
                       L 400 ${180 - (studentGpaHistory[3].val - 1) * 50}
                       L 400 180 L 20 180 Z`}
                    fill="url(#personalCurveGrad)"
                  />

                  {studentGpaHistory.map((pt, idx) => {
                    const cx = 20 + idx * 126.6;
                    const cy = 180 - (pt.val - 1) * 50;
                    return (
                      <circle key={idx} cx={cx} cy={cy} r="4.5" fill="var(--ink)" stroke="var(--violet)" strokeWidth="2.5" />
                    );
                  })}

                  <text x="20" y="200" fill="var(--faint)" fontSize="9px" fontWeight="600">W1</text>
                  <text x="146" y="200" fill="var(--faint)" fontSize="9px" fontWeight="600">W4</text>
                  <text x="272" y="200" fill="var(--faint)" fontSize="9px" fontWeight="600">W8</text>
                  <text x="390" y="200" fill="var(--faint)" fontSize="9px" fontWeight="600">W12</text>
                </svg>
              ) : (
                <div style={{ padding: '2rem', textAlign: 'center', color: 'var(--faint)' }}>No comparative distribution data available.</div>
              )}
            </div>

            <div className={styles.chartLegend}>
              <div className={styles.legendItem}>
                <span className={styles.legendLineIndigo} />
                <span>My GPA progress</span>
              </div>
              <div className={styles.legendItem}>
                <span className={styles.legendLineDottedGreen} />
                <span>Cohort aggregate average</span>
              </div>
            </div>
          </section>

          <section className={styles.sectionCard}>
            <h2 className={styles.sectionTitle}>Recommended Study Targets</h2>
            <div className={styles.modulesList}>
              {studyModules.map((mod, i) => (
                <div key={i} className={styles.moduleItem}>
                  <div className={styles.moduleHeader}>
                    <span className={styles.moduleName}>{mod.name}</span>
                    <span className={mod.status === 'Recommended' ? styles.statusBadgeRec : styles.statusBadgeComp}>
                      {mod.status}
                    </span>
                  </div>
                  <div className={styles.moduleMeta} style={{ fontFamily: 'monospace' }}>
                    Est. effort: {mod.duration}
                  </div>
                </div>
              ))}
            </div>
          </section>
        </div>
      </div>
    </div>
  );
};
