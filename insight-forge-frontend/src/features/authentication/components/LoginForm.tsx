'use client';

import React, { useState } from 'react';
import { useAuthLoading, useAuthError, useAuthActions } from '../store/authStore';
import { useWorkspaceTenant, useWorkspaceActions } from '../../workspace/store/workspaceStore';
import styles from './LoginForm.module.css';

export const LoginForm: React.FC = () => {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [mfaCode, setMfaCode] = useState('');

  const loading = useAuthLoading();
  const error = useAuthError();
  const { submitLogin } = useAuthActions();

  const tenant = useWorkspaceTenant();
  const { resetWorkspace } = useWorkspaceActions();

  const handleFormSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (loading) return;

    const payload = {
      email: email.trim(),
      password,
      mfa_code: mfaCode.trim(),
    };

    const success = await submitLogin(payload);
    if (!success) {
      // Clear sensitive fields instantly on security failure
      setEmail('');
      setPassword('');
      setMfaCode('');
    }
  };

  return (
    <div className={styles.container}>
      <div className={styles.card}>
        <div className={styles.tenantBranding}>
          {tenant?.logoUrl && (
            <img src={tenant.logoUrl} alt={`${tenant.name} Logo`} className={styles.logo} />
          )}
          <h2 className={styles.title}>Sign in to {tenant?.name || 'Workspace'}</h2>
          <button onClick={resetWorkspace} className={styles.changeTenantButton} disabled={loading}>
            ← Change workspace
          </button>
        </div>

        <form onSubmit={handleFormSubmit} className={styles.form} noValidate>
          <div className={styles.inputGroup}>
            <label htmlFor="auth-email" className={styles.label}>
              Academic Email Address
            </label>
            <input
              id="auth-email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              className={styles.input}
              placeholder="name@institution.edu"
              required
              disabled={loading}
            />
          </div>

          <div className={styles.inputGroup}>
            <label htmlFor="auth-password" className={styles.label}>
              Account Password
            </label>
            <input
              id="auth-password"
              type="password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              className={styles.input}
              placeholder="••••••••••••"
              required
              disabled={loading}
            />
          </div>

          <div className={styles.inputGroup}>
            <label htmlFor="auth-mfa" className={styles.label}>
              MFA Authenticator Pin
            </label>
            <input
              id="auth-mfa"
              type="text"
              pattern="[0-9]*"
              inputMode="numeric"
              maxLength={6}
              value={mfaCode}
              onChange={(e) => setMfaCode(e.target.value.replace(/\D/g, ''))}
              className={styles.input}
              placeholder="000000"
              required
              disabled={loading}
            />
          </div>

          {error && (
            <div className={styles.securityBadge} role="alert">
              <span className={styles.securityBadgeIcon}>🔒</span>
              <span className={styles.securityBadgeText}>{error}</span>
            </div>
          )}

          <button
            type="submit"
            className={styles.submitButton}
            disabled={!email || !password || mfaCode.length !== 6 || loading}
          >
            {loading ? <span className={styles.spinner} /> : 'Verify Identity'}
          </button>
        </form>
      </div>
    </div>
  );
};
