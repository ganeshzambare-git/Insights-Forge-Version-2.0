import { create } from 'zustand';

export interface TrendPoint {
  step: string;
  gpa: number;
}

interface SimulationState {
  creditRatio: number;
  targetCohorts: number;
  classCapacity: number;
  isDirty: boolean;
  loading: boolean;
  error: string | null;
  successRate: number | null;
  averageGpa: number | null;
  trend: TrendPoint[];
  abortController: AbortController | null;
  actions: {
    setCreditRatio: (val: number) => void;
    setTargetCohorts: (val: number) => void;
    setClassCapacity: (val: number) => void;
    resetSandbox: () => void;
    runSimulation: () => Promise<void>;
  };
}

const DEFAULT_CREDIT_RATIO = 0.5;
const DEFAULT_TARGET_COHORTS = 10;
const DEFAULT_CLASS_CAPACITY = 30;

const useSimulationStoreInternal = create<SimulationState>((set, get) => ({
  creditRatio: DEFAULT_CREDIT_RATIO,
  targetCohorts: DEFAULT_TARGET_COHORTS,
  classCapacity: DEFAULT_CLASS_CAPACITY,
  isDirty: false,
  loading: false,
  error: null,
  successRate: null,
  averageGpa: null,
  trend: [],
  abortController: null,
  actions: {
    setCreditRatio: (creditRatio) => set({ creditRatio, isDirty: true }),
    setTargetCohorts: (targetCohorts) => set({ targetCohorts, isDirty: true }),
    setClassCapacity: (classCapacity) => set({ classCapacity, isDirty: true }),
    resetSandbox: () => {
      const { abortController } = get();
      if (abortController) {
        abortController.abort();
      }
      set({
        creditRatio: DEFAULT_CREDIT_RATIO,
        targetCohorts: DEFAULT_TARGET_COHORTS,
        classCapacity: DEFAULT_CLASS_CAPACITY,
        isDirty: false,
        loading: false,
        error: null,
        successRate: null,
        averageGpa: null,
        trend: [],
        abortController: null,
      });
    },
    runSimulation: async () => {
      const { creditRatio, targetCohorts, classCapacity, abortController } = get();
      
      if (abortController) {
        abortController.abort();
      }

      const controller = new AbortController();
      set({ loading: true, error: null, abortController: controller });

      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
        const token = typeof window !== 'undefined' ? sessionStorage.getItem('__access_token') : '';

        const res = await fetch(`${apiUrl}/api/v1/simulations/project-curves`, {
          method: 'POST',
          signal: controller.signal,
          headers: {
            'Content-Type': 'application/json',
            'Authorization': token ? `Bearer ${token}` : ''
          },
          body: JSON.stringify({
            credit_ratio: creditRatio,
            target_cohorts: targetCohorts,
            class_capacity: classCapacity
          })
        });

        if (!res.ok) {
          throw new Error(`Simulation failed. Status: ${res.status}`);
        }

        const json = await res.json();
        if (json.success) {
          set({
            successRate: json.data.success_rate,
            averageGpa: json.data.average_gpa,
            trend: json.data.trend || [],
            loading: false,
            abortController: null
          });
        } else {
          throw new Error(json.message || 'Simulation rejection.');
        }
      } catch (err: any) {
        if (err.name === 'AbortError') {
          return;
        }
        set({
          error: err.message || 'Calculation core interruption.',
          loading: false,
          abortController: null
        });
      }
    }
  }
}));

export const useCreditRatio = () => useSimulationStoreInternal((s) => s.creditRatio);
export const useTargetCohorts = () => useSimulationStoreInternal((s) => s.targetCohorts);
export const useClassCapacity = () => useSimulationStoreInternal((s) => s.classCapacity);
export const useIsSandboxDirty = () => useSimulationStoreInternal((s) => s.isDirty);
export const useSimulationLoading = () => useSimulationStoreInternal((s) => s.loading);
export const useSimulationError = () => useSimulationStoreInternal((s) => s.error);
export const useSimulationSuccessRate = () => useSimulationStoreInternal((s) => s.successRate);
export const useSimulationAverageGpa = () => useSimulationStoreInternal((s) => s.averageGpa);
export const useSimulationTrend = () => useSimulationStoreInternal((s) => s.trend);
export const useSimulationActions = () => useSimulationStoreInternal((s) => s.actions);
