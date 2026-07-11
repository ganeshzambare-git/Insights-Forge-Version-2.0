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
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', color: 'var(--muted)' }}>
        Redirecting to dashboard...
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', minHeight: '100vh', background: 'var(--bg)' }}>
      {/* Brand panel — a single committed brand surface (auth hero) */}
      <aside
        style={{
          width: '42%',
          maxWidth: '520px',
          position: 'relative',
          overflow: 'hidden',
          background:
            'linear-gradient(160deg, oklch(0.42 0.10 222) 0%, oklch(0.32 0.075 235) 100%)',
          color: 'oklch(0.97 0.01 220)',
          display: 'flex',
          flexDirection: 'column',
          justifyContent: 'space-between',
          padding: '3.5rem 3rem',
          boxSizing: 'border-box',
        }}
        className="authBrandPanel"
      >
        {/* soft light bloom */}
        <div
          aria-hidden
          style={{
            position: 'absolute',
            inset: 0,
            background:
              'radial-gradient(600px 300px at 85% 5%, oklch(0.9 0.08 210 / 0.28), transparent 60%)',
            pointerEvents: 'none',
          }}
        />
        <div style={{ position: 'relative' }}>
          <div
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.55rem',
              fontSize: '0.78rem',
              fontWeight: 600,
              letterSpacing: '0.14em',
              textTransform: 'uppercase',
              color: 'oklch(0.86 0.03 210)',
            }}
          >
            <span
              style={{
                width: '22px',
                height: '22px',
                borderRadius: '6px',
                background: 'oklch(0.97 0.01 220)',
                color: 'oklch(0.38 0.09 222)',
                display: 'grid',
                placeItems: 'center',
                fontFamily: 'var(--font-serif)',
                fontWeight: 600,
                fontSize: '0.9rem',
              }}
            >
              IF
            </span>
            Insight Forge
          </div>
        </div>

        <div style={{ position: 'relative' }}>
          <h1
            style={{
              fontFamily: 'var(--font-serif)',
              fontWeight: 500,
              fontSize: 'clamp(2.2rem, 3.4vw, 3.1rem)',
              lineHeight: 1.05,
              letterSpacing: '-0.02em',
              marginBottom: '1rem',
              textWrap: 'balance',
            }}
          >
            Clearer decisions for every cohort.
          </h1>
          <p
            style={{
              color: 'oklch(0.86 0.025 215)',
              fontSize: '1rem',
              lineHeight: 1.6,
              maxWidth: '38ch',
            }}
          >
            An institutional intelligence workspace — attendance, performance,
            risk and resources, read at a glance.
          </p>
        </div>

        <div
          style={{
            position: 'relative',
            fontSize: '0.8rem',
            color: 'oklch(0.78 0.03 215)',
          }}
        >
          © 2026 ReadyNest Partners
        </div>
      </aside>

      <main
        style={{
          flex: 1,
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          padding: '2rem',
        }}
      >
        {!tenant ? <WorkspacePortal /> : <LoginForm />}
      </main>
    </div>
  );
}
