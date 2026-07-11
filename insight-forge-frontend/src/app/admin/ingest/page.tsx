'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { RoleGuard } from '../../../features/authentication/components/RoleGuard';
import { DatasetUploadPage } from '../../../features/ingestion/upload/components/DatasetUploadPage';

export default function IngestPage() {
  const router = useRouter();

  const handleReturn = () => {
    router.push('/admin');
  };

  const MismatchFallback = (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      backgroundColor: 'var(--bg)',
      color: 'var(--ink)',
      padding: '2rem',
      textAlign: 'center'
    }}>
      <div style={{ fontSize: '3rem', marginBottom: '1.5rem' }}>🔒</div>
      <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.75rem' }}>Access Denied</h2>
      <p style={{ color: 'var(--muted)', maxWidth: '440px', marginBottom: '2rem', fontSize: '0.95rem', lineHeight: '1.5' }}>
        You do not have administrative clearance to access dataset ingestion modules.
      </p>
      <button 
        onClick={handleReturn}
        style={{
          padding: '0.75rem 1.5rem',
          backgroundColor: 'var(--surface-2)',
          color: 'var(--ink)',
          border: 'none',
          borderRadius: '0.375rem',
          fontWeight: 600,
          cursor: 'pointer'
        }}
      >
        Return to Admin
      </button>
    </div>
  );

  return (
    <RoleGuard allowedRoles={['Admin']} fallback={MismatchFallback}>
      <main style={{ minHeight: '100vh', backgroundColor: 'var(--bg)', color: 'var(--ink)' }}>
        <div style={{
          borderBottom: '1px solid var(--border)',
          padding: '1rem 2rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: 'var(--surface)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <span style={{ fontWeight: 800, color: 'var(--brand)' }}>InsightForge Ingress Console</span>
            <span style={{ fontSize: '0.75rem', color: 'var(--faint)', border: '1px solid var(--faint)', borderRadius: '0.25rem', padding: '0.125rem 0.375rem', textTransform: 'uppercase', fontWeight: 700 }}>
              Ingest
            </span>
          </div>
          <button 
            onClick={handleReturn}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: 'transparent',
              border: '1px solid var(--border-strong)',
              borderRadius: '0.375rem',
              color: 'var(--muted)',
              cursor: 'pointer',
              fontSize: '0.85rem'
            }}
          >
            ← Back to Console
          </button>
        </div>

        <DatasetUploadPage />
      </main>
    </RoleGuard>
  );
}
