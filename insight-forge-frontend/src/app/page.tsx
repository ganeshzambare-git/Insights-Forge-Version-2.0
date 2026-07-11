'use client';

import React, { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useIsAuthenticated, useCurrentUser, useAuthActions } from '../features/authentication/store/authStore';
import { useWorkspaceTenant } from '../features/workspace/store/workspaceStore';
import { getAccessToken } from '../core/api/apiClient';
import { RoleGuard } from '../features/authentication/components/RoleGuard';

export default function Home() {
  const router = useRouter();
  const isAuthenticated = useIsAuthenticated();
  const currentUser = useCurrentUser();
  const { logout, initializeSession } = useAuthActions();
  const tenant = useWorkspaceTenant();

  const [file, setFile] = useState<File | null>(null);
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<any>(null);
  const [error, setError] = useState<string | null>(null);

  // Initialize session on mount
  useEffect(() => {
    initializeSession();
  }, [initializeSession]);

  // Redirect guard
  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }
    if (currentUser?.role === 'Student') {
      router.push('/student');
    }
  }, [isAuthenticated, currentUser, router]);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    if (e.target.files && e.target.files[0]) {
      setFile(e.target.files[0]);
    }
  };

  const handleAnalyze = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!file) return;

    setLoading(true);
    setError(null);
    setResult(null);

    const formData = new FormData();
    formData.append('file', file);

    try {
      const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
      const token = getAccessToken();
      const tenantId = typeof window !== 'undefined' ? sessionStorage.getItem('__tenant_context_id') : '';

      const response = await fetch(`${apiUrl}/api/v1/ai/analyze`, {
        method: 'POST',
        headers: {
          'Authorization': `Bearer ${token}`,
          'X-Tenant-ID': tenantId || '',
        },
        body: formData,
      });

      if (!response.ok) {
        throw new Error(`API analysis failed with status: ${response.status}`);
      }

      const envelope = await response.json();
      if (!envelope.success) {
        throw new Error(envelope.message || 'Pipeline orchestration failed.');
      }

      setResult(envelope.data);
    } catch (err: any) {
      setError(err.message || 'An unexpected connection error occurred.');
    } finally {
      setLoading(false);
    }
  };

  if (!isAuthenticated) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '100vh', color: 'var(--muted)' }}>
        Verifying session...
      </div>
    );
  }

  return (
    <main className="dashboard-container">
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        gap: '1rem',
        flexWrap: 'wrap',
        paddingBottom: '1.25rem',
        marginBottom: '2.5rem',
        borderBottom: '1px solid var(--border)',
      }}>
        <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.6rem', fontWeight: 600, letterSpacing: '0.02em', color: 'var(--ink)' }}>
          <span style={{ width: '26px', height: '26px', borderRadius: '7px', background: 'var(--brand)', color: 'oklch(0.99 0 0)', display: 'grid', placeItems: 'center', fontFamily: 'var(--font-serif)', fontSize: '0.95rem' }}>IF</span>
          Insight Forge
        </div>
        <div style={{ display: 'flex', gap: '0.9rem', alignItems: 'center' }}>
          <div style={{ textAlign: 'right', fontSize: '0.85rem', lineHeight: 1.3 }}>
            <div style={{ color: 'var(--ink)', fontWeight: 600 }}>{currentUser?.email}</div>
            <div style={{ color: 'var(--muted)' }}>{currentUser?.role} {tenant ? `· ${tenant.name}` : ''}</div>
          </div>
          <RoleGuard allowedRoles={['Admin']}>
            <button onClick={() => router.push('/admin')} className="btn">
              Admin Console
            </button>
          </RoleGuard>
          <button onClick={logout} className="btn btn-secondary">
            Sign Out
          </button>
        </div>
      </div>

      <header className="header">
        <h1 className="title">Decision Intelligence, distilled.</h1>
        <p className="subtitle">Upload a dataset and let the multi-agent pipeline surface anomalies, findings, and prioritized recommendations.</p>
      </header>

      <section className="glass-card">
        <h2 style={{ marginBottom: '1rem', fontWeight: 600 }}>Analyze New Dataset</h2>
        <form onSubmit={handleAnalyze}>
          <input
            type="file"
            accept=".csv,.json"
            onChange={handleFileChange}
            className="input-file"
            required
          />
          <button type="submit" className="btn" disabled={loading || !file}>
            {loading ? 'Executing Multi-Agent Workflow...' : 'Run Decision Audit Pipeline'}
          </button>
        </form>

        {error && (
          <div style={{ marginTop: '1rem', color: 'var(--critical)', fontWeight: 500 }}>
            Error: {error}
          </div>
        )}
      </section>

      {result && (
        <>
          <section className="metrics-grid">
            <article className="metric-card">
              <h3>Corporate Health Index</h3>
              <div className="metric-val">
                {result.consolidated_report.business_health_score !== undefined
                  ? `${result.consolidated_report.business_health_score.toFixed(1)}%`
                  : 'N/A'}
              </div>
            </article>

            <article className="metric-card">
              <h3>Pipeline Telemetry Duration</h3>
              <div className="metric-val" style={{ color: 'var(--violet)' }}>
                {result.metrics
                  ? `${result.metrics.reduce((acc: number, m: any) => acc + m.execution_time_ms, 0).toFixed(1)} ms`
                  : 'N/A'}
              </div>
            </article>

            <article className="metric-card">
              <h3>Findings Count</h3>
              <div className="metric-val" style={{ color: 'var(--safe)' }}>
                {result.consolidated_report.key_findings ? result.consolidated_report.key_findings.length : 0}
              </div>
            </article>
          </section>

          {result.consolidated_report.executive_summary && (
            <section className="glass-card">
              <h3 style={{ marginBottom: '0.75rem', color: 'var(--brand-ink)', fontWeight: 600 }}>C-Suite Executive Summary</h3>
              <p style={{ lineHeight: '1.65', fontSize: '1.05rem', color: 'var(--ink-soft)' }}>
                {result.consolidated_report.executive_summary}
              </p>
            </section>
          )}

          {result.consolidated_report.key_findings && result.consolidated_report.key_findings.length > 0 && (
            <section className="glass-card">
              <h3 style={{ marginBottom: '1rem', fontWeight: 600 }}>Key Findings & Quality Warnings</h3>
              <table className="tbl">
                <thead>
                  <tr>
                    <th>Finding / Title</th>
                    <th>Analytical Evidence</th>
                    <th>Business Impact</th>
                  </tr>
                </thead>
                <tbody>
                  {result.consolidated_report.key_findings.map((f: any, idx: number) => (
                    <tr key={idx}>
                      <td style={{ fontWeight: 600 }}>{f.title}</td>
                      <td><code>{f.evidence || 'N/A'}</code></td>
                      <td>{f.business_impact}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}

          {result.consolidated_report.strategic_recommendations && result.consolidated_report.strategic_recommendations.length > 0 && (
            <section className="glass-card">
              <h3 style={{ marginBottom: '1rem', fontWeight: 600 }}>Prioritized Strategic Recommendations</h3>
              <table className="tbl">
                <thead>
                  <tr>
                    <th>Recommendation</th>
                    <th>Priority</th>
                    <th>Est. ROI</th>
                    <th>Timeline</th>
                    <th>Owner</th>
                  </tr>
                </thead>
                <tbody>
                  {result.consolidated_report.strategic_recommendations.map((r: any, idx: number) => (
                    <tr key={idx}>
                      <td style={{ fontWeight: 600 }}>{r.title}</td>
                      <td>
                        <span className={`badge badge-${r.priority.toLowerCase()}`}>
                          {r.priority}
                        </span>
                      </td>
                      <td style={{ color: 'var(--safe)', fontWeight: 700 }}>{r.estimated_roi.toFixed(0)}%</td>
                      <td>{r.timeline}</td>
                      <td>{r.owner}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </section>
          )}

          {result.metrics && (
            <section className="glass-card">
              <h3 style={{ marginBottom: '1rem', fontWeight: 600 }}>Agent Execution Timings</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {result.metrics.map((m: any, idx: number) => (
                  <div key={idx} style={{ display: 'flex', justifyContent: 'space-between', paddingBottom: '0.6rem', borderBottom: '1px solid var(--border)' }}>
                    <span style={{ fontWeight: 600 }}>{m.agent_name}</span>
                    <span style={{ color: 'var(--violet)', fontWeight: 600 }}>{m.execution_time_ms.toFixed(3)} ms ({m.status})</span>
                  </div>
                ))}
              </div>
            </section>
          )}
        </>
      )}
    </main>
  );
}
