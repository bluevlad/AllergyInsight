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
 * SGTi 정보 API
 */
export const sgtiApi = {
  // SGTi 제품 정보 조회
  getInfo: () => api.get('/sgti/info'),

  // 등급 정보 조회
  getGrades: () => api.get('/sgti/grades'),
};

/**
 * 진단 API
 */
export const diagnosisApi = {
  // 진단 결과 저장
  create: (diagnosisResults, diagnosisDate = null, patientInfo = null) =>
    api.post('/diagnosis', {
      diagnosis_results: diagnosisResults,
      diagnosis_date: diagnosisDate,
      patient_info: patientInfo,
    }),

  // 진단 결과 조회
  get: (diagnosisId) => api.get(`/diagnosis/${diagnosisId}`),

  // 진단 결과 목록 조회
  list: (limit = 50, offset = 0) =>
    api.get('/diagnosis', { params: { limit, offset } }),

  // 진단 결과 삭제
  delete: (diagnosisId) => api.delete(`/diagnosis/${diagnosisId}`),
};

/**
 * 처방 API
 */
export const prescriptionApi = {
  // 처방 권고 생성 (진단 ID 사용)
  generateFromDiagnosis: (diagnosisId) =>
    api.post('/prescription/generate', {
      diagnosis_id: diagnosisId,
    }),

  // 처방 권고 생성 (직접 입력)
  generate: (diagnosisResults, diagnosisDate = null) =>
    api.post('/prescription/generate', {
      diagnosis_results: diagnosisResults,
      diagnosis_date: diagnosisDate,
    }),

  // 처방 권고 조회
  get: (prescriptionId) => api.get(`/prescription/${prescriptionId}`),

  // 진단 ID로 처방 권고 조회
  getByDiagnosis: (diagnosisId) =>
    api.get(`/prescription/by-diagnosis/${diagnosisId}`),

  // 처방 권고 목록 조회
  list: (limit = 50, offset = 0) =>
    api.get('/prescription', { params: { limit, offset } }),
};

/**
 * 헬스 체크
 */
export const healthCheck = () => api.get('/health');

export default api;
