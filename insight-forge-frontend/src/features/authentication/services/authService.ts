import { apiClient } from '../../../core/api/apiClient';

export const authService = {
  async login(payload: any): Promise<any> {
    return apiClient.post<any>('/auth/login', {
      corporate_email: payload.email,
      password: payload.password,
      remember_me: true,
    });
  },
  async logout(): Promise<void> {
    return apiClient.post('/auth/logout', {});
  }
};
