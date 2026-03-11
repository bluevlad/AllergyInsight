/**
 * Analytics API Client
 *
 * /api/public/analytics/* 엔드포인트와 통신합니다.
 * 공개 API로 인증 불필요합니다.
 */
import axios from 'axios';

const API_BASE = import.meta.env.VITE_API_URL || '';

const api = axios.create({
  baseURL: `${API_BASE}/api/public/analytics`,
});

export const analyticsApi = {
  getOverview: () => api.get('/overview').then(r => r.data),
  getAllergenTrend: (allergenCode, limit = 12) => api.get(`/trend/${allergenCode}`, { params: { limit } }).then(r => r.data),
  getKeywordsOverview: () => api.get('/keywords/overview').then(r => r.data),
  getKeywordTrend: (params) => api.get('/keywords/trend', { params }).then(r => r.data),
  getSummary: () => api.get('/summary').then(r => r.data),
  getPaperStats: () => api.get('/papers/stats').then(r => r.data),
  // Insight Reports
  getInsightReports: (params) => api.get('/insights', { params }).then(r => r.data),
  getInsightAllergens: () => api.get('/insights/allergens').then(r => r.data),
  getInsightDetail: (reportId) => api.get(`/insights/${reportId}`).then(r => r.data),
};

export default analyticsApi;
