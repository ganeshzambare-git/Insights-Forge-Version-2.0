'use client';

import React from 'react';
import { RoleGuard } from '../../../features/authentication/components/RoleGuard';
import { SecurityAuditPage } from '../../../features/administration/security/components/SecurityAuditPage';

export default function SecurityPage() {
  return (
    <RoleGuard allowedRoles={['Admin']}>
      <SecurityAuditPage />
    </RoleGuard>
  );
}
