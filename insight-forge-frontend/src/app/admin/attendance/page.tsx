'use client';

import React from 'react';
import { RoleGuard } from '../../../features/authentication/components/RoleGuard';
import { AttendanceAnalyticsPage } from '../../../features/analytics/attendance/components/AttendanceAnalyticsPage';

export default function AttendancePage() {
  return (
    <RoleGuard allowedRoles={['Admin', 'Dean']}>
      <AttendanceAnalyticsPage />
    </RoleGuard>
  );
}
