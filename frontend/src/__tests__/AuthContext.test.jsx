/**
 * AuthContext 테스트
 *
 * 인증 컨텍스트의 기능을 테스트합니다.
 */
import React from 'react';
import { render, screen, waitFor, act } from '@testing-library/react';
import { AuthProvider, useAuth } from '../shared/contexts/AuthContext';
import { authApi } from '../shared/services/api';

// API mock
jest.mock('../shared/services/api', () => ({
  authApi: {
    getMe: jest.fn(),
    loginSimple: jest.fn(),
    registerSimple: jest.fn(),
    registerKit: jest.fn(),
    logout: jest.fn(),
  },
}));

// localStorage mock
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

// 테스트용 컴포넌트
const TestComponent = () => {
  const auth = useAuth();
  return (
    <div>
      <span data-testid="loading">{auth.loading ? 'true' : 'false'}</span>
      <span data-testid="authenticated">{auth.isAuthenticated ? 'true' : 'false'}</span>
      <span data-testid="user-name">{auth.user?.name || 'none'}</span>
      <span data-testid="user-role">{auth.user?.role || 'none'}</span>
      <span data-testid="is-admin">{auth.isAdmin ? 'true' : 'false'}</span>
      <span data-testid="is-professional">{auth.isProfessional ? 'true' : 'false'}</span>
      <span data-testid="is-consumer">{auth.isConsumer ? 'true' : 'false'}</span>
      <span data-testid="default-app">{auth.getDefaultApp()}</span>
      <button data-testid="logout" onClick={auth.logout}>Logout</button>
    </div>
  );
};

describe('AuthContext', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  describe('초기 상태', () => {
    it('토큰이 없으면 비인증 상태로 시작', async () => {
      localStorageMock.getItem.mockReturnValue(null);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('false');
      });

      expect(screen.getByTestId('authenticated').textContent).toBe('false');
      expect(screen.getByTestId('user-name').textContent).toBe('none');
    });

    it('토큰이 있으면 사용자 정보를 가져옴', async () => {
      localStorageMock.getItem.mockReturnValue('test-token');
      authApi.getMe.mockResolvedValue({
        id: 1,
        name: '테스트유저',
        role: 'user',
      });

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('false');
      });

      expect(screen.getByTestId('authenticated').textContent).toBe('true');
      expect(screen.getByTestId('user-name').textContent).toBe('테스트유저');
    });

    it('토큰이 유효하지 않으면 토큰을 제거', async () => {
      localStorageMock.getItem.mockReturnValue('invalid-token');
      authApi.getMe.mockRejectedValue(new Error('Unauthorized'));

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('false');
      });

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
      expect(screen.getByTestId('authenticated').textContent).toBe('false');
    });
  });

  describe('역할 기반 체크', () => {
    it('일반 사용자는 consumer로 판단', async () => {
      localStorageMock.getItem.mockReturnValue('test-token');
      authApi.getMe.mockResolvedValue({
        id: 1,
        name: '환자',
        role: 'user',
      });

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('false');
      });

      expect(screen.getByTestId('is-admin').textContent).toBe('false');
      expect(screen.getByTestId('is-professional').textContent).toBe('false');
      expect(screen.getByTestId('is-consumer').textContent).toBe('true');
      expect(screen.getByTestId('default-app').textContent).toBe('consumer');
    });

    it('의사는 professional로 판단', async () => {
      localStorageMock.getItem.mockReturnValue('test-token');
      authApi.getMe.mockResolvedValue({
        id: 2,
        name: '의사',
        role: 'doctor',
      });

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('false');
      });

      expect(screen.getByTestId('is-admin').textContent).toBe('false');
      expect(screen.getByTestId('is-professional').textContent).toBe('true');
      expect(screen.getByTestId('is-consumer').textContent).toBe('false');
      expect(screen.getByTestId('default-app').textContent).toBe('professional');
    });

    it('admin은 관리자 및 professional로 판단', async () => {
      localStorageMock.getItem.mockReturnValue('test-token');
      authApi.getMe.mockResolvedValue({
        id: 3,
        name: '관리자',
        role: 'admin',
      });

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('false');
      });

      expect(screen.getByTestId('is-admin').textContent).toBe('true');
      expect(screen.getByTestId('is-professional').textContent).toBe('true');
      expect(screen.getByTestId('is-consumer').textContent).toBe('false');
    });

    it('super_admin은 관리자로 판단', async () => {
      localStorageMock.getItem.mockReturnValue('test-token');
      authApi.getMe.mockResolvedValue({
        id: 4,
        name: '슈퍼관리자',
        role: 'super_admin',
      });

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('false');
      });

      expect(screen.getByTestId('is-admin').textContent).toBe('true');
    });
  });

  describe('로그아웃', () => {
    it('로그아웃 시 토큰 제거 및 사용자 초기화', async () => {
      localStorageMock.getItem.mockReturnValue('test-token');
      authApi.getMe.mockResolvedValue({
        id: 1,
        name: '테스트유저',
        role: 'user',
      });
      authApi.logout.mockResolvedValue({});

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('authenticated').textContent).toBe('true');
      });

      await act(async () => {
        screen.getByTestId('logout').click();
      });

      await waitFor(() => {
        expect(screen.getByTestId('authenticated').textContent).toBe('false');
      });

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
    });

    it('로그아웃 API 실패해도 토큰은 제거', async () => {
      localStorageMock.getItem.mockReturnValue('test-token');
      authApi.getMe.mockResolvedValue({
        id: 1,
        name: '테스트유저',
        role: 'user',
      });
      authApi.logout.mockRejectedValue(new Error('Network error'));

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('authenticated').textContent).toBe('true');
      });

      await act(async () => {
        screen.getByTestId('logout').click();
      });

      await waitFor(() => {
        expect(screen.getByTestId('authenticated').textContent).toBe('false');
      });

      expect(localStorageMock.removeItem).toHaveBeenCalledWith('access_token');
    });
  });

  describe('useAuth hook', () => {
    it('AuthProvider 없이 사용 시 에러 발생', () => {
      // 콘솔 에러 무시
      const consoleSpy = jest.spyOn(console, 'error').mockImplementation(() => {});

      expect(() => {
        render(<TestComponent />);
      }).toThrow('useAuth must be used within AuthProvider');

      consoleSpy.mockRestore();
    });
  });

  describe('getDefaultApp', () => {
    it('비로그인 상태에서는 login 반환', async () => {
      localStorageMock.getItem.mockReturnValue(null);

      render(
        <AuthProvider>
          <TestComponent />
        </AuthProvider>
      );

      await waitFor(() => {
        expect(screen.getByTestId('loading').textContent).toBe('false');
      });

      expect(screen.getByTestId('default-app').textContent).toBe('login');
    });
  });
});
