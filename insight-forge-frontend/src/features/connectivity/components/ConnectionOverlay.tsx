'use client';

import React from 'react';
import styles from './ConnectionOverlay.module.css';

interface ConnectionOverlayProps {
  attempt: number;
  isReconnecting: boolean;
  maxAttemptsReached: boolean;
  onRetry: () => void;
}

export const ConnectionOverlay: React.FC<ConnectionOverlayProps> = ({
  attempt,
  isReconnecting,
  maxAttemptsReached,
  onRetry,
}) => {
  return (
    <div className={styles.overlay} role="alert" aria-live="assertive">
      <div className={styles.dialog}>
        <div className={styles.icon}></div>
        <h3 className={styles.title}>Network Link Failure</h3>
        
        <p className={styles.message}>
          FastAPI gateway connection offline. Attempting exponential reconnection...
        </p>

        {isReconnecting && (
          <div className={styles.retryStatus}>
            <span className={styles.spinner} />
            <span>Connection check attempt {attempt} of 5...</span>
          </div>
        )}

        {maxAttemptsReached && (
          <div className={styles.exhaustedBlock}>
            <p className={styles.exhaustedMessage}>
              Automatic reconnection sequence exhausted. The platform failed to contact the gateway cores.
            </p>
            <button onClick={onRetry} className={styles.retryBtn}>
              Manual Reconnect Check
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
