'use client';

import React, { useEffect } from 'react';
import {
  useSelectedTask,
  useTaskIsLoadingTask,
  useTaskPollingId,
  useTaskError,
  useTaskActions,
} from '../store/taskStatusStore';
import { TaskProgressCard } from './TaskProgressCard';
import { TaskStatusIndicator } from './TaskStatusIndicator';
import { TaskProgressTimeline } from './TaskProgressTimeline';
import { TaskResultBanner } from './TaskResultBanner';
import styles from './TaskProgressMonitorPage.module.css';

export const TaskProgressMonitorPage: React.FC = () => {
  const selectedTask = useSelectedTask();
  const isLoadingTask = useTaskIsLoadingTask();
  const pollingId = useTaskPollingId();
  const error = useTaskError();
  const { fetchTaskList, stopPolling } = useTaskActions();

  useEffect(() => {
    fetchTaskList();
    return () => { stopPolling(); };
  }, [fetchTaskList, stopPolling]);

  return (
    <main className={styles.page}>
      <header className={styles.pageHeader}>
        <div>
          <h1 className={styles.pageTitle}>Background Task Monitor</h1>
          <p className={styles.pageSubtitle}>
            Real-time execution status for long-running platform jobs.
          </p>
        </div>
        {pollingId && (
          <div className={styles.pollingBadge} aria-live="polite">
            <span className={styles.pulsingDot} aria-hidden="true" />
            Polling {pollingId}
          </div>
        )}
      </header>

      {error && (
        <div className={styles.errorBannerGlobal} role="alert">
          <strong>Error:</strong> {error}
          <button className={styles.retryBtn} onClick={fetchTaskList}>Retry</button>
        </div>
      )}

      <section aria-label="Task registry">
        <h2 className={styles.sectionTitle}>Active Job Registry</h2>
        <TaskProgressCard />
      </section>

      {selectedTask && (
        <section className={styles.detailPanel} aria-label="Selected task detail">
          <div className={styles.detailHeader}>
            <div>
              <h2 className={styles.sectionTitle}>Task Detail</h2>
              <code className={styles.taskId}>{selectedTask.task_id}</code>
            </div>
            <TaskStatusIndicator status={selectedTask.status} />
          </div>

          {isLoadingTask && (
            <div className={styles.statusRow} role="status" aria-live="polite">
              <span className={styles.spinner} aria-hidden="true" />
              Refreshing task status…
            </div>
          )}

          {/* Progress bar */}
          <div className={styles.detailProgressWrap}>
            <div className={styles.progressBarTrack}>
              <div
                className={styles.progressBarFill}
                style={{
                  width: `${selectedTask.progress_pct}%`,
                  backgroundColor:
                    selectedTask.status === 'Failed' ? 'var(--critical)'
                    : selectedTask.status === 'Completed' ? 'var(--safe)'
                    : 'var(--brand)',
                  transition: 'width 0.5s ease',
                }}
                role="progressbar"
                aria-valuenow={selectedTask.progress_pct}
                aria-valuemin={0}
                aria-valuemax={100}
              />
            </div>
            <span className={styles.progressPct}>{selectedTask.progress_pct}%</span>
          </div>

          <TaskResultBanner />
          <TaskProgressTimeline />
        </section>
      )}
    </main>
  );
};
