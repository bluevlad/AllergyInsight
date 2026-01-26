/**
 * Consumer API Client
 *
 * /api/consumer/* 엔드포인트와 통신합니다.
 */
import apiClient from '../../../shared/services/apiClient';

export const consumerApi = {
  // ============================================================================
  // My Diagnosis
  // ============================================================================
  my: {
    getDiagnoses: () => apiClient.get('/consumer/my/diagnoses'),
    getLatest: () => apiClient.get('/consumer/my/diagnoses/latest'),
    getDiagnosis: (id) => apiClient.get(`/consumer/my/diagnoses/${id}`),
    getGuide: (id) => apiClient.get(`/consumer/my/diagnoses/${id}/guide`),
  },

  // ============================================================================
  // Guide
  // ============================================================================
  guide: {
    getFoods: (allergenCodes) =>
      apiClient.get('/consumer/guide/foods', {
        params: allergenCodes ? { allergen_codes: allergenCodes } : {},
      }),
    getSymptoms: (allergenCodes) =>
      apiClient.get('/consumer/guide/symptoms', {
        params: allergenCodes ? { allergen_codes: allergenCodes } : {},
      }),
    getLifestyle: (allergenCodes) =>
      apiClient.get('/consumer/guide/lifestyle', {
        params: allergenCodes ? { allergen_codes: allergenCodes } : {},
      }),
    getCrossReactivity: (allergenCode) =>
      apiClient.get('/consumer/guide/cross-reactivity', {
        params: { allergen_code: allergenCode },
      }),
  },

  // ============================================================================
  // Emergency
  // ============================================================================
  emergency: {
    getGuidelines: () => apiClient.get('/consumer/emergency/guidelines'),
    getActionPlan: (severity) =>
      apiClient.get('/consumer/emergency/action-plan', {
        params: severity ? { severity } : {},
      }),
    getEpinephrineGuide: () => apiClient.get('/consumer/emergency/epinephrine-guide'),
    getHospitalChecklist: () => apiClient.get('/consumer/emergency/hospital-checklist'),
  },

  // ============================================================================
  // Kit
  // ============================================================================
  kit: {
    register: (data) =>
      apiClient.post('/consumer/kit/register', {
        serial_number: data.serialNumber,
        pin: data.pin,
      }),
    checkStatus: (serialNumber) =>
      apiClient.get(`/consumer/kit/status/${serialNumber}`),
    getMyKits: () => apiClient.get('/consumer/kit/my-kits'),
  },
};

export default consumerApi;
