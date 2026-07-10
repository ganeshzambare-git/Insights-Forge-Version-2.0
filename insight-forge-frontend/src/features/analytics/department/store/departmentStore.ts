import { create } from 'zustand';

export interface StudentRecord {
  id: string;
  name: string;
  department: string;
  term_gpa: number;
  risk_level: 'High' | 'Medium' | 'Low';
  term_credits: number;
  status: string;
}

interface DepartmentState {
  scope: string;
  records: StudentRecord[];
  loading: boolean;
  error: string | null;
  timeoutOccurred: boolean;
  actions: {
    setScope: (scope: string) => void;
    fetchDepartmentRecords: (scope: string) => Promise<void>;
  };
}

const useDepartmentStoreInternal = create<DepartmentState>((set) => ({
  scope: 'Engineering',
  records: [],
  loading: false,
  error: null,
  timeoutOccurred: false,
  actions: {
    setScope: (scope) => set({ scope }),
    fetchDepartmentRecords: async (scope) => {
      set({ loading: true, error: null, timeoutOccurred: false, scope });
      
      const controller = new AbortController();
      const timeoutId = setTimeout(() => {
        controller.abort();
      }, 2500);

      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
        const token = typeof window !== 'undefined' ? sessionStorage.getItem('__access_token') : '';

        // Inject delay query string parameter if mock TimeoutTrigger is triggered
        const queryParam = scope === 'TimeoutTrigger' ? 'TimeoutTrigger&delay=6' : scope;

        const res = await fetch(`${apiUrl}/api/v1/analytics/department-records?scope=${queryParam}`, {
          method: 'GET',
          signal: controller.signal,
          headers: token ? { 
            'Authorization': `Bearer ${token}`,
            'Cache-Control': 'no-store'
          } : { 'Cache-Control': 'no-store' }
        });

        clearTimeout(timeoutId);

        if (!res.ok) {
          throw new Error(`Server returned error code: ${res.status}`);
        }

        const data = await res.json();
        if (data.success) {
          set({
            records: data.data.records || [],
            loading: false,
          });
        } else {
          throw new Error(data.message || 'Verification failure.');
        }
      } catch (err: any) {
        clearTimeout(timeoutId);
        if (err.name === 'AbortError') {
          set({
            timeoutOccurred: true,
            records: [],
            loading: false,
          });
        } else {
          set({
            error: err.message || 'Interrupted connection to database gateways.',
            loading: false,
          });
        }
      }
    },
  },
}));

export const useDepartmentScope = () => useDepartmentStoreInternal((s) => s.scope);
export const useDepartmentRecords = () => useDepartmentStoreInternal((s) => s.records);
export const useDepartmentLoading = () => useDepartmentStoreInternal((s) => s.loading);
export const useDepartmentError = () => useDepartmentStoreInternal((s) => s.error);
export const useDepartmentTimeoutOccurred = () => useDepartmentStoreInternal((s) => s.timeoutOccurred);
export const useDepartmentActions = () => useDepartmentStoreInternal((s) => s.actions);
