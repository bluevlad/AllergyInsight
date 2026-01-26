/**
 * Shared Core API - 공통 API 모듈
 *
 * 인증, 알러젠 정보 등 Professional과 Consumer에서 공유하는 API입니다.
 */
import apiClient from './apiClient';

/**
 * 인증 API
 */
export const authApi = {
  // 현재 사용자 정보
  getMe: () => apiClient.get('/auth/me'),

  // 로그아웃
  logout: () => apiClient.post('/auth/logout'),

  // 간편 등록
  registerSimple: (data) => apiClient.post('/auth/simple/register', {
    name: data.name,
    phone: data.phone || null,
    birth_date: data.birthDate || null,
    serial_number: data.serialNumber,
    pin: data.pin,
  }),

  // 간편 로그인
  loginSimple: (data) => apiClient.post('/auth/simple/login', {
    name: data.name,
    birth_date: data.birthDate || null,
    phone: data.phone || null,
    access_pin: data.accessPin,
  }),

  // 키트 등록 (로그인 사용자)
  registerKit: (serialNumber, pin) => apiClient.post('/auth/register-kit', {
    serial_number: serialNumber,
    pin: pin,
  }),
};

/**
 * 알러젠 정보 API
 */
export const allergenApi = {
  // 알러젠 목록 조회
  getAll: () => apiClient.get('/allergens'),
};

/**
 * SGTi 정보 API
 */
export const sgtiApi = {
  // SGTi 제품 정보 조회
  getInfo: () => apiClient.get('/sgti/info'),

  // 등급 정보 조회
  getGrades: () => apiClient.get('/sgti/grades'),
};

/**
 * 헬스 체크
 */
export const healthCheck = () => apiClient.get('/health');

export default apiClient;
