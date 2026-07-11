import { create } from 'zustand';

interface UploadState {
  loading: boolean;
  error: string | null;
  progress: number;
  qualityScore: number | null;
  datasetId: string | null;
  uploadStatus: 'idle' | 'validating' | 'uploading' | 'completed' | 'failed';
  validationLog: string[];
  xhr: XMLHttpRequest | null;
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
  datasetId: null,
  uploadStatus: 'idle',
  validationLog: [],
  xhr: null,
  actions: {
    setValidation: (score, logs) => set({ qualityScore: score, validationLog: logs, uploadStatus: 'idle' }),
    // Streams the whole file to the real ingestion endpoint in a single
    // multipart request. The backend stores the raw file and registers a
    // dataset (Pending) before handing off to the cleaning worker.
    startChunkedUpload: (file) => {
      return new Promise<void>((resolve) => {
        set({ uploadStatus: 'uploading', error: null, progress: 0, datasetId: null });

        const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
        const token = typeof window !== 'undefined' ? sessionStorage.getItem('__access_token') : '';
        const tenantId = typeof window !== 'undefined' ? sessionStorage.getItem('__tenant_context_id') : '';

        const formData = new FormData();
        formData.append('file', file, file.name);

        const xhr = new XMLHttpRequest();
        set({ xhr });
        xhr.open('POST', `${apiUrl}/api/v1/ingestion/upload`);
        if (token) xhr.setRequestHeader('Authorization', `Bearer ${token}`);
        if (tenantId) xhr.setRequestHeader('X-Tenant-ID', tenantId);

        // Real upload progress reported by the browser.
        xhr.upload.onprogress = (event) => {
          if (event.lengthComputable) {
            set({ progress: Math.round((event.loaded / event.total) * 100) });
          }
        };

        const fail = (message: string) => {
          set({ error: message, uploadStatus: 'failed', xhr: null });
          resolve();
        };

        xhr.onload = () => {
          let payload: any = null;
          try {
            payload = JSON.parse(xhr.responseText);
          } catch {
            payload = null;
          }

          if (xhr.status >= 200 && xhr.status < 300 && payload?.success) {
            set({
              progress: 100,
              uploadStatus: 'completed',
              datasetId: payload?.data?.dataset_id ?? null,
              xhr: null,
            });
            resolve();
            return;
          }

          const message =
            payload?.message ||
            payload?.errors?.[0]?.message ||
            `Upload failed. Server status: ${xhr.status}`;
          fail(message);
        };

        xhr.onerror = () => fail('Network interruption encountered.');
        xhr.onabort = () => {
          set({ error: 'Upload cancelled by user.', uploadStatus: 'idle', xhr: null });
          resolve();
        };

        xhr.send(formData);
      });
    },
    cancelUpload: () => {
      const { xhr } = get();
      if (xhr) {
        xhr.abort();
      }
    },
    resetUpload: () => {
      set({
        loading: false,
        error: null,
        progress: 0,
        qualityScore: null,
        datasetId: null,
        uploadStatus: 'idle',
        validationLog: [],
        xhr: null,
      });
    },
  },
}));

export const useUploadProgress = () => useUploadStoreInternal((s) => s.progress);
export const useUploadStatus = () => useUploadStoreInternal((s) => s.uploadStatus);
export const useUploadError = () => useUploadStoreInternal((s) => s.error);
export const useUploadQualityScore = () => useUploadStoreInternal((s) => s.qualityScore);
export const useUploadValidationLog = () => useUploadStoreInternal((s) => s.validationLog);
export const useUploadDatasetId = () => useUploadStoreInternal((s) => s.datasetId);
export const useUploadActions = () => useUploadStoreInternal((s) => s.actions);
