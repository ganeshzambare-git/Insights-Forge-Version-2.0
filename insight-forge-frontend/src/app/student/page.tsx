'use client';

import React, { useEffect, useState, Suspense } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { ProtectedRoute } from '../../features/authentication/components/ProtectedRoute';
import { StudentDashboard } from '../../features/students/dashboard/components/StudentDashboard';
import { useAuthActions } from '../../features/authentication/store/authStore';

function StudentWorkspaceContent() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const { logout } = useAuthActions();
  const [unauthorizedAlert, setUnauthorizedAlert] = useState(false);

  useEffect(() => {
    if (searchParams.get('unauthorized') === 'true') {
      setUnauthorizedAlert(true);
      const timer = setTimeout(() => {
        setUnauthorizedAlert(false);
      }, 5000);
      return () => clearTimeout(timer);
    }
  }, [searchParams]);

  const handleLogout = async () => {
    await logout();
    router.push('/login');
  };

  return (
    <ProtectedRoute allowedRoles={['Student']}>
      <main style={{ minHeight: '100vh', backgroundColor: '#020617', color: '#f8fafc', paddingBottom: '4rem' }}>
        <div style={{
          borderBottom: '1px solid rgba(255, 255, 255, 0.05)',
          padding: '1rem 2rem',
          display: 'flex',
          justifyContent: 'space-between',
          alignItems: 'center',
          backgroundColor: '#0f172a'
        }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
            <span style={{ fontWeight: 800, color: '#10b981' }}>Student Personal Workspace</span>
            <span style={{ fontSize: '0.75rem', color: '#38bdf8', border: '1px solid #0284c7', borderRadius: '0.25rem', padding: '0.125rem 0.375rem', textTransform: 'uppercase', fontWeight: 700 }}>
              Learner Profile
            </span>
          </div>
          <button 
            onClick={handleLogout}
            style={{
              padding: '0.5rem 1rem',
              backgroundColor: 'transparent',
              border: '1px solid rgba(255, 255, 255, 0.1)',
              borderRadius: '0.375rem',
              color: '#f87171',
              cursor: 'pointer',
              fontSize: '0.85rem'
            }}
          >
            Logout
          </button>
        </div>

        {unauthorizedAlert && (
          <div 
            style={{
              margin: '1.5rem',
              backgroundColor: 'rgba(239, 68, 68, 0.15)',
              border: '2px solid #ef4444',
              borderRadius: '0.5rem',
              padding: '1rem',
              color: '#f87171',
              fontWeight: 700,
              fontSize: '0.9rem',
              display: 'flex',
              alignItems: 'center',
              gap: '0.5rem'
            }}
            role="alert"
          >
            <span>⚠️</span> Access permitted check failed. Redirected back securely.
          </div>
        )}

        <StudentDashboard />
      </main>
    </ProtectedRoute>
  );
}

export default function StudentWorkspacePage() {
  return (
    <Suspense fallback={<div style={{ padding: '2rem', color: '#ffffff' }}>Loading workspace session...</div>}>
      <StudentWorkspaceContent />
    </Suspense>
  );
}
