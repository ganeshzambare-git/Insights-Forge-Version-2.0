'use client';

import React, { useEffect, useRef, useState } from 'react';
import {
  useRosterRecords,
  useRosterLoading,
  useRosterError,
  useRosterActions,
} from '../store/rosterStore';
import { useDebouncedSearch } from '../../../../shared/hooks/useDebouncedSearch';
import { RiskIndicatorBadge } from './RiskIndicatorBadge';
import { CoachingDrawer } from '../../interventions/components/CoachingDrawer';
import styles from './FacultyRosterPage.module.css';

export interface StudentRosterItem {
  id: string;
  name: string;
  email: string;
  gpa: number;
  status: string;
  risk_level?: string;
}

export const FacultyRosterPage: React.FC = () => {
  const records = useRosterRecords();
  const loading = useRosterLoading();
  const error = useRosterError();
  const { fetchCohortRoster } = useRosterActions();

  const [query, setQuery] = useState('');
  const [selectedStudent, setSelectedStudent] = useState<StudentRosterItem | null>(null);
  const debouncedQuery = useDebouncedSearch(query, 300);

  const [scrollTop, setScrollTop] = useState(0);
  const containerRef = useRef<HTMLDivElement>(null);

  // Fetch roster when debounced search query changes
  useEffect(() => {
    fetchCohortRoster('88888888-8888-8888-8888-888888888888', debouncedQuery);
  }, [fetchCohortRoster, debouncedQuery]);

  const handleScroll = (e: React.UIEvent<HTMLDivElement>) => {
    setScrollTop(e.currentTarget.scrollTop);
  };

  const clearSearch = () => {
    setQuery('');
  };

  const ROW_HEIGHT = 44;
  const VIEWPORT_HEIGHT = 400;

  const totalHeight = records.length * ROW_HEIGHT;
  const startIndex = Math.max(0, Math.floor(scrollTop / ROW_HEIGHT) - 5);
  const endIndex = Math.min(records.length, Math.ceil((scrollTop + VIEWPORT_HEIGHT) / ROW_HEIGHT) + 5);

  const visibleRecords = records.slice(startIndex, endIndex).map((record, index) => ({
    record,
    absoluteIndex: startIndex + index,
  }));

  return (
    <div className={styles.container}>
      <h3 className={styles.title}>Faculty Roster Visualizer</h3>
      <p className={styles.subtitle}>
        High-scale custom row virtualization rendering 200 student files with sticky headers.
      </p>

      {/* Task 16: Search input toolbar */}
      <div className={styles.toolbar}>
        <div className={styles.searchWrapper}>
          <label htmlFor="roster-search-input" className={styles.srOnly}>Search students</label>
          <input
            id="roster-search-input"
            type="text"
            className={styles.searchInput}
            placeholder="Search students by name or email..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
          />
          {query && (
            <button onClick={clearSearch} className={styles.clearBtn} aria-label="Clear search input">
              Clear
            </button>
          )}
        </div>
        {loading && <div className={styles.smallLoader}>Searching...</div>}
      </div>

      {error && records.length === 0 && (
        <div className={styles.errorCard}>
          <p>⚠️ Roster connection error: {error}</p>
          <button onClick={() => fetchCohortRoster('88888888-8888-8888-8888-888888888888', query)} className={styles.retryBtn}>
            Retry Connection
          </button>
        </div>
      )}

      {/* Task 16: Empty search results state */}
      {!loading && records.length === 0 && query && (
        <div className={styles.emptyStatePanel} role="status">
          <div className={styles.emptyIcon}>🔍</div>
          <h4>No Match Found</h4>
          <p>Roster search returned zero records. Broaden search keywords or clear queries to list all cohort items.</p>
          <button onClick={clearSearch} className={styles.resetSearchBtn}>
            Clear Search Filter
          </button>
        </div>
      )}

      {records.length > 0 && (
        <div className={styles.viewportWrapper}>
          <div className={styles.stickyHeader}>
            <div className={styles.headerCell} style={{ width: '10%' }}>Index</div>
            <div className={styles.headerCell} style={{ width: '25%' }}>Student Name</div>
            <div className={styles.headerCell} style={{ width: '25%' }}>Institutional Email</div>
            <div className={styles.headerCell} style={{ width: '10%' }}>GPA</div>
            <div className={styles.headerCell} style={{ width: '15%' }}>Risk Badge</div>
            <div className={styles.headerCell} style={{ width: '15%' }}>Roster Status</div>
          </div>

          <div 
            ref={containerRef}
            onScroll={handleScroll}
            className={styles.scrollContainer}
            style={{ height: `${VIEWPORT_HEIGHT}px` }}
          >
            <div style={{ height: `${totalHeight}px`, width: '100%', position: 'relative' }}>
              {visibleRecords.map(({ record, absoluteIndex }) => {
                const bg = absoluteIndex % 2 === 0 ? '#FFFFFF' : '#F7FAFC';
                return (
                  <div 
                    key={record.id}
                    role="button"
                    tabIndex={0}
                    onClick={() => setSelectedStudent(record)}
                    onKeyDown={(e) => {
                      if (e.key === 'Enter' || e.key === ' ') {
                        e.preventDefault();
                        setSelectedStudent(record);
                      }
                    }}
                    className={styles.rosterRow}
                    style={{
                      position: 'absolute',
                      top: `${absoluteIndex * ROW_HEIGHT}px`,
                      height: `${ROW_HEIGHT}px`,
                      backgroundColor: bg,
                      width: '100%',
                      display: 'flex',
                      alignItems: 'center'
                    }}
                    aria-label={`Student row: ${record.name}, GPA: ${record.gpa.toFixed(2)}, click to log coaching interventions.`}
                  >
                    <div className={styles.cell} style={{ width: '10%', fontWeight: 700 }}>#{absoluteIndex + 1}</div>
                    <div className={styles.cell} style={{ width: '25%', fontWeight: 600 }}>{record.name}</div>
                    <div className={styles.cell} style={{ width: '25%' }}>{record.email}</div>
                    <div className={styles.cell} style={{ width: '10%' }}>{record.gpa.toFixed(2)}</div>
                    
                    {/* Task 17: Machine Learning Risk Indicators Badges */}
                    <div className={styles.cell} style={{ width: '15%' }}>
                      <RiskIndicatorBadge riskLevel={record.risk_level} />
                    </div>

                    <div className={styles.cell} style={{ width: '15%' }}>
                      <span className={record.status === 'Enrolled' ? styles.statusEnrolled : styles.statusProbation}>
                        {record.status}
                      </span>
                    </div>
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      )}

      {records.length > 0 && (
        <div className={styles.footerCount}>
          Rendering virtual window slots: <strong>{startIndex} - {endIndex}</strong> of {records.length} database logs.
        </div>
      )}

      {/* Task 18: Coaching Interventions slide side panel */}
      {selectedStudent && (
        <CoachingDrawer
          student={selectedStudent}
          onClose={() => setSelectedStudent(null)}
          onSubmitSuccess={() => {
            fetchCohortRoster('88888888-8888-8888-8888-888888888888', debouncedQuery);
          }}
        />
      )}
    </div>
  );
};
