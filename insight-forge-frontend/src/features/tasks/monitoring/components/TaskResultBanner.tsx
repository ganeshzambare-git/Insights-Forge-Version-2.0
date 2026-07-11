'use client';

import React from 'react';
import { useSelectedTask, useTaskIsLoadingTask } from '../store/taskStatusStore';
import { TaskStatusIndicator } from './TaskStatusIndicator';
import styles from './TaskProgressMonitorPage.module.css';

export const TaskResultBanner: React.FC = () => {
  const task = useSelectedTask();
  const isLoading = useTaskIsLoadingTask();

  if (isLoading || !task) return null;

  if (task.status === 'Completed' && task.result) {
    return (
      <div className={styles.successBanner} role="alert" aria-live="polite">
        <div className={styles.bannerHeader}>
          <TaskStatusIndicator status="Completed" />
          <strong>Task completed successfully</strong>
        </div>
        {task.result.record_count !== undefined && (
          <p>Records processed: <strong>{task.result.record_count.toLocaleString()}</strong></p>
        )}
        {task.result.file_size_kb !== undefined && (
          <p>Output file size: <strong>{task.result.file_size_kb} KB</strong></p>
        )}
        {task.result.download_url && (
          <a href={task.result.download_url} className={styles.downloadLink} aria-label="Download task output file">
            Download Output
          </a>
        )}
      </div>
    );
  }

  if (task.status === 'Failed' && task.error) {
    return (
      <div className={styles.errorBannerTask} role="alert" aria-live="assertive">
        <div className={styles.bannerHeader}>
          <TaskStatusIndicator status="Failed" />
          <strong>Task failed</strong>
        </div>
        <p className={styles.errorCode}>Error Code: <code>{task.error.code}</code></p>
        <p>{task.error.message}</p>
        {task.error.recovery && (
          <div className={styles.recoveryBlock}>
            <strong>Recovery Guidance:</strong>
            <p>{task.error.recovery}</p>
          </div>
        )}
      </div>
    );
  }

  return null;
};
