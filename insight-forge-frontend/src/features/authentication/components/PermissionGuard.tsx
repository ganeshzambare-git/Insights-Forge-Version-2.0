'use client';

import React from 'react';
import { useIsAuthenticated, useCurrentUser } from '../store/authStore';

// Simple client-side mapping from user roles to active scopes
const rolePermissionsMap: Record<string, string[]> = {
  Admin: [
    'admin.dashboard',
    'data.upload',
    'analytics.view',
    'cohorts.read',
    'metrics.read',
    'interventions.write'
  ],
  Dean: [
    'analytics.view',
    'cohorts.read',
    'metrics.read',
    'interventions.write'
  ],
  Faculty: [
    'analytics.view',
    'cohorts.read',
    'metrics.read',
    'interventions.write'
  ],
  Student: [
    'analytics.view',
    'metrics.read'
  ],
};

interface PermissionGuardProps {
  permission: string;
  fallback?: React.ReactNode;
  children: React.ReactNode;
}

export const PermissionGuard: React.FC<PermissionGuardProps> = ({
  permission,
  fallback = null,
  children,
}) => {
  const isAuthenticated = useIsAuthenticated();
  const currentUser = useCurrentUser();

  if (!isAuthenticated || !currentUser) {
    return <>{fallback}</>;
  }

  const permissions = rolePermissionsMap[currentUser.role] || [];
  const hasPermission = permissions.includes(permission);

  if (!hasPermission) {
    return <>{fallback}</>;
  }

  return <>{children}</>;
};
