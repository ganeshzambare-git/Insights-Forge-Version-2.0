import { apiClient } from '../../../core/api/apiClient';
import { TenantInfo } from '../../../shared/types/common';

export const tenantService = {
  async verifyTenant(slug: string): Promise<TenantInfo> {
    return apiClient.get<TenantInfo>(`/tenants/verify/${encodeURIComponent(slug)}`);
  }
};
