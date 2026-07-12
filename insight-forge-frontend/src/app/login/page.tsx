'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { AuthShell } from '@/components/AuthShell';
import { api, setSession, ApiError } from '@/lib/api';

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const result = await api.login(email, password);
      setSession(result);
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Try again.');
      setLoading(false);
    }
  }

  return (
    <AuthShell
      title="Welcome back"
      subtitle="Log in to your institution’s workspace."
      footer={
        <>
          New to Insight Forge?{' '}
          <Link href="/signup" style={{ color: 'var(--action-blue-ink)', fontWeight: 500 }}>
            Create a workspace
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} style={{ display: 'grid', gap: 16 }} noValidate>
        <div className="field">
          <label htmlFor="email">Work email</label>
          <input
            id="email"
            className="input"
            type="email"
            placeholder="admin@springfield.edu"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            required
            autoComplete="email"
          />
        </div>

        <div className="field">
          <label htmlFor="password">Password</label>
          <input
            id="password"
            className="input"
            type="password"
            placeholder="Your password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            autoComplete="current-password"
          />
        </div>

        {error && (
          <div
            role="alert"
            style={{
              background: '#fdf0ef',
              color: '#b23b30',
              borderRadius: 'var(--r-input)',
              padding: '10px 12px',
              fontSize: 'var(--text-body-sm)',
            }}
          >
            {error}
          </div>
        )}

        <button type="submit" className="btn btn--lg btn--block" disabled={loading}>
          {loading ? 'Logging in…' : 'Log in'}
        </button>
      </form>
    </AuthShell>
  );
}
