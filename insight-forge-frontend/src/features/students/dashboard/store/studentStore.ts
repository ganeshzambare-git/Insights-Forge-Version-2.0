import { create } from 'zustand';

export interface GradeRecord {
  subject: string;
  grade: string;
  score: number;
}

export interface AttendanceItem {
  date: string;
  status: string;
}

export interface StudyModule {
  name: string;
  status: string;
  duration: string;
}

export interface GpaHistoryPoint {
  label: string;
  val: number;
}

interface StudentState {
  selectedTerm: string;
  loading: boolean;
  error: string | null;
  gpa: number;
  attendanceRate: number;
  ledgerEmpty: boolean;
  records: GradeRecord[];
  attendanceHistory: AttendanceItem[];
  studyModules: StudyModule[];
  studentGpaHistory: GpaHistoryPoint[];
  cohortGpaHistory: GpaHistoryPoint[];
  actions: {
    setSelectedTerm: (term: string) => void;
    fetchStudentDashboardData: () => Promise<void>;
  };
}

const useStudentStoreInternal = create<StudentState>((set, get) => ({
  selectedTerm: 'Fall 2026',
  loading: false,
  error: null,
  gpa: 0.0,
  attendanceRate: 0,
  ledgerEmpty: false,
  records: [],
  attendanceHistory: [],
  studyModules: [],
  studentGpaHistory: [],
  cohortGpaHistory: [],
  actions: {
    setSelectedTerm: (selectedTerm) => {
      set({ selectedTerm });
      get().actions.fetchStudentDashboardData();
    },
    fetchStudentDashboardData: async () => {
      const { selectedTerm } = get();
      set({ loading: true, error: null });

      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
        const token = typeof window !== 'undefined' ? sessionStorage.getItem('__access_token') : '';

        const progressRes = await fetch(`${apiUrl}/api/v1/student/progress-summary?term=${encodeURIComponent(selectedTerm)}`, {
          method: 'GET',
          headers: token ? { 'Authorization': `Bearer ${token}` } : undefined
        });

        if (!progressRes.ok) {
          throw new Error(`Progress query failed. Status: ${progressRes.status}`);
        }
        const progressJson = await progressRes.json();

        const gradesRes = await fetch(`${apiUrl}/api/v1/student/normalized-grades?term=${encodeURIComponent(selectedTerm)}`, {
          method: 'GET',
          headers: token ? { 'Authorization': `Bearer ${token}` } : undefined
        });

        if (!gradesRes.ok) {
          throw new Error(`Grades query failed. Status: ${gradesRes.status}`);
        }
        const gradesJson = await gradesRes.json();

        if (progressJson.success && gradesJson.success) {
          set({
            gpa: progressJson.data.gpa || 0.0,
            attendanceRate: progressJson.data.attendance_rate || 0,
            ledgerEmpty: progressJson.data.ledger_empty || false,
            records: progressJson.data.records || [],
            attendanceHistory: progressJson.data.attendance_history || [],
            studyModules: progressJson.data.study_modules || [],
            studentGpaHistory: gradesJson.data.student_gpa_history || [],
            cohortGpaHistory: gradesJson.data.cohort_gpa_history || [],
            loading: false
          });
        } else {
          throw new Error(progressJson.message || gradesJson.message || 'Analytics query failure.');
        }
      } catch (err: any) {
        set({
          error: err.message || 'Failed connecting to student analytics gateway.',
          loading: false
        });
      }
    }
  }
}));

export const useStudentSelectedTerm = () => useStudentStoreInternal((s) => s.selectedTerm);
export const useStudentLoading = () => useStudentStoreInternal((s) => s.loading);
export const useStudentError = () => useStudentStoreInternal((s) => s.error);
export const useStudentGpa = () => useStudentStoreInternal((s) => s.gpa);
export const useStudentAttendanceRate = () => useStudentStoreInternal((s) => s.attendanceRate);
export const useStudentLedgerEmpty = () => useStudentStoreInternal((s) => s.ledgerEmpty);
export const useStudentRecords = () => useStudentStoreInternal((s) => s.records);
export const useStudentAttendanceHistory = () => useStudentStoreInternal((s) => s.attendanceHistory);
export const useStudentStudyModules = () => useStudentStoreInternal((s) => s.studyModules);
export const useStudentGpaHistory = () => useStudentStoreInternal((s) => s.studentGpaHistory);
export const useCohortGpaHistory = () => useStudentStoreInternal((s) => s.cohortGpaHistory);
export const useStudentActions = () => useStudentStoreInternal((s) => s.actions);
