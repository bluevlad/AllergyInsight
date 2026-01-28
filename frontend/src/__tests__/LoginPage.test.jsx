/**
 * LoginPage 테스트
 *
 * 로그인/회원가입 페이지의 기능을 테스트합니다.
 */
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';
import LoginPage from '../pages/LoginPage';
import { AuthProvider } from '../shared/contexts/AuthContext';
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

    it('로그인 모드에서 접속 PIN 입력 필드 표시', async () => {
      renderLoginPage();

      await waitFor(() => {
        expect(screen.getByLabelText('접속 PIN')).toBeInTheDocument();
      });
    });

    it('회원가입 모드로 전환 시 시리얼번호/PIN 필드 표시', async () => {
      renderLoginPage();

      await waitFor(() => {
        expect(screen.getByText('AllergyInsight')).toBeInTheDocument();
      });

      // 회원가입 탭 클릭 - mode-tab 클래스를 가진 버튼 찾기
      const tabButtons = screen.getAllByRole('button');
      const registerTab = tabButtons.find(btn =>
        btn.textContent === '회원가입' && btn.classList.contains('mode-tab')
      );
      fireEvent.click(registerTab);

      expect(screen.getByLabelText('검사키트 시리얼번호')).toBeInTheDocument();
      expect(screen.getByLabelText('검사키트 PIN')).toBeInTheDocument();
    });

    it('전화번호/생년월일 토글 작동', async () => {
      renderLoginPage();

      await waitFor(() => {
        expect(screen.getByLabelText('전화번호')).toBeInTheDocument();
      });

      // 생년월일 버튼 클릭
      const toggleButtons = screen.getAllByRole('button');
      const birthdateBtn = toggleButtons.find(btn =>
        btn.textContent === '생년월일' && btn.classList.contains('toggle-btn')
      );
      fireEvent.click(birthdateBtn);

      expect(screen.getByLabelText('생년월일')).toBeInTheDocument();
      expect(screen.queryByLabelText('전화번호')).not.toBeInTheDocument();

      // 다시 전화번호로 전환
      const phoneBtn = toggleButtons.find(btn =>
        btn.textContent === '전화번호' && btn.classList.contains('toggle-btn')
      );
      fireEvent.click(phoneBtn);

      expect(screen.getByLabelText('전화번호')).toBeInTheDocument();
    });
  });

  describe('테스트 계정 기능', () => {
    it('테스트 계정 정보가 표시됨', async () => {
      renderLoginPage();

      await waitFor(() => {
        expect(screen.getByText('테스트 계정')).toBeInTheDocument();
      });
      expect(screen.getByText('김철수')).toBeInTheDocument();
      expect(screen.getByText('010-9999-8888')).toBeInTheDocument();
      expect(screen.getByText('715302')).toBeInTheDocument();
    });

    it('테스트 계정으로 채우기 버튼 작동', async () => {
      renderLoginPage();

      await waitFor(() => {
        expect(screen.getByText('테스트 계정으로 채우기')).toBeInTheDocument();
      });

      fireEvent.click(screen.getByText('테스트 계정으로 채우기'));

      expect(screen.getByLabelText('이름')).toHaveValue('김철수');
      expect(screen.getByLabelText('전화번호')).toHaveValue('010-9999-8888');
      expect(screen.getByLabelText('접속 PIN')).toHaveValue('715302');
    });
  });

  describe('로그인 기능', () => {
    it('로그인 폼 제출 시 API 호출', async () => {
      authApi.loginSimple.mockResolvedValue({
        access_token: 'test-token',
        user: { id: 1, name: '테스트유저', role: 'user' },
      });
      authApi.getMe.mockResolvedValue({
        id: 1,
        name: '테스트유저',
        role: 'user',
      });

      renderLoginPage();

      await waitFor(() => {
        expect(screen.getByLabelText('이름')).toBeInTheDocument();
      });

      // 폼 입력
      fireEvent.change(screen.getByLabelText('이름'), {
        target: { value: '테스트유저' },
      });
      fireEvent.change(screen.getByLabelText('전화번호'), {
        target: { value: '010-1234-5678' },
      });
      fireEvent.change(screen.getByLabelText('접속 PIN'), {
        target: { value: '123456' },
      });

      // 폼 제출
      const form = screen.getByLabelText('이름').closest('form');
      fireEvent.submit(form);

      await waitFor(() => {
        expect(authApi.loginSimple).toHaveBeenCalledWith({
          name: '테스트유저',
          phone: '010-1234-5678',
          accessPin: '123456',
        });
      });
    });

    it('로그인 실패 시 에러 메시지 표시', async () => {
      authApi.loginSimple.mockRejectedValue({
        response: { data: { detail: 'PIN이 일치하지 않습니다.' } },
      });

      renderLoginPage();

      await waitFor(() => {
        expect(screen.getByLabelText('이름')).toBeInTheDocument();
      });

      // 폼 입력
      fireEvent.change(screen.getByLabelText('이름'), {
        target: { value: '테스트유저' },
      });
      fireEvent.change(screen.getByLabelText('전화번호'), {
        target: { value: '010-1234-5678' },
      });
      fireEvent.change(screen.getByLabelText('접속 PIN'), {
        target: { value: 'wrong' },
      });

      // 폼 제출
      const form = screen.getByLabelText('이름').closest('form');
      fireEvent.submit(form);

      await waitFor(() => {
        expect(screen.getByText('PIN이 일치하지 않습니다.')).toBeInTheDocument();
      });
    });
  });

  describe('회원가입 기능', () => {
    it('회원가입 폼 제출 시 API 호출', async () => {
      authApi.registerSimple.mockResolvedValue({
        access_token: 'test-token',
        user: { id: 1, name: '신규유저', role: 'user' },
        access_pin: '987654',
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

      await waitFor(() => {
        expect(screen.getByLabelText('검사키트 시리얼번호')).toBeInTheDocument();
      });

      // 폼 입력
      fireEvent.change(screen.getByLabelText('이름'), {
        target: { value: '신규유저' },
      });
      fireEvent.change(screen.getByLabelText('전화번호'), {
        target: { value: '010-5555-5555' },
      });
      fireEvent.change(screen.getByLabelText('검사키트 시리얼번호'), {
        target: { value: 'SGT-2024-TEST-0001' },
      });
      fireEvent.change(screen.getByLabelText('검사키트 PIN'), {
        target: { value: '111111' },
      });

      // 폼 제출
      const form = screen.getByLabelText('이름').closest('form');
      fireEvent.submit(form);

      await waitFor(() => {
        expect(authApi.registerSimple).toHaveBeenCalled();
      });
    });

    it('회원가입 실패 시 에러 메시지 표시', async () => {
      authApi.registerSimple.mockRejectedValue({
        response: { data: { detail: '이미 등록된 키트입니다.' } },
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

      await waitFor(() => {
        expect(screen.getByLabelText('검사키트 시리얼번호')).toBeInTheDocument();
      });

      // 폼 입력
      fireEvent.change(screen.getByLabelText('이름'), {
        target: { value: '신규유저' },
      });
      fireEvent.change(screen.getByLabelText('전화번호'), {
        target: { value: '010-5555-5555' },
      });
      fireEvent.change(screen.getByLabelText('검사키트 시리얼번호'), {
        target: { value: 'SGT-2024-TEST-0001' },
      });
      fireEvent.change(screen.getByLabelText('검사키트 PIN'), {
        target: { value: '111111' },
      });

      // 폼 제출
      const form = screen.getByLabelText('이름').closest('form');
      fireEvent.submit(form);

      await waitFor(() => {
        expect(screen.getByText('이미 등록된 키트입니다.')).toBeInTheDocument();
      });
    });
  });

  describe('폼 입력', () => {
    it('입력 필드 변경 시 에러 메시지 초기화', async () => {
      authApi.loginSimple.mockRejectedValue({
        response: { data: { detail: '에러 발생' } },
      });

      renderLoginPage();

      await waitFor(() => {
        expect(screen.getByLabelText('이름')).toBeInTheDocument();
      });

      // 폼 입력 및 제출로 에러 발생
      fireEvent.change(screen.getByLabelText('이름'), {
        target: { value: '테스트' },
      });
      fireEvent.change(screen.getByLabelText('전화번호'), {
        target: { value: '010-1234-5678' },
      });
      fireEvent.change(screen.getByLabelText('접속 PIN'), {
        target: { value: '123456' },
      });

      // 폼 제출
      const form = screen.getByLabelText('이름').closest('form');
      fireEvent.submit(form);

      await waitFor(() => {
        expect(screen.getByText('에러 발생')).toBeInTheDocument();
      });

      // 입력 필드 변경 시 에러 메시지가 사라짐
      fireEvent.change(screen.getByLabelText('이름'), {
        target: { value: '새이름' },
      });

      expect(screen.queryByText('에러 발생')).not.toBeInTheDocument();
    });
  });
});
