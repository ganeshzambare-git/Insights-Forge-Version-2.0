'use client';

import React from 'react';
import { useIsAuthenticated, useCurrentUser } from '../store/authStore';

interface RoleGuardProps {
  allowedRoles: ('Admin' | 'Dean' | 'Faculty' | 'Student')[];
  fallback?: React.ReactNode;
  children: React.ReactNode;
}

export const RoleGuard: React.FC<RoleGuardProps> = ({
  allowedRoles,
  fallback = null,
  children,
}) => {
  const isAuthenticated = useIsAuthenticated();
  const currentUser = useCurrentUser();

  if (!isAuthenticated || !currentUser) {
    return <>{fallback}</>;
  }

  const hasAccess = allowedRoles.includes(currentUser.role);

  if (!hasAccess) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};
