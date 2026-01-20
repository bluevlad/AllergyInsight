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

// 요청 인터셉터 - 토큰 추가
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  },
  (error) => Promise.reject(error)
);

// 응답 인터셉터
api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    console.error('API Error:', error);
    // 401 에러 시 토큰 제거
    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
    }
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

/**
 * 인증 API
 */
export const authApi = {
  // 현재 사용자 정보
  getMe: () => api.get('/auth/me'),

  // 로그아웃
  logout: () => api.post('/auth/logout'),

  // 간편 등록
  registerSimple: (data) => api.post('/auth/simple/register', {
    name: data.name,
    phone: data.phone || null,
    birth_date: data.birthDate || null,
    serial_number: data.serialNumber,
    pin: data.pin,
  }),

  // 간편 로그인
  loginSimple: (data) => api.post('/auth/simple/login', {
    name: data.name,
    birth_date: data.birthDate || null,
    phone: data.phone || null,
    access_pin: data.accessPin,
  }),

  // 키트 등록 (로그인 사용자)
  registerKit: (serialNumber, pin) => api.post('/auth/register-kit', {
    serial_number: serialNumber,
    pin: pin,
  }),
};

/**
 * 진단 이력 API (인증 필요)
 */
export const myDiagnosisApi = {
  // 내 진단 이력
  getAll: () => api.get('/diagnosis/my'),

  // 최신 진단 요약
  getLatest: () => api.get('/diagnosis/my/latest'),

  // 특정 진단 상세
  get: (diagnosisId) => api.get(`/diagnosis/my/${diagnosisId}`),

  // 알러젠 정보
  getAllergenInfo: () => api.get('/diagnosis/allergen-info'),

  // 환자 가이드 (증상, 식이관리, 응급대처)
  getPatientGuide: (diagnosisId) => api.get(`/diagnosis/my/${diagnosisId}/patient-guide`),
};

export default api;
