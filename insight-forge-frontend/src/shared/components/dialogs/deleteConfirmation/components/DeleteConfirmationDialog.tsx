'use client';

import React, { useEffect, useRef } from 'react';
import {
  useDeleteIsDeleting,
  useDeleteIsConfirming,
  useDeleteConflictError,
  useDeleteDependencies,
  useDeleteActions,
} from '../store/deleteStore';
import styles from './DeleteConfirmationDialog.module.css';

interface DeleteConfirmationDialogProps {
  cohortId: string;
  cohortCode: string;
  onSuccess: () => void;
}

export const DeleteConfirmationDialog: React.FC<DeleteConfirmationDialogProps> = ({
  cohortId,
  cohortCode,
  onSuccess,
}) => {
  const isDeleting = useDeleteIsDeleting();
  const isConfirming = useDeleteIsConfirming();
  const conflictError = useDeleteConflictError();
  const dependencies = useDeleteDependencies();
  const { confirmDeleteCohort, cancelDelete } = useDeleteActions();

  const modalRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLElement | null>(null);

  useEffect(() => {
    triggerRef.current = document.activeElement as HTMLElement;
    return () => {
      triggerRef.current?.focus();
    };
  }, []);

  useEffect(() => {
    if (!isConfirming) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        cancelDelete();
        return;
      }
      if (e.key === 'Tab') {
        if (!modalRef.current) return;
        const focusable = modalRef.current.querySelectorAll<HTMLElement>('button, a, [tabindex="0"]');
        if (focusable.length === 0) return;
        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (e.shiftKey) {
          if (document.activeElement === first) { last.focus(); e.preventDefault(); }
        } else {
          if (document.activeElement === last) { first.focus(); e.preventDefault(); }
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [isConfirming, cancelDelete]);

  if (!isConfirming) return null;

  const handleConfirm = async () => {
    const deleted = await confirmDeleteCohort(cohortId);
    if (deleted) {
      onSuccess();
    }
  };

  return (
    <div className={styles.overlay} onClick={cancelDelete}>
      <div
        ref={modalRef}
        className={styles.modal}
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        <header className={styles.header}>
          <h3 id="modal-title" className={styles.title}>Confirm Cohort Removal</h3>
          <button onClick={cancelDelete} className={styles.closeBtn} aria-label="Cancel deletion">✕</button>
        </header>

        <div className={styles.content}>
          <p className={styles.warningText}>
            Are you sure you want to delete cohort <strong>{cohortCode}</strong>? This operation checks active dependencies.
          </p>

          {conflictError && (
            <div className={styles.conflictPanel} role="alert">
              <h4 className={styles.conflictTitle}>Referential Constraint Check Failed</h4>
              <p className={styles.conflictMsg}>{conflictError}</p>
              {dependencies.length > 0 && (
                <div className={styles.dependencySection}>
                  <h5 className={styles.dependencyTitle}>Active Database Relations:</h5>
                  <ul className={styles.dependencyList}>
                    {dependencies.map((dep, idx) => (
                      <li key={idx} className={styles.dependencyItem}>
                        <span className={styles.entityType}>{dep.type}</span>{' '}
                        (ID: <code style={{ fontFamily: 'monospace' }}>{dep.id}</code>)
                        <div className={styles.entitySummary}>{dep.summary}</div>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          )}
        </div>

        <footer className={styles.footer}>
          <button
            onClick={handleConfirm}
            className={styles.deleteBtn}
            disabled={isDeleting || !!conflictError}
          >
            {isDeleting ? 'Deleting...' : 'Confirm Expunge'}
          </button>
          <button onClick={cancelDelete} className={styles.cancelBtn} disabled={isDeleting}>
            Close Dialog
          </button>
        </footer>
      </div>
    </div>
  );
};
