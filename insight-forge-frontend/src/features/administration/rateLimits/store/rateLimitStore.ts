import { create } from 'zustand';
import { apiClient } from '../../../../core/api/apiClient';

export interface RateLimitLog {
  id: string;
  tenant_name: string;
  timestamp: string;
  request_rate: number;
  limit_threshold: number;
  is_violation: boolean;
}

interface RateLimitState {
  logs: RateLimitLog[];
  loading: boolean;
  error: string | null;
  timeRangeMin: number; // minutes slider filter (0 to 60)
  tenantFilter: string; // 'All' or specific tenant name
  actions: {
    fetchRateLimitLogs: () => Promise<void>;
    setTimeRangeMin: (minutes: number) => void;
    setTenantFilter: (tenant: string) => void;
  };
}

const useRateLimitStoreInternal = create<RateLimitState>((set) => ({
  logs: [],
  loading: false,
  error: null,
  timeRangeMin: 60,
  tenantFilter: 'All',
  actions: {
    fetchRateLimitLogs: async () => {
      set({ loading: true, error: null });
      try {
        const res: any = await apiClient.get('/admin/rate-limit-logs');
        set({
          logs: res.logs || [],
          loading: false,
        });
      } catch (err: any) {
        set({
          error: err.message || 'Failed to fetch rate limit logs from endpoints.',
          loading: false,
        });
      }
    },
    setTimeRangeMin: (timeRangeMin) => set({ timeRangeMin }),
    setTenantFilter: (tenantFilter) => set({ tenantFilter }),
  },
}));

export const useRateLimitLogs = () => useRateLimitStoreInternal((s) => s.logs);
export const useRateLimitLoading = () => useRateLimitStoreInternal((s) => s.loading);
export const useRateLimitError = () => useRateLimitStoreInternal((s) => s.error);
export const useRateLimitTimeRange = () => useRateLimitStoreInternal((s) => s.timeRangeMin);
export const useRateLimitTenantFilter = () => useRateLimitStoreInternal((s) => s.tenantFilter);
export const useRateLimitActions = () => useRateLimitStoreInternal((s) => s.actions);
