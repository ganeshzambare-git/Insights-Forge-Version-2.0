import Link from 'next/link';
import type { ReactNode } from 'react';
import { Logo } from './Logo';

// Centered auth surface: brand panel on the left (desktop), form on the right.
export function AuthShell({
  title,
  subtitle,
  children,
  footer,
}: {
  title: string;
  subtitle: string;
  children: ReactNode;
  footer: ReactNode;
}) {
  return (
    <div className="auth-wrap">
      <aside className="auth-aside">
        <Link href="/" aria-label="Insight Forge home">
          <Logo onDark />
        </Link>
        <div>
          <h2 style={{ fontSize: 'var(--text-heading)', color: 'var(--white)', maxWidth: 320, marginBottom: 12 }}>
            From raw CSV to a decision, in one screen.
          </h2>
          <p style={{ color: 'rgba(255,255,255,0.68)', fontSize: 'var(--text-body-sm)', maxWidth: 320 }}>
            KPIs, risk cohorts, and ranked actions — computed by a deterministic pipeline, isolated
            to your institution’s tenant.
          </p>
        </div>
        <span style={{ fontSize: 'var(--text-caption)', color: 'rgba(255,255,255,0.4)' }}>
          Insight Forge · decision intelligence for education
        </span>
      </aside>

      <main className="auth-main">
        <div className="auth-card">
          <div className="auth-card__brand">
            <Link href="/" aria-label="Insight Forge home">
              <Logo />
            </Link>
          </div>
          <h1 style={{ fontSize: 'var(--text-heading)', marginBottom: 6 }}>{title}</h1>
          <p style={{ color: 'var(--slate)', marginBottom: 26 }}>{subtitle}</p>
          {children}
          <p style={{ marginTop: 22, fontSize: 'var(--text-body-sm)', color: 'var(--slate)', textAlign: 'center' }}>
            {footer}
          </p>
        </div>
      </main>
    </div>
  );
}
