'use client';

import React from 'react';
import {
  useGradeValue,
  useGradeValidationError,
  useGradeIsSubmitting,
  useGradeSubmitSuccess,
  useGradeActions,
} from '../store/gradeStore';
import styles from './GradeEditor.module.css';

export const GradeEditor: React.FC = () => {
  const gradeValue = useGradeValue();
  const error = useGradeValidationError();
  const isSubmitting = useGradeIsSubmitting();
  const success = useGradeSubmitSuccess();
  const { setGradeValue, formatGradeValue, submitGrade } = useGradeActions();

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (error || !gradeValue.trim()) return;
    await submitGrade();
  };

  const isInvalid = !!error || !gradeValue.trim();

  return (
    <div className={styles.card}>
      <h3 className={styles.title}>Grade Ledger Editor</h3>
      <p className={styles.subtitle}>Enter term numeric decimals. Enforces absolute scale constraints.</p>

      <form onSubmit={handleSubmit} className={styles.form}>
        <div className={styles.inputWrapper}>
          <label htmlFor="numeric-grade-input" className={styles.label}>
            Term Evaluation Score (0.00 - 100.00)
          </label>
          <input
            id="numeric-grade-input"
            type="text"
            className={`${styles.input} ${error ? styles.invalidInput : ''}`}
            placeholder="e.g. 95.50"
            value={gradeValue}
            onChange={(e) => setGradeValue(e.target.value)}
            onBlur={formatGradeValue}
            disabled={isSubmitting}
            aria-invalid={!!error}
            aria-describedby={error ? "grade-error-desc" : undefined}
          />

          {error && (
            <div id="grade-error-desc" className={styles.validationBadge} role="alert">
              {error}
            </div>
          )}

          {success && (
            <div className={styles.successBadge} role="status">
              Term grade recorded successfully in local state ledger.
            </div>
          )}
        </div>

        <button
          type="submit"
          className={styles.submitBtn}
          disabled={isInvalid || isSubmitting}
        >
          {isSubmitting ? 'Recording...' : 'Update Grade Entry'}
        </button>
      </form>
    </div>
  );
};
