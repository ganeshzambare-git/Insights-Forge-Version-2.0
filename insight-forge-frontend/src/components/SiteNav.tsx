'use client';

import Link from 'next/link';
import { useEffect, useState } from 'react';
import { Logo } from './Logo';

// Sticky marketing header. Gains a subtle surface + shadow after the first scroll.
export function SiteNav() {
  const [scrolled, setScrolled] = useState(false);

  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener('scroll', onScroll, { passive: true });
    return () => window.removeEventListener('scroll', onScroll);
  }, []);

  return (
    <header
      style={{
        position: 'sticky',
        top: 0,
        zIndex: 'var(--z-sticky)' as unknown as number,
        background: scrolled ? 'rgba(244,244,244,0.82)' : 'transparent',
        backdropFilter: scrolled ? 'saturate(180%) blur(10px)' : 'none',
        borderBottom: scrolled ? '1px solid var(--silver)' : '1px solid transparent',
        transition: 'background 0.3s ease, border-color 0.3s ease',
      }}
    >
      <div
        className="shell"
        style={{
          height: 64,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
        }}
      >
        <Link href="/" aria-label="Insight Forge home">
          <Logo />
        </Link>

        <nav style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <Link
            href="/login"
            className="btn btn--ghost btn--rect"
            style={{ background: 'transparent', borderColor: 'transparent' }}
          >
            Log in
          </Link>
          <Link href="/signup" className="btn btn--rect">
            Get started
          </Link>
        </nav>
      </div>
    </header>
  );
}
