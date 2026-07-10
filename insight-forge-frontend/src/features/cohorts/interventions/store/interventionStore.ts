import { create } from 'zustand';

interface InterventionState {
  loading: boolean;
  error: string | null;
  success: boolean;
  actions: {
    recordIntervention: (studentUserId: string, notes: string) => Promise<void>;
    resetIntervention: () => void;
  };
}

const useInterventionStoreInternal = create<InterventionState>((set) => ({
  loading: false,
  error: null,
  success: false,
  actions: {
    recordIntervention: async (studentUserId, notes) => {
      set({ loading: true, error: null, success: false });
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
        const token = typeof window !== 'undefined' ? sessionStorage.getItem('__access_token') : '';

        const res = await fetch(`${apiUrl}/api/v1/interventions/record`, {
          method: 'POST',
          headers: {
            'Authorization': token ? `Bearer ${token}` : '',
            'Content-Type': 'application/json'
          },
          body: JSON.stringify({
            tenant_id: 'tenant-001',
            student_user_id: studentUserId,
            intervention_notes: notes
          })
        });

        if (!res.ok) {
          throw new Error(`Intervention submission failed. Status: ${res.status}`);
        }

        const json = await res.json();
        if (json.success) {
          set({ success: true, loading: false });
        } else {
          throw new Error(json.message || 'Failed recording intervention.');
        }
      } catch (err: any) {
        set({
          error: err.message || 'Failed connecting to interventions persistent gateway.',
          loading: false,
          success: false
        });
      }
    },
    resetIntervention: () => {
      set({
        loading: false,
        error: null,
        success: false
      });
    }
  }
}));

export const useInterventionLoading = () => useInterventionStoreInternal((s) => s.loading);
export const useInterventionError = () => useInterventionStoreInternal((s) => s.error);
export const useInterventionSuccess = () => useInterventionStoreInternal((s) => s.success);
export const useInterventionActions = () => useInterventionStoreInternal((s) => s.actions);
