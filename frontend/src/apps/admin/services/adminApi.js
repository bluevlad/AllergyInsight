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

  // ============================================================================
  // Competitor News
  // ============================================================================
  news: {
    list: (params = {}) => apiClient.get('/admin/news', { params }),
    search: (params = {}) => apiClient.get('/admin/news/search', { params }),
    companies: () => apiClient.get('/admin/news/companies'),
    collect: (data) => apiClient.post('/admin/news/collect', data),
    toggleRead: (id) => apiClient.put(`/admin/news/${id}/read`),
    toggleImportant: (id) => apiClient.put(`/admin/news/${id}/important`),
    stats: () => apiClient.get('/admin/news/stats'),
    analyze: (data = {}) => apiClient.post('/admin/news/analyze', data),
    getAnalysis: (id) => apiClient.get(`/admin/news/${id}/analysis`),
    reanalyze: (id) => apiClient.post(`/admin/news/${id}/reanalyze`),
    schedulerStatus: () => apiClient.get('/admin/scheduler/status'),
    triggerScheduler: (data) => apiClient.post('/admin/scheduler/trigger', data),
    updateSchedulerConfig: (data) => apiClient.put('/admin/scheduler/config', data),
  },

  // ============================================================================
  // Newsletter
  // ============================================================================
  newsletter: {
    preview: (params = {}) => apiClient.get('/admin/newsletter/preview', { params, responseType: 'text', transformResponse: [(data) => data] }),
    send: (data) => apiClient.post('/admin/newsletter/send', data),
    history: (params = {}) => apiClient.get('/admin/newsletter/history', { params }),
    stats: () => apiClient.get('/admin/newsletter/stats'),
  },

  // ============================================================================
  // Subscribers
  // ============================================================================
  subscribers: {
    list: (params = {}) => apiClient.get('/admin/subscribers', { params }),
    get: (id) => apiClient.get(`/admin/subscribers/${id}`),
    update: (id, data) => apiClient.put(`/admin/subscribers/${id}`, data),
    delete: (id) => apiClient.delete(`/admin/subscribers/${id}`),
    stats: () => apiClient.get('/admin/subscribers/stats'),
  },
};

export default adminApi;
