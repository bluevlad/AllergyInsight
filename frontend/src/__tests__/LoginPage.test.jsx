/**
 * LoginPage 테스트
 *
 * 이메일+비밀번호 로그인/회원가입 페이지의 기능을 테스트합니다.
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import LoginPage from '../pages/LoginPage';
import { AuthProvider } from '../shared/contexts/AuthContext';
import { authApi } from '../shared/services/api';

// API mock
jest.mock('../shared/services/api', () => ({
  authApi: {
    getMe: jest.fn(),
    loginEmail: jest.fn(),
    sendVerificationCode: jest.fn(),
    registerEmail: jest.fn(),
    loginSimple: jest.fn(),
    registerSimple: jest.fn(),
    registerKit: jest.fn(),
    loginAdmin: jest.fn(),
    logout: jest.fn(),
  },
}));

// react-router-dom navigate mock
const mockNavigate = jest.fn();
jest.mock('react-router-dom', () => ({
  ...jest.requireActual('react-router-dom'),
  useNavigate: () => mockNavigate,
}));

// localStorage mock
const localStorageMock = {
  getItem: jest.fn(),
  setItem: jest.fn(),
  removeItem: jest.fn(),
  clear: jest.fn(),
};
Object.defineProperty(window, 'localStorage', { value: localStorageMock });

// 테스트용 렌더 헬퍼
const renderLoginPage = () => {
  return render(
    <MemoryRouter>
      <AuthProvider>
        <LoginPage />
      </AuthProvider>
    </MemoryRouter>
  );
};

describe('LoginPage', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorageMock.getItem.mockReturnValue(null);
  });

  describe('UI 렌더링', () => {
    it('로그인 페이지가 올바르게 렌더링됨', async () => {
      renderLoginPage();

      await waitFor(() => {
        expect(screen.getByText('AllergyInsight')).toBeInTheDocument();
      });
      expect(screen.getByText('알러지 검사 결과 조회 서비스')).toBeInTheDocument();
      expect(screen.getByText('Google로 계속하기')).toBeInTheDocument();
    });

    it('로그인 모드에서 이메일/비밀번호 입력 필드 표시', async () => {
      renderLoginPage();

      await waitFor(() => {
        expect(screen.getByLabelText('이메일')).toBeInTheDocument();
      });
      expect(screen.getByLabelText('비밀번호')).toBeInTheDocument();
    });

    it('회원가입 모드로 전환 시 이메일 입력 필드 표시', async () => {
      renderLoginPage();

      await waitFor(() => {
        expect(screen.getByText('AllergyInsight')).toBeInTheDocument();
      });

      const tabButtons = screen.getAllByRole('button');
      const registerTab = tabButtons.find(btn =>
        btn.textContent === '회원가입' && btn.classList.contains('mode-tab')
      );
      fireEvent.click(registerTab);

      expect(screen.getByLabelText('이메일')).toBeInTheDocument();
      expect(screen.getByText('인증 코드 받기')).toBeInTheDocument();
    });
  });

  describe('로그인 기능', () => {
    it('로그인 폼 제출 시 API 호출', async () => {
      authApi.loginEmail.mockResolvedValue({
        access_token: 'test-token',
        user: { id: 1, name: '테스트유저', role: 'user' },
      });

      renderLoginPage();

      await waitFor(() => {
        expect(screen.getByLabelText('이메일')).toBeInTheDocument();
      });

      fireEvent.change(screen.getByLabelText('이메일'), {
        target: { value: 'test@example.com' },
      });
      fireEvent.change(screen.getByLabelText('비밀번호'), {
        target: { value: 'testpass' },
      });

      const form = screen.getByLabelText('이메일').closest('form');
      fireEvent.submit(form);

      await waitFor(() => {
        expect(authApi.loginEmail).toHaveBeenCalledWith({
          email: 'test@example.com',
          password: 'testpass',
        });
      });
    });

    it('로그인 실패 시 에러 메시지 표시', async () => {
      authApi.loginEmail.mockRejectedValue({
        response: { data: { detail: '이메일 또는 비밀번호가 올바르지 않습니다.' } },
      });

      renderLoginPage();

      await waitFor(() => {
        expect(screen.getByLabelText('이메일')).toBeInTheDocument();
      });

      fireEvent.change(screen.getByLabelText('이메일'), {
        target: { value: 'test@example.com' },
      });
      fireEvent.change(screen.getByLabelText('비밀번호'), {
        target: { value: 'wrong' },
      });

      const form = screen.getByLabelText('이메일').closest('form');
      fireEvent.submit(form);

      await waitFor(() => {
        expect(screen.getByText('이메일 또는 비밀번호가 올바르지 않습니다.')).toBeInTheDocument();
      });
    });
  });

  describe('회원가입 기능', () => {
    it('인증 코드 발송 요청', async () => {
      authApi.sendVerificationCode.mockResolvedValue({
        message: '인증 코드가 발송되었습니다.',
      });

      renderLoginPage();

      await waitFor(() => {
        expect(screen.getByText('AllergyInsight')).toBeInTheDocument();
      });

      // 회원가입 탭 클릭
      const tabButtons = screen.getAllByRole('button');
      const registerTab = tabButtons.find(btn =>
        btn.textContent === '회원가입' && btn.classList.contains('mode-tab')
      );
      fireEvent.click(registerTab);

      fireEvent.change(screen.getByLabelText('이메일'), {
        target: { value: 'new@example.com' },
      });

      const form = screen.getByLabelText('이메일').closest('form');
      fireEvent.submit(form);

      await waitFor(() => {
        expect(authApi.sendVerificationCode).toHaveBeenCalledWith({
          email: 'new@example.com',
        });
      });
    });
  });

  describe('폼 입력', () => {
    it('입력 필드 변경 시 에러 메시지 초기화', async () => {
      authApi.loginEmail.mockRejectedValue({
        response: { data: { detail: '에러 발생' } },
      });

      renderLoginPage();

      await waitFor(() => {
        expect(screen.getByLabelText('이메일')).toBeInTheDocument();
      });

      fireEvent.change(screen.getByLabelText('이메일'), {
        target: { value: 'test@example.com' },
      });
      fireEvent.change(screen.getByLabelText('비밀번호'), {
        target: { value: 'wrong' },
      });

      const form = screen.getByLabelText('이메일').closest('form');
      fireEvent.submit(form);

      await waitFor(() => {
        expect(screen.getByText('에러 발생')).toBeInTheDocument();
      });

      fireEvent.change(screen.getByLabelText('이메일'), {
        target: { value: 'new@example.com' },
      });

      expect(screen.queryByText('에러 발생')).not.toBeInTheDocument();
    });
  });
});
