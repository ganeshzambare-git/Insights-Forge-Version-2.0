'use client';

import React from 'react';
import {
  useExportLoading,
  useExportError,
  useExportStatus,
  useExportProgress,
  useExportActions,
} from '../store/exportStore';
import styles from './AuditExportPanel.module.css';

export const AuditExportPanel: React.FC = () => {
  const loading = useExportLoading();
  const error = useExportError();
  const exportStatus = useExportStatus();
  const progress = useExportProgress();
  const { startExport, resetExport } = useExportActions();

  return (
    <div className={styles.container}>
      <h3 className={styles.title}>Academic Audit Compliance</h3>
      <p className={styles.subtitle}>Generate and compile comprehensive academic audit packets for institutional compliance reviews.</p>

      <div className={styles.actionWrapper}>
        <button
          onClick={startExport}
          className={styles.exportBtn}
          disabled={exportStatus === 'exporting' || loading}
        >
          {exportStatus === 'exporting' ? (
            <div className={styles.spinnerWrapper}>
              <span className={styles.spinner} />
              <span>Compiling Packet ({progress}%)...</span>
            </div>
          ) : (
            'Generate Compliance Export'
          )}
        </button>

        {exportStatus === 'completed' && (
          <div className={styles.successCard} role="status">
            <div className={styles.successIcon}></div>
            <div className={styles.successBody}>
              <p className={styles.successMessage}>
                Audit compliance packet compiled successfully. Download available securely.
              </p>
              <div className={styles.btnRow}>
                <a href="#download" className={styles.downloadLink} onClick={(e) => e.preventDefault()}>
                  Secure Download Link
                </a>
                <button onClick={resetExport} className={styles.resetLink}>
                  Clear
                </button>
              </div>
            </div>
          </div>
        )}

        {exportStatus === 'failed' && error && (
          <div className={styles.errorCard} role="alert">
            <p>Failed compiling compliance packet: {error}</p>
            <button onClick={resetExport} className={styles.resetLink}>
              Try Again
            </button>
          </div>
        )}
      </div>
    </div>
  );
};
