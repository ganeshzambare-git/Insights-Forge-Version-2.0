import { create } from 'zustand';

// ── Types ───────────────────────────────────────────────────
export interface AttendanceTrendPoint {
  month: string;
  attendance_rate: number;
  cohort: string;
  semester: string;
}

export interface AttendanceSummaryMetrics {
  average_attendance_rate: number;
  peak_attendance_rate: number;
  trough_attendance_rate: number;
  total_months: number;
}

export interface AttendanceFilters {
  semester: string;
  cohortCode: string;
}

interface AttendanceState {
  trend: AttendanceTrendPoint[];
  summary: AttendanceSummaryMetrics | null;
  filters: AttendanceFilters;
  isLoading: boolean;
  error: string | null;
  actions: {
    fetchAttendanceSummary: () => Promise<void>;
    setFilter: (key: keyof AttendanceFilters, value: string) => void;
    clearFilters: () => void;
  };
}

const DEFAULT_FILTERS: AttendanceFilters = { semester: '', cohortCode: '' };

const useAttendanceStoreInternal = create<AttendanceState>((set, get) => ({
  trend: [],
  summary: null,
  filters: DEFAULT_FILTERS,
  isLoading: false,
  error: null,
  actions: {
    fetchAttendanceSummary: async () => {
      set({ isLoading: true, error: null });
      try {
        const { filters } = get();
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
        const params = new URLSearchParams();
        if (filters.semester) params.set('semester', filters.semester);
        if (filters.cohortCode) params.set('cohort_code', filters.cohortCode);

        const token = typeof window !== 'undefined' ? sessionStorage.getItem('__access_token') : '';
        const res = await fetch(
          `${apiUrl}/api/v1/analytics/attendance/summary?${params.toString()}`,
          { headers: token ? { Authorization: `Bearer ${token}` } : {} }
        );

        if (!res.ok) throw new Error(`Request failed: ${res.status}`);
        const json = await res.json();

        set({
          trend: json.data.trend ?? [],
          summary: json.data.summary ?? null,
          isLoading: false,
        });
      } catch (err: any) {
        set({ error: err.message ?? 'Failed to load attendance data.', isLoading: false });
      }
    },
    setFilter: (key, value) => {
      set((s) => ({ filters: { ...s.filters, [key]: value } }));
    },
    clearFilters: () => {
      set({ filters: DEFAULT_FILTERS });
    },
  },
}));

export const useAttendanceTrend = () => useAttendanceStoreInternal((s) => s.trend);
export const useAttendanceSummary = () => useAttendanceStoreInternal((s) => s.summary);
export const useAttendanceFilters = () => useAttendanceStoreInternal((s) => s.filters);
export const useAttendanceIsLoading = () => useAttendanceStoreInternal((s) => s.isLoading);
export const useAttendanceError = () => useAttendanceStoreInternal((s) => s.error);
export const useAttendanceActions = () => useAttendanceStoreInternal((s) => s.actions);
