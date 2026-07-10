'use client';

import React from 'react';
import { RoleGuard } from '../../../features/authentication/components/RoleGuard';
import { CourseAnalyticsPage } from '../../../features/analytics/curriculum/components/CourseAnalyticsPage';

export default function CoursesPage() {
  return (
    <RoleGuard allowedRoles={['Admin', 'Dean']}>
      <CourseAnalyticsPage />
    </RoleGuard>
  );
}
