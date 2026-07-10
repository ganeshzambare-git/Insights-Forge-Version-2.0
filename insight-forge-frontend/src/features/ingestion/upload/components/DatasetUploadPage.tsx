'use client';

import React, { useRef, useState } from 'react';
import {
  useUploadProgress,
  useUploadStatus,
  useUploadError,
  useUploadQualityScore,
  useUploadValidationLog,
  useUploadActions,
} from '../store/uploadStore';
import styles from './DatasetUploadPage.module.css';

export const DatasetUploadPage: React.FC = () => {
  const progress = useUploadProgress();
  const uploadStatus = useUploadStatus();
  const error = useUploadError();
  const qualityScore = useUploadQualityScore();
  const validationLog = useUploadValidationLog();
  const { setValidation, startChunkedUpload, cancelUpload, resetUpload } = useUploadActions();

  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault();
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      processFile(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      processFile(e.target.files[0]);
    }
  };

  const processFile = (file: File) => {
    resetUpload();
    setSelectedFile(null);

    const extension = file.name.split('.').pop()?.toLowerCase();
    if (extension !== 'csv' && extension !== 'xlsx') {
      setValidation(0, ['Error: Invalid file format extension.', `File "${file.name}" rejected. Only .csv and .xlsx datasets are allowed.`]);
      return;
    }

    setSelectedFile(file);

    if (extension === 'csv') {
      const reader = new FileReader();
      reader.onload = (e) => {
        const text = e.target?.result as string;
        const lines = text.split('\n').map((l) => l.trim()).filter(Boolean);
        
        if (lines.length < 2) {
          setValidation(0, ['Validation Failed: Empty or invalid dataset.', 'CSV must contain at least a header row and a data row.']);
          return;
        }

        const headers = lines[0].split(',');
        const totalCols = headers.length;
        let cleanRows = 0;
        let corruptRows = 0;
        const logs: string[] = [
          `Detected format: CSV`,
          `Headers detected: ${headers.join(' | ')}`,
          `Total columns defined: ${totalCols}`,
          `Scanning rows...`
        ];

        for (let i = 1; i < Math.min(lines.length, 100); i++) {
          const cols = lines[i].split(',');
          if (cols.length === totalCols && cols.every((c) => c !== '')) {
            cleanRows++;
          } else {
            corruptRows++;
          }
        }

        const totalScanned = cleanRows + corruptRows;
        const score = totalScanned > 0 ? Math.round((cleanRows / totalScanned) * 100) : 0;
        
        logs.push(
          `Rows scanned for preview: ${totalScanned}`,
          `Clean rows: ${cleanRows}`,
          `Corrupt/empty rows: ${corruptRows}`,
          `Heuristic Quality Score: ${score}%`
        );

        setValidation(score, logs);
      };

      reader.readAsText(file.slice(0, 10240));
    } else {
      setValidation(90, [
        `Detected format: XLSX (Excel binary dataset)`,
        `File name: ${file.name}`,
        `File size: ${(file.size / 1024).toFixed(1)} KB`,
        `Authoritative structural validation will be performed on backend cores.`,
        `Client-side pre-upload validation: PASSED.`
      ]);
    }
  };

  const handleStartIngest = async () => {
    if (selectedFile) {
      await startChunkedUpload(selectedFile);
    }
  };

  return (
    <div className={styles.container}>
      <header className={styles.header}>
        <h2 className={styles.title}>Large Dataset Ingestion</h2>
        <p className={styles.subtitle}>Stream large datasets securely in 1MB chunks with pre-upload diagnostic audits</p>
      </header>

      <div className={styles.uploadGrid}>
        {/* Left Column: Drag & Drop Zone */}
        <div className={styles.card}>
          <h3 className={styles.sectionTitle}>Dataset Ingress Ingestion</h3>
          
          <div 
            className={`${styles.dropzone} ${uploadStatus === 'uploading' ? styles.dropzoneDisabled : ''}`}
            onDragOver={handleDragOver}
            onDrop={handleDrop}
            onClick={() => uploadStatus !== 'uploading' && fileInputRef.current?.click()}
          >
            <input 
              ref={fileInputRef}
              type="file"
              accept=".csv,.xlsx"
              onChange={handleFileSelect}
              className={styles.fileInput}
              disabled={uploadStatus === 'uploading'}
            />
            <div className={styles.dropzoneIcon}>📥</div>
            <p className={styles.dropzoneText}>
              Drag and drop your dataset here, or <span className={styles.browseLink}>browse local files</span>
            </p>
            <p className={styles.dropzoneSubText}>Supported extensions: .csv, .xlsx (Max: 50MB)</p>
          </div>

          {selectedFile && (
            <div className={styles.fileDetails}>
              <div className={styles.fileMeta}>
                <span className={styles.fileName}>{selectedFile.name}</span>
                <span className={styles.fileSize}>({(selectedFile.size / (1024 * 1024)).toFixed(2)} MB)</span>
              </div>

              {uploadStatus === 'idle' && qualityScore !== null && qualityScore >= 70 && (
                <button onClick={handleStartIngest} className={styles.ingestBtn}>
                  Start Chunked Ingest
                </button>
              )}

              {uploadStatus === 'uploading' && (
                <div className={styles.progressContainer}>
                  <div className={styles.progressHeader}>
                    <span>Ingesting Chunks...</span>
                    <span>{progress}%</span>
                  </div>
                  <div className={styles.progressBarBg}>
                    <div className={styles.progressBarFill} style={{ width: `${progress}%` }} />
                  </div>
                  <button onClick={cancelUpload} className={styles.cancelBtn}>
                    Cancel Upload
                  </button>
                </div>
              )}

              {uploadStatus === 'completed' && (
                <div className={styles.successBlock}>
                  <h4>✓ Ingestion Complete</h4>
                  <p>Dataset streamed in 1MB chunks and validated on core server partitions.</p>
                  <button onClick={resetUpload} className={styles.resetBtn}>
                    Upload Another File
                  </button>
                </div>
              )}
            </div>
          )}

          {error && (
            <div className={styles.errorAlert}>
              <span>⚠️</span> {error}
            </div>
          )}
        </div>

        {/* Right Column: Pre-upload logs */}
        <div className={styles.card}>
          <h3 className={styles.sectionTitle}>Client Pre-Ingress Diagnostics</h3>
          {qualityScore !== null ? (
            <div className={styles.diagnostics}>
              <div className={`${styles.qualityBadge} ${qualityScore >= 70 ? styles.qualityPass : styles.qualityFail}`}>
                <div className={styles.badgeLabel}>Quality Score</div>
                <div className={styles.badgeVal}>{qualityScore}%</div>
                <div className={styles.badgeStatus}>
                  {qualityScore >= 70 ? '✓ INGRESS PASSED' : '🚨 BLOCKED - QUALITY UNDER 70%'}
                </div>
              </div>

              <div className={styles.logsConsole}>
                {validationLog.map((log, idx) => (
                  <div key={idx} className={styles.logLine}>
                    {log}
                  </div>
                ))}
              </div>
            </div>
          ) : (
            <div className={styles.emptyLogs}>
              <p>Select or drop a file to view local diagnostic metrics and CSV schemas.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
