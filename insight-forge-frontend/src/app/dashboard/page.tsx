'use client';

import { useCallback, useEffect, useState } from 'react';
import { useRouter } from 'next/navigation';
import { AppHeader } from '@/components/AppHeader';
import { UploadDropzone } from '@/components/UploadDropzone';
import { CountUp } from '@/components/CountUp';
import { BarChart } from '@/components/charts/BarChart';
import { DonutChart } from '@/components/charts/DonutChart';
import { Histogram } from '@/components/charts/Histogram';
import { MetricRanges } from '@/components/charts/MetricRanges';
import { LineChart } from '@/components/charts/LineChart';
import {
  api,
  getToken,
  getUser,
  ApiError,
  type Dataset,
  type DatasetRecord,
  type PipelineReport,
  type SessionUser,
} from '@/lib/api';
import {
  numericColumns,
  categoricalColumns,
  timestampColumns,
  meaningOf,
  distribution,
  histogram,
  metricRanges,
  avgByCategory,
  timeSeries,
  primaryMeasure,
  summarizeNumeric,
  summarizeSlices,
  summarizeGroups,
  recommendationBars,
  agentTimingBars,
} from '@/lib/derive';

export default function DashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<SessionUser | null>(null);
  const [ready, setReady] = useState(false);

  const [datasets, setDatasets] = useState<Dataset[]>([]);
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [report, setReport] = useState<PipelineReport | null>(null);
  const [records, setRecords] = useState<DatasetRecord[]>([]);

  const [uploading, setUploading] = useState(false);
  const [loadingReport, setLoadingReport] = useState(false);
  const [toast, setToast] = useState<string | null>(null);

  const loadDatasets = useCallback(async () => {
    const list = await api.listDatasets();
    setDatasets(list);
    return list;
  }, []);

  // Auth guard + initial load.
  useEffect(() => {
    if (!getToken()) {
      router.replace('/login');
      return;
    }
    setUser(getUser());
    (async () => {
      try {
        const list = await loadDatasets();
        if (list.length > 0) setSelectedId(list[0].dataset_id);
      } catch (err) {
        if (err instanceof ApiError && err.status === 401) {
          router.replace('/login');
          return;
        }
        setToast(err instanceof ApiError ? err.message : 'Could not load datasets.');
      } finally {
        setReady(true);
      }
    })();
  }, [router, loadDatasets]);

  // Load report + records for the selected dataset.
  useEffect(() => {
    if (!selectedId) {
      setReport(null);
      setRecords([]);
      return;
    }
    let cancelled = false;
    setLoadingReport(true);
    (async () => {
      try {
        const [rep, recs] = await Promise.all([
          api.getReport(selectedId),
          api.getRecords(selectedId, 300),
        ]);
        if (!cancelled) {
          setReport(rep);
          setRecords(recs);
        }
      } catch (err) {
        if (!cancelled) setToast(err instanceof ApiError ? err.message : 'Could not load the report.');
      } finally {
        if (!cancelled) setLoadingReport(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, [selectedId]);

  async function handleUpload(file: File) {
    setUploading(true);
    setToast(null);
    try {
      const result = await api.ingest(file);
      await loadDatasets();
      setSelectedId(result.dataset_id);
      setToast(`“${result.dataset_name}” ingested — ${result.row_count} rows.`);
    } catch (err) {
      setToast(err instanceof ApiError ? err.message : 'Upload failed.');
    } finally {
      setUploading(false);
    }
  }

  if (!ready) {
    return (
      <>
        <AppHeader user={null} />
        <main className="shell app-main">
          <SkeletonBlock />
        </main>
      </>
    );
  }

  return (
    <>
      <AppHeader user={user} />
      <main className="shell app-main" style={{ display: 'grid', gap: 20 }}>
        <div style={{ display: 'flex', alignItems: 'baseline', justifyContent: 'space-between', flexWrap: 'wrap', gap: 8 }}>
          <div>
            <h1 style={{ fontSize: 'var(--text-heading)' }}>Datasets</h1>
            <p style={{ color: 'var(--slate)', fontSize: 'var(--text-body-sm)', marginTop: 2 }}>
              Upload data, then read the analysis it produces.
            </p>
          </div>
        </div>

        {datasets.length === 0 ? (
          <EmptyState onFile={handleUpload} busy={uploading} />
        ) : (
          <div className="dash-layout">
            <aside className="dash-side">
              <UploadDropzone onFile={handleUpload} busy={uploading} compact />
              <DatasetList datasets={datasets} selectedId={selectedId} onSelect={setSelectedId} />
            </aside>

            <section style={{ minWidth: 0 }}>
              {loadingReport || !report ? (
                <SkeletonBlock />
              ) : (
                <ReportView
                  report={report}
                  records={records}
                  dataset={datasets.find((d) => d.dataset_id === selectedId) ?? null}
                />
              )}
            </section>
          </div>
        )}
      </main>

      {toast && <Toast message={toast} onClose={() => setToast(null)} />}
    </>
  );
}

/* ---------------- Report view ---------------- */

function ReportView({
  report,
  records,
  dataset,
}: {
  report: PipelineReport;
  records: DatasetRecord[];
  dataset: Dataset | null;
}) {
  const r = report.consolidated_report;
  const health = r.business_health_score ?? Number(dataset?.health_score ?? 0);
  const kpis = r.discovered_kpis ?? [];
  const insights = r.business_insights ?? [];
  const recs = r.strategic_recommendations ?? [];

  const numCols = numericColumns(r);
  const catCols = categoricalColumns(r);
  const dateCols = timestampColumns(r);
  const ranges = metricRanges(records, r);

  const measure = primaryMeasure(r);
  const measureLabel = measure ? meaningOf(r, measure) : '';

  // Group comparison (line): avg measure across the richest dimension.
  const dimChoices = catCols
    .map((c) => ({ c, n: distribution(records, c).length }))
    .filter((d) => d.n >= 2 && d.n <= 10)
    .sort((a, b) => b.n - a.n);
  const groupDim = dimChoices[0]?.c;
  const groupBars = measure && groupDim ? avgByCategory(records, measure, groupDim) : [];

  // Time trend (line): avg measure per month of the first date column.
  const trend = measure && dateCols[0] ? timeSeries(records, measure, dateCols[0]) : [];

  const recBars = recommendationBars(r);
  const timingBars = agentTimingBars(report.metrics);

  return (
    <div style={{ display: 'grid', gap: 28 }}>
      <div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10, flexWrap: 'wrap' }}>
          <h2 style={{ fontSize: 'var(--text-heading-sm)' }}>{dataset?.dataset_name ?? 'Report'}</h2>
          <span className="tag">{r.estimated_industry ?? 'Dataset'}</span>
          <span className="tag">{dataset?.processing_status ?? 'Ready'}</span>
        </div>
      </div>

      {/* Stat row */}
      <div className="stat-row">
        <StatTile label="Health score" value={<CountUp value={health} decimals={0} suffix="%" />} accent />
        <StatTile label="Rows analyzed" value={<CountUp value={dataset?.row_count ?? records.length} />} />
        <StatTile label="KPIs found" value={<CountUp value={kpis.length} />} />
        <StatTile label="Insights" value={<CountUp value={insights.length} />} />
        <StatTile label="Actions" value={<CountUp value={recs.length} />} />
      </div>

      {/* Executive summary */}
      {r.executive_summary && (
        <div>
          <div className="card">
            <h3 style={{ fontSize: 'var(--text-subheading)', marginBottom: 8 }}>Executive summary</h3>
            <p style={{ color: 'var(--graphite)', lineHeight: 1.6, maxWidth: '72ch' }}>{r.executive_summary}</p>
          </div>
        </div>
      )}

      {/* Best / worst / average across every metric */}
      {ranges.length > 0 && (
        <div className="card">
          <CardTitle title="Metric summary" sub="lowest · average · highest" />
          <div style={{ marginTop: 18 }}>
            <MetricRanges data={ranges} animateOnMount />
          </div>
          <p className="chart-caption">
            The blue dot marks the average; the bar spans the lowest and highest value recorded for
            each metric — a quick read on typical level and spread.
          </p>
        </div>
      )}

      {/* Trends & comparisons — line charts */}
      {(trend.length > 1 || groupBars.length > 1) && (
        <div className="dash-grid">
          {trend.length > 1 && (
            <div className="card">
              <CardTitle title={`${measureLabel} over time`} sub="monthly average" />
              <div style={{ marginTop: 18 }}>
                <LineChart data={trend} animateOnMount ariaLabel={`${measureLabel} trend over time`} />
              </div>
              <p className="chart-caption">
                Average {measureLabel.toLowerCase()} for each enrolment period, earliest to latest —
                shows whether it is trending up or down.
              </p>
            </div>
          )}

          {groupBars.length > 1 && groupDim && (
            <div className="card">
              <CardTitle title={`${measureLabel} by ${meaningOf(r, groupDim)}`} sub="group average" />
              <div style={{ marginTop: 18 }}>
                <LineChart
                  data={groupBars.map((b) => ({ label: b.label, value: b.value }))}
                  animateOnMount
                  ariaLabel={`Average ${measureLabel} by ${meaningOf(r, groupDim)}`}
                />
              </div>
              <p className="chart-caption">{summarizeGroups(groupBars, measureLabel)}</p>
            </div>
          )}
        </div>
      )}

      {/* Every field, charted */}
      <div>
        <h3 style={{ fontSize: 'var(--text-subheading)', margin: '4px 0 2px' }}>Field distributions</h3>
        <p style={{ color: 'var(--slate)', fontSize: 'var(--text-body-sm)', marginBottom: 18 }}>
          Every column in your dataset, charted in the format that fits it.
        </p>
        <div className="dash-grid">
          {numCols.map((col) => {
            const h = histogram(records, col);
            if (h.length === 0) return null;
            return (
              <div className="card" key={`num-${col}`}>
                <CardTitle title={meaningOf(r, col)} sub="value distribution" />
                <div style={{ marginTop: 18 }}>
                  <Histogram data={h} animateOnMount ariaLabel={`${meaningOf(r, col)} distribution`} />
                </div>
                <p className="chart-caption">{summarizeNumeric(records, col)}</p>
              </div>
            );
          })}
          {catCols.map((col) => {
            const slices = distribution(records, col);
            if (slices.length === 0) return null;
            return (
              <div className="card" key={`cat-${col}`}>
                <CardTitle title={meaningOf(r, col)} sub="category share" />
                <div style={{ marginTop: 14 }}>
                  {slices.length <= 5 ? (
                    <DonutChart
                      data={slices}
                      centerValue={String(records.length)}
                      centerLabel="rows"
                      animateOnMount
                      ariaLabel={`${meaningOf(r, col)} distribution`}
                    />
                  ) : (
                    <BarChart
                      data={slices.map((s) => ({ label: s.label, value: s.value }))}
                      animateOnMount
                      ariaLabel={`${meaningOf(r, col)} distribution`}
                    />
                  )}
                </div>
                <p className="chart-caption">{summarizeSlices(slices)}</p>
              </div>
            );
          })}
        </div>
      </div>

      {/* Recommendations / pipeline timings — full width */}
      <div className="card">
        {recBars.length > 0 ? (
          <>
            <CardTitle title="Recommendations" sub="by est. ROI" />
            <div style={{ marginTop: 16 }}>
              <BarChart data={recBars} unit="%" animateOnMount ariaLabel="Recommendations by estimated ROI" />
            </div>
            <p className="chart-caption">
              Actions the pipeline ranked highest by estimated return — the longest bar is the top priority.
            </p>
          </>
        ) : (
          <>
            <CardTitle title="Pipeline timings" sub="per agent" />
            <div style={{ marginTop: 16 }}>
              <BarChart data={timingBars} unit=" ms" animateOnMount ariaLabel="Agent execution timings" />
            </div>
            <p className="chart-caption">How long each analysis agent took to process this dataset.</p>
          </>
        )}
      </div>

      {/* Insights + recommendations */}
      <div className="dash-grid">
        {insights.length > 0 && (
          <div>
            <div className="card">
              <CardTitle title="Key findings" sub={`${insights.length}`} />
              <ul style={{ listStyle: 'none', margin: '12px 0 0', padding: 0, display: 'grid', gap: 12 }}>
                {insights.slice(0, 6).map((it, i) => (
                  <li key={i} style={{ display: 'grid', gap: 3 }}>
                    <span style={{ fontWeight: 500, fontSize: 'var(--text-body-sm)' }}>{it.title}</span>
                    {it.description && (
                      <span style={{ color: 'var(--slate)', fontSize: 'var(--text-body-sm)' }}>{it.description}</span>
                    )}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}

        {recs.length > 0 && (
          <div>
            <div className="card">
              <CardTitle title="Recommended actions" sub={`${recs.length}`} />
              <ul style={{ listStyle: 'none', margin: '12px 0 0', padding: 0, display: 'grid', gap: 12 }}>
                {recs.slice(0, 6).map((rec, i) => (
                  <li key={i} style={{ display: 'flex', justifyContent: 'space-between', gap: 12, alignItems: 'baseline' }}>
                    <span style={{ fontWeight: 500, fontSize: 'var(--text-body-sm)' }}>{rec.title}</span>
                    {rec.priority && <span className="tag">{rec.priority}</span>}
                  </li>
                ))}
              </ul>
            </div>
          </div>
        )}
      </div>

      {report.warnings.length > 0 && (
        <div>
          <details className="card" style={{ background: 'var(--white)' }}>
            <summary style={{ cursor: 'pointer', fontSize: 'var(--text-body-sm)', color: 'var(--slate)' }}>
              {report.warnings.length} finding(s) the pipeline rejected as unsupported
            </summary>
            <ul style={{ margin: '12px 0 0', paddingLeft: 18, color: 'var(--slate)', fontSize: 'var(--text-body-sm)', display: 'grid', gap: 6 }}>
              {report.warnings.slice(0, 8).map((w, i) => (
                <li key={i}>{w}</li>
              ))}
            </ul>
          </details>
        </div>
      )}
    </div>
  );
}

/* ---------------- small pieces ---------------- */

function StatTile({ label, value, accent }: { label: string; value: React.ReactNode; accent?: boolean }) {
  return (
    <div className="card" style={{ padding: 18 }}>
      <div style={{ fontSize: 'var(--text-caption)', color: 'var(--slate)', marginBottom: 6 }}>{label}</div>
      <div
        style={{
          fontFamily: 'var(--font-display)',
          fontWeight: 600,
          fontSize: 30,
          letterSpacing: '-0.02em',
          color: accent ? 'var(--action-blue-ink)' : 'var(--graphite)',
        }}
      >
        {value}
      </div>
    </div>
  );
}

function CardTitle({ title, sub }: { title: string; sub?: string }) {
  return (
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'baseline', gap: 12 }}>
      <span style={{ fontWeight: 500, fontSize: 'var(--text-body)', color: 'var(--graphite)' }}>{title}</span>
      {sub && <span style={{ fontSize: 'var(--text-caption)', color: 'var(--slate)' }}>{sub}</span>}
    </div>
  );
}

function DatasetList({
  datasets,
  selectedId,
  onSelect,
}: {
  datasets: Dataset[];
  selectedId: string | null;
  onSelect: (id: string) => void;
}) {
  return (
    <div className="card" style={{ padding: 8 }}>
      <ul style={{ listStyle: 'none', margin: 0, padding: 0, display: 'grid', gap: 2 }}>
        {datasets.map((d) => {
          const active = d.dataset_id === selectedId;
          return (
            <li key={d.dataset_id}>
              <button
                onClick={() => onSelect(d.dataset_id)}
                aria-current={active}
                style={{
                  width: '100%',
                  textAlign: 'left',
                  border: 'none',
                  cursor: 'pointer',
                  background: active ? 'var(--paper)' : 'transparent',
                  borderRadius: 8,
                  padding: '10px 12px',
                  display: 'grid',
                  gap: 2,
                  transition: 'background 0.15s ease',
                }}
              >
                <span style={{ fontWeight: 500, fontSize: 'var(--text-body-sm)', color: 'var(--graphite)', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
                  {d.dataset_name}
                </span>
                <span style={{ fontSize: 'var(--text-caption)', color: 'var(--slate)' }}>
                  {(d.row_count ?? 0).toLocaleString()} rows · {d.health_score != null ? `${Math.round(Number(d.health_score))}% health` : d.processing_status}
                </span>
              </button>
            </li>
          );
        })}
      </ul>
    </div>
  );
}

function EmptyState({ onFile, busy }: { onFile: (f: File) => void; busy: boolean }) {
  return (
    <div className="card" style={{ padding: 'clamp(24px, 5vw, 48px)', textAlign: 'center', display: 'grid', gap: 18, placeItems: 'center' }}>
      <div style={{ maxWidth: 440 }}>
        <h2 style={{ fontSize: 'var(--text-heading)', marginBottom: 10 }}>Analyze your first dataset</h2>
        <p style={{ color: 'var(--slate)' }}>
          Upload a CSV or JSON of student or academic data. The pipeline profiles it, computes real
          statistics, and returns KPIs, cohorts, and ranked actions.
        </p>
      </div>
      <div style={{ width: '100%', maxWidth: 520 }}>
        <UploadDropzone onFile={onFile} busy={busy} />
      </div>
    </div>
  );
}

function SkeletonBlock() {
  return (
    <div style={{ display: 'grid', gap: 16 }} aria-hidden="true">
      <div className="skl" style={{ height: 90 }} />
      <div className="skl" style={{ height: 220 }} />
      <div className="skl" style={{ height: 260 }} />
    </div>
  );
}

function Toast({ message, onClose }: { message: string; onClose: () => void }) {
  useEffect(() => {
    const t = setTimeout(onClose, 4200);
    return () => clearTimeout(t);
  }, [onClose]);
  return (
    <div
      role="status"
      style={{
        position: 'fixed',
        bottom: 20,
        left: '50%',
        transform: 'translateX(-50%)',
        zIndex: 70,
        background: 'var(--ink)',
        color: 'var(--white)',
        padding: '11px 16px',
        borderRadius: 'var(--r-pill)',
        fontSize: 'var(--text-body-sm)',
        boxShadow: 'var(--shadow-pop)',
        maxWidth: '90vw',
      }}
    >
      {message}
    </div>
  );
}
