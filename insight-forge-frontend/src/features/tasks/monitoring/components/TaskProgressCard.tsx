'use client';

import React from 'react';
import { useTaskList, useTaskIsLoadingList, useTaskActions, type TaskSummary } from '../store/taskStatusStore';
import { TaskStatusIndicator } from './TaskStatusIndicator';
import styles from './TaskProgressMonitorPage.module.css';

export const TaskProgressCard: React.FC = () => {
  const taskList = useTaskList();
  const isLoading = useTaskIsLoadingList();
  const { selectTask } = useTaskActions();

  if (isLoading) {
    return (
      <div className={styles.statusRow} role="status" aria-live="polite">
        <span className={styles.spinner} aria-hidden="true" />
        Loading task registry…
      </div>
    );
  }

  if (!taskList.length) {
    return (
      <div className={styles.emptyState} role="status">
        No background tasks found in the current execution registry.
      </div>
    );
  }

  return (
    <div className={styles.cardGrid} role="list" aria-label="Background task list">
      {taskList.map((task: TaskSummary) => (
        <button
          key={task.task_id}
          className={styles.taskCard}
          onClick={() => selectTask(task.task_id)}
          role="listitem"
          aria-label={`View task ${task.task_id}, type ${task.task_type}, status ${task.status}`}
        >
          <div className={styles.taskCardHeader}>
            <span className={styles.taskType}>{task.task_type}</span>
            <TaskStatusIndicator status={task.status} size="sm" />
          </div>
          <code className={styles.taskId}>{task.task_id}</code>
          <div className={styles.progressBarWrap}>
            <div
              className={styles.progressBarFill}
              style={{
                width: `${task.progress_pct}%`,
                backgroundColor: task.status === 'Failed' ? 'var(--critical)'
                  : task.status === 'Completed' ? 'var(--safe)' : 'var(--brand)',
              }}
              role="progressbar"
              aria-valuenow={task.progress_pct}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label={`Task progress: ${task.progress_pct}%`}
            />
          </div>
          <span className={styles.progressPct}>{task.progress_pct}%</span>
          {task.started_at && (
            <span className={styles.taskMeta}>
              Started: {new Date(task.started_at).toLocaleTimeString()}
            </span>
          )}
        </button>
      ))}
    </div>
  );
};
