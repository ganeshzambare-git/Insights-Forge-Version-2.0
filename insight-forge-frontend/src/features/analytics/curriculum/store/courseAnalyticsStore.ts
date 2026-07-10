import { create } from 'zustand';

// ── Types ───────────────────────────────────────────────────
export interface CourseEvaluationRecord {
  course_id: string;
  course_name: string;
  department: string;
  cohort_code: string;
  avg_score: number;
  pass_rate: number;
  enrollment: number;
  evaluations_submitted: number;
  kpi_status: 'Exceeding' | 'On Track' | 'At Risk' | 'Critical';
}

export interface CourseFilters {
  department: string;
  cohortCode: string;
}

interface CourseAnalyticsState {
  courses: CourseEvaluationRecord[];
  totalCourses: number;
  filters: CourseFilters;
  isLoading: boolean;
  error: string | null;
  actions: {
    fetchCourseEvaluation: () => Promise<void>;
    setFilter: (key: keyof CourseFilters, value: string) => void;
    clearFilters: () => void;
  };
}

const DEFAULT_FILTERS: CourseFilters = { department: '', cohortCode: '' };

const useCourseAnalyticsStoreInternal = create<CourseAnalyticsState>((set, get) => ({
  courses: [],
  totalCourses: 0,
  filters: DEFAULT_FILTERS,
  isLoading: false,
  error: null,
  actions: {
    fetchCourseEvaluation: async () => {
      set({ isLoading: true, error: null });
      try {
        const { filters } = get();
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
        const params = new URLSearchParams();
        if (filters.department) params.set('department', filters.department);
        if (filters.cohortCode) params.set('cohort_code', filters.cohortCode);

        const token = typeof window !== 'undefined' ? sessionStorage.getItem('__access_token') : '';
        const res = await fetch(
          `${apiUrl}/api/v1/analytics/courses/evaluation?${params.toString()}`,
          { headers: token ? { Authorization: `Bearer ${token}` } : {} }
        );

        if (!res.ok) throw new Error(`Request failed: ${res.status}`);
        const json = await res.json();

        set({
          courses: json.data.courses ?? [],
          totalCourses: json.data.total_courses ?? 0,
          isLoading: false,
        });
      } catch (err: any) {
        set({ error: err.message ?? 'Failed to load course evaluation data.', isLoading: false });
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

export const useCourseList = () => useCourseAnalyticsStoreInternal((s) => s.courses);
export const useTotalCourses = () => useCourseAnalyticsStoreInternal((s) => s.totalCourses);
export const useCourseFilters = () => useCourseAnalyticsStoreInternal((s) => s.filters);
export const useCourseIsLoading = () => useCourseAnalyticsStoreInternal((s) => s.isLoading);
export const useCourseError = () => useCourseAnalyticsStoreInternal((s) => s.error);
export const useCourseActions = () => useCourseAnalyticsStoreInternal((s) => s.actions);
