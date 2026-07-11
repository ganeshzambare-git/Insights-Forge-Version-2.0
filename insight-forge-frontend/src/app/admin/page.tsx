'use client';

import React, { useState } from 'react';
import { useRouter } from 'next/navigation';
import { RoleGuard } from '../../features/authentication/components/RoleGuard';
import { AdminDashboard } from '../../features/dashboard/components/AdminDashboard';
import { GradeEditor } from '../../features/students/grades/components/GradeEditor';
import { DeadLetterPanel } from '../../features/ingestion/deadLetter/components/DeadLetterPanel';
import { DeleteConfirmationDialog } from '../../shared/components/dialogs/deleteConfirmation/components/DeleteConfirmationDialog';
import { useDeleteActions } from '../../shared/components/dialogs/deleteConfirmation/store/deleteStore';

export default function AdminPage() {
  const router = useRouter();
  const [showDeleteDialog, setShowDeleteDialog] = useState(false);
  const { startDeleteCohort } = useDeleteActions();

  const handleReturn = () => {
    router.push('/');
  };

  const MismatchFallback = (
    <div style={{
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: 'var(--bg)',
      color: 'var(--ink)',
      padding: '2rem',
      textAlign: 'center'
    }}>
      <div style={{ fontSize: '2.5rem', marginBottom: '1.25rem' }}></div>
      <h2 style={{ fontFamily: 'var(--font-serif)', fontWeight: 500, fontSize: '1.7rem', marginBottom: '0.75rem' }}>Access Denied</h2>
      <p style={{ color: 'var(--muted)', maxWidth: '440px', marginBottom: '2rem', fontSize: '0.95rem', lineHeight: '1.55' }}>
        You do not have the required administrative clearance to view this console. A security exception event has been logged.
      </p>
      <button onClick={handleReturn} className="btn btn-secondary">
        Return to Home
      </button>
    </div>
  );

  return (
    <RoleGuard allowedRoles={['Admin']} fallback={MismatchFallback}>
      <main style={{ minHeight: '100vh', background: 'var(--bg)', color: 'var(--ink)' }}>
        <div style={{
          borderBottom: '1px solid var(--border)',
          padding: '1rem 2rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: 'var(--surface)',
          position: 'sticky',
          top: 0,
          zIndex: 'var(--z-sticky)',
          backdropFilter: 'saturate(1.1)'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.85rem' }}>
            <span style={{ display: 'inline-flex', alignItems: 'center', gap: '0.55rem', fontWeight: 600, color: 'var(--ink)' }}>
              <span style={{ width: '24px', height: '24px', borderRadius: '6px', background: 'var(--brand)', color: 'oklch(0.99 0 0)', display: 'grid', placeItems: 'center', fontFamily: 'var(--font-serif)', fontSize: '0.85rem' }}>IF</span>
              Insight Forge
            </span>
            <span style={{ fontSize: '0.68rem', color: 'var(--brand-ink)', background: 'var(--brand-wash)', border: '1px solid color-mix(in oklch, var(--brand) 22%, transparent)', borderRadius: '999px', padding: '0.15rem 0.55rem', textTransform: 'uppercase', fontWeight: 700, letterSpacing: '0.06em' }}>
              Admin
            </span>
          </div>
          <button
            onClick={handleReturn}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: 'transparent',
              border: '1px solid var(--border-strong)',
              borderRadius: 'var(--r-sm)',
              color: 'var(--ink-soft)',
              cursor: 'pointer',
              fontSize: '0.85rem',
              fontWeight: 600
            }}
          >
            ← Back to Home
          </button>
        </div>

        {/* Sub-features shortcuts navigation bar */}
        <div style={{
          display: 'flex',
          gap: '1rem',
          padding: '1.5rem 1.5rem 0 1.5rem',
          flexWrap: 'wrap'
        }}>
          <button 
            onClick={() => router.push('/admin/keys')}
            style={{
              padding: '0.85rem 1.3rem',
              backgroundColor: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--r-sm)',
              color: 'var(--ink)',
              fontWeight: 600,
              fontSize: '0.9rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.55rem',
              minHeight: '46px',
              boxShadow: 'var(--shadow-sm)'
            }}
          >
            SSO Key Manager
          </button>
          <button 
            onClick={() => router.push('/admin/limits')}
            style={{
              padding: '0.85rem 1.3rem',
              backgroundColor: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--r-sm)',
              color: 'var(--ink)',
              fontWeight: 600,
              fontSize: '0.9rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.55rem',
              minHeight: '46px',
              boxShadow: 'var(--shadow-sm)'
            }}
          >
            Rate Limit Observabilities
          </button>
          <button 
            onClick={() => router.push('/admin/ingest')}
            style={{
              padding: '0.85rem 1.3rem',
              backgroundColor: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--r-sm)',
              color: 'var(--ink)',
              fontWeight: 600,
              fontSize: '0.9rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.55rem',
              minHeight: '46px',
              boxShadow: 'var(--shadow-sm)'
            }}
          >
            High-Scale Dataset Ingest
          </button>
          <button 
            onClick={() => router.push('/admin/executive')}
            style={{
              padding: '0.85rem 1.3rem',
              backgroundColor: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--r-sm)',
              color: 'var(--ink)',
              fontWeight: 600,
              fontSize: '0.9rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.55rem',
              minHeight: '46px',
              boxShadow: 'var(--shadow-sm)'
            }}
          >
            Executive KPI Canvas
          </button>
          <button 
            onClick={() => router.push('/admin/sandbox')}
            style={{
              padding: '0.85rem 1.3rem',
              backgroundColor: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--r-sm)',
              color: 'var(--ink)',
              fontWeight: 600,
              fontSize: '0.9rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.55rem',
              minHeight: '46px',
              boxShadow: 'var(--shadow-sm)'
            }}
          >
            Simulation Sandbox Workspace
          </button>
          <button
            onClick={() => router.push('/admin/attendance')}
            style={{
              padding: '0.85rem 1.3rem',
              backgroundColor: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--r-sm)',
              color: 'var(--ink)',
              fontWeight: 600,
              fontSize: '0.9rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.55rem',
              minHeight: '46px',
              boxShadow: 'var(--shadow-sm)'
            }}
          >
            Attendance Analytics
          </button>
          <button
            onClick={() => router.push('/admin/courses')}
            style={{
              padding: '0.85rem 1.3rem',
              backgroundColor: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--r-sm)',
              color: 'var(--ink)',
              fontWeight: 600,
              fontSize: '0.9rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.55rem',
              minHeight: '46px',
              boxShadow: 'var(--shadow-sm)'
            }}
          >
            Course Performance
          </button>
          <button
            onClick={() => router.push('/admin/finance')}
            style={{
              padding: '0.85rem 1.3rem',
              backgroundColor: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--r-sm)',
              color: 'var(--ink)',
              fontWeight: 600,
              fontSize: '0.9rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.55rem',
              minHeight: '46px',
              boxShadow: 'var(--shadow-sm)'
            }}
          >
            Financial Dashboard
          </button>
          <button
            onClick={() => router.push('/admin/tasks')}
            style={{
              padding: '0.85rem 1.3rem',
              backgroundColor: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--r-sm)',
              color: 'var(--ink)',
              fontWeight: 600,
              fontSize: '0.9rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.55rem',
              minHeight: '46px',
              boxShadow: 'var(--shadow-sm)'
            }}
          >
            Background Task Monitor
          </button>
          <button
            onClick={() => router.push('/admin/security')}
            style={{
              padding: '0.85rem 1.3rem',
              backgroundColor: 'var(--surface)',
              border: '1px solid var(--border)',
              borderRadius: 'var(--r-sm)',
              color: 'var(--ink)',
              fontWeight: 600,
              fontSize: '0.9rem',
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.55rem',
              minHeight: '46px',
              boxShadow: 'var(--shadow-sm)'
            }}
          >
            Security Audit Log
          </button>
        </div>

        <AdminDashboard />

        {/* Phase 6: Data Integrity Panels */}
        <div style={{ padding: '0 1.5rem', display: 'flex', flexDirection: 'column', gap: '1.5rem', paddingBottom: '3rem' }}>

          {/* Task 22: Grade Ledger Constraint Validator */}
          <GradeEditor />

          {/* Task 23: Dead-Letter Ingestion Diagnostics */}
          <DeadLetterPanel />

          {/* Task 24: Referential Integrity Delete Guard Trigger */}
          <div style={{
            background: 'var(--surface)',
            border: '1px solid var(--border)',
            borderRadius: 'var(--r)',
            padding: '1.75rem',
            boxShadow: 'var(--shadow-sm)'
          }}>
            <h3 style={{ color: 'var(--ink)', fontSize: '1.05rem', fontWeight: 600, marginBottom: '0.3rem' }}>Cohort Management</h3>
            <p style={{ color: 'var(--muted)', fontSize: '0.88rem', marginBottom: '1.25rem', maxWidth: '60ch' }}>
              Expunge inactive cohort partitions. Referential integrity conflicts are surfaced before removal.
            </p>
            <button
              onClick={() => { startDeleteCohort(); setShowDeleteDialog(true); }}
              style={{
                padding: '0.65rem 1.2rem',
                backgroundColor: 'var(--critical-wash)',
                color: 'var(--critical)',
                border: '1px solid color-mix(in oklch, var(--critical) 24%, transparent)',
                borderRadius: 'var(--r-sm)',
                fontWeight: 600,
                cursor: 'pointer',
                minHeight: '44px'
              }}
            >
              Delete Demo Cohort
            </button>
          </div>
        </div>

        {showDeleteDialog && (
          <DeleteConfirmationDialog
            cohortId="88888888-8888-8888-8888-888888888888"
            cohortCode="CS-DEMO-2026"
            onSuccess={() => setShowDeleteDialog(false)}
          />
        )}
      </main>
    </RoleGuard>
  );
}
