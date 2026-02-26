/**
 * 공개 구독 API 클라이언트 (인증 토큰 불필요)
 */
import axios from 'axios';

const subscribeClient = axios.create({
  baseURL: '/api/subscribe',
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
});

// 응답 인터셉터: response.data 직접 반환
subscribeClient.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const message = error.response?.data?.detail || error.message || '요청 실패';
    return Promise.reject(new Error(message));
  }
);

export const subscribeApi = {
  subscribe: (data) => subscribeClient.post('', data),
  verify: (data) => subscribeClient.post('/verify', data),
  getStatus: (email) => subscribeClient.get('/status', { params: { email } }),
  unsubscribe: (data) => subscribeClient.post('/unsubscribe', data),
  updateKeywords: (data) => subscribeClient.put('/keywords', data),
  resendVerification: (data) => subscribeClient.post('/resend-verification', data),
};

export default subscribeApi;
