'use client';

import React, { useEffect, useRef } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useIsAuthenticated, useAuthActions } from '../store/authStore';
import { useWorkspaceActions } from '../../workspace/store/workspaceStore';
import { useTimeLeft, useIsExpired, useSessionTimeoutActions } from '../store/sessionTimeoutStore';
import { SessionTimeoutOverlay } from './SessionTimeoutOverlay';

export const SessionLifecycleProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const router = useRouter();
  const searchParams = useSearchParams();
  const isAuthenticated = useIsAuthenticated();
  const { logout } = useAuthActions();
  const { resetWorkspace } = useWorkspaceActions();
  const isExpired = useIsExpired();
  const { tick, setDuration, resetTimer } = useSessionTimeoutActions();

  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Set duration depending on test URL flag: ?test_timeout=10
  useEffect(() => {
    if (isAuthenticated) {
      if (typeof window !== 'undefined') {
        const params = new URLSearchParams(window.location.search);
        const testTimeoutParam = params.get('test_timeout');
        if (testTimeoutParam) {
          const customSecs = parseInt(testTimeoutParam, 10);
          if (!isNaN(customSecs)) {
            setDuration(customSecs);
            return;
          }
        }
      }
      setDuration(900); // 15 mins default (900 seconds)
    }
  }, [isAuthenticated, setDuration]);

  // Start countdown ticker
  useEffect(() => {
    if (isAuthenticated && !isExpired) {
      resetTimer();
      intervalRef.current = setInterval(() => {
        tick();
      }, 1000);
    }

    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
      }
    };
  }, [isAuthenticated, isExpired, tick, resetTimer]);

  // Expiration actions: logout, reset stores, clear sessionStorage, redirect
  useEffect(() => {
    if (isExpired && isAuthenticated) {
      const timer = setTimeout(() => {
        logout().then(() => {
          resetWorkspace();
          router.push('/login');
        });
      }, 300); // Wait for the 300ms fade transition to complete

      return () => clearTimeout(timer);
    }
  }, [isExpired, isAuthenticated, logout, resetWorkspace, router]);

  // Activity tracking listener to reset countdown timer
  useEffect(() => {
    const handleUserInteraction = () => {
      if (isAuthenticated && !isExpired) {
        resetTimer();
      }
    };

    if (isAuthenticated && !isExpired) {
      window.addEventListener('click', handleUserInteraction);
      window.addEventListener('keydown', handleUserInteraction);
    }

    return () => {
      window.removeEventListener('click', handleUserInteraction);
      window.removeEventListener('keydown', handleUserInteraction);
    };
  }, [isAuthenticated, isExpired, resetTimer]);

  return (
    <>
      {children}
      {isAuthenticated && (
        <SessionTimeoutOverlay 
          onExtend={resetTimer} 
          onLogout={async () => {
            await logout();
            resetWorkspace();
            router.push('/login');
          }} 
        />
      )}
    </>
  );
};
