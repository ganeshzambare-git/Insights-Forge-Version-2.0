'use client';

import React from 'react';
import { RoleGuard } from '../../../features/authentication/components/RoleGuard';
import { ResourceAllocationPage } from '../../../features/finance/allocation/components/ResourceAllocationPage';

export default function FinancePage() {
  return (
    <RoleGuard allowedRoles={['Admin', 'Dean']}>
      <ResourceAllocationPage />
    </RoleGuard>
  );
}
