import { create } from 'zustand';

interface SessionTimeoutState {
  timeLeft: number;
  duration: number; // default: 900 (15 min)
  isWarning: boolean;
  isExpired: boolean;
  actions: {
    tick: () => void;
    resetTimer: () => void;
    setDuration: (seconds: number) => void;
  };
}

const useSessionTimeoutStoreInternal = create<SessionTimeoutState>((set, get) => ({
  timeLeft: 900,
  duration: 900,
  isWarning: false,
  isExpired: false,
  actions: {
    tick: () => {
      const { timeLeft, isExpired } = get();
      if (isExpired) return;
      if (timeLeft <= 1) {
        set({ timeLeft: 0, isExpired: true, isWarning: false });
      } else {
        const nextTime = timeLeft - 1;
        set({
          timeLeft: nextTime,
          isWarning: nextTime <= 60, // Warn during last 60 seconds
        });
      }
    },
    resetTimer: () => {
      const { duration } = get();
      set({ timeLeft: duration, isWarning: false, isExpired: false });
    },
    setDuration: (seconds) => {
      set({ duration: seconds, timeLeft: seconds, isWarning: false, isExpired: false });
    },
  },
}));

export const useTimeLeft = () => useSessionTimeoutStoreInternal((s) => s.timeLeft);
export const useIsWarning = () => useSessionTimeoutStoreInternal((s) => s.isWarning);
export const useIsExpired = () => useSessionTimeoutStoreInternal((s) => s.isExpired);
export const useSessionTimeoutActions = () => useSessionTimeoutStoreInternal((s) => s.actions);
