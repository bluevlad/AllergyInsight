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

const allergenApi = axios.create({
  baseURL: `${API_BASE}/api/allergens`,
});

export const analyticsApi = {
  getOverview: () => api.get('/overview').then(r => r.data),
  getAllergenTrend: (allergenCode, limit = 12) => api.get(`/trend/${allergenCode}`, { params: { limit } }).then(r => r.data),
  // 알러젠 마스터 데이터
  getAllergenList: (params) => allergenApi.get('/', { params }).then(r => r.data),
  getAllergenDetail: (code) => allergenApi.get(`/${code}`).then(r => r.data),
  getAllergenCategories: () => allergenApi.get('/categories').then(r => r.data),
  getKeywordsOverview: () => api.get('/keywords/overview').then(r => r.data),
  getKeywordTrend: (params) => api.get('/keywords/trend', { params }).then(r => r.data),
  getSummary: () => api.get('/summary').then(r => r.data),
  getPaperStats: () => api.get('/papers/stats').then(r => r.data),
  // Insight Reports
  getInsightReports: (params) => api.get('/insights', { params }).then(r => r.data),
  getInsightAllergens: () => api.get('/insights/allergens').then(r => r.data),
  getInsightDetail: (reportId) => api.get(`/insights/${reportId}`).then(r => r.data),
  // 최근 수집 뉴스
  getRecentNews: (params) => api.get('/news/recent', { params }).then(r => r.data),
  // 논문 알러젠 트렌드 (Phase 1)
  getPaperTrendOverview: () => api.get('/allergen-trend/overview').then(r => r.data),
  getPaperTrend: (allergenCode, params) => api.get(`/allergen-trend/${allergenCode}`, { params }).then(r => r.data),
  getPaperTrendRanking: (params) => api.get('/allergen-trend/ranking', { params }).then(r => r.data),
  // 치료법 트렌드 (Phase 2)
  getTreatmentOverview: () => api.get('/treatments/overview').then(r => r.data),
  getTreatmentsByAllergen: (allergenCode) => api.get(`/treatments/${allergenCode}`).then(r => r.data),
  getEmergingTreatments: (params) => api.get('/treatments/emerging', { params }).then(r => r.data),
  // 역학 데이터 (Phase 4)
  getEpidemiologyOverview: () => api.get('/epidemiology/overview').then(r => r.data),
  getEpidemiologyByAllergen: (allergenCode, params) => api.get(`/epidemiology/${allergenCode}`, { params }).then(r => r.data),
  // 종합 트렌드 (Phase 3)
  getComprehensiveTrend: (allergenCode) => api.get(`/allergen-comprehensive/${allergenCode}`).then(r => r.data),
};

export default analyticsApi;
