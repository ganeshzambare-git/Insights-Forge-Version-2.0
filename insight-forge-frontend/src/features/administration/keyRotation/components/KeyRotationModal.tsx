'use client';

import React, { useEffect, useRef, useState } from 'react';
import {
  useKeyRotationLoading,
  useKeyRotationError,
  useKeyRotationStep,
  useKeyRotationActions,
} from '../store/keyRotationStore';
import styles from './KeyRotationModal.module.css';

export const KeyRotationModal: React.FC = () => {
  const loading = useKeyRotationLoading();
  const error = useKeyRotationError();
  const step = useKeyRotationStep();
  const { closeModal, setStep, rotateKeys } = useKeyRotationActions();

  const [confirmText, setConfirmText] = useState('');
  
  const modalRef = useRef<HTMLDivElement>(null);
  const triggerRef = useRef<HTMLElement | null>(null);

  // Focus restoration on unmount
  useEffect(() => {
    if (typeof document !== 'undefined') {
      triggerRef.current = document.activeElement as HTMLElement;
    }
    return () => {
      triggerRef.current?.focus();
    };
  }, []);

  // Escape to dismiss and Tab trapping loops
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      if (e.key === 'Escape' && !loading) {
        closeModal();
        return;
      }

      if (e.key === 'Tab' && modalRef.current) {
        const focusableElements = modalRef.current.querySelectorAll(
          'a[href], button, input, textarea, select, [tabindex]:not([tabindex="-1"])'
        );
        if (focusableElements.length === 0) return;
        const firstElement = focusableElements[0] as HTMLElement;
        const lastElement = focusableElements[focusableElements.length - 1] as HTMLElement;

        if (e.shiftKey) {
          if (document.activeElement === firstElement) {
            lastElement.focus();
            e.preventDefault();
          }
        } else {
          if (document.activeElement === lastElement) {
            firstElement.focus();
            e.preventDefault();
          }
        }
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    
    // Auto-focus input on mount
    setTimeout(() => {
      const input = modalRef.current?.querySelector('input, button') as HTMLElement;
      input?.focus();
    }, 50);

    return () => {
      window.removeEventListener('keydown', handleKeyDown);
    };
  }, [closeModal, loading]);

  const handleNextStep = () => {
    if (confirmText.toUpperCase() === 'ROTATE') {
      setStep('confirm');
    }
  };

  const handleExecute = async () => {
    await rotateKeys();
  };

  return (
    <div className={styles.backdrop} onClick={() => !loading && closeModal()}>
      <div 
        ref={modalRef} 
        className={styles.modal} 
        onClick={(e) => e.stopPropagation()}
        role="dialog"
        aria-modal="true"
        aria-labelledby="modal-title"
      >
        <header className={styles.header}>
          <h2 id="modal-title" className={styles.title}>
            {step === 'warning' && 'SSO Key Rotation - Warning'}
            {step === 'confirm' && 'SSO Key Rotation - Final Approval'}
            {step === 'success' && 'SSO Key Rotation - Success'}
          </h2>
          {!loading && step !== 'success' && (
            <button onClick={closeModal} className={styles.closeBtn} aria-label="Close dialog">
              &times;
            </button>
          )}
        </header>

        <div className={styles.body}>
          {step === 'warning' && (
            <>
              <div className={styles.warningAlert} role="alert">
                <span className={styles.alertIcon}>⚠️</span>
                <p className={styles.alertText}>
                  Warning: This will invalidate all active sessions. Confirm immediate rotation of cryptographic SSO keys?
                </p>
              </div>

              <div className={styles.inputSection}>
                <label htmlFor="confirm-rotate-input" className={styles.label}>
                  Type <strong>ROTATE</strong> to continue:
                </label>
                <input
                  id="confirm-rotate-input"
                  type="text"
                  value={confirmText}
                  onChange={(e) => setConfirmText(e.target.value)}
                  className={styles.input}
                  placeholder="ROTATE"
                  disabled={loading}
                  autoComplete="off"
                />
              </div>
            </>
          )}

          {step === 'confirm' && (
            <div className={styles.confirmSection}>
              <div className={styles.confirmBadge}>🔒 Re-verification Required</div>
              <p className={styles.confirmMessage}>
                This operation is permanent and irreversible. All federated identity claims will reject old tokens immediately, logging out all active users.
              </p>
              <p className={styles.question}>Are you absolutely certain you wish to proceed?</p>
            </div>
          )}

          {step === 'success' && (
            <div className={styles.successSection}>
              <div className={styles.successIcon}>✓</div>
              <p className={styles.successMessage}>
                Cryptographic signing keys rotated successfully. Old tokens are invalidated.
              </p>
            </div>
          )}

          {error && (
            <div className={styles.errorAlert} role="alert">
              {error}
            </div>
          )}
        </div>

        <footer className={styles.footer}>
          {step === 'warning' && (
            <>
              <button 
                onClick={closeModal} 
                className={styles.cancelButton}
                disabled={loading}
              >
                Cancel
              </button>
              <button 
                onClick={handleNextStep} 
                className={styles.continueButton}
                disabled={confirmText.toUpperCase() !== 'ROTATE' || loading}
              >
                Continue
              </button>
            </>
          )}

          {step === 'confirm' && (
            <>
              <button 
                onClick={() => setStep('warning')} 
                className={styles.cancelButton}
                disabled={loading}
              >
                Back
              </button>
              <button 
                onClick={handleExecute} 
                className={styles.executeButton}
                disabled={loading}
              >
                {loading ? 'Rotating Keys...' : 'Confirm immediate rotation'}
              </button>
            </>
          )}

          {step === 'success' && (
            <button 
              onClick={closeModal} 
              className={styles.finishButton}
            >
              Finish
            </button>
          )}
        </footer>
      </div>
    </div>
  );
};
