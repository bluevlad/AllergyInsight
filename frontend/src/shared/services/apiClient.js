/**
 * Shared API Client - Axios 인스턴스
 *
 * 모든 API 호출에서 공통으로 사용하는 Axios 인스턴스입니다.
 * Professional과 Consumer 앱에서 공유합니다.
 */
import axios from 'axios';

const API_BASE = '/api';

const apiClient = axios.create({
  baseURL: API_BASE,
  timeout: 60000,
  headers: {
    'Content-Type': 'application/json',
  },
});

// 요청 인터셉터 - 토큰 추가
apiClient.interceptors.request.use(
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
apiClient.interceptors.response.use(
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

export default apiClient;
