import { create } from 'zustand';

interface ExportState {
  loading: boolean;
  error: string | null;
  exportStatus: 'idle' | 'exporting' | 'completed' | 'failed';
  progress: number;
  actions: {
    startExport: () => Promise<void>;
    resetExport: () => void;
  };
}

const useExportStoreInternal = create<ExportState>((set, get) => ({
  loading: false,
  error: null,
  exportStatus: 'idle',
  progress: 0,
  actions: {
    startExport: async () => {
      set({ loading: true, error: null, exportStatus: 'exporting', progress: 0 });
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
        const token = typeof window !== 'undefined' ? sessionStorage.getItem('__access_token') : '';

        const res = await fetch(`${apiUrl}/api/v1/analytics/export-audit-packet`, {
          method: 'POST',
          headers: {
            'Authorization': token ? `Bearer ${token}` : '',
            'Content-Type': 'application/json'
          }
        });

        if (!res.ok) {
          throw new Error(`Export request failed. Status: ${res.status}`);
        }

        const json = await res.json();
        if (json.success) {
          set({ loading: false });
          
          let currentProgress = 0;
          const intervalId = setInterval(() => {
            currentProgress += 25;
            set({ progress: currentProgress });
            if (currentProgress >= 100) {
              clearInterval(intervalId);
              set({ exportStatus: 'completed' });
            }
          }, 1000);
        } else {
          throw new Error(json.message || 'Export start failed.');
        }
      } catch (err: any) {
        set({
          error: err.message || 'Audit export core server error.',
          exportStatus: 'failed',
          loading: false
        });
      }
    },
    resetExport: () => {
      set({
        loading: false,
        error: null,
        exportStatus: 'idle',
        progress: 0
      });
    }
  }
}));

export const useExportLoading = () => useExportStoreInternal((s) => s.loading);
export const useExportError = () => useExportStoreInternal((s) => s.error);
export const useExportStatus = () => useExportStoreInternal((s) => s.exportStatus);
export const useExportProgress = () => useExportStoreInternal((s) => s.progress);
export const useExportActions = () => useExportStoreInternal((s) => s.actions);
