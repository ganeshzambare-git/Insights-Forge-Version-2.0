'use client';

import Link from 'next/link';
import { useRouter } from 'next/navigation';
import { Logo } from './Logo';
import { clearSession, type SessionUser } from '@/lib/api';

export function AppHeader({ user }: { user: SessionUser | null }) {
  const router = useRouter();

  function logout() {
    clearSession();
    router.push('/login');
  }

  const initial = user?.corporate_email?.[0]?.toUpperCase() ?? '?';

  return (
    <header
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 40,
        background: 'rgba(244,244,244,0.85)',
        backdropFilter: 'saturate(180%) blur(10px)',
        borderBottom: '1px solid var(--silver)',
      }}
    >
      <div
        className="shell"
        style={{ height: 60, display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}
      >
        <Link href="/dashboard" aria-label="Dashboard">
          <Logo />
        </Link>

        <div style={{ display: 'flex', alignItems: 'center', gap: 14 }}>
          <span style={{ display: 'flex', alignItems: 'center', gap: 9 }}>
            <span
              aria-hidden="true"
              style={{
                width: 28,
                height: 28,
                borderRadius: '50%',
                background: 'var(--ink)',
                color: 'var(--white)',
                display: 'grid',
                placeItems: 'center',
                fontSize: 13,
                fontWeight: 600,
              }}
            >
              {initial}
            </span>
            <span style={{ fontSize: 'var(--text-body-sm)', color: 'var(--graphite)', maxWidth: 180, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
              {user?.corporate_email ?? '—'}
            </span>
          </span>
          <button className="btn btn--ghost btn--rect" onClick={logout}>
            Log out
          </button>
        </div>
      </div>
    </header>
  );
}
