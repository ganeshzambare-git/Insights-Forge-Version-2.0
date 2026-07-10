'use client';

import React from 'react';
import { useSelectedTask } from '../store/taskStatusStore';
import styles from './TaskProgressMonitorPage.module.css';

export const TaskProgressTimeline: React.FC = () => {
  const task = useSelectedTask();
  if (!task || !task.timeline.length) return null;

  return (
    <section className={styles.timelineSection} aria-label="Task execution timeline">
      <h3 className={styles.sectionTitle}>Execution Timeline</h3>
      <ol className={styles.timeline}>
        {task.timeline.map((event, idx) => (
          <li key={idx} className={styles.timelineItem}>
            <span className={styles.timelineDot} aria-hidden="true" />
            <div className={styles.timelineContent}>
              <span className={styles.timelineEvent}>{event.event}</span>
              <time className={styles.timelineTs} dateTime={event.timestamp}>
                {new Date(event.timestamp).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', second: '2-digit' })}
              </time>
            </div>
          </li>
        ))}
      </ol>
    </section>
  );
};
