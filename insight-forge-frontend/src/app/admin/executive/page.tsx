'use client';

import React from 'react';
import { useRouter } from 'next/navigation';
import { RoleGuard } from '../../../features/authentication/components/RoleGuard';
import { ExecutiveDashboard } from '../../../features/analytics/executive/components/ExecutiveDashboard';
import { DepartmentFilterPanel } from '../../../features/analytics/department/components/DepartmentFilterPanel';

export default function ExecutiveAnalyticsPage() {
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
      backgroundColor: '#020617',
      color: '#ffffff',
      padding: '2rem',
      textAlign: 'center'
    }}>
      <div style={{ fontSize: '3rem', marginBottom: '1.5rem' }}>🔒</div>
      <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.75rem' }}>Access Denied</h2>
      <p style={{ color: '#94a3b8', maxWidth: '440px', marginBottom: '2rem', fontSize: '0.95rem', lineHeight: '1.5' }}>
        You do not have institutional executive clearance to access Dean-1 KPI canvases.
      </p>
      <button 
        onClick={handleReturn}
        style={{
          padding: '0.75rem 1.5rem',
          backgroundColor: '#334155',
          color: '#ffffff',
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
    <RoleGuard allowedRoles={['Admin', 'Dean']} fallback={MismatchFallback}>
      <main style={{ minHeight: '100vh', backgroundColor: '#020617', color: '#f8fafc', paddingBottom: '3rem' }}>
        <div style={{
          borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
          padding: '1rem 2rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: '#0f172a'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <span style={{ fontWeight: 800, color: '#38bdf8' }}>Dean Decision Portal</span>
            <span style={{ fontSize: '0.75rem', color: '#818cf8', border: '1px solid #4f46e5', borderRadius: '0.25rem', padding: '0.125rem 0.375rem', textTransform: 'uppercase', fontWeight: 700 }}>
              Dean-1 Canvas
            </span>
          </div>
          <button 
            onClick={handleReturn}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: 'transparent',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '0.375rem',
              color: '#94a3b8',
              cursor: 'pointer',
              fontSize: '0.85rem'
            }}
          >
            ← Back to Console
          </button>
        </div>

        <ExecutiveDashboard />

        <hr style={{ border: 'none', borderTop: '1px solid rgba(255,255,255,0.05)', margin: '1rem 2.5rem' }} />

        <DepartmentFilterPanel />
      </main>
    </RoleGuard>
  );
}
