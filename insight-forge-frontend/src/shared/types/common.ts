export interface TenantInfo {
  id: string;
  name: string;
  slug: string;
  logoUrl?: string;
  isActive: boolean;
}

export interface UserSessionProfile {
  userId: string;
  email: string;
  role: 'Admin' | 'Dean' | 'Faculty' | 'Student';
  tenantId: string;
}

export interface SecurityBadgeLog {
  event: string;
  timestamp: string;
  metadata?: Record<string, any>;
}
