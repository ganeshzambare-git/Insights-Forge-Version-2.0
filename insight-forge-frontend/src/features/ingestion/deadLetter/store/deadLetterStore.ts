import { create } from 'zustand';

export interface DeadLetterLog {
  payload_id: string;
  error_summary: string;
  timestamp: string;
  status: string;
}

interface DeadLetterState {
  logs: DeadLetterLog[];
  loading: boolean;
  error: string | null;
  actions: {
    fetchDeadLetterLogs: () => Promise<void>;
  };
}

const useDeadLetterStoreInternal = create<DeadLetterState>((set) => ({
  logs: [],
  loading: false,
  error: null,
  actions: {
    fetchDeadLetterLogs: async () => {
      set({ loading: true, error: null });
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
        const token = typeof window !== 'undefined' ? sessionStorage.getItem('__access_token') : '';

        const res = await fetch(`${apiUrl}/api/v1/ingest/dead-letter-logs`, {
          method: 'GET',
          headers: token ? { 'Authorization': `Bearer ${token}` } : undefined
        });

        if (!res.ok) {
          throw new Error(`Ingestion logs query failed. Status: ${res.status}`);
        }
        const json = await res.json();
        if (json.success) {
          set({ logs: json.data.logs || [], loading: false });
        } else {
          throw new Error(json.message || 'Failed retrieving dead-letter logs.');
        }
      } catch (err: any) {
        set({
          error: err.message || 'Failed connecting to dead-letter diagnostics gateway.',
          loading: false
        });
      }
    }
  }
}));

export const useDeadLetterLogs = () => useDeadLetterStoreInternal((s) => s.logs);
export const useDeadLetterLoading = () => useDeadLetterStoreInternal((s) => s.loading);
export const useDeadLetterError = () => useDeadLetterStoreInternal((s) => s.error);
export const useDeadLetterActions = () => useDeadLetterStoreInternal((s) => s.actions);
