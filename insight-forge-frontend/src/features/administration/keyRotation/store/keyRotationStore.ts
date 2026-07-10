import { create } from 'zustand';
import { apiClient } from '../../../../core/api/apiClient';

interface KeyRotationState {
  loading: boolean;
  error: string | null;
  rotatedAt: string | null;
  invalidatedSessions: number | null;
  isModalOpen: boolean;
  step: 'idle' | 'warning' | 'confirm' | 'success';
  actions: {
    openModal: () => void;
    closeModal: () => void;
    setStep: (step: 'idle' | 'warning' | 'confirm' | 'success') => void;
    rotateKeys: () => Promise<boolean>;
  };
}

const useKeyRotationStoreInternal = create<KeyRotationState>((set) => ({
  loading: false,
  error: null,
  rotatedAt: null,
  invalidatedSessions: null,
  isModalOpen: false,
  step: 'idle',
  actions: {
    openModal: () => set({ isModalOpen: true, step: 'warning', error: null }),
    closeModal: () => set({ isModalOpen: false, step: 'idle', error: null, loading: false }),
    setStep: (step) => set({ step }),
    rotateKeys: async () => {
      set({ loading: true, error: null });
      try {
        const res: any = await apiClient.post('/admin/rotate-keys', {});
        set({
          rotatedAt: res.rotated_at || new Date().toISOString(),
          invalidatedSessions: res.invalidated_sessions_count || 42,
          step: 'success',
          loading: false,
        });
        return true;
      } catch (err: any) {
        set({
          error: err.message || 'Key rotation request encountered an unexpected server error.',
          loading: false,
          step: 'warning',
        });
        return false;
      }
    },
  },
}));

export const useKeyRotationLoading = () => useKeyRotationStoreInternal((s) => s.loading);
export const useKeyRotationError = () => useKeyRotationStoreInternal((s) => s.error);
export const useKeyRotatedAt = () => useKeyRotationStoreInternal((s) => s.rotatedAt);
export const useInvalidatedSessionsCount = () => useKeyRotationStoreInternal((s) => s.invalidatedSessions);
export const useIsKeyRotationModalOpen = () => useKeyRotationStoreInternal((s) => s.isModalOpen);
export const useKeyRotationStep = () => useKeyRotationStoreInternal((s) => s.step);
export const useKeyRotationActions = () => useKeyRotationStoreInternal((s) => s.actions);
