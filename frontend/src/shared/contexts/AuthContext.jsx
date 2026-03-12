/**
 * Shared Authentication Context
 *
 * Professional과 Consumer 앱에서 공유하는 인증 컨텍스트입니다.
 */
import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { authApi } from '../services/api';

const AuthContext = createContext(null);

export const useAuth = () => {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within AuthProvider');
  }
  return context;
};

// 역할 정의
const PROFESSIONAL_ROLES = ['doctor', 'nurse', 'lab_tech', 'hospital_admin', 'admin', 'super_admin'];
const ADMIN_ROLES = ['admin', 'super_admin'];
const SUPER_ADMIN_ROLES = ['super_admin'];

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [accessPin, setAccessPin] = useState(null);

  // Check if token exists and fetch user
  const checkAuth = useCallback(async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setLoading(false);
      return null;
    }

    try {
      const response = await authApi.getMe();
      setUser(response);
      return response; // 사용자 정보 반환
    } catch (error) {
      console.error('Auth check failed:', error);
      localStorage.removeItem('access_token');
      return null;
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // Google ID 토큰 검증 후 로그인
  const verifyGoogleToken = async (credential) => {
    try {
      const response = await authApi.verifyGoogleToken(credential);
      localStorage.setItem('access_token', response.access_token);
      setUser(response.user);
      return { success: true, user: response.user };
    } catch (error) {
      throw error;
    }
  };

  // Email verification code
  const sendVerificationCode = async (data) => {
    try {
      const response = await authApi.sendVerificationCode(data);
      return { success: true, message: response.message };
    } catch (error) {
      throw error;
    }
  };

  // Email registration (verify + set password)
  const registerEmail = async (data) => {
    try {
      const response = await authApi.registerEmail(data);
      localStorage.setItem('access_token', response.access_token);
      setUser(response.user);
      return { success: true, user: response.user };
    } catch (error) {
      throw error;
    }
  };

  // Email + password login
  const loginEmail = async (data) => {
    try {
      const response = await authApi.loginEmail(data);
      localStorage.setItem('access_token', response.access_token);
      setUser(response.user);
      return { success: true, user: response.user };
    } catch (error) {
      throw error;
    }
  };

  // Legacy: Simple registration
  const registerSimple = async (data) => {
    try {
      const response = await authApi.registerSimple(data);
      localStorage.setItem('access_token', response.access_token);
      setUser(response.user);
      setAccessPin(response.access_pin);
      return { success: true, accessPin: response.access_pin };
    } catch (error) {
      throw error;
    }
  };

  // Legacy: Simple login
  const loginSimple = async (data) => {
    try {
      const response = await authApi.loginSimple(data);
      localStorage.setItem('access_token', response.access_token);
      setUser(response.user);
      return { success: true, user: response.user };
    } catch (error) {
      throw error;
    }
  };

  // Admin login (name + PIN only)
  const loginAdmin = async (data) => {
    try {
      const response = await authApi.loginAdmin(data);
      localStorage.setItem('access_token', response.access_token);
      setUser(response.user);
      return { success: true, user: response.user };
    } catch (error) {
      console.error('Admin login failed:', error);
      throw error;
    }
  };

  // Register kit (for logged-in users)
  const registerKit = async (serialNumber, pin) => {
    try {
      const response = await authApi.registerKit(serialNumber, pin);
      return { success: true, diagnosis: response };
    } catch (error) {
      console.error('Kit registration failed:', error);
      throw error;
    }
  };

  // Handle OAuth callback
  const handleOAuthCallback = async (token) => {
    localStorage.setItem('access_token', token);
    const user = await checkAuth();
    return { user }; // 사용자 정보 반환
  };

  // Logout
  const logout = async () => {
    try {
      await authApi.logout();
    } catch (error) {
      console.error('Logout error:', error);
    } finally {
      localStorage.removeItem('access_token');
      setUser(null);
      setAccessPin(null);
    }
  };

  // Clear access PIN display
  const clearAccessPin = () => {
    setAccessPin(null);
  };

  // 역할 기반 체크
  const isAdmin = user && ADMIN_ROLES.includes(user.role);
  const isSuperAdmin = user && SUPER_ADMIN_ROLES.includes(user.role);
  const isProfessional = user && PROFESSIONAL_ROLES.includes(user.role);
  const isHospitalStaff = user && ['doctor', 'nurse', 'lab_tech', 'hospital_admin'].includes(user.role);
  const isConsumer = user && !isProfessional;

  // 접근 가능한 앱 결정
  const getDefaultApp = () => {
    if (!user) return 'login';
    if (isSuperAdmin || isAdmin) return 'admin';
    if (isProfessional) return 'professional';
    return 'consumer';
  };

  const value = {
    user,
    loading,
    accessPin,
    isAuthenticated: !!user,
    isAdmin,
    isSuperAdmin,
    isProfessional,
    isHospitalStaff,
    isConsumer,
    getDefaultApp,
    verifyGoogleToken,
    sendVerificationCode,
    registerEmail,
    loginEmail,
    registerSimple,
    loginSimple,
    loginAdmin,
    registerKit,
    handleOAuthCallback,
    logout,
    clearAccessPin,
    checkAuth,
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
};

export default AuthContext;
