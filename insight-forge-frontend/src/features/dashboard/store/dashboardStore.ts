import { create } from 'zustand';
import { apiClient } from '../../../core/api/apiClient';

export interface ServerHealth {
  status: string;
  cpu_utilization: number;
  ram_utilization: number;
  db_connection_pool: number;
}

export interface PySparkLoad {
  load_percentage: number;
  queue_size: number;
  status: string;
}

export interface TrafficPoint {
  time: string;
  requests: number;
}

export interface InboundTraffic {
  current_rate_per_sec: number;
  total_requests_24h: number;
  history_24h: TrafficPoint[];
}

export interface ClusterMetrics {
  server_health: ServerHealth;
  pyspark_load: PySparkLoad;
  inbound_traffic: InboundTraffic;
  last_updated: string;
}

interface DashboardState {
  metrics: ClusterMetrics | null;
  loading: boolean;
  error: string | null;
  reloadCount: number;
  actions: {
    fetchMetrics: () => Promise<void>;
  };
}

const useDashboardStoreInternal = create<DashboardState>((set, get) => ({
  metrics: null,
  loading: false,
  error: null,
  reloadCount: 0,
  actions: {
    fetchMetrics: async () => {
      set({ loading: true, error: null });
      try {
        const metrics = await apiClient.get<ClusterMetrics>('/admin/cluster-metrics');
        set((state) => ({
          metrics,
          loading: false,
          reloadCount: state.reloadCount + 1,
        }));
      } catch (err: any) {
        set({
          error: err.message || 'Failed to fetch cluster metrics.',
          loading: false,
        });
      }
    },
  },
}));

export const useDashboardMetrics = () => useDashboardStoreInternal((s) => s.metrics);
export const useDashboardLoading = () => useDashboardStoreInternal((s) => s.loading);
export const useDashboardError = () => useDashboardStoreInternal((s) => s.error);
export const useDashboardReloadCount = () => useDashboardStoreInternal((s) => s.reloadCount);
export const useDashboardActions = () => useDashboardStoreInternal((s) => s.actions);
