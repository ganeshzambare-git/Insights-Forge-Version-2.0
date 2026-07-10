import { create } from 'zustand';

export interface StudentRosterItem {
  id: string;
  name: string;
  email: string;
  gpa: number;
  status: string;
  risk_level?: string;
}

interface RosterState {
  cohortId: string;
  searchQuery: string;
  records: StudentRosterItem[];
  loading: boolean;
  error: string | null;
  abortController: AbortController | null;
  actions: {
    setSearchQuery: (query: string) => void;
    fetchCohortRoster: (cohortId: string, search?: string) => Promise<void>;
  };
}

const useRosterStoreInternal = create<RosterState>((set, get) => ({
  cohortId: '',
  searchQuery: '',
  records: [],
  loading: false,
  error: null,
  abortController: null,
  actions: {
    setSearchQuery: (searchQuery) => set({ searchQuery }),
    fetchCohortRoster: async (cohortId, search = '') => {
      const { abortController } = get();
      if (abortController) {
        abortController.abort();
      }

      const controller = new AbortController();
      set({ loading: true, error: null, cohortId, abortController: controller });

      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
        const token = typeof window !== 'undefined' ? sessionStorage.getItem('__access_token') : '';

        const searchParam = search ? `?search=${encodeURIComponent(search)}` : '';
        const res = await fetch(`${apiUrl}/api/v1/cohorts/${cohortId}/roster${searchParam}`, {
          method: 'GET',
          signal: controller.signal,
          headers: token ? { 'Authorization': `Bearer ${token}` } : undefined
        });

        if (!res.ok) {
          throw new Error(`Roster failure. Status: ${res.status}`);
        }

        const json = await res.json();
        if (json.success) {
          set({
            records: json.data.records || [],
            loading: false,
            abortController: null
          });
        } else {
          throw new Error(json.message || 'Failed to fetch roster.');
        }
      } catch (err: any) {
        if (err.name === 'AbortError') {
          return;
        }
        set({
          error: err.message || 'Failed to connect to roster gateway.',
          loading: false,
          abortController: null
        });
      }
    }
  }
}));

export const useRosterRecords = () => useRosterStoreInternal((s) => s.records);
export const useRosterLoading = () => useRosterStoreInternal((s) => s.loading);
export const useRosterError = () => useRosterStoreInternal((s) => s.error);
export const useRosterSearchQuery = () => useRosterStoreInternal((s) => s.searchQuery);
export const useRosterActions = () => useRosterStoreInternal((s) => s.actions);
