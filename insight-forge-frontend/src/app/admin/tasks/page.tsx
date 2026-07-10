'use client';

import React from 'react';
import { RoleGuard } from '../../../features/authentication/components/RoleGuard';
import { TaskProgressMonitorPage } from '../../../features/tasks/monitoring/components/TaskProgressMonitorPage';

export default function TasksPage() {
  return (
    <RoleGuard allowedRoles={['Admin', 'Dean']}>
      <TaskProgressMonitorPage />
    </RoleGuard>
  );
}
