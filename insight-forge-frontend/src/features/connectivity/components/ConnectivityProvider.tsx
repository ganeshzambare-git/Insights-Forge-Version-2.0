'use client';

import React, { createContext, useContext, useEffect, useRef } from 'react';
import {
  useIsOnline,
  useIsLocked,
  useReconnectAttempt,
  useIsReconnecting,
  useMaxAttemptsReached,
  useConnectivityActions,
} from '../store/connectivityStore';
import { ConnectionOverlay } from './ConnectionOverlay';

const ConnectivityContext = createContext<null>(null);

export const ConnectivityProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const isOnline = useIsOnline();
  const locked = useIsLocked();
  const attempt = useReconnectAttempt();
  const isReconnecting = useIsReconnecting();
  const maxAttemptsReached = useMaxAttemptsReached();
  const { setOnline, setOffline, incrementAttempt, setReconnecting, setMaxAttemptsReached, resetStore } = useConnectivityActions();

  const retryTimerRef = useRef<any>(null);
  const heartbeatIntervalRef = useRef<any>(null);

  const checkLiveness = async (): Promise<boolean> => {
    const apiUrl = process.env.NEXT_PUBLIC_API_URL || '';
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 4000); // 4s timeout boundary

      const res = await fetch(`${apiUrl}/api/v1/health`, {
        method: 'GET',
        signal: controller.signal,
        cache: 'no-store',
      });
      clearTimeout(timeoutId);
      
      if (res.ok) {
        return true;
      }
      return false;
    } catch {
      return false;
    }
  };

  const executeReconnectSequence = async () => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
    }
    
    setOffline();
    setReconnecting(true);

    const backoffSchedule = [1000, 2000, 4000, 8000, 16000];

    const runAttempt = async (attemptIndex: number) => {
      if (attemptIndex >= backoffSchedule.length) {
        setReconnecting(false);
        setMaxAttemptsReached(true);
        return;
      }

      incrementAttempt();
      
      const success = await checkLiveness();
      if (success) {
        setOnline();
        startHeartbeat();
      } else {
        const nextDelay = backoffSchedule[attemptIndex];
        retryTimerRef.current = setTimeout(() => {
          runAttempt(attemptIndex + 1);
        }, nextDelay);
      }
    };

    runAttempt(0);
  };

  const startHeartbeat = () => {
    if (heartbeatIntervalRef.current) {
      clearInterval(heartbeatIntervalRef.current);
    }

    heartbeatIntervalRef.current = setInterval(async () => {
      const ok = await checkLiveness();
      if (!ok) {
        executeReconnectSequence();
      }
    }, 10000);
  };

  const handleManualRetry = async () => {
    setReconnecting(true);
    const ok = await checkLiveness();
    if (ok) {
      setOnline();
      startHeartbeat();
    } else {
      setReconnecting(false);
    }
  };

  useEffect(() => {
    startHeartbeat();
    return () => {
      if (heartbeatIntervalRef.current) clearInterval(heartbeatIntervalRef.current);
      if (retryTimerRef.current) clearTimeout(retryTimerRef.current);
    };
  }, []);

  return (
    <ConnectivityContext.Provider value={null}>
      <div style={{ position: 'relative', minHeight: '100vh' }}>
        <div style={{ 
          opacity: locked ? 0.4 : 1, 
          pointerEvents: locked ? 'none' : 'auto',
          transition: 'opacity 0.3s ease'
        }}>
          {children}
        </div>

        {locked && (
          <ConnectionOverlay 
            attempt={attempt} 
            isReconnecting={isReconnecting} 
            maxAttemptsReached={maxAttemptsReached} 
            onRetry={handleManualRetry}
          />
        )}
      </div>
    </ConnectivityContext.Provider>
  );
};

export const useConnectivity = () => useContext(ConnectivityContext);
