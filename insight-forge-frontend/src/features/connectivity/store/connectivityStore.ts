import { create } from 'zustand';

interface ConnectivityState {
  isOnline: boolean;
  reconnectAttempt: number;
  isReconnecting: boolean;
  locked: boolean;
  maxAttemptsReached: boolean;
  actions: {
    setOnline: () => void;
    setOffline: () => void;
    incrementAttempt: () => void;
    setReconnecting: (reconnecting: boolean) => void;
    setLocked: (locked: boolean) => void;
    setMaxAttemptsReached: (reached: boolean) => void;
    resetStore: () => void;
  };
}

const useConnectivityStoreInternal = create<ConnectivityState>((set) => ({
  isOnline: true,
  reconnectAttempt: 0,
  isReconnecting: false,
  locked: false,
  maxAttemptsReached: false,
  actions: {
    setOnline: () => set({ 
      isOnline: true, 
      reconnectAttempt: 0, 
      isReconnecting: false, 
      locked: false, 
      maxAttemptsReached: false 
    }),
    setOffline: () => set({ 
      isOnline: false, 
      locked: true 
    }),
    incrementAttempt: () => set((state) => ({ 
      reconnectAttempt: state.reconnectAttempt + 1 
    })),
    setReconnecting: (isReconnecting) => set({ isReconnecting }),
    setLocked: (locked) => set({ locked }),
    setMaxAttemptsReached: (maxAttemptsReached) => set({ maxAttemptsReached, isReconnecting: false }),
    resetStore: () => set({
      isOnline: true,
      reconnectAttempt: 0,
      isReconnecting: false,
      locked: false,
      maxAttemptsReached: false,
    }),
  },
}));

export const useIsOnline = () => useConnectivityStoreInternal((s) => s.isOnline);
export const useReconnectAttempt = () => useConnectivityStoreInternal((s) => s.reconnectAttempt);
export const useIsReconnecting = () => useConnectivityStoreInternal((s) => s.isReconnecting);
export const useIsLocked = () => useConnectivityStoreInternal((s) => s.locked);
export const useMaxAttemptsReached = () => useConnectivityStoreInternal((s) => s.maxAttemptsReached);
export const useConnectivityActions = () => useConnectivityStoreInternal((s) => s.actions);
