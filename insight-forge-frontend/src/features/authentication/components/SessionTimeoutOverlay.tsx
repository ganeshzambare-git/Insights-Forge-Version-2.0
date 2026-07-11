'use client';

import React from 'react';
import { useTimeLeft, useIsWarning, useIsExpired, useSessionTimeoutActions } from '../store/sessionTimeoutStore';
import styles from './SessionTimeoutOverlay.module.css';

interface SessionTimeoutOverlayProps {
  onExtend: () => void;
  onLogout: () => void;
}

export const SessionTimeoutOverlay: React.FC<SessionTimeoutOverlayProps> = ({ onExtend, onLogout }) => {
  const timeLeft = useTimeLeft();
  const isWarning = useIsWarning();
  const isExpired = useIsExpired();
  const { resetTimer } = useSessionTimeoutActions();

  const handleExtend = () => {
    resetTimer();
    onExtend();
  };

  if (!isWarning && !isExpired) return null;

  return (
    <div className={`${styles.overlay} ${isExpired ? styles.expired : ''}`} role="alert" aria-live="assertive">
      <div className={styles.modal}>
        <div className={styles.iconContainer}>
          {isExpired ? '⏳' : ''}
        </div>
        <h2 className={styles.title}>
          {isExpired ? 'Session Expired' : 'Session Expiring Soon'}
        </h2>
        <p className={styles.message}>
          {isExpired 
            ? 'Your secure session has ended. Redirecting to the workspace selector...'
            : `For security, your session will automatically log out in ${timeLeft} seconds due to inactivity.`
          }
        </p>
        {!isExpired && (
          <div className={styles.buttonGroup}>
            <button onClick={handleExtend} className={styles.extendButton}>
              Extend Session
            </button>
            <button onClick={onLogout} className={styles.logoutButton}>
              Sign Out Now
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
