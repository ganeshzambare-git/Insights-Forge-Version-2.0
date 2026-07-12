'use client';

import { useRef, useState } from 'react';

type UploadDropzoneProps = {
  onFile: (file: File) => void;
  busy: boolean;
  compact?: boolean;
};

export function UploadDropzone({ onFile, busy, compact }: UploadDropzoneProps) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [dragging, setDragging] = useState(false);

  function pick(file: File | undefined) {
    if (!file) return;
    onFile(file);
  }

  return (
    <div
      onDragOver={(e) => {
        e.preventDefault();
        if (!busy) setDragging(true);
      }}
      onDragLeave={() => setDragging(false)}
      onDrop={(e) => {
        e.preventDefault();
        setDragging(false);
        if (!busy) pick(e.dataTransfer.files?.[0]);
      }}
      role="button"
      tabIndex={0}
      onClick={() => !busy && inputRef.current?.click()}
      onKeyDown={(e) => {
        if ((e.key === 'Enter' || e.key === ' ') && !busy) {
          e.preventDefault();
          inputRef.current?.click();
        }
      }}
      aria-label="Upload a CSV or JSON dataset"
      aria-busy={busy}
      style={{
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        textAlign: 'center',
        gap: 10,
        padding: compact ? '22px' : '40px 24px',
        borderRadius: 'var(--r-card)',
        border: `1.5px dashed ${dragging ? 'var(--action-blue)' : 'var(--silver)'}`,
        background: dragging ? 'var(--info-bg)' : 'var(--white)',
        cursor: busy ? 'progress' : 'pointer',
        transition: 'border-color 0.18s ease, background 0.18s ease',
      }}
    >
      <input
        ref={inputRef}
        type="file"
        accept=".csv,.json"
        hidden
        onChange={(e) => {
          pick(e.target.files?.[0]);
          e.target.value = '';
        }}
      />
      <span
        aria-hidden="true"
        style={{
          width: 40,
          height: 40,
          borderRadius: 10,
          background: 'var(--paper)',
          display: 'grid',
          placeItems: 'center',
        }}
      >
        <svg width="20" height="20" viewBox="0 0 24 24" fill="none" stroke="var(--graphite)" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round">
          <path d="M12 16V4" />
          <path d="m7 9 5-5 5 5" />
          <path d="M4 16v2a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2v-2" />
        </svg>
      </span>
      <div>
        <div style={{ fontWeight: 500, color: 'var(--graphite)', fontSize: 'var(--text-body)' }}>
          {busy ? 'Analyzing your dataset…' : 'Drop a CSV or JSON, or click to browse'}
        </div>
        <div style={{ fontSize: 'var(--text-body-sm)', color: 'var(--slate)', marginTop: 2 }}>
          {busy ? 'Running the four-agent pipeline' : 'Rows are stored to your tenant and analyzed instantly'}
        </div>
      </div>
    </div>
  );
}
