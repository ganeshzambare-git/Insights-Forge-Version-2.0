import { create } from 'zustand';
import { UserSessionProfile } from '../../../shared/types/common';
import { setAccessToken } from '../../../core/api/apiClient';
import { authService } from '../services/authService';

interface AuthState {
  isAuthenticated: boolean;
  user: UserSessionProfile | null;
  loading: boolean;
  error: string | null;
  actions: {
    submitLogin: (payload: any) => Promise<boolean>;
    clearErrors: () => void;
    logout: () => Promise<void>;
    initializeSession: () => void;
  };
}

const useAuthStoreInternal = create<AuthState>((set) => ({
  isAuthenticated: false,
  user: null,
  loading: false,
  error: null,
  actions: {
    submitLogin: async (payload) => {
      set({ loading: true, error: null });
      try {
        const resData = await authService.login(payload);

        const { access_token, user } = resData;

        // Store access token privately inside the apiClient closure (prevents XSS leaks)
        setAccessToken(access_token);

        const profile: UserSessionProfile = {
          userId: user.user_id,
          email: user.corporate_email,
          role: user.assigned_role,
          tenantId: user.tenant_id,
        };

        set({ isAuthenticated: true, user: profile, loading: false });
        if (typeof window !== 'undefined') {
          sessionStorage.setItem('__user_profile', JSON.stringify(profile));
          sessionStorage.setItem('__access_token', access_token);
        }
        return true;
      } catch (err: any) {
        set({
          error: 'Invalid email, password, or MFA code. Security event logged.',
          loading: false,
        });
        return false;
      }
    },
    clearErrors: () => set({ error: null }),
    logout: async () => {
      set({ loading: true });
      try {
        await authService.logout();
      } catch (err) {
        // ignore errors during logout to guarantee cleanup
      } finally {
        setAccessToken(null);
        set({ isAuthenticated: false, user: null, loading: false, error: null });
        if (typeof window !== 'undefined') {
          sessionStorage.removeItem('__user_profile');
          sessionStorage.removeItem('__access_token');
        }
      }
    },
    initializeSession: () => {
      if (typeof window !== 'undefined') {
        const cachedProfile = sessionStorage.getItem('__user_profile');
        const cachedToken = sessionStorage.getItem('__access_token');
        if (cachedProfile && cachedToken) {
          try {
            const profile = JSON.parse(cachedProfile);
            setAccessToken(cachedToken);
            set({ isAuthenticated: true, user: profile });
          } catch (e) {
            sessionStorage.removeItem('__user_profile');
            sessionStorage.removeItem('__access_token');
          }
        }
      }
    }
  },
}));

export const useIsAuthenticated = () => useAuthStoreInternal((s) => s.isAuthenticated);
export const useCurrentUser = () => useAuthStoreInternal((s) => s.user);
export const useAuthLoading = () => useAuthStoreInternal((s) => s.loading);
export const useAuthError = () => useAuthStoreInternal((s) => s.error);
export const useAuthActions = () => useAuthStoreInternal((s) => s.actions);
