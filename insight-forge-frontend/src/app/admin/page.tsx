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
      backgroundColor: '#020617',
      color: '#ffffff',
      padding: '2rem',
      textAlign: 'center'
    }}>
      <div style={{ fontSize: '3rem', marginBottom: '1.5rem' }}>🔒</div>
      <h2 style={{ fontSize: '1.5rem', fontWeight: 700, marginBottom: '0.75rem' }}>Access Denied</h2>
      <p style={{ color: '#94a3b8', maxWidth: '440px', marginBottom: '2rem', fontSize: '0.95rem', lineHeight: '1.5' }}>
        You do not have the required administrative clearance to view this console. A security exception event has been logged.
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
        Return to Home
      </button>
    </div>
  );

  return (
    <RoleGuard allowedRoles={['Admin']} fallback={MismatchFallback}>
      <main style={{ minHeight: '100vh', backgroundColor: '#020617', color: '#f8fafc' }}>
        <div style={{
          borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
          padding: '1rem 2rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: '#0f172a'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <span style={{ fontWeight: 800, color: '#38bdf8' }}>InsightForge Console</span>
            <span style={{ fontSize: '0.75rem', color: '#64748b', border: '1px solid #475569', borderRadius: '0.25rem', padding: '0.125rem 0.375rem', textTransform: 'uppercase', fontWeight: 700 }}>
              Admin Partition
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
            ← Return to Dashboard
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
              padding: '0.75rem 1.5rem',
              backgroundColor: 'rgba(30, 41, 59, 0.4)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '0.5rem',
              color: '#ffffff',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              minHeight: '44px'
            }}
          >
            🔑 SSO Key Manager
          </button>
          <button 
            onClick={() => router.push('/admin/limits')}
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: 'rgba(30, 41, 59, 0.4)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '0.5rem',
              color: '#ffffff',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              minHeight: '44px'
            }}
          >
            🚨 Rate Limit Observabilities
          </button>
          <button 
            onClick={() => router.push('/admin/ingest')}
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: 'rgba(30, 41, 59, 0.4)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '0.5rem',
              color: '#ffffff',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              minHeight: '44px'
            }}
          >
            📥 High-Scale Dataset Ingest
          </button>
          <button 
            onClick={() => router.push('/admin/executive')}
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: 'rgba(30, 41, 59, 0.4)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '0.5rem',
              color: '#ffffff',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              minHeight: '44px'
            }}
          >
            📊 Executive KPI Canvas
          </button>
          <button 
            onClick={() => router.push('/admin/sandbox')}
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: 'rgba(30, 41, 59, 0.4)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '0.5rem',
              color: '#ffffff',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              minHeight: '44px'
            }}
          >
            🧪 Simulation Sandbox Workspace
          </button>
          <button
            onClick={() => router.push('/admin/attendance')}
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: 'rgba(30, 41, 59, 0.4)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '0.5rem',
              color: '#ffffff',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              minHeight: '44px'
            }}
          >
            📅 Attendance Analytics
          </button>
          <button
            onClick={() => router.push('/admin/courses')}
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: 'rgba(30, 41, 59, 0.4)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '0.5rem',
              color: '#ffffff',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              minHeight: '44px'
            }}
          >
            📚 Course Performance
          </button>
          <button
            onClick={() => router.push('/admin/finance')}
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: 'rgba(30, 41, 59, 0.4)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '0.5rem',
              color: '#ffffff',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              minHeight: '44px'
            }}
          >
            💰 Financial Dashboard
          </button>
          <button
            onClick={() => router.push('/admin/tasks')}
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: 'rgba(30, 41, 59, 0.4)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '0.5rem',
              color: '#ffffff',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              minHeight: '44px'
            }}
          >
            ⚙️ Background Task Monitor
          </button>
          <button
            onClick={() => router.push('/admin/security')}
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: 'rgba(30, 41, 59, 0.4)',
              border: '1px solid rgba(255, 255, 255, 0.08)',
              borderRadius: '0.5rem',
              color: '#ffffff',
              fontWeight: 600,
              cursor: 'pointer',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem',
              minHeight: '44px'
            }}
          >
            🔐 Security Audit Log
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
            background: 'rgba(30, 41, 59, 0.4)',
            backdropFilter: 'blur(12px)',
            border: '1px solid rgba(255, 255, 255, 0.08)',
            borderRadius: '0.75rem',
            padding: '1.5rem'
          }}>
            <h3 style={{ color: '#ffffff', fontSize: '1.1rem', fontWeight: 700, marginBottom: '0.25rem' }}>Cohort Management</h3>
            <p style={{ color: '#94a3b8', fontSize: '0.85rem', marginBottom: '1.25rem' }}>
              Expunge inactive cohort partitions. Referential integrity conflicts are surfaced before removal.
            </p>
            <button
              onClick={() => { startDeleteCohort(); setShowDeleteDialog(true); }}
              style={{
                padding: '0.625rem 1.25rem',
                backgroundColor: 'rgba(239, 68, 68, 0.15)',
                color: '#f87171',
                border: '1px solid rgba(239, 68, 68, 0.25)',
                borderRadius: '0.375rem',
                fontWeight: 700,
                cursor: 'pointer',
                minHeight: '44px'
              }}
            >
              🗑️ Delete Demo Cohort
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
