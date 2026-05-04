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
  // Analytics
  // ============================================================================
  analytics: {
    overview: () => apiClient.get('/admin/analytics/overview'),
    trend: (allergenCode, params = {}) => apiClient.get(`/admin/analytics/trend/${allergenCode}`, { params }),
    aggregate: (params = {}) => apiClient.post('/admin/analytics/aggregate', null, { params }),
    keywordsOverview: () => apiClient.get('/admin/analytics/keywords/overview'),
    keywordsTrend: (params = {}) => apiClient.get('/admin/analytics/keywords/trend', { params }),
    keywordsExtract: (params = {}) => apiClient.post('/admin/analytics/keywords/extract', null, { params }),
    activityStats: (params = {}) => apiClient.get('/admin/analytics/activity/stats', { params }),
  },

  // ============================================================================
  // Drugs (수집·제품·병태생리 엣지 감수)
  // ============================================================================
  drugs: {
    status: () => apiClient.get('/admin/drugs/status'),
    runIngest: (data = {}) => apiClient.post('/admin/drug-ingest/run', data),
    listProducts: (params = {}) => apiClient.get('/admin/drugs/products', { params }),
    getProduct: (id) => apiClient.get(`/admin/drugs/products/${id}`),
    listUnmapped: (params = {}) => apiClient.get('/admin/drugs/unmapped', { params }),
    resolveUnmapped: (id, rxcui) =>
      apiClient.post(`/admin/drugs/unmapped/${id}/resolve`, { rxcui }),
    listPathophys: () => apiClient.get('/admin/drugs/pathophys'),
    listAtcEdges: (pathophysId) =>
      apiClient.get(`/admin/drugs/pathophys/${pathophysId}/atc`),
    createAtcEdge: (pathophysId, data) =>
      apiClient.post(`/admin/drugs/pathophys/${pathophysId}/atc`, data),
    deleteAtcEdge: (edgeId) =>
      apiClient.delete(`/admin/drugs/pathophys/atc/${edgeId}`),
    verifyAtcEdge: (edgeId) =>
      apiClient.post(`/admin/drugs/pathophys/atc/${edgeId}/verify`),
    listSymptomEdges: (params = {}) =>
      apiClient.get('/admin/drugs/pathophys/symptom-edges', { params }),
    createSymptomEdge: (data) =>
      apiClient.post('/admin/drugs/pathophys/symptom-edges', data),
    deleteSymptomEdge: (edgeId) =>
      apiClient.delete(`/admin/drugs/pathophys/symptom-edges/${edgeId}`),
    verifySymptomEdge: (edgeId) =>
      apiClient.post(`/admin/drugs/pathophys/symptom-edges/${edgeId}/verify`),
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

  // ============================================================================
  // Strategic Intel (내부 경영 분석 — super_admin 전용)
  // ============================================================================
  strategicIntel: {
    matrix: (params = {}) => apiClient.get('/admin/strategic-intel/matrix', { params }),
    listHypotheses: (params = {}) => apiClient.get('/admin/strategic-intel/hypotheses', { params }),
    getHypothesis: (id) => apiClient.get(`/admin/strategic-intel/hypotheses/${id}`),
    listReports: (params = {}) => apiClient.get('/admin/strategic-intel/reports', { params }),
    getReport: (id) => apiClient.get(`/admin/strategic-intel/reports/${id}`),
    generateEventReport: (hypothesisId) =>
      apiClient.post(`/admin/strategic-intel/reports/event/${hypothesisId}`),
    generateMonthlyReport: (year, month) =>
      apiClient.post('/admin/strategic-intel/reports/monthly', { year, month }),
    stats: (params = {}) => apiClient.get('/admin/strategic-intel/stats', { params }),
  },
};

export default adminApi;
