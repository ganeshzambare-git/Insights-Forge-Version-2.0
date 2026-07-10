import { create } from 'zustand';
import { TenantInfo } from '../../../shared/types/common';
import { tenantService } from '../services/tenantService';

interface WorkspaceState {
  slug: string;
  loading: boolean;
  error: string | null;
  tenantInfo: TenantInfo | null;
  actions: {
    setSlug: (slug: string) => void;
    verifyWorkspace: () => Promise<void>;
    resetWorkspace: () => void;
  };
}

const useWorkspaceStoreInternal = create<WorkspaceState>((set, get) => ({
  slug: '',
  loading: false,
  error: null,
  tenantInfo: null,
  actions: {
    setSlug: (slug) => set({ slug: slug.trim().toLowerCase(), error: null }),
    verifyWorkspace: async () => {
      const { slug } = get();
      if (!slug || slug.length <= 3) return;

      set({ loading: true, error: null });
      try {
        const tenantInfo = await tenantService.verifyTenant(slug);
        set({ tenantInfo, loading: false });
        if (typeof window !== 'undefined') {
          sessionStorage.setItem('__tenant_context_id', tenantInfo.id);
        }
      } catch (err: any) {
        set({
          error: 'Workspace alias not found. Please contact your system administrator.',
          tenantInfo: null,
          loading: false,
        });
      }
    },
    resetWorkspace: () => {
      set({ slug: '', tenantInfo: null, error: null, loading: false });
      if (typeof window !== 'undefined') {
        sessionStorage.removeItem('__tenant_context_id');
      }
    },
  },
}));

export const useWorkspaceSlug = () => useWorkspaceStoreInternal((s) => s.slug);
export const useWorkspaceLoading = () => useWorkspaceStoreInternal((s) => s.loading);
export const useWorkspaceError = () => useWorkspaceStoreInternal((s) => s.error);
export const useWorkspaceTenant = () => useWorkspaceStoreInternal((s) => s.tenantInfo);
export const useWorkspaceActions = () => useWorkspaceStoreInternal((s) => s.actions);
