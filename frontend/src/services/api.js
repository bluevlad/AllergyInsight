/**
 * AllergyInsight API 클라이언트
 */
import axios from 'axios';

const API_BASE = '/api';

const api = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 응답 인터셉터
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error);
    throw error;
  }
);

/**
 * 통계 API
 */
export const statsApi = {
  // 전체 통계 조회
  getStats: () => api.get('/stats'),

  // 요약 통계 조회
  getSummary: () => api.get('/stats/summary'),

  // 통계 초기화
  reset: () => api.delete('/stats/reset'),
};

/**
 * 검색 API
 */
export const searchApi = {
  // 논문 검색
  search: (allergen, options = {}) =>
    api.post('/search', {
      allergen,
      include_cross_reactivity: options.includeCrossReactivity ?? true,
      max_results: options.maxResults ?? 20,
    }),

  // 배치 검색 시작
  batchSearch: (allergens, grades = null) =>
    api.post('/batch/search', {
      allergens,
      grades,
      include_cross_reactivity: true,
    }),

  // 배치 상태 조회
  getBatchStatus: (jobId) => api.get(`/batch/status/${jobId}`),

  // 배치 결과 조회
  getBatchResults: (jobId) => api.get(`/batch/results/${jobId}`),
};

/**
 * Q&A API
 */
export const qaApi = {
  // 질문하기
  ask: (question, allergen = 'peanut', maxCitations = 5) =>
    api.post('/qa', {
      question,
      allergen,
      max_citations: maxCitations,
    }),

  // 사전 정의 질문 조회
  getQuestions: (allergen = 'peanut') =>
    api.get(`/qa/questions/${allergen}`),
};

/**
 * 알러지 정보 API
 */
export const allergenApi = {
  // 알러지 목록 조회
  getAll: () => api.get('/allergens'),
};

/**
 * 헬스 체크
 */
export const healthCheck = () => api.get('/health');

export default api;
