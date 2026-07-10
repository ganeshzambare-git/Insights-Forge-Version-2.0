'use client';

import React, { useEffect, useRef } from 'react';
import { useSelectedLog, useAuditIsTracing, useAuditTraceResult, useAuditActions } from '../store/securityAuditStore';
import styles from './SecurityAuditPage.module.css';

export const AuditDetailsDrawer: React.FC = () => {
  const log = useSelectedLog();
  const isTracing = useAuditIsTracing();
  const traceResult = useAuditTraceResult();
  const { selectLog, initiateTrace } = useAuditActions();
  const closeRef = useRef<HTMLButtonElement>(null);

  useEffect(() => {
    if (log) closeRef.current?.focus();
  }, [log]);

  useEffect(() => {
    if (!log) return;
    const onKey = (e: KeyboardEvent) => {
      if (e.key === 'Escape') selectLog(null);
    };
    window.addEventListener('keydown', onKey);
    return () => window.removeEventListener('keydown', onKey);
  }, [log, selectLog]);

  if (!log) return null;

  return (
    <div className={styles.drawerOverlay} onClick={() => selectLog(null)}>
      <aside
        className={styles.drawer}
        onClick={(e) => e.stopPropagation()}
        role="complementary"
        aria-label="Audit record detail drawer"
        aria-modal="true"
      >
        <div className={styles.drawerHeader}>
          <h2 className={styles.drawerTitle}>Audit Detail</h2>
          <button
            ref={closeRef}
            onClick={() => selectLog(null)}
            className={styles.drawerClose}
            aria-label="Close audit detail drawer"
          >
            ✕
          </button>
        </div>

        <div className={styles.drawerBody}>
          <dl className={styles.metaGrid}>
            {[
              { label: 'Audit ID',      val: log.audit_id,       mono: true  },
              { label: 'Event Type',    val: log.event_type,     mono: true  },
              { label: 'Severity',      val: log.severity,       mono: false },
              { label: 'Source IP',     val: log.source_ip,      mono: true  },
              { label: 'User',          val: log.user_email,     mono: false },
              { label: 'Session Token', val: log.session_token ?? '—', mono: true },
              { label: 'Timestamp',     val: new Date(log.timestamp).toLocaleString(), mono: true },
            ].map(({ label, val, mono }) => (
              <React.Fragment key={label}>
                <dt className={styles.metaLabel}>{label}</dt>
                <dd className={mono ? `${styles.metaVal} ${styles.mono}` : styles.metaVal}>{val}</dd>
              </React.Fragment>
            ))}
          </dl>

          <div className={styles.metadataBlock}>
            <h3 className={styles.metadataTitle}>Raw Metadata</h3>
            <pre className={styles.metadataPre}>{JSON.stringify(log.metadata, null, 2)}</pre>
          </div>

          {/* Trace Action Panel */}
          <div className={styles.tracePanel}>
            <h3 className={styles.traceTitle}>Forensic Trace</h3>
            <p className={styles.traceDesc}>
              Initiate a backend forensic trace on this event. The platform will queue an investigation
              pipeline and return a trace reference.
            </p>
            <button
              onClick={() => initiateTrace(log.audit_id)}
              disabled={isTracing}
              className={styles.traceBtn}
              aria-label={`Initiate forensic trace for ${log.audit_id}`}
            >
              {isTracing ? (
                <><span className={styles.spinner} aria-hidden="true" /> Tracing…</>
              ) : (
                '🔍 Initiate Trace'
              )}
            </button>
            {traceResult && (
              <div className={styles.traceResult} role="status" aria-live="polite">
                {traceResult}
              </div>
            )}
          </div>
        </div>
      </aside>
    </div>
  );
};
