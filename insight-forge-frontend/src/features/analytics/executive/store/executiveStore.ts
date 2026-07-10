import { create } from 'zustand';
import { apiClient } from '../../../../core/api/apiClient';

export interface KPIOverview {
  total_students: number;
  critical_risk: number;
  active_interventions: number;
  completion_rate: number;
}

export interface DepartmentMetric {
  name: string;
  gpa: number;
  student_count: number;
  budget_allocated: number;
}

export interface ResourceAllocation {
  pyspark_cores_quota: number;
  pyspark_cores_active: number;
  software_licenses_total: number;
  software_licenses_active: number;
  gpu_clusters_active: number;
}

interface ExecutiveState {
  loading: boolean;
  error: string | null;
  kpis: KPIOverview | null;
  departments: DepartmentMetric[];
  resourceAllocation: ResourceAllocation | null;
  actions: {
    fetchExecutiveSummary: () => Promise<void>;
  };
}

const useExecutiveStoreInternal = create<ExecutiveState>((set) => ({
  loading: false,
  error: null,
  kpis: null,
  departments: [],
  resourceAllocation: null,
  actions: {
    fetchExecutiveSummary: async () => {
      set({ loading: true, error: null });
      try {
        const res: any = await apiClient.get('/analytics/executive-summary');
        set({
          kpis: res.kpis || null,
          departments: res.departments || [],
          resourceAllocation: res.resource_allocation || null,
          loading: false,
        });
      } catch (err: any) {
        set({
          error: err.message || 'Failed to retrieve executive canvas summaries.',
          loading: false,
        });
      }
    },
  },
}));

export const useExecutiveLoading = () => useExecutiveStoreInternal((s) => s.loading);
export const useExecutiveError = () => useExecutiveStoreInternal((s) => s.error);
export const useExecutiveKPIs = () => useExecutiveStoreInternal((s) => s.kpis);
export const useExecutiveDepartments = () => useExecutiveStoreInternal((s) => s.departments);
export const useExecutiveResourceAllocation = () => useExecutiveStoreInternal((s) => s.resourceAllocation);
export const useExecutiveActions = () => useExecutiveStoreInternal((s) => s.actions);
