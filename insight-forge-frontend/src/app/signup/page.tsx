'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { useState } from 'react';
import { AuthShell } from '@/components/AuthShell';
import { api, setSession, ApiError } from '@/lib/api';

export default function SignupPage() {
  const router = useRouter();
  const [org, setOrg] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function onSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const result = await api.signup(org, email, password);
      setSession(result);
      router.push('/dashboard');
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Something went wrong. Try again.');
      setLoading(false);
    }
  }

  return (
    <AuthShell
      title="Create your workspace"
      subtitle="Set up your institution and its first admin account."
      footer={
        <>
          Already have an account?{' '}
          <Link href="/login" style={{ color: 'var(--action-blue-ink)', fontWeight: 500 }}>
            Log in
          </Link>
        </>
      }
    >
      <form onSubmit={onSubmit} style={{ display: 'grid', gap: 16 }} noValidate>
        <div className="field">
          <label htmlFor="org">Organization name</label>
          <input
            id="org"
            className="input"
            placeholder="Springfield College"
            value={org}
            onChange={(e) => setOrg(e.target.value)}
            required
            minLength={2}
            autoComplete="organization"
          />
        </div>

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
            placeholder="At least 8 characters"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            required
            minLength={8}
            autoComplete="new-password"
            aria-describedby="pw-hint"
          />
          <span id="pw-hint" style={{ fontSize: 'var(--text-caption)', color: 'var(--stone)' }}>
            8+ chars with upper, lower, a number, and a symbol.
          </span>
        </div>

        {error && <FormError message={error} />}

        <button type="submit" className="btn btn--lg btn--block" disabled={loading}>
          {loading ? 'Creating workspace…' : 'Create workspace'}
        </button>
      </form>
    </AuthShell>
  );
}

function FormError({ message }: { message: string }) {
  return (
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
      {message}
    </div>
  );
}
