import { create } from 'zustand';

interface UploadState {
  loading: boolean;
  error: string | null;
  progress: number;
  qualityScore: number | null;
  uploadStatus: 'idle' | 'validating' | 'uploading' | 'completed' | 'failed';
  validationLog: string[];
  abortController: AbortController | null;
  actions: {
    setValidation: (score: number, logs: string[]) => void;
    startChunkedUpload: (file: File) => Promise<void>;
    cancelUpload: () => void;
    resetUpload: () => void;
  };
}

const useUploadStoreInternal = create<UploadState>((set, get) => ({
  loading: false,
  error: null,
  progress: 0,
  qualityScore: null,
  uploadStatus: 'idle',
  validationLog: [],
  abortController: null,
  actions: {
    setValidation: (score, logs) => set({ qualityScore: score, validationLog: logs, uploadStatus: 'idle' }),
    startChunkedUpload: async (file) => {
      const controller = new AbortController();
      set({ uploadStatus: 'uploading', error: null, progress: 0, abortController: controller });

      const CHUNK_SIZE = 1024 * 1024; // 1 MB chunk boundaries
      const totalChunks = Math.ceil(file.size / CHUNK_SIZE);
      const fileId = `ingest-${Date.now()}-${Math.random().toString(36).substring(2, 7)}`;

      try {
        for (let i = 0; i < totalChunks; i++) {
          if (controller.signal.aborted) {
            throw new Error('Upload cancelled by user.');
          }

          const start = i * CHUNK_SIZE;
          const end = Math.min(start + CHUNK_SIZE, file.size);
          const chunkBlob = file.slice(start, end);

          const formData = new FormData();
          formData.append('file_id', fileId);
          formData.append('chunk_index', i.toString());
          formData.append('total_chunks', totalChunks.toString());
          formData.append('file', chunkBlob, file.name);

          const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
          const token = typeof window !== 'undefined' ? sessionStorage.getItem('__access_token') : '';

          const res = await fetch(`${apiUrl}/api/v1/ingest/upload-telemetry`, {
            method: 'POST',
            body: formData,
            signal: controller.signal,
            headers: token ? { 'Authorization': `Bearer ${token}` } : undefined
          });

          if (!res.ok) {
            throw new Error(`Failed to transmit chunk ${i + 1}. Server status: ${res.status}`);
          }

          const data = await res.json();
          if (!data.success) {
            throw new Error(data.message || `Ingest rejection on chunk ${i + 1}.`);
          }

          const percentage = Math.round(((i + 1) / totalChunks) * 100);
          set({ progress: percentage });
        }

        set({ uploadStatus: 'completed', abortController: null });
      } catch (err: any) {
        if (err.name === 'AbortError' || err.message === 'Upload cancelled by user.') {
          set({ error: 'Upload cancelled by user.', uploadStatus: 'idle', abortController: null });
        } else {
          set({ error: err.message || 'Network interruption encountered.', uploadStatus: 'failed', abortController: null });
        }
      }
    },
    cancelUpload: () => {
      const { abortController } = get();
      if (abortController) {
        abortController.abort();
      }
    },
    resetUpload: () => {
      set({
        loading: false,
        error: null,
        progress: 0,
        qualityScore: null,
        uploadStatus: 'idle',
        validationLog: [],
        abortController: null,
      });
    },
  },
}));

export const useUploadProgress = () => useUploadStoreInternal((s) => s.progress);
export const useUploadStatus = () => useUploadStoreInternal((s) => s.uploadStatus);
export const useUploadError = () => useUploadStoreInternal((s) => s.error);
export const useUploadQualityScore = () => useUploadStoreInternal((s) => s.qualityScore);
export const useUploadValidationLog = () => useUploadStoreInternal((s) => s.validationLog);
export const useUploadActions = () => useUploadStoreInternal((s) => s.actions);
