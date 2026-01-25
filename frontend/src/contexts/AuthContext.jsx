/**
 * Authentication Context
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

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null);
  const [loading, setLoading] = useState(true);
  const [accessPin, setAccessPin] = useState(null);

  // Check if token exists and fetch user
  const checkAuth = useCallback(async () => {
    const token = localStorage.getItem('access_token');
    if (!token) {
      setLoading(false);
      return;
    }

    try {
      const response = await authApi.getMe();
      setUser(response);
    } catch (error) {
      console.error('Auth check failed:', error);
      localStorage.removeItem('access_token');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // Google login redirect
  const loginWithGoogle = () => {
    const backendUrl = import.meta.env.VITE_API_URL || '';
    window.location.href = `${backendUrl}/api/auth/google/login`;
  };

  // Simple registration
  const registerSimple = async (data) => {
    try {
      const response = await authApi.registerSimple(data);
      localStorage.setItem('access_token', response.access_token);
      setUser(response.user);
      setAccessPin(response.access_pin);
      return { success: true, accessPin: response.access_pin };
    } catch (error) {
      console.error('Registration failed:', error);
      throw error;
    }
  };

  // Simple login
  const loginSimple = async (data) => {
    try {
      const response = await authApi.loginSimple(data);
      localStorage.setItem('access_token', response.access_token);
      setUser(response.user);
      return { success: true };
    } catch (error) {
      console.error('Login failed:', error);
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
    await checkAuth();
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

  // Phase 2: Hospital staff role check
  const hospitalStaffRoles = ['doctor', 'nurse', 'lab_tech', 'hospital_admin'];
  const isHospitalStaff = user && hospitalStaffRoles.includes(user.role);

  const value = {
    user,
    loading,
    accessPin,
    isAuthenticated: !!user,
    isAdmin: user?.role === 'admin' || user?.role === 'super_admin',
    isHospitalStaff,
    loginWithGoogle,
    registerSimple,
    loginSimple,
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
