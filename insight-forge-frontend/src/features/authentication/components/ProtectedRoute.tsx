'use client';

import React, { useEffect } from 'react';
import { useRouter } from 'next/navigation';
import { useCurrentUser, useIsAuthenticated } from '../store/authStore';

interface ProtectedRouteProps {
  allowedRoles: ('Admin' | 'Dean' | 'Faculty' | 'Student')[];
  children: React.ReactNode;
}

export const ProtectedRoute: React.FC<ProtectedRouteProps> = ({ allowedRoles, children }) => {
  const router = useRouter();
  const isAuthenticated = useIsAuthenticated();
  const currentUser = useCurrentUser();

  useEffect(() => {
    if (!isAuthenticated) {
      router.push('/login');
      return;
    }

    if (currentUser && !allowedRoles.includes(currentUser.role)) {
      const searchParams = new URLSearchParams();
      searchParams.set('unauthorized', 'true');
      
      let redirectPath = '/login';
      if (currentUser.role === 'Student') {
        redirectPath = '/student';
      } else if (currentUser.role === 'Admin' || currentUser.role === 'Dean' || currentUser.role === 'Faculty') {
        redirectPath = '/admin';
      }
      
      router.push(`${redirectPath}?${searchParams.toString()}`);
    }
  }, [isAuthenticated, currentUser, allowedRoles, router]);

  if (!isAuthenticated || !currentUser || !allowedRoles.includes(currentUser.role)) {
    return null;
  }

  return <>{children}</>;
};
export default ProtectedRoute;
