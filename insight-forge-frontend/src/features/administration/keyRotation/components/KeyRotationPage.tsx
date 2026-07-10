'use client';

import React from 'react';
import {
  useIsKeyRotationModalOpen,
  useKeyRotatedAt,
  useInvalidatedSessionsCount,
  useKeyRotationActions,
} from '../store/keyRotationStore';
import { KeyRotationModal } from './KeyRotationModal';
import styles from './KeyRotationPage.module.css';

export const KeyRotationPage: React.FC = () => {
  const isModalOpen = useIsKeyRotationModalOpen();
  const rotatedAt = useKeyRotatedAt();
  const invalidatedCount = useInvalidatedSessionsCount();
  const { openModal } = useKeyRotationActions();

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h2 className={styles.title}>SSO Signing-Key Administration</h2>
        <p className={styles.subtitle}>Manage cryptographic secrets governing federated authentication profiles</p>
      </header>

      <div className={styles.dashboardGrid}>
        {/* Active Key Status Card */}
        <div className={styles.card}>
          <h3 className={styles.cardTitle}>Cryptographic Configuration</h3>
          <div className={styles.statusRow}>
            <span className={styles.statusLabel}>Active Key State</span>
            <span className={styles.statusBadge}>Valid</span>
          </div>
          <div className={styles.statusRow}>
            <span className={styles.statusLabel}>SSO Encryption Standard</span>
            <span className={styles.statusValue}>RS256 (RSA 2048-bit)</span>
          </div>
          <div className={styles.statusRow}>
            <span className={styles.statusLabel}>Key Authority Version</span>
            <span className={styles.statusValue}>v3.1.2</span>
          </div>
          <div className={styles.statusRow}>
            <span className={styles.statusLabel}>Last Rotation Date</span>
            <span className={styles.statusValue}>
              {rotatedAt ? new Date(rotatedAt).toLocaleString() : '2026-07-01 10:00:00 (Scheduled)'}
            </span>
          </div>
        </div>

        {/* Action Panel Card */}
        <div className={styles.card}>
          <h3 className={styles.cardTitle}>Signing Key Operations</h3>
          <p className={styles.helpText}>
            Rotating signing keys invalidates all current user tokens immediately. Users must log back in via institutional MFA providers. Typically performed on a 90-day cycle or during security audits.
          </p>
          <button onClick={openModal} className={styles.actionBtn}>
            Rotate Cryptographic Keys
          </button>
          {invalidatedCount !== null && (
            <div className={styles.eventLog}>
              🟢 Latest Security Event: Rotated keys and terminated {invalidatedCount} sessions.
            </div>
          )}
        </div>
      </div>

      {isModalOpen && <KeyRotationModal />}
    </div>
  );
};
