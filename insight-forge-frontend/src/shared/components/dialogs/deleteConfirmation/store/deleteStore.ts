import { create } from 'zustand';

export interface DependentEntity {
  type: string;
  id: string;
  summary: string;
}

interface DeleteState {
  isDeleting: boolean;
  isConfirming: boolean;
  conflictError: string | null;
  dependencies: DependentEntity[];
  actions: {
    startDeleteCohort: () => void;
    confirmDeleteCohort: (cohortId: string) => Promise<boolean>;
    cancelDelete: () => void;
  };
}

const useDeleteStoreInternal = create<DeleteState>((set) => ({
  isDeleting: false,
  isConfirming: false,
  conflictError: null,
  dependencies: [],
  actions: {
    startDeleteCohort: () => {
      set({ isConfirming: true, conflictError: null, dependencies: [] });
    },
    confirmDeleteCohort: async (cohortId) => {
      set({ isDeleting: true, conflictError: null, dependencies: [] });
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
        const token = typeof window !== 'undefined' ? sessionStorage.getItem('__access_token') : '';

        const res = await fetch(`${apiUrl}/api/v1/cohorts/${cohortId}`, {
          method: 'DELETE',
          headers: token ? { 'Authorization': `Bearer ${token}` } : undefined
        });

        if (res.status === 409) {
          const json = await res.json();
          set({
            conflictError: json.message || 'Referential integrity conflict occurred.',
            dependencies: json.data?.dependencies || [],
            isDeleting: false
          });
          return false;
        }

        if (!res.ok) {
          throw new Error(`Deletion failed with status: ${res.status}`);
        }

        set({ isDeleting: false, isConfirming: false });
        return true;
      } catch (err: any) {
        set({
          conflictError: err.message || 'An unexpected connection error occurred.',
          isDeleting: false
        });
        return false;
      }
    },
    cancelDelete: () => {
      set({ isDeleting: false, isConfirming: false, conflictError: null, dependencies: [] });
    }
  }
}));

export const useDeleteIsDeleting = () => useDeleteStoreInternal((s) => s.isDeleting);
export const useDeleteIsConfirming = () => useDeleteStoreInternal((s) => s.isConfirming);
export const useDeleteConflictError = () => useDeleteStoreInternal((s) => s.conflictError);
export const useDeleteDependencies = () => useDeleteStoreInternal((s) => s.dependencies);
export const useDeleteActions = () => useDeleteStoreInternal((s) => s.actions);
