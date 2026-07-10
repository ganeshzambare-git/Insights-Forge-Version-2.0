import { create } from 'zustand';

// ── Types ────────────────────────────────────────────────────
export type AuditSeverity = 'INFO' | 'WARNING' | 'CRITICAL';

export interface AuditLogRecord {
  audit_id: string;
  event_type: string;
  severity: AuditSeverity;
  source_ip: string;
  session_token: string | null;
  user_email: string;
  timestamp: string;
  metadata: Record<string, unknown>;
}

export interface AuditFilters {
  eventType: string;
  severity: string;
  sourceIp: string;
}

interface SecurityAuditState {
  logs: AuditLogRecord[];
  totalRecords: number;
  filters: AuditFilters;
  selectedLog: AuditLogRecord | null;
  isLoading: boolean;
  isTracing: boolean;
  traceResult: string | null;
  error: string | null;
  actions: {
    fetchAuditLogs: () => Promise<void>;
    setFilter: (key: keyof AuditFilters, value: string) => void;
    clearFilters: () => void;
    selectLog: (log: AuditLogRecord | null) => void;
    initiateTrace: (auditId: string) => Promise<void>;
  };
}

const DEFAULT_FILTERS: AuditFilters = { eventType: '', severity: '', sourceIp: '' };

const useSecurityAuditStoreInternal = create<SecurityAuditState>((set, get) => ({
  logs: [],
  totalRecords: 0,
  filters: DEFAULT_FILTERS,
  selectedLog: null,
  isLoading: false,
  isTracing: false,
  traceResult: null,
  error: null,
  actions: {
    fetchAuditLogs: async () => {
      set({ isLoading: true, error: null });
      try {
        const { filters } = get();
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
        const params = new URLSearchParams();
        if (filters.eventType) params.set('event_type', filters.eventType);
        if (filters.severity) params.set('severity', filters.severity);
        if (filters.sourceIp) params.set('source_ip', filters.sourceIp);

        const token = typeof window !== 'undefined' ? sessionStorage.getItem('__access_token') : '';
        const res = await fetch(
          `${apiUrl}/api/v1/admin/security-audit-logs?${params.toString()}`,
          { headers: token ? { Authorization: `Bearer ${token}` } : {} }
        );
        if (!res.ok) throw new Error(`Request failed: ${res.status}`);
        const json = await res.json();
        set({ logs: json.data.logs ?? [], totalRecords: json.data.total_records ?? 0, isLoading: false });
      } catch (err: any) {
        set({ error: err.message ?? 'Failed to load audit logs.', isLoading: false });
      }
    },

    setFilter: (key, value) => {
      set((s) => ({ filters: { ...s.filters, [key]: value } }));
    },

    clearFilters: () => {
      set({ filters: DEFAULT_FILTERS });
    },

    selectLog: (log) => {
      set({ selectedLog: log, traceResult: null });
    },

    initiateTrace: async (auditId) => {
      set({ isTracing: true, traceResult: null });
      try {
        // Simulated trace — in production this would call a dedicated backend endpoint
        await new Promise((r) => setTimeout(r, 1500));
        set({
          traceResult: `Trace initiated for audit record ${auditId}. Backend forensic analysis queued at ${new Date().toISOString()}.`,
          isTracing: false,
        });
        // Refresh audit logs after trace
        get().actions.fetchAuditLogs();
      } catch (err: any) {
        set({ error: err.message ?? 'Trace initiation failed.', isTracing: false });
      }
    },
  },
}));

export const useAuditLogs = () => useSecurityAuditStoreInternal((s) => s.logs);
export const useAuditTotalRecords = () => useSecurityAuditStoreInternal((s) => s.totalRecords);
export const useAuditFilters = () => useSecurityAuditStoreInternal((s) => s.filters);
export const useSelectedLog = () => useSecurityAuditStoreInternal((s) => s.selectedLog);
export const useAuditIsLoading = () => useSecurityAuditStoreInternal((s) => s.isLoading);
export const useAuditIsTracing = () => useSecurityAuditStoreInternal((s) => s.isTracing);
export const useAuditTraceResult = () => useSecurityAuditStoreInternal((s) => s.traceResult);
export const useAuditError = () => useSecurityAuditStoreInternal((s) => s.error);
export const useAuditActions = () => useSecurityAuditStoreInternal((s) => s.actions);
