/**
 * Professional API Client
 *
 * /api/pro/* 엔드포인트와 통신합니다.
 */
import apiClient from '../../../shared/services/apiClient';

export const proApi = {
  // ============================================================================
  // Dashboard
  // ============================================================================
  dashboard: {
    getStats: () => apiClient.get('/pro/dashboard/stats'),
    getDoctorStats: () => apiClient.get('/pro/dashboard/doctors'),
    getAllergenStats: (period = 'month') =>
      apiClient.get('/pro/dashboard/allergens', { params: { period } }),
    getOrganization: () => apiClient.get('/pro/dashboard/organization'),
  },

  // ============================================================================
  // Diagnosis
  // ============================================================================
  diagnosis: {
    create: (data) => apiClient.post('/pro/diagnosis', data),
    get: (id) => apiClient.get(`/pro/diagnosis/${id}`),
    update: (id, data) => apiClient.put(`/pro/diagnosis/${id}`, data),
    getByPatient: (patientId, limit = 10) =>
      apiClient.get(`/pro/diagnosis/patient/${patientId}`, { params: { limit } }),
    getAllergenInfo: () => apiClient.get('/pro/diagnosis/allergen-info'),
  },

  // ============================================================================
  // Patients
  // ============================================================================
  patients: {
    list: (params = {}) => apiClient.get('/pro/patients', { params }),
    get: (id) => apiClient.get(`/pro/patients/${id}`),
    create: (data) => apiClient.post('/pro/patients', data),
    createNew: (data) => apiClient.post('/pro/patients/new', data),
    update: (id, data) => apiClient.put(`/pro/patients/${id}`, data),
    searchByPhone: (phone) =>
      apiClient.get('/pro/patients/search/by-phone', { params: { phone } }),
    getDiagnoses: (patientId) =>
      apiClient.get(`/pro/patients/${patientId}/diagnoses`),
  },

  // ============================================================================
  // Research
  // ============================================================================
  research: {
    search: (query) => apiClient.post('/pro/research/search', query),
    listPapers: (params = {}) => apiClient.get('/pro/research/papers', { params }),
    getPaper: (id) => apiClient.get(`/pro/research/papers/${id}`),
    createPaper: (data, autoExtract = true) =>
      apiClient.post('/pro/research/papers', data, {
        params: { auto_extract_links: autoExtract },
      }),
    getCitations: (allergenCode, params = {}) =>
      apiClient.get(`/pro/research/citations/${allergenCode}`, { params }),
    askQuestion: (data) => apiClient.post('/pro/research/qa', data),
  },
};

export default proApi;
