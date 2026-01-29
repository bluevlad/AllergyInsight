/**
 * Admin API Client
 *
 * /api/admin/* 엔드포인트와 통신합니다.
 */
import apiClient from '../../../shared/services/apiClient';

export const adminApi = {
  // ============================================================================
  // Dashboard
  // ============================================================================
  dashboard: {
    get: () => apiClient.get('/admin/dashboard'),
    getStats: () => apiClient.get('/admin/dashboard'),
  },

  // ============================================================================
  // Users
  // ============================================================================
  users: {
    list: (params = {}) => apiClient.get('/admin/users', { params }),
    get: (id) => apiClient.get(`/admin/users/${id}`),
    update: (id, data) => apiClient.put(`/admin/users/${id}`, data),
    updateRole: (id, role) => apiClient.put(`/admin/users/${id}/role`, { role }),
    delete: (id) => apiClient.delete(`/admin/users/${id}`),
  },

  // ============================================================================
  // Allergens
  // ============================================================================
  allergens: {
    list: (params = {}) => apiClient.get('/admin/allergens', { params }),
    get: (code) => apiClient.get(`/admin/allergens/${code}`),
    update: (code, data) => apiClient.put(`/admin/allergens/${code}`, data),
  },

  // ============================================================================
  // Papers
  // ============================================================================
  papers: {
    list: (params = {}) => apiClient.get('/admin/papers', { params }),
    get: (id) => apiClient.get(`/admin/papers/${id}`),
    create: (data) => apiClient.post('/admin/papers', data),
    update: (id, data) => apiClient.put(`/admin/papers/${id}`, data),
    delete: (id) => apiClient.delete(`/admin/papers/${id}`),
  },

  // ============================================================================
  // Organizations
  // ============================================================================
  organizations: {
    list: (params = {}) => apiClient.get('/admin/organizations', { params }),
    get: (id) => apiClient.get(`/admin/organizations/${id}`),
    approve: (id) => apiClient.post(`/admin/organizations/${id}/approve`),
    reject: (id, reason) => apiClient.post(`/admin/organizations/${id}/reject`, { reason }),
    delete: (id) => apiClient.delete(`/admin/organizations/${id}`),
  },
};

export default adminApi;
