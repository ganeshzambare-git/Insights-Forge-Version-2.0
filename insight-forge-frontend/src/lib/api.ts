// Insight Forge API client — talks to the FastAPI backend's /api/v1 surface.
// Every backend response uses the envelope { success, message, data, errors }.

export const API_BASE =
  process.env.NEXT_PUBLIC_API_URL?.replace(/\/$/, '') || 'http://localhost:8000';

const TOKEN_KEY = 'if_access_token';
const USER_KEY = 'if_user';

export type SessionUser = {
  user_id: string;
  tenant_id: string;
  corporate_email: string;
  assigned_role: string;
};

export type AuthResult = {
  access_token: string;
  refresh_token: string;
  token_type: string;
  expires_in: number;
  user: SessionUser;
  tenant?: { tenant_id: string; tenant_slug: string; tenant_name: string };
};

export type Dataset = {
  dataset_id: string;
  tenant_id: string;
  dataset_name: string;
  original_filename: string;
  source_format: string;
  processing_status: string;
  row_count: number | null;
  size_bytes: number | null;
  health_score: number | null;
  created_at: string;
};

export type IngestResult = {
  dataset_id: string;
  dataset_name: string;
  row_count: number;
  column_count: number;
  columns: string[];
  processing_status: string;
  health_score: number | null;
};

export type DatasetRecord = { row_index: number; payload: Record<string, unknown> };

export type PipelineReport = {
  success: boolean;
  metrics: { agent_name: string; execution_time_ms: number; status: string }[];
  warnings: string[];
  consolidated_report: ConsolidatedReport;
};

export type ConsolidatedReport = {
  estimated_industry?: string;
  estimated_business_domain?: string;
  detected_entities?: string[];
  columns_understanding?: Record<
    string,
    { business_meaning: string; classification: string; confidence: number }
  >;
  discovered_kpis?: {
    kpi_name: string;
    aggregation_type: string;
    required_columns: string[];
    business_purpose?: string;
  }[];
  business_insights?: { title: string; description?: string }[];
  detected_anomalies?: { title: string; description?: string }[];
  strategic_recommendations?: {
    title: string;
    priority?: string;
    estimated_roi?: number;
    timeline?: string;
    owner?: string;
  }[];
  business_health_score?: number;
  executive_summary?: string;
};

export class ApiError extends Error {
  status: number;
  constructor(message: string, status: number) {
    super(message);
    this.status = status;
  }
}

/* ---------------- session storage ---------------- */

export function getToken(): string | null {
  if (typeof window === 'undefined') return null;
  return window.localStorage.getItem(TOKEN_KEY);
}

export function getUser(): SessionUser | null {
  if (typeof window === 'undefined') return null;
  const raw = window.localStorage.getItem(USER_KEY);
  return raw ? (JSON.parse(raw) as SessionUser) : null;
}

export function setSession(result: AuthResult): void {
  window.localStorage.setItem(TOKEN_KEY, result.access_token);
  window.localStorage.setItem(USER_KEY, JSON.stringify(result.user));
}

export function clearSession(): void {
  window.localStorage.removeItem(TOKEN_KEY);
  window.localStorage.removeItem(USER_KEY);
}

/* ---------------- core request ---------------- */

async function request<T>(
  path: string,
  options: { method?: string; body?: unknown; auth?: boolean; form?: FormData } = {},
): Promise<T> {
  const headers: Record<string, string> = {};
  if (options.auth) {
    const token = getToken();
    if (token) headers['Authorization'] = `Bearer ${token}`;
  }

  let body: BodyInit | undefined;
  if (options.form) {
    body = options.form; // browser sets multipart boundary
  } else if (options.body !== undefined) {
    headers['Content-Type'] = 'application/json';
    body = JSON.stringify(options.body);
  }

  let res: Response;
  try {
    res = await fetch(`${API_BASE}${path}`, {
      method: options.method || 'GET',
      headers,
      body,
    });
  } catch {
    throw new ApiError(
      'Could not reach the server. Is the backend running on ' + API_BASE + '?',
      0,
    );
  }

  let json: { success?: boolean; message?: string; data?: T; errors?: unknown } = {};
  try {
    json = await res.json();
  } catch {
    // fall through to status-based error
  }

  if (!res.ok || json.success === false) {
    throw new ApiError(json.message || `Request failed (${res.status})`, res.status);
  }
  return json.data as T;
}

/* ---------------- endpoints ---------------- */

export const api = {
  signup: (organization_name: string, corporate_email: string, password: string) =>
    request<AuthResult>('/api/v1/auth/signup', {
      method: 'POST',
      body: { organization_name, corporate_email, password },
    }),

  login: (corporate_email: string, password: string) =>
    request<AuthResult>('/api/v1/auth/login', {
      method: 'POST',
      body: { corporate_email, password },
    }),

  me: () => request<SessionUser>('/api/v1/auth/me', { auth: true }),

  ingest: (file: File) => {
    const form = new FormData();
    form.append('file', file);
    return request<IngestResult>('/api/v1/ingestion', {
      method: 'POST',
      auth: true,
      form,
    });
  },

  listDatasets: () => request<Dataset[]>('/api/v1/datasets', { auth: true }),

  getRecords: (id: string, limit = 200) =>
    request<DatasetRecord[]>(`/api/v1/datasets/${id}/records?limit=${limit}`, {
      auth: true,
    }),

  getReport: (id: string) =>
    request<PipelineReport>(`/api/v1/reports/${id}`, { auth: true }),
};
