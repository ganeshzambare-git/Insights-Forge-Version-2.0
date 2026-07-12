// Turn real stored rows + the pipeline report into chart-ready data.
// No invented numbers — everything traces to the dataset or the backend report.

import type { ConsolidatedReport, DatasetRecord } from './api';
import type { Point } from '@/components/charts/LineChart';
import type { Bar } from '@/components/charts/BarChart';
import type { Slice } from '@/components/charts/DonutChart';

const SLICE_COLORS = ['#101010', '#0099ff', '#898989', '#6b7280', '#c8ccd2', '#242424'];

export function parseNumber(v: unknown): number | null {
  if (typeof v === 'number') return Number.isFinite(v) ? v : null;
  if (typeof v !== 'string') return null;
  const cleaned = v.replace(/[$,%\s]/g, '');
  if (cleaned === '') return null;
  const n = Number(cleaned);
  return Number.isFinite(n) ? n : null;
}

function classified(report: ConsolidatedReport, kinds: string[]): string[] {
  const cu = report.columns_understanding ?? {};
  return Object.entries(cu)
    .filter(([, meta]) => kinds.includes(meta.classification))
    .map(([col]) => col);
}

export function numericColumns(report: ConsolidatedReport): string[] {
  return classified(report, ['Measure', 'Financial']);
}

export function categoricalColumns(report: ConsolidatedReport): string[] {
  return classified(report, ['Categorical', 'Boolean', 'Geographic']);
}

export function timestampColumns(report: ConsolidatedReport): string[] {
  return classified(report, ['Timestamp']);
}

// Average of a measure per month of a date column, in chronological order.
export function timeSeries(records: DatasetRecord[], measureCol: string, dateCol: string): Point[] {
  const buckets = new Map<string, { total: number; n: number }>();
  for (const r of records) {
    const raw = String(r.payload[dateCol] ?? '');
    const month = raw.slice(0, 7); // YYYY-MM
    const v = parseNumber(r.payload[measureCol]);
    if (!/^\d{4}-\d{2}$/.test(month) || v === null) continue;
    const cur = buckets.get(month) ?? { total: 0, n: 0 };
    cur.total += v;
    cur.n += 1;
    buckets.set(month, cur);
  }
  return Array.from(buckets.entries())
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([label, { total, n }]) => ({ label, value: Math.round((total / n) * 100) / 100 }));
}

export function meaningOf(report: ConsolidatedReport, col: string): string {
  return report.columns_understanding?.[col]?.business_meaning ?? col;
}

// A numeric column across rows, in original order (capped for legibility).
export function lineFromColumn(records: DatasetRecord[], col: string, cap = 40): Point[] {
  const rows = records
    .map((r) => parseNumber(r.payload[col]))
    .filter((n): n is number => n !== null);
  const step = rows.length > cap ? Math.ceil(rows.length / cap) : 1;
  const out: Point[] = [];
  for (let i = 0; i < rows.length; i += step) {
    out.push({ label: String(i + 1), value: Math.round(rows[i] * 100) / 100 });
  }
  return out;
}

const STATUS_COLORS: Record<string, string> = {
  safe: '#101010',
  amber: '#898989',
  critical: '#0099ff',
  pass: '#101010',
  fail: '#0099ff',
  true: '#101010',
  false: '#898989',
};

// Category distribution of a column -> donut slices (top 6 by count).
export function distribution(records: DatasetRecord[], col: string): Slice[] {
  const counts = new Map<string, number>();
  for (const r of records) {
    const raw = r.payload[col];
    if (raw === null || raw === undefined || String(raw).trim() === '') continue;
    const key = String(raw);
    counts.set(key, (counts.get(key) ?? 0) + 1);
  }
  const sorted = Array.from(counts.entries()).sort((a, b) => b[1] - a[1]).slice(0, 6);
  return sorted.map(([label, value], i) => ({
    label,
    value,
    color: STATUS_COLORS[label.toLowerCase()] ?? SLICE_COLORS[i % SLICE_COLORS.length],
  }));
}

export type NumStats = { min: number; max: number; avg: number; count: number; values: number[] };

export function numericStats(records: DatasetRecord[], col: string): NumStats | null {
  const values = records
    .map((r) => parseNumber(r.payload[col]))
    .filter((n): n is number => n !== null);
  if (values.length === 0) return null;
  const min = Math.min(...values);
  const max = Math.max(...values);
  const avg = values.reduce((a, b) => a + b, 0) / values.length;
  return { min, max, avg, count: values.length, values };
}

function roundNice(n: number): number {
  return Math.abs(n) >= 100 ? Math.round(n) : Math.round(n * 100) / 100;
}

// Distribution of a numeric column into value buckets (for a histogram).
export function histogram(records: DatasetRecord[], col: string, bins = 8): Point[] {
  const s = numericStats(records, col);
  if (!s) return [];
  if (s.min === s.max) return [{ label: String(roundNice(s.min)), value: s.values.length }];
  const width = (s.max - s.min) / bins;
  const counts = new Array(bins).fill(0);
  for (const v of s.values) {
    let idx = Math.floor((v - s.min) / width);
    if (idx >= bins) idx = bins - 1;
    if (idx < 0) idx = 0;
    counts[idx] += 1;
  }
  return counts.map((c, i) => ({ label: String(roundNice(s.min + i * width)), value: c }));
}

export type MetricRange = { label: string; min: number; avg: number; max: number };

// Best / worst / average for every numeric column.
export function metricRanges(records: DatasetRecord[], report: ConsolidatedReport): MetricRange[] {
  return numericColumns(report)
    .map((col) => {
      const s = numericStats(records, col);
      if (!s) return null;
      return {
        label: meaningOf(report, col),
        min: roundNice(s.min),
        avg: roundNice(s.avg),
        max: roundNice(s.max),
      };
    })
    .filter((m): m is MetricRange => m !== null);
}

// Average of a measure grouped by a category -> bars (highest first).
export function avgByCategory(
  records: DatasetRecord[],
  measureCol: string,
  dimCol: string,
): Bar[] {
  const sums = new Map<string, { total: number; n: number }>();
  for (const r of records) {
    const cat = r.payload[dimCol];
    const val = parseNumber(r.payload[measureCol]);
    if (cat === null || cat === undefined || String(cat).trim() === '' || val === null) continue;
    const key = String(cat);
    const cur = sums.get(key) ?? { total: 0, n: 0 };
    cur.total += val;
    cur.n += 1;
    sums.set(key, cur);
  }
  return Array.from(sums.entries())
    .map(([label, { total, n }]) => ({ label, value: roundNice(total / n), sub: `${n}` }))
    .sort((a, b) => b.value - a.value)
    .slice(0, 8);
}

// Prefer a performance-style measure (gpa/score/rate/attendance) for comparisons.
export function primaryMeasure(report: ConsolidatedReport): string | undefined {
  const nums = numericColumns(report);
  const preferred = nums.find((c) => /gpa|grade|score|rate|attendance|mark|result|percent/i.test(c));
  return preferred ?? nums[0];
}

/* ---------- plain-language summaries shown under each chart ---------- */

export function summarizeNumeric(records: DatasetRecord[], col: string): string {
  const s = numericStats(records, col);
  if (!s) return '';
  return `Ranges ${roundNice(s.min).toLocaleString()}–${roundNice(s.max).toLocaleString()}, averaging ${roundNice(s.avg).toLocaleString()} across ${s.count} rows.`;
}

export function summarizeSlices(slices: Slice[], noun = 'rows'): string {
  if (slices.length === 0) return '';
  const total = slices.reduce((a, b) => a + b.value, 0) || 1;
  const top = slices[0];
  const pct = Math.round((top.value / total) * 100);
  return `${top.label} is the largest group — ${pct}% of ${total} ${noun}.`;
}

export function summarizeGroups(bars: Bar[], measureLabel: string): string {
  if (bars.length < 2) return '';
  const best = bars[0];
  const worst = bars[bars.length - 1];
  return `${best.label} has the highest average ${measureLabel.toLowerCase()} (${best.value.toLocaleString()}); ${worst.label} the lowest (${worst.value.toLocaleString()}).`;
}

export function recommendationBars(report: ConsolidatedReport): Bar[] {
  return (report.strategic_recommendations ?? [])
    .filter((r) => typeof r.estimated_roi === 'number')
    .slice(0, 6)
    .map((r) => ({
      label: r.title,
      value: Math.round(r.estimated_roi as number),
      sub: r.priority,
    }));
}

export function agentTimingBars(
  metrics: { agent_name: string; execution_time_ms: number; status: string }[],
): Bar[] {
  return metrics.map((m) => ({
    label: m.agent_name.replace(/-/g, ' '),
    value: Math.round(m.execution_time_ms * 100) / 100,
    sub: m.status,
  }));
}
