'use client';

import Link from 'next/link';
import { motion, useReducedMotion } from 'framer-motion';
import { SiteNav } from '@/components/SiteNav';
import { Reveal } from '@/components/Reveal';
import { CountUp } from '@/components/CountUp';
import { LineChart } from '@/components/charts/LineChart';
import { BarChart } from '@/components/charts/BarChart';
import { DonutChart } from '@/components/charts/DonutChart';

const trend = [
  { label: 'Wk 1', value: 71 },
  { label: 'Wk 2', value: 68 },
  { label: 'Wk 3', value: 74 },
  { label: 'Wk 4', value: 70 },
  { label: 'Wk 5', value: 78 },
  { label: 'Wk 6', value: 83 },
  { label: 'Wk 7', value: 81 },
  { label: 'Wk 8', value: 88 },
];

const cohorts = [
  { label: 'Safe', value: 61, color: 'var(--c-safe)' },
  { label: 'Amber', value: 27, color: 'var(--c-amber)' },
  { label: 'Critical', value: 12, color: 'var(--c-critical)' },
];

const recs = [
  { label: 'Targeted tutoring · Physics', value: 42, sub: 'est. lift' },
  { label: 'Attendance outreach', value: 31, sub: 'est. lift' },
  { label: 'Cohort re-balancing', value: 18, sub: 'est. lift' },
];

const pipeline = [
  { n: '01', title: 'Data Engineer', body: 'Profiles every column, classifies types, and scores data quality — deterministically.' },
  { n: '02', title: 'Data Analyst', body: 'Runs real statistics: trends, correlations, outliers. Rejects findings the data can’t support.' },
  { n: '03', title: 'Business Analyst', body: 'Traces anomalies to root causes and weighs hypotheses into concrete opportunities.' },
  { n: '04', title: 'Executive Report', body: 'Ranks recommendations by impact and writes the summary a dean can act on.' },
];

const heroStagger = { hidden: {}, show: { transition: { staggerChildren: 0.09, delayChildren: 0.05 } } };
const heroItem = {
  hidden: { opacity: 0, y: 18 },
  show: { opacity: 1, y: 0, transition: { duration: 0.7, ease: [0.22, 1, 0.36, 1] as const } },
};

export default function LandingPage() {
  const reduce = useReducedMotion();

  return (
    <>
      <SiteNav />

      <main>
        {/* Hero */}
        <section className="shell" style={{ paddingTop: 'clamp(48px, 8vw, 96px)', paddingBottom: 'var(--section-gap)' }}>
          <div className="hero-grid">
            <motion.div
              variants={reduce ? undefined : heroStagger}
              initial={reduce ? undefined : 'hidden'}
              animate={reduce ? undefined : 'show'}
              style={{ maxWidth: 560 }}
            >
              <motion.span variants={heroItem} className="tag" style={{ marginBottom: 20 }}>
                <span style={{ width: 6, height: 6, borderRadius: 999, background: 'var(--action-blue)' }} />
                Decision intelligence for education
              </motion.span>

              <motion.h1 variants={heroItem} style={{ fontSize: 'var(--text-display)', letterSpacing: '-0.03em', marginBottom: 18 }}>
                Turn educational data into decisions.
              </motion.h1>

              <motion.p variants={heroItem} style={{ fontSize: 'var(--text-subheading)', color: 'var(--slate)', lineHeight: 1.5, maxWidth: 480, marginBottom: 28 }}>
                Upload a CSV. A deterministic multi-agent pipeline profiles it, computes real
                statistics, and hands back KPIs, risk cohorts, and ranked actions — no spreadsheets,
                no waiting on a data team.
              </motion.p>

              <motion.div variants={heroItem} style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
                <Link href="/signup" className="btn btn--lg">Start for free</Link>
                <Link href="#how" className="btn btn--ghost btn--lg">See how it works</Link>
              </motion.div>

              <motion.p variants={heroItem} style={{ marginTop: 16, fontSize: 'var(--text-body-sm)', color: 'var(--stone)' }}>
                No credit card · Your data stays in your tenant.
              </motion.p>
            </motion.div>

            <HeroVisual />
          </div>
        </section>

        {/* Capability strip */}
        <section className="shell" style={{ paddingBottom: 'var(--section-gap)' }}>
          <Reveal>
            <div className="strip">
              <StripStat value={<CountUp value={4} />} label="specialist agents, run in sequence" />
              <StripStat value={<CountUp value={100} suffix="%" />} label="deterministic — same data, same answer" />
              <StripStat value={<>~<CountUp value={2} suffix="s" /></>} label="from upload to full report" />
            </div>
          </Reveal>
        </section>

        {/* How it works */}
        <section id="how" className="shell" style={{ paddingBottom: 'var(--section-gap)' }}>
          <Reveal>
            <div style={{ maxWidth: 620, marginBottom: 44 }}>
              <h2 style={{ fontSize: 'var(--text-heading-lg)', marginBottom: 14 }}>One pipeline, four specialists.</h2>
              <p style={{ fontSize: 'var(--text-subheading)', color: 'var(--slate)' }}>
                Not a black box. Each stage does one job on your real data and passes its findings
                to the next — so every number on the report is traceable.
              </p>
            </div>
          </Reveal>

          <ol className="pipeline">
            {pipeline.map((step, i) => (
              <Reveal key={step.n} delay={i * 0.06}>
                <li className="card pipeline__card">
                  <span className="pipeline__n">{step.n}</span>
                  <h3 style={{ fontSize: 'var(--text-heading-sm)', margin: '14px 0 8px' }}>{step.title}</h3>
                  <p style={{ color: 'var(--slate)', fontSize: 'var(--text-body-sm)' }}>{step.body}</p>
                </li>
              </Reveal>
            ))}
          </ol>
        </section>

        {/* Capabilities with live charts */}
        <section className="shell" style={{ paddingBottom: 'var(--section-gap)' }}>
          <FeatureBlock
            kicker="Trends"
            title="Watch performance move over time."
            body="Every numeric measure becomes a trend line the moment it lands — attendance, GPA, completion — with the direction called out for you."
            visual={
              <div className="card" style={{ padding: 20 }}>
                <ChartHeader title="Average attendance" delta="+17 pts" />
                <LineChart data={trend} ariaLabel="Attendance trending upward over eight weeks" />
              </div>
            }
          />

          <FeatureBlock
            reverse
            kicker="Risk cohorts"
            title="See who needs attention, at a glance."
            body="Students are grouped Safe / Amber / Critical from their real indicators, so an intervention list writes itself."
            visual={
              <div className="card" style={{ padding: 24 }}>
                <ChartHeader title="Cohort risk mix" delta="892 students" />
                <div style={{ marginTop: 12 }}>
                  <DonutChart data={cohorts} centerValue="61%" centerLabel="on track" ariaLabel="Risk cohort distribution donut" />
                </div>
              </div>
            }
          />

          <FeatureBlock
            kicker="Recommendations"
            title="Ranked actions, not just charts."
            body="The pipeline weighs opportunities and hands back a prioritized list with estimated lift — the decision, made explicit."
            visual={
              <div className="card" style={{ padding: 24 }}>
                <ChartHeader title="Recommended actions" delta="by est. lift" />
                <div style={{ marginTop: 16 }}>
                  <BarChart data={recs} unit="%" ariaLabel="Recommended actions ranked by estimated lift" />
                </div>
              </div>
            }
          />
        </section>

        {/* Final CTA */}
        <section className="shell" style={{ paddingBottom: 'var(--section-gap)' }}>
          <Reveal>
            <div className="cta">
              <h2 style={{ fontSize: 'var(--text-heading-lg)', color: 'var(--white)', marginBottom: 12 }}>
                Your next decision is one upload away.
              </h2>
              <p style={{ color: 'rgba(255,255,255,0.7)', fontSize: 'var(--text-subheading)', maxWidth: 460, margin: '0 auto 26px' }}>
                Create your institution’s workspace and analyze your first dataset in minutes.
              </p>
              <Link href="/signup" className="btn btn--lg" style={{ background: 'var(--white)', color: 'var(--ink)' }}>
                Create your workspace
              </Link>
            </div>
          </Reveal>
        </section>
      </main>

      <footer style={{ borderTop: '1px solid var(--silver)' }}>
        <div className="shell" style={{ minHeight: 72, display: 'flex', alignItems: 'center', justifyContent: 'space-between', flexWrap: 'wrap', gap: 12, paddingBlock: 16 }}>
          <span style={{ fontSize: 'var(--text-body-sm)', color: 'var(--slate)' }}>
            Insight Forge — decision intelligence for education
          </span>
          <span style={{ fontSize: 'var(--text-caption)', color: 'var(--stone)' }}>
            Built on a deterministic, tenant-isolated backend.
          </span>
        </div>
      </footer>
    </>
  );
}

function StripStat({ value, label }: { value: React.ReactNode; label: string }) {
  return (
    <div>
      <div style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: 30, color: 'var(--graphite)', letterSpacing: '-0.02em' }}>
        {value}
      </div>
      <div style={{ fontSize: 'var(--text-body-sm)', color: 'var(--slate)', marginTop: 4 }}>{label}</div>
    </div>
  );
}

function ChartHeader({ title, delta }: { title: string; delta: string }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', marginBottom: 8 }}>
      <span style={{ fontSize: 'var(--text-body-sm)', fontWeight: 500, color: 'var(--graphite)' }}>{title}</span>
      <span style={{ fontSize: 'var(--text-caption)', color: 'var(--action-blue-ink)', fontWeight: 500 }}>{delta}</span>
    </div>
  );
}

function FeatureBlock({
  kicker,
  title,
  body,
  visual,
  reverse,
}: {
  kicker: string;
  title: string;
  body: string;
  visual: React.ReactNode;
  reverse?: boolean;
}) {
  return (
    <div className={`feature${reverse ? ' feature--reverse' : ''}`}>
      <Reveal className="feature__text">
        <span className="eyebrow" style={{ marginBottom: 12 }}>{kicker}</span>
        <h3 style={{ fontSize: 'var(--text-heading)', margin: '4px 0 12px', maxWidth: 420 }}>{title}</h3>
        <p style={{ color: 'var(--slate)', maxWidth: 420 }}>{body}</p>
      </Reveal>
      <Reveal className="feature__visual" delay={0.08}>{visual}</Reveal>
    </div>
  );
}

function HeroVisual() {
  const reduce = useReducedMotion();
  return (
    <motion.div
      initial={reduce ? undefined : { opacity: 0, y: 24, scale: 0.98 }}
      animate={reduce ? undefined : { opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.9, delay: 0.15, ease: [0.22, 1, 0.36, 1] }}
      className="card"
      style={{ padding: 20 }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 16 }}>
        <div>
          <div style={{ fontSize: 'var(--text-caption)', color: 'var(--slate)' }}>students_fall.csv</div>
          <div style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: 18 }}>Analysis report</div>
        </div>
        <span className="tag" style={{ background: 'var(--info-bg)', color: 'var(--action-blue-ink)' }}>Ready</span>
      </div>

      <div style={{ background: 'var(--paper)', borderRadius: 10, padding: 14, marginBottom: 12 }}>
        <ChartHeader title="Average GPA" delta="+0.4" />
        <LineChart data={trend} height={150} ariaLabel="GPA trend preview" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 12 }}>
        <div style={{ background: 'var(--paper)', borderRadius: 10, padding: 14 }}>
          <div style={{ fontSize: 'var(--text-caption)', color: 'var(--slate)', marginBottom: 8 }}>Health score</div>
          <div style={{ fontFamily: 'var(--font-display)', fontWeight: 600, fontSize: 34, color: 'var(--graphite)' }}>
            <CountUp value={94} suffix="%" />
          </div>
          <div style={{ fontSize: 'var(--text-caption)', color: 'var(--action-blue-ink)', marginTop: 2 }}>Certified clean</div>
        </div>
        <div style={{ background: 'var(--paper)', borderRadius: 10, padding: 14, display: 'flex', flexDirection: 'column' }}>
          <div style={{ fontSize: 'var(--text-caption)', color: 'var(--slate)', marginBottom: 8 }}>Cohorts</div>
          <div style={{ display: 'flex', justifyContent: 'center' }}>
            <DonutChart data={cohorts} size={92} thickness={13} showLegend={false} ariaLabel="Cohort mix preview" />
          </div>
        </div>
      </div>
    </motion.div>
  );
}
