export interface ApiResponseEnvelope<T> {
  success: boolean;
  message: string;
  data: T;
  meta?: Record<string, any>;
  errors?: any;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public message: string,
    public errors?: any
  ) {
    super(message);
    this.name = 'ApiError';
  }
}

// Private JWT token closure
let accessToken: string | null = null;

export const setAccessToken = (token: string | null) => {
  accessToken = token;
};

export const getAccessToken = () => {
  return accessToken;
};

const BASE_URL = process.env.NEXT_PUBLIC_API_URL 
  ? `${process.env.NEXT_PUBLIC_API_URL}/api/v1`
  : '/api/v1';

async function request<T>(
  endpoint: string,
  options: RequestInit = {},
  timeoutMs = 15000
): Promise<T> {
  const controller = new AbortController();
  const id = setTimeout(() => controller.abort(), timeoutMs);

  const headers = new Headers(options.headers);
  if (!headers.has('Content-Type') && !(options.body instanceof FormData)) {
    headers.set('Content-Type', 'application/json');
  }

  // Inject JWT if it exists in our private closure
  if (accessToken) {
    headers.set('Authorization', `Bearer ${accessToken}`);
  }

  // Auto-extract tenant ID from active workspace store state
  const activeTenantId = typeof window !== 'undefined' ? sessionStorage.getItem('__tenant_context_id') : null;
  if (activeTenantId) {
    headers.set('X-Tenant-ID', activeTenantId);
  }

  const config: RequestInit = {
    ...options,
    headers,
    signal: controller.signal,
  };

  try {
    const response = await fetch(`${BASE_URL}${endpoint}`, config);
    clearTimeout(id);

    if (response.status === 204) {
      return {} as T;
    }

    const payload: ApiResponseEnvelope<T> = await response.json();

    if (!response.ok) {
      throw new ApiError(
        response.status,
        payload.message || 'An unexpected server error occurred',
        payload.errors
      );
    }

    return payload.data;
  } catch (error: any) {
    clearTimeout(id);
    if (error.name === 'AbortError') {
      throw new ApiError(408, 'Network connection timed out.');
    }
    if (error instanceof ApiError) {
      throw error;
    }
    throw new ApiError(500, error.message || 'Network communication failure');
  }
}

export const apiClient = {
  get: <T>(url: string, opts?: RequestInit) => request<T>(url, { ...opts, method: 'GET' }),
  post: <T>(url: string, body: any, opts?: RequestInit) =>
    request<T>(url, { ...opts, method: 'POST', body: optionsBody(body) }),
  patch: <T>(url: string, body: any, opts?: RequestInit) =>
    request<T>(url, { ...opts, method: 'PATCH', body: optionsBody(body) }),
  delete: <T>(url: string, opts?: RequestInit) => request<T>(url, { ...opts, method: 'DELETE' }),
};

function optionsBody(body: any) {
  if (body instanceof FormData) {
    return body;
  }
  return JSON.stringify(body);
}
