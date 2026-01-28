/**
 * 테스트 유틸리티
 *
 * 테스트에서 공통으로 사용하는 유틸리티 함수와 wrapper를 정의합니다.
 */
import React from 'react';
import { render } from '@testing-library/react';
import { BrowserRouter, MemoryRouter } from 'react-router-dom';

/**
 * AuthProvider mock
 * 테스트에서 인증 상태를 제어할 수 있도록 합니다.
 */
const MockAuthContext = React.createContext(null);

export const MockAuthProvider = ({
  children,
  user = null,
  loading = false,
  isAuthenticated = false,
  ...props
}) => {
  const value = {
    user,
    loading,
    accessPin: null,
    isAuthenticated,
    isAdmin: user?.role === 'admin' || user?.role === 'super_admin',
    isProfessional: ['doctor', 'nurse', 'lab_tech', 'hospital_admin', 'admin'].includes(user?.role),
    isHospitalStaff: ['doctor', 'nurse', 'lab_tech', 'hospital_admin'].includes(user?.role),
    isConsumer: user && !['doctor', 'nurse', 'lab_tech', 'hospital_admin', 'admin'].includes(user?.role),
    getDefaultApp: () => user ? (user.role === 'user' ? 'consumer' : 'professional') : 'login',
    loginWithGoogle: jest.fn(),
    registerSimple: jest.fn(),
    loginSimple: jest.fn(),
    registerKit: jest.fn(),
    handleOAuthCallback: jest.fn(),
    logout: jest.fn(),
    clearAccessPin: jest.fn(),
    checkAuth: jest.fn(),
    ...props,
  };

  return (
    <MockAuthContext.Provider value={value}>
      {children}
    </MockAuthContext.Provider>
  );
};

/**
 * 모든 Provider를 포함한 wrapper
 */
const AllTheProviders = ({ children }) => {
  return (
    <BrowserRouter>
      <MockAuthProvider>
        {children}
      </MockAuthProvider>
    </BrowserRouter>
  );
};

/**
 * Custom render with providers
 * 모든 Provider를 자동으로 감싸서 렌더링합니다.
 */
const customRender = (ui, options) =>
  render(ui, { wrapper: AllTheProviders, ...options });

/**
 * Render with custom auth state
 * 특정 인증 상태로 렌더링합니다.
 */
export const renderWithAuth = (ui, authProps = {}, options = {}) => {
  const Wrapper = ({ children }) => (
    <BrowserRouter>
      <MockAuthProvider {...authProps}>
        {children}
      </MockAuthProvider>
    </BrowserRouter>
  );

  return render(ui, { wrapper: Wrapper, ...options });
};

/**
 * Render with custom route
 * 특정 경로에서 렌더링합니다.
 */
export const renderWithRouter = (ui, { route = '/' } = {}) => {
  window.history.pushState({}, 'Test page', route);
  return render(ui, { wrapper: BrowserRouter });
};

/**
 * Render with MemoryRouter
 * 특정 경로 히스토리와 함께 렌더링합니다.
 */
export const renderWithMemoryRouter = (ui, { initialEntries = ['/'] } = {}) => {
  return render(
    <MemoryRouter initialEntries={initialEntries}>
      {ui}
    </MemoryRouter>
  );
};

// re-export everything
export * from '@testing-library/react';
export { customRender as render };

/**
 * Mock user data
 */
export const mockUsers = {
  patient: {
    id: 1,
    name: '테스트환자',
    phone: '010-1234-5678',
    role: 'user',
    created_at: '2025-01-01T00:00:00Z',
  },
  doctor: {
    id: 2,
    name: '테스트의사',
    phone: '010-8888-8888',
    role: 'doctor',
    created_at: '2025-01-01T00:00:00Z',
  },
  admin: {
    id: 3,
    name: '관리자',
    phone: '010-9999-9999',
    role: 'admin',
    created_at: '2025-01-01T00:00:00Z',
  },
};

/**
 * Mock diagnosis data
 */
export const mockDiagnosis = {
  id: 1,
  results: {
    peanut: 4,
    milk: 2,
    egg: 1,
    wheat: 0,
    shrimp: 3,
  },
  diagnosis_date: '2025-01-01T00:00:00Z',
  kit_serial: 'TEST-KIT-001',
};

/**
 * Wait for loading to finish
 */
export const waitForLoadingToFinish = () =>
  new Promise((resolve) => setTimeout(resolve, 0));
