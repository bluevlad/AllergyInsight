/**
 * AllergyInsight API 클라이언트 - Re-export for backward compatibility
 *
 * @deprecated 이 경로는 deprecated입니다.
 * 대신 'shared/services/api' 또는 앱별 API 클라이언트를 사용하세요:
 * - Professional: 'apps/professional/services/proApi'
 * - Consumer: 'apps/consumer/services/consumerApi'
 */

// Re-export from shared
export {
  authApi,
  allergenApi,
  sgtiApi,
  healthCheck,
  default as apiClient,
} from '../shared/services/api';

// Re-export apiClient as default
import apiClient from '../shared/services/apiClient';
export default apiClient;

// Legacy APIs - kept for backward compatibility
// These should be migrated to the appropriate app-specific API clients

/**
 * 통계 API
 */
export const statsApi = {
  getStats: () => apiClient.get('/stats'),
  getSummary: () => apiClient.get('/stats/summary'),
  reset: () => apiClient.delete('/stats/reset'),
};

/**
 * 검색 API
 */
export const searchApi = {
  search: (allergen, options = {}) =>
    apiClient.post('/search', {
      allergen,
      include_cross_reactivity: options.includeCrossReactivity ?? true,
      max_results: options.maxResults ?? 20,
    }),
  batchSearch: (allergens, grades = null) =>
    apiClient.post('/batch/search', {
      allergens,
      grades,
      include_cross_reactivity: true,
    }),
  getBatchStatus: (jobId) => apiClient.get(`/batch/status/${jobId}`),
  getBatchResults: (jobId) => apiClient.get(`/batch/results/${jobId}`),
};

/**
 * Q&A API
 */
export const qaApi = {
  ask: (question, allergen = 'peanut', maxCitations = 5) =>
    apiClient.post('/qa', {
      question,
      allergen,
      max_citations: maxCitations,
    }),
  getQuestions: (allergen = 'peanut') =>
    apiClient.get(`/qa/questions/${allergen}`),
};

/**
 * 진단 API
 */
export const diagnosisApi = {
  create: (diagnosisResults, diagnosisDate = null, patientInfo = null) =>
    apiClient.post('/diagnosis', {
      diagnosis_results: diagnosisResults,
      diagnosis_date: diagnosisDate,
      patient_info: patientInfo,
    }),
  get: (diagnosisId) => apiClient.get(`/diagnosis/${diagnosisId}`),
  list: (limit = 50, offset = 0) =>
    apiClient.get('/diagnosis', { params: { limit, offset } }),
  delete: (diagnosisId) => apiClient.delete(`/diagnosis/${diagnosisId}`),
};

/**
 * 처방 API
 */
export const prescriptionApi = {
  generateFromDiagnosis: (diagnosisId) =>
    apiClient.post('/prescription/generate', {
      diagnosis_id: diagnosisId,
    }),
  generate: (diagnosisResults, diagnosisDate = null) =>
    apiClient.post('/prescription/generate', {
      diagnosis_results: diagnosisResults,
      diagnosis_date: diagnosisDate,
    }),
  get: (prescriptionId) => apiClient.get(`/prescription/${prescriptionId}`),
  getByDiagnosis: (diagnosisId) =>
    apiClient.get(`/prescription/by-diagnosis/${diagnosisId}`),
  list: (limit = 50, offset = 0) =>
    apiClient.get('/prescription', { params: { limit, offset } }),
};

/**
 * 진단 이력 API (인증 필요)
 */
export const myDiagnosisApi = {
  getAll: () => apiClient.get('/diagnosis/my'),
  getLatest: () => apiClient.get('/diagnosis/my/latest'),
  get: (diagnosisId) => apiClient.get(`/diagnosis/my/${diagnosisId}`),
  getAllergenInfo: () => apiClient.get('/diagnosis/allergen-info'),
  getPatientGuide: (diagnosisId) => apiClient.get(`/diagnosis/my/${diagnosisId}/patient-guide`),
};

/**
 * 논문/출처 API
 */
export const papersApi = {
  list: (params = {}) => apiClient.get('/papers', { params }),
  get: (paperId) => apiClient.get(`/papers/${paperId}`),
  create: (paperData) => apiClient.post('/papers', paperData),
  update: (paperId, paperData) => apiClient.put(`/papers/${paperId}`, paperData),
  delete: (paperId) => apiClient.delete(`/papers/${paperId}`),
  addLink: (paperId, linkData) => apiClient.post(`/papers/${paperId}/links`, linkData),
  removeLink: (paperId, linkId) => apiClient.delete(`/papers/${paperId}/links/${linkId}`),
  getCitationsForAllergen: (allergenCode, linkType = null) =>
    apiClient.get(`/papers/citations/${allergenCode}`, { params: { link_type: linkType } }),
  getCitationsByType: (linkType, allergenCode = null) =>
    apiClient.get(`/papers/citations/by-type/${linkType}`, { params: { allergen_code: allergenCode } }),
};

/**
 * 병원 관리 API (Phase 2)
 */
export const hospitalApi = {
  getDashboard: () => apiClient.get('/hospital/dashboard'),
  getDoctorStats: () => apiClient.get('/hospital/doctors/stats'),
  getPatients: (params = {}) => apiClient.get('/hospital/patients', { params }),
  getPatient: (patientId) => apiClient.get(`/hospital/patients/${patientId}`),
  registerPatient: (data) => apiClient.post('/hospital/patients', data),
  registerNewPatient: (data) => apiClient.post('/hospital/patients/new', data),
  updatePatient: (patientId, data) => apiClient.put(`/hospital/patients/${patientId}`, data),
  signConsent: (patientId, data) => apiClient.post(`/hospital/patients/${patientId}/consent`, data),
  getMyHospitals: () => apiClient.get('/hospital/my-hospitals'),
  getPatientDiagnoses: (patientId) => apiClient.get(`/hospital/patients/${patientId}/diagnoses`),
  createDiagnosis: (patientId, data) => apiClient.post(`/hospital/patients/${patientId}/diagnoses`, data),
};
