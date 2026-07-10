'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useWorkspaceTenant } from '../../features/workspace/store/workspaceStore';
import { useIsAuthenticated, useAuthActions } from '../../features/authentication/store/authStore';
import { WorkspacePortal } from '../../features/workspace/components/WorkspacePortal';
import { LoginForm } from '../../features/authentication/components/LoginForm';

export default function LoginPage() {
  const router = useRouter();
  const tenant = useWorkspaceTenant();
  const isAuthenticated = useIsAuthenticated();
  const { initializeSession } = useAuthActions();

  // Recover session from sessionStorage on reload
  useEffect(() => {
    initializeSession();
  }, [initializeSession]);

  // If authenticated, redirect to dashboard root
  useEffect(() => {
    if (isAuthenticated) {
      router.push('/');
    }
  }, [isAuthenticated, router]);

  if (isAuthenticated) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', color: '#94a3b8' }}>
        Redirecting to dashboard...
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', backgroundColor: '#020617' }}>
      {/* Left aligned branding panel */}
      <div style={{
        width: '400px',
        backgroundColor: '#0f172a',
        borderRight: '1px solid rgba(255, 255, 255, 0.05)',
        display: 'flex',
        flexDirection: 'column',
        justifyContent: 'space-between',
        padding: '3rem 2.5rem',
        boxSizing: 'border-box'
      }}>
        <div>
          <h1 style={{
            fontSize: '2rem',
            fontWeight: 800,
            background: 'linear-gradient(135deg, #38bdf8 0%, #818cf8 100%)',
            WebkitBackgroundClip: 'text',
            WebkitTextFillColor: 'transparent',
            marginBottom: '0.5rem'
          }}>InsightForge AI</h1>
          <p style={{ color: '#64748b', fontSize: '0.9rem', lineHeight: '1.5' }}>
            Enterprise Multi-Agent Platform governing educational diagnostics and decision intelligence partitions.
          </p>
        </div>
        <div style={{ fontSize: '0.8rem', color: '#475569' }}>
          &copy; 2026 ReadyNest Partners. All rights reserved.
        </div>
      </div>

      <div style={{ flex: 1, display: 'flex', justifyContent: 'center', alignItems: 'center' }}>
        {!tenant ? <WorkspacePortal /> : <LoginForm />}
      </div>
    </div>
  );
}
