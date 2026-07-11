'use client';

import { useEffect, useRef, useState } from 'react';
import styles from './landing.module.css';

/* ----------------------------- mini charts ----------------------------- */

function AreaLine({ points, labels, stroke = 'var(--brand)' }: { points: number[]; labels: string[]; stroke?: string }) {
  const w = 520, h = 220, pl = 42, pr = 16, pt = 18, pb = 34;
  const max = Math.max(...points) * 1.08, min = Math.min(...points) * 0.94;
  const cw = w - pl - pr, ch = h - pt - pb;
  const xy = points.map((v, i) => [pl + (i / (points.length - 1)) * cw, pt + ch - ((v - min) / (max - min)) * ch]);
  const line = xy.map((p, i) => `${i ? 'L' : 'M'}${p[0]},${p[1]}`).join(' ');
  const area = `${line} L${xy[xy.length - 1][0]},${pt + ch} L${xy[0][0]},${pt + ch} Z`;
  return (
    <svg viewBox={`0 0 ${w} ${h}`} width="100%" height="auto" role="img" aria-label="Attendance trend">
      <defs>
        <linearGradient id="ig-area" x1="0" y1="0" x2="0" y2="1">
          <stop offset="0%" stopColor="var(--brand)" stopOpacity="0.22" />
          <stop offset="100%" stopColor="var(--brand)" stopOpacity="0" />
        </linearGradient>
      </defs>
      {[0, 0.5, 1].map((g, i) => {
        const y = pt + ch - g * ch;
        return (
          <g key={i}>
            <line x1={pl} y1={y} x2={w - pr} y2={y} stroke="var(--border)" strokeDasharray="3 4" />
            <text x={pl - 8} y={y + 4} fontSize="11" textAnchor="end" fill="var(--muted)">{Math.round(min + g * (max - min))}</text>
          </g>
        );
      })}
      <path d={area} fill="url(#ig-area)" />
      <path d={line} fill="none" stroke={stroke} strokeWidth="3" strokeLinecap="round" strokeLinejoin="round" />
      {xy.map((p, i) => (
        <g key={i}>
          <circle cx={p[0]} cy={p[1]} r="4.5" fill="var(--surface)" stroke={stroke} strokeWidth="2.5" />
          <text x={p[0]} y={h - 12} fontSize="11" textAnchor="middle" fill="var(--muted)">{labels[i]}</text>
        </g>
      ))}
    </svg>
  );
}

function Donut({ segments, size = 190 }: { segments: { value: number; color: string }[]; size?: number }) {
  const total = segments.reduce((a, s) => a + s.value, 0);
  const r = 66, c = 2 * Math.PI * r, cx = size / 2, cy = size / 2;
  let off = 0;
  return (
    <svg viewBox={`0 0 ${size} ${size}`} width={size} height={size} role="img" aria-label="Risk distribution">
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--surface-3)" strokeWidth="20" />
      {segments.map((s, i) => {
        const frac = s.value / total;
        const el = <circle key={i} cx={cx} cy={cy} r={r} fill="none" stroke={s.color} strokeWidth="20" strokeDasharray={`${frac * c} ${c - frac * c}`} strokeDashoffset={-off * c} transform={`rotate(-90 ${cx} ${cy})`} />;
        off += frac;
        return el;
      })}
      <text x={cx} y={cy - 2} textAnchor="middle" fontFamily="var(--font-serif)" fontSize="28" fill="var(--ink)">{segments[0].value}%</text>
      <text x={cx} y={cy + 18} textAnchor="middle" fontSize="12" fill="var(--muted)">on track</text>
    </svg>
  );
}

function BarsV({ items }: { items: { label: string; value: number; color?: string }[] }) {
  const w = 520, h = 230, pb = 40, pt = 16, gap = 26;
  const bw = (w - gap * (items.length + 1)) / items.length, ch = h - pt - pb;
  return (
    <svg viewBox={`0 0 ${w} ${h}`} width="100%" height="auto" role="img" aria-label="Programme scores">
      {[0, 50, 100].map((g, i) => {
        const y = pt + ch - (g / 100) * ch;
        return <g key={i}><line x1={0} y1={y} x2={w} y2={y} stroke="var(--border)" strokeDasharray="3 4" /><text x={2} y={y - 4} fontSize="10" fill="var(--muted)">{g}</text></g>;
      })}
      {items.map((it, i) => {
        const x = gap + i * (bw + gap), bh = (it.value / 100) * ch, y = pt + ch - bh;
        return (
          <g key={i}>
            <rect x={x} y={y} width={bw} height={bh} rx="7" fill={it.color || 'var(--brand)'} />
            <text x={x + bw / 2} y={y - 8} fontSize="13" textAnchor="middle" fontFamily="var(--font-serif)" fill="var(--ink)">{it.value}</text>
            <text x={x + bw / 2} y={h - 14} fontSize="11" textAnchor="middle" fill="var(--muted)">{it.label}</text>
          </g>
        );
      })}
    </svg>
  );
}

function BarsH({ items, unit = '', color = 'var(--brand)' }: { items: { label: string; value: number; sub?: string }[]; unit?: string; color?: string }) {
  const max = Math.max(...items.map((i) => i.value));
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '1.05rem' }}>
      {items.map((it, i) => (
        <div key={i}>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.86rem', marginBottom: '0.35rem' }}>
            <span style={{ color: 'var(--ink)', fontWeight: 600 }}>{it.label}</span>
            <span style={{ color: 'var(--muted)' }}>{it.value}{unit}{it.sub ? ` · ${it.sub}` : ''}</span>
          </div>
          <div style={{ height: '9px', background: 'var(--surface-3)', borderRadius: '999px', overflow: 'hidden' }}>
            <div style={{ width: `${(it.value / max) * 100}%`, height: '100%', borderRadius: '999px', background: color }} />
          </div>
        </div>
      ))}
    </div>
  );
}

/* per-list-item mini sparkline for the floating preview */
function Spark({ pts, color = 'var(--brand)' }: { pts: number[]; color?: string }) {
  const w = 268, h = 120, max = Math.max(...pts), min = Math.min(...pts);
  const d = pts.map((v, i) => `${i ? 'L' : 'M'}${(i / (pts.length - 1)) * w},${h - ((v - min) / (max - min || 1)) * (h - 16) - 8}`).join(' ');
  return (
    <svg viewBox={`0 0 ${w} ${h}`} width="100%" height="120" preserveAspectRatio="none">
      <path d={`${d} L${w},${h} L0,${h} Z`} fill={color} opacity="0.12" />
      <path d={d} fill="none" stroke={color} strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

/* --------------------------------- data --------------------------------- */

const LIST_ITEMS = [
  { title: 'Attendance', meta: 'trend by term', spark: [79, 80, 83, 84, 87], color: 'var(--brand)' },
  { title: 'Performance', meta: 'grades & GPA', spark: [72, 78, 76, 83, 86], color: 'var(--violet)' },
  { title: 'Risk', meta: 'Safe · Amber · Critical', spark: [40, 55, 48, 62, 70], color: 'var(--warn)' },
  { title: 'Resources', meta: 'budget & utilization', spark: [30, 42, 38, 55, 60], color: 'var(--safe)' },
  { title: 'Interventions', meta: 'coaching log', spark: [10, 24, 20, 32, 44], color: 'var(--critical)' },
];

const PIPELINE = [
  ['01', 'Ingest', 'Files stream to storage in 1 MB chunks. Nothing is parsed on the way in — the raw upload is preserved and a dataset is registered.'],
  ['02', 'Clean', 'The cleaning step validates rows, normalizes grades and attendance, and materializes structured metrics — flagging the rows it had to skip.'],
  ['03', 'Analyze', 'Deterministic analytics classify risk tiers and health scores; the four-agent AI pipeline reads the whole profile end to end.'],
  ['04', 'Decide', 'Prioritized recommendations, KPIs and alerts land on role-scoped dashboards for faculty, deans and admins.'],
];

/* --------------------------------- page --------------------------------- */

export default function LandingPage() {
  const previewRef = useRef<HTMLDivElement | null>(null);
  const navRef = useRef<HTMLElement | null>(null);
  const [preview, setPreview] = useState<number | null>(null);

  // smooth scroll (Lenis) + nav "scrolled" state. Reveals are CSS-only
  // (scroll-timeline) so content is never gated behind JS.
  useEffect(() => {
    let lenis: any;
    let rafId = 0;
    let cancelled = false;
    (async () => {
      const { default: Lenis } = await import('lenis');
      if (cancelled) return;
      lenis = new Lenis({ duration: 1.1 });
      lenis.on('scroll', ({ scroll }: { scroll: number }) => {
        if (navRef.current) navRef.current.classList.toggle(styles.navScrolled, scroll > 40);
      });
      const raf = (time: number) => {
        lenis.raf(time);
        rafId = requestAnimationFrame(raf);
      };
      rafId = requestAnimationFrame(raf);
    })();

    return () => {
      cancelled = true;
      cancelAnimationFrame(rafId);
      lenis?.destroy();
    };
  }, []);

  // cursor-follow preview for the hover list
  const onListMove = (e: React.MouseEvent) => {
    const el = previewRef.current;
    if (!el) return;
    el.style.transform = `translate(${e.clientX - 150}px, ${e.clientY - 100}px) scale(${preview !== null ? 1 : 0.7})`;
  };

  return (
    <div className={styles.page} onMouseMove={onListMove}>
      {/* floating preview */}
      <div
        ref={previewRef}
        className={styles.floatPreview}
        style={{ opacity: preview !== null ? 1 : 0 }}
      >
        {preview !== null && (
          <>
            <div style={{ fontSize: '0.78rem', fontWeight: 600, color: 'var(--ink)', marginBottom: '0.4rem' }}>
              {LIST_ITEMS[preview].title}
            </div>
            <Spark pts={LIST_ITEMS[preview].spark} color={LIST_ITEMS[preview].color} />
          </>
        )}
      </div>

      {/* Nav */}
      <nav ref={navRef} className={styles.nav}>
        <a href="#top" className={styles.brand} style={{ textDecoration: 'none' }}>
          <span className={styles.brandMark}>IF</span>
          Insight Forge
        </a>
        <div className={styles.navMenu}>
          {[
            ['Platform', ['Ingestion', 'Cleaning', 'Analytics']],
            ['Academics', ['Attendance', 'Performance', 'Risk']],
            ['AI', ['Data Engineer', 'Analyst', 'Executive report']],
            ['Finance', ['Budgets', 'Utilization']],
          ].map(([h, subs]) => (
            <div className={styles.navCol} key={h as string}>
              <h4>{h as string}</h4>
              <div className={styles.sub}>
                {(subs as string[]).map((s) => (
                  <span key={s}>{s}</span>
                ))}
              </div>
            </div>
          ))}
        </div>
        <a href="/login" className={styles.navCta}>
          Sign in →
        </a>
      </nav>

      {/* Hero */}
      <header className={styles.hero} id="top">
        <span className={styles.heroPill}>
          <b>Live</b> Multi-tenant · secure by row-level isolation
        </span>
        <h1 className={styles.heroTitle}>
          Decision
          <span className={styles.circle}>◍</span>
          Intelligence
        </h1>
        <p className={styles.heroSub}>
          Insight Forge ingests a college&rsquo;s messy exports, cleans them, and reads back
          attendance, performance, risk and resources — the whole institution, at a glance.
        </p>
        <div className={styles.heroCtas}>
          <a href="/login" className={styles.btnSolid}>Open the workspace →</a>
          <a href="#pipeline" className={styles.btnLine}>See how it works</a>
        </div>

        <div className={styles.marquee}>
          <div className={styles.marqueeTrack}>
            {[...Array(2)].map((_, k) => (
              <span key={k} style={{ display: 'inline-flex' }}>
                {['Attendance', 'Performance', 'Risk tiers', 'Finance', 'AI pipeline', 'Ingestion', 'Interventions', 'Real-time', 'Multi-tenant'].map((t) => (
                  <span key={t}>{t}</span>
                ))}
              </span>
            ))}
          </div>
        </div>
      </header>

      {/* Hover-preview list */}
      <section className={styles.listSection}>
        <div className={styles.wrap}>
          <div className={styles.listGrid}>
            <div data-reveal>
              <span className={styles.eyebrow}>What it reads</span>
              <h2 className={styles.big}>One platform, the whole student picture.</h2>
              <p className={styles.lede}>
                Every signal an institution already collects — turned into something a dean can
                actually act on. Hover to preview each dimension.
              </p>
            </div>
            <div className={styles.list}>
              {LIST_ITEMS.map((it, i) => (
                <div
                  key={it.title}
                  className={styles.listRow}
                  onMouseEnter={() => setPreview(i)}
                  onMouseLeave={() => setPreview(null)}
                >
                  <h3>{it.title}</h3>
                  <span>{it.meta}</span>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Reel / dashboard preview band */}
      <section className={styles.reel}>
        <div className={styles.reelInner}>
          <h2 data-reveal>Read your institution at a glance.</h2>
          <p data-reveal>
            Attendance, risk and resources — composed on one canvas, updated the moment a
            dataset lands.
          </p>
          <div className={styles.reelFrame} data-reveal>
            <div className={styles.reelCard}>
              <div className={styles.lbl}><span>Attendance · Fall term</span><span className="badge badge-safe">Improving</span></div>
              <AreaLine points={[79, 80, 83, 84, 87]} labels={['W1', 'W4', 'W8', 'W11', 'W14']} />
            </div>
            <div className={styles.reelStats}>
              {[['84%', 'Health index'], ['58%', 'On track'], ['$965k', 'Allocated'], ['4', 'AI agents']].map(([n, l]) => (
                <div className={styles.reelStat} key={l}>
                  <div className="n" style={{ fontFamily: 'var(--font-serif)', fontSize: '1.9rem', fontWeight: 500 }}>{n}</div>
                  <div className="l" style={{ fontSize: '0.78rem', color: 'var(--muted)', marginTop: '0.35rem' }}>{l}</div>
                </div>
              ))}
            </div>
          </div>
        </div>
      </section>

      {/* Sticky graph sections */}
      <section id="academics" className={styles.stickySection}>
        <div className={styles.wrap}>
          <div className={styles.stickyGrid}>
            <div className={styles.stickyLeft} data-reveal>
              <span className={styles.eyebrow}>Academic intelligence</span>
              <h2 className={styles.big}>See every cohort&rsquo;s trajectory.</h2>
              <p className={styles.lede}>
                Attendance is aggregated across reporting periods and cohorts, so engagement
                trends surface before they show up in grades — and the same records power
                course performance and risk.
              </p>
              <div className={styles.detailRow}>
                <span className={styles.ic}>↗</span>
                <div><strong>Trend, not snapshots.</strong><p>A 79% → 87% recovery reads instantly.</p></div>
              </div>
              <div className={styles.detailRow}>
                <span className={styles.ic}>◎</span>
                <div><strong>Explainable risk tiers.</strong><p>Safe / Amber / Critical from fixed thresholds.</p></div>
              </div>
            </div>
            <div>
              <div className={styles.chartCard} data-reveal>
                <div className={styles.chartHead}><span className="t" style={{ fontWeight: 600 }}>Average attendance by term</span><span className="m" style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>3 cohorts · 2026</span></div>
                <AreaLine points={[80, 83, 87]} labels={['Spring', 'Summer', 'Fall']} />
              </div>
              <div className={styles.chartCard} data-reveal>
                <div className={styles.chartHead}><span className="t" style={{ fontWeight: 600 }}>Student risk distribution</span><span className="m" style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>current term</span></div>
                <div style={{ display: 'flex', gap: '1.75rem', alignItems: 'center', flexWrap: 'wrap', justifyContent: 'center' }}>
                  <Donut segments={[{ value: 58, color: 'var(--safe)' }, { value: 27, color: 'var(--warn)' }, { value: 15, color: 'var(--critical)' }]} />
                  <div className={styles.legend}>
                    <span><i style={{ background: 'var(--safe)' }} />Safe — GPA ≥ 3.0, attendance ≥ 85%</span>
                    <span><i style={{ background: 'var(--warn)' }} />Amber — early warning signs</span>
                    <span><i style={{ background: 'var(--critical)' }} />Critical — needs intervention</span>
                  </div>
                </div>
              </div>
              <div className={styles.chartCard} data-reveal>
                <div className={styles.chartHead}><span className="t" style={{ fontWeight: 600 }}>Average score by programme</span><span className="m" style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>out of 100</span></div>
                <BarsV items={[{ label: 'ENG-2026', value: 86, color: 'var(--safe)' }, { label: 'MTH-2026', value: 84 }, { label: 'CS-2026', value: 82 }, { label: 'DS-2026', value: 73, color: 'var(--warn)' }]} />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* AI + finance split band */}
      <section className={styles.stickySection}>
        <div className={styles.wrap}>
          <div className={styles.stickyGrid}>
            <div className={styles.stickyLeft} data-reveal>
              <span className={styles.eyebrow}>The AI pipeline</span>
              <h2 className={styles.big}>Four analysts, one report.</h2>
              <p className={styles.lede}>
                A chain of specialised agents walks each dataset end to end — Data Engineer,
                Data Analyst, Business Analyst, Executive Report — handing an evolving context
                down the line. The report is the sum of the chain, not a single prompt.
              </p>
            </div>
            <div>
              <div className={styles.chartCard} data-reveal>
                <div className={styles.chartHead}><span className="t" style={{ fontWeight: 600 }}>Agent execution · last run</span><span className="m" style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>sequential</span></div>
                <BarsH unit=" ms" color="var(--violet)" items={[{ label: 'Data Engineer', value: 20.9, sub: 'profiling' }, { label: 'Data Analyst', value: 6.8, sub: 'insights' }, { label: 'Business Analyst', value: 4.1, sub: 'strategy' }, { label: 'Executive Report', value: 1.1, sub: 'summary' }]} />
              </div>
              <div className={styles.chartCard} data-reveal>
                <div className={styles.chartHead}><span className="t" style={{ fontWeight: 600 }}>Budget utilization by category</span><span className="m" style={{ fontSize: '0.8rem', color: 'var(--muted)' }}>FY-2026 · $965k</span></div>
                <BarsH unit="%" items={[{ label: 'Student Services', value: 36, sub: '$95k' }, { label: 'Infrastructure', value: 30, sub: '$120k' }, { label: 'Faculty Resources', value: 24, sub: '$540k' }, { label: 'Research & Development', value: 15, sub: '$210k' }]} />
              </div>
            </div>
          </div>
        </div>
      </section>

      {/* Pipeline accordion */}
      <section id="pipeline" className={styles.accSection}>
        <div className={styles.wrap}>
          <div data-reveal>
            <span className={styles.eyebrow}>The flow</span>
            <h2 className={styles.big}>From a messy CSV to a confident call.</h2>
          </div>
          <div className={styles.acc}>
            {PIPELINE.map(([idx, title, body]) => (
              <div className={styles.accRow} key={idx} data-reveal>
                <div className={styles.accOver} />
                <span className={styles.accIdx}>{idx}</span>
                <div className={styles.accBody}>
                  <h3>{title}</h3>
                  <p>{body}</p>
                </div>
                <span className={styles.accArrow}>→</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* CTA */}
      <section className={styles.ctaBand}>
        <h2 data-reveal>Every tenant, sealed off from the next.</h2>
        <p data-reveal>
          Row-level security in the database, short-lived JWTs, role-based access, and
          real-time cleaning on background tasks — no paid workers required.
        </p>
        <a href="/login" className={styles.ctaBtn} data-reveal>Open the workspace →</a>
      </section>

      <footer className={styles.footer}>
        <span className={styles.brand}><span className={styles.brandMark}>IF</span> Insight Forge</span>
        <span>© 2026 ReadyNest Partners · Educational Decision Intelligence</span>
      </footer>
    </div>
  );
}
