'use client';

import React, { useEffect, useRef, useState } from 'react';
import {
  useInterventionLoading,
  useInterventionError,
  useInterventionSuccess,
  useInterventionActions,
} from '../store/interventionStore';
import styles from './CoachingDrawer.module.css';

interface StudentRosterItem {
  id: string;
  name: string;
  email: string;
  gpa: number;
  status: string;
  risk_level?: string;
}

interface CoachingDrawerProps {
  student: StudentRosterItem | null;
  onClose: () => void;
  onSubmitSuccess: () => void;
}

export const CoachingDrawer: React.FC<CoachingDrawerProps> = ({ student, onClose, onSubmitSuccess }) => {
  const loading = useInterventionLoading();
  const error = useInterventionError();
  const success = useInterventionSuccess();
  const { recordIntervention, resetIntervention } = useInterventionActions();

  const [notes, setNotes] = useState('');
  const [validationError, setValidationError] = useState<string | null>(null);

  const drawerRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLElement | null>(null);
  const textareaRef = useRef<HTMLTextAreaElement>(null);

  useEffect(() => {
    if (student) {
      triggerRef.current = document.activeElement as HTMLElement;
      resetIntervention();
      setNotes('');
      setValidationError(null);
      setTimeout(() => {
        textareaRef.current?.focus();
      }, 100);
    }
  }, [student, resetIntervention]);

  useEffect(() => {
    if (!student) return;

    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape') {
        onClose();
        triggerRef.current?.focus();
        return;
      }

      if (e.key === 'Tab') {
        if (!drawerRef.current) return;
        const focusableElements = drawerRef.current.querySelectorAll<HTMLElement>(
          'button, textarea, a, [tabindex="0"]'
        );
        if (focusableElements.length === 0) return;
        const first = focusableElements[0];
        const last = focusableElements[focusableElements.length - 1];

        if (e.shiftKey) {
          if (document.activeElement === first) {
            last.focus();
            e.preventDefault();
          }
        } else {
          if (document.activeElement === last) {
            first.focus();
            e.preventDefault();
          }
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [student, onClose]);

  if (!student) return null;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setValidationError(null);

    const trimmedNotes = notes.trim();
    if (!trimmedNotes) {
      setValidationError('Coaching notes are required.');
      return;
    }

    if (trimmedNotes.length > 1000) {
      setValidationError('Coaching notes cannot exceed 1000 characters.');
      return;
    }

    await recordIntervention(student.id, trimmedNotes);
    onSubmitSuccess();
  };

  return (
    <div className={styles.overlay} onClick={() => { onClose(); triggerRef.current?.focus(); }}>
      <div 
        ref={drawerRef}
        className={styles.drawer} 
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="drawer-student-name"
      >
        <header className={styles.header}>
          <h2 id="drawer-student-name" className={styles.title}>Coaching Workspace</h2>
          <button 
            onClick={() => { onClose(); triggerRef.current?.focus(); }} 
            className={styles.closeBtn}
            aria-label="Close coaching drawer"
          >
            ✕
          </button>
        </header>

        <div className={styles.content}>
          <section className={styles.profileSection}>
            <h3 className={styles.sectionTitle}>Student Profile</h3>
            <div className={styles.profileCard}>
              <div className={styles.profileRow}>
                <span className={styles.profileLabel}>Name:</span>
                <span className={styles.profileVal}>{student.name}</span>
              </div>
              <div className={styles.profileRow}>
                <span className={styles.profileLabel}>Email:</span>
                <span className={styles.profileVal}>{student.email}</span>
              </div>
              <div className={styles.profileRow}>
                <span className={styles.profileLabel}>Term GPA:</span>
                <span className={styles.profileVal}>{student.gpa.toFixed(2)}</span>
              </div>
              {student.risk_level && (
                <div className={styles.profileRow}>
                  <span className={styles.profileLabel}>Risk:</span>
                  <span className={styles.profileVal}>{student.risk_level}</span>
                </div>
              )}
            </div>
          </section>

          <section className={styles.notesSection}>
            <h3 className={styles.sectionTitle}>Log Academic Intervention</h3>
            
            {success ? (
              <div className={styles.successMessage} role="status">
                <div className={styles.successIcon}>✓</div>
                <p>Academic intervention action recorded securely.</p>
                <button 
                  onClick={() => { onClose(); triggerRef.current?.focus(); }} 
                  className={styles.doneBtn}
                >
                  Done
                </button>
              </div>
            ) : (
              <form onSubmit={handleSubmit} className={styles.form}>
                <div className={styles.textareaWrapper}>
                  <label htmlFor="coaching-notes-textarea" className={styles.notesLabel}>
                    Intervention Notes (Max 1000 characters)
                  </label>
                  <textarea
                    id="coaching-notes-textarea"
                    ref={textareaRef}
                    className={`${styles.textarea} ${validationError ? styles.invalidField : ''}`}
                    placeholder="Enter academic support details, tutoring setups, or attendance review actions..."
                    value={notes}
                    onChange={(e) => setNotes(e.target.value)}
                    maxLength={1010}
                    disabled={loading}
                    aria-invalid={validationError ? 'true' : 'false'}
                  />
                  {validationError && (
                    <span className={styles.validationText} role="alert">
                      {validationError}
                    </span>
                  )}
                  {error && (
                    <span className={styles.validationText} role="alert">
                      ⚠️ {error}
                    </span>
                  )}
                </div>

                <div className={styles.formActions}>
                  <button
                    type="submit"
                    className={styles.submitBtn}
                    disabled={loading}
                  >
                    {loading ? 'Submitting...' : 'Record Action Notes'}
                  </button>
                  <button
                    type="button"
                    onClick={() => { onClose(); triggerRef.current?.focus(); }}
                    className={styles.cancelBtn}
                    disabled={loading}
                  >
                    Cancel
                  </button>
                </div>
              </form>
            )}
          </section>
        </div>
      </div>
    </div>
  );
};
