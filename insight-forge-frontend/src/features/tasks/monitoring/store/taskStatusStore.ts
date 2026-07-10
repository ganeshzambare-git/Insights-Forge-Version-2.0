import { create } from 'zustand';

// ── Types ────────────────────────────────────────────────────
export type TaskStatus = 'Pending' | 'Running' | 'Completed' | 'Failed';

export interface TaskTimelineEvent {
  event: string;
  timestamp: string;
}

export interface TaskErrorDetail {
  code: string;
  message: string;
  recovery: string;
}

export interface TaskResultDetail {
  download_url?: string;
  record_count?: number;
  file_size_kb?: number;
}

export interface TaskRecord {
  task_id: string;
  task_type: string;
  status: TaskStatus;
  progress_pct: number;
  started_at: string | null;
  completed_at: string | null;
  timeline: TaskTimelineEvent[];
  result: TaskResultDetail | null;
  error: TaskErrorDetail | null;
}

export interface TaskSummary {
  task_id: string;
  task_type: string;
  status: TaskStatus;
  progress_pct: number;
  started_at: string | null;
}

interface TaskStatusState {
  taskList: TaskSummary[];
  selectedTask: TaskRecord | null;
  isLoadingList: boolean;
  isLoadingTask: boolean;
  pollingTaskId: string | null;
  error: string | null;
  actions: {
    fetchTaskList: () => Promise<void>;
    fetchTaskStatus: (taskId: string) => Promise<void>;
    startPolling: (taskId: string) => void;
    stopPolling: () => void;
    selectTask: (taskId: string) => void;
  };
}

let _pollInterval: ReturnType<typeof setInterval> | null = null;

const useTaskStatusStoreInternal = create<TaskStatusState>((set, get) => ({
  taskList: [],
  selectedTask: null,
  isLoadingList: false,
  isLoadingTask: false,
  pollingTaskId: null,
  error: null,
  actions: {
    fetchTaskList: async () => {
      set({ isLoadingList: true, error: null });
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
        const token = typeof window !== 'undefined' ? sessionStorage.getItem('__access_token') : '';
        const res = await fetch(`${apiUrl}/api/v1/tasks/list`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        if (!res.ok) throw new Error(`Request failed: ${res.status}`);
        const json = await res.json();
        set({ taskList: json.data.tasks ?? [], isLoadingList: false });
      } catch (err: any) {
        set({ error: err.message ?? 'Failed to load task list.', isLoadingList: false });
      }
    },

    fetchTaskStatus: async (taskId) => {
      set({ isLoadingTask: true, error: null });
      try {
        const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
        const token = typeof window !== 'undefined' ? sessionStorage.getItem('__access_token') : '';
        const res = await fetch(`${apiUrl}/api/v1/tasks/status/${taskId}`, {
          headers: token ? { Authorization: `Bearer ${token}` } : {},
        });
        if (!res.ok) throw new Error(`Request failed: ${res.status}`);
        const json = await res.json();
        const task: TaskRecord = json.data;
        set({ selectedTask: task, isLoadingTask: false });

        // Stop polling on terminal states
        if (task.status === 'Completed' || task.status === 'Failed') {
          get().actions.stopPolling();
        }
      } catch (err: any) {
        set({ error: err.message ?? 'Failed to fetch task status.', isLoadingTask: false });
      }
    },

    startPolling: (taskId) => {
      if (_pollInterval) clearInterval(_pollInterval);
      set({ pollingTaskId: taskId });
      get().actions.fetchTaskStatus(taskId);
      _pollInterval = setInterval(() => {
        const { pollingTaskId } = get();
        if (pollingTaskId) {
          get().actions.fetchTaskStatus(pollingTaskId);
        }
      }, 4000); // poll every 4 seconds
    },

    stopPolling: () => {
      if (_pollInterval) { clearInterval(_pollInterval); _pollInterval = null; }
      set({ pollingTaskId: null });
    },

    selectTask: (taskId) => {
      get().actions.startPolling(taskId);
    },
  },
}));

export const useTaskList = () => useTaskStatusStoreInternal((s) => s.taskList);
export const useSelectedTask = () => useTaskStatusStoreInternal((s) => s.selectedTask);
export const useTaskIsLoadingList = () => useTaskStatusStoreInternal((s) => s.isLoadingList);
export const useTaskIsLoadingTask = () => useTaskStatusStoreInternal((s) => s.isLoadingTask);
export const useTaskPollingId = () => useTaskStatusStoreInternal((s) => s.pollingTaskId);
export const useTaskError = () => useTaskStatusStoreInternal((s) => s.error);
export const useTaskActions = () => useTaskStatusStoreInternal((s) => s.actions);
