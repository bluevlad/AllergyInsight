/**
 * Login Page - Email + Password & Google OAuth (ID 토큰 방식)
 */
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../shared/contexts/AuthContext';

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

const LoginPage = () => {
  const navigate = useNavigate();
  const { verifyGoogleToken, loginEmail, sendVerificationCode, registerEmail, getDefaultApp } = useAuth();
  const googleBtnRef = useRef(null);

  const [mode, setMode] = useState('login'); // 'login', 'register', 'verify'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [message, setMessage] = useState('');

  const [formData, setFormData] = useState({
    email: '',
    password: '',
    passwordConfirm: '',
    verificationCode: '',
  });

  // Google Identity Services 초기화 (스크립트 로드 대기)
  useEffect(() => {
    if (!GOOGLE_CLIENT_ID) return;

    const initGoogleBtn = () => {
      if (!window.google?.accounts?.id || !googleBtnRef.current) return;
      window.google.accounts.id.initialize({
        client_id: GOOGLE_CLIENT_ID,
        callback: handleGoogleCredential,
      });
      window.google.accounts.id.renderButton(
        googleBtnRef.current,
        { theme: 'outline', size: 'large', width: '100%', text: 'continue_with', locale: 'ko' }
      );
    };

    if (window.google?.accounts?.id) {
      initGoogleBtn();
    } else {
      // GIS 스크립트가 아직 로드되지 않은 경우 대기
      const interval = setInterval(() => {
        if (window.google?.accounts?.id) {
          clearInterval(interval);
          initGoogleBtn();
        }
      }, 100);
      return () => clearInterval(interval);
    }
  }, [mode]);

  const handleGoogleCredential = async (response) => {
    setLoading(true);
    setError('');
    try {
      const result = await verifyGoogleToken(response.credential);
      navigate(getRedirectPath(result.user?.role));
    } catch (err) {
      const detail = err.response?.data?.detail || 'Google 로그인에 실패했습니다.';
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setError('');
  };

  // Role-based redirect
  const PROFESSIONAL_ROLES = ['doctor', 'nurse', 'lab_tech', 'hospital_admin', 'admin', 'super_admin'];
  const ADMIN_ROLES = ['admin', 'super_admin'];

  const getRedirectPath = (role) => {
    if (ADMIN_ROLES.includes(role)) return '/admin';
    if (PROFESSIONAL_ROLES.includes(role)) return '/pro';
    return '/app';
  };

  // Step 1: Send verification code
  const handleSendCode = async (e) => {
    e.preventDefault();
    if (!formData.email) return;

    setLoading(true);
    setError('');
    try {
      await sendVerificationCode({ email: formData.email });
      setMode('verify');
      setMessage('인증 코드가 이메일로 발송되었습니다.');
    } catch (err) {
      const detail = err.response?.data?.detail || '인증 코드 발송에 실패했습니다.';
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  // Step 2: Verify code + set password
  const handleRegister = async (e) => {
    e.preventDefault();
    if (formData.password !== formData.passwordConfirm) {
      setError('비밀번호가 일치하지 않습니다.');
      return;
    }
    if (formData.password.length < 4) {
      setError('비밀번호는 4자 이상이어야 합니다.');
      return;
    }

    setLoading(true);
    setError('');
    try {
      const result = await registerEmail({
        email: formData.email,
        code: formData.verificationCode,
        password: formData.password,
      });
      navigate(getRedirectPath(result.user?.role));
    } catch (err) {
      const detail = err.response?.data?.detail || '회원가입에 실패했습니다.';
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  // Login with email + password
  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');
    try {
      const result = await loginEmail({
        email: formData.email,
        password: formData.password,
      });
      navigate(getRedirectPath(result.user?.role));
    } catch (err) {
      const detail = err.response?.data?.detail || '로그인에 실패했습니다.';
      setError(detail);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>AllergyInsight</h1>
        <p className="subtitle">알러지 검사 결과 조회 서비스</p>

        {/* Mode Tabs */}
        {mode !== 'verify' && (
          <div className="mode-tabs">
            <button
              className={`mode-tab ${mode === 'login' ? 'active' : ''}`}
              onClick={() => { setMode('login'); setError(''); setMessage(''); }}
            >
              로그인
            </button>
            <button
              className={`mode-tab ${mode === 'register' ? 'active' : ''}`}
              onClick={() => { setMode('register'); setError(''); setMessage(''); }}
            >
              회원가입
            </button>
          </div>
        )}

        {/* Google Login (ID 토큰 방식) */}
        {mode !== 'verify' && (
          <>
            <div ref={googleBtnRef} className="google-btn-wrapper" />

            <div className="divider">
              <span>또는</span>
            </div>
          </>
        )}

        {/* Login Form */}
        {mode === 'login' && (
          <form onSubmit={handleLogin}>
            <div className="form-group">
              <label>이메일</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="your@email.com"
                required
              />
            </div>
            <div className="form-group">
              <label>비밀번호</label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="비밀번호"
                required
              />
            </div>
            {error && <div className="error-message">{error}</div>}
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? '처리 중...' : '로그인'}
            </button>

            {/* 테스트 계정 안내 */}
            <div className="test-account-box">
              <div className="test-account-header">
                <span className="test-badge">TEST</span>
                <span>테스트 계정</span>
              </div>
              <div className="test-account-content">
                <div className="test-row">
                  <span className="test-label">이메일:</span>
                  <span className="test-value">kincs@unmong.com</span>
                </div>
                <div className="test-row">
                  <span className="test-label">비밀번호:</span>
                  <span className="test-value pw">123456</span>
                </div>
              </div>
              <button
                type="button"
                className="btn-fill-test"
                onClick={() => {
                  setFormData(prev => ({
                    ...prev,
                    email: 'kincs@unmong.com',
                    password: '123456',
                  }));
                }}
              >
                테스트 계정으로 채우기
              </button>
            </div>
          </form>
        )}

        {/* Register Step 1: Email input */}
        {mode === 'register' && (
          <form onSubmit={handleSendCode}>
            <div className="form-group">
              <label>이메일</label>
              <input
                type="email"
                name="email"
                value={formData.email}
                onChange={handleChange}
                placeholder="your@email.com"
                required
              />
            </div>
            {error && <div className="error-message">{error}</div>}
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? '발송 중...' : '인증 코드 받기'}
            </button>
            <p className="info-text">
              입력한 이메일로 6자리 인증 코드가 발송됩니다.
            </p>
          </form>
        )}

        {/* Register Step 2: Verify + Password */}
        {mode === 'verify' && (
          <form onSubmit={handleRegister}>
            {message && <div className="success-message">{message}</div>}
            <div className="form-group">
              <label>이메일</label>
              <input
                type="email"
                value={formData.email}
                disabled
                style={{ background: '#f5f5f5' }}
              />
            </div>
            <div className="form-group">
              <label>인증 코드</label>
              <input
                type="text"
                name="verificationCode"
                value={formData.verificationCode}
                onChange={handleChange}
                placeholder="6자리 인증 코드"
                maxLength={6}
                required
              />
            </div>
            <div className="form-group">
              <label>비밀번호</label>
              <input
                type="password"
                name="password"
                value={formData.password}
                onChange={handleChange}
                placeholder="비밀번호 (4자 이상)"
                required
              />
            </div>
            <div className="form-group">
              <label>비밀번호 확인</label>
              <input
                type="password"
                name="passwordConfirm"
                value={formData.passwordConfirm}
                onChange={handleChange}
                placeholder="비밀번호 재입력"
                required
              />
            </div>
            {error && <div className="error-message">{error}</div>}
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? '처리 중...' : '회원가입 완료'}
            </button>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => { setMode('register'); setMessage(''); setError(''); }}
            >
              뒤로
            </button>
          </form>
        )}
      </div>

      <style>{`
        .login-container {
          display: flex;
          justify-content: center;
          align-items: center;
          min-height: 100vh;
          padding: 1rem;
          background: #f8f9fa;
        }

        .login-card {
          background: white;
          border-radius: 12px;
          box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
          padding: 2rem;
          width: 100%;
          max-width: 400px;
        }

        .login-card h1 {
          text-align: center;
          margin: 0;
          color: #2196F3;
          font-size: 1.75rem;
        }

        .subtitle {
          text-align: center;
          color: #666;
          margin: 0.5rem 0 1.5rem;
          font-size: 0.9rem;
        }

        .mode-tabs {
          display: flex;
          border: 1px solid #ddd;
          border-radius: 8px;
          overflow: hidden;
          margin-bottom: 1.5rem;
        }

        .mode-tab {
          flex: 1;
          padding: 0.75rem;
          border: none;
          background: #f5f5f5;
          cursor: pointer;
          font-size: 0.95rem;
          transition: all 0.2s;
        }

        .mode-tab.active {
          background: #2196F3;
          color: white;
        }

        .btn {
          width: 100%;
          padding: 0.75rem 1rem;
          border: none;
          border-radius: 8px;
          font-size: 1rem;
          cursor: pointer;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.5rem;
          transition: all 0.2s;
        }

        .google-btn-wrapper {
          display: flex;
          justify-content: center;
        }

        .btn-primary {
          background: #2196F3;
          color: white;
          margin-top: 1rem;
        }

        .btn-primary:hover:not(:disabled) {
          background: #1976D2;
        }

        .btn-primary:disabled {
          background: #90CAF9;
          cursor: not-allowed;
        }

        .btn-secondary {
          background: white;
          color: #666;
          border: 1px solid #ddd;
          margin-top: 0.5rem;
        }

        .btn-secondary:hover {
          background: #f5f5f5;
        }

        .divider {
          display: flex;
          align-items: center;
          margin: 1.5rem 0;
          color: #999;
          font-size: 0.85rem;
        }

        .divider::before,
        .divider::after {
          content: '';
          flex: 1;
          border-bottom: 1px solid #ddd;
        }

        .divider span {
          padding: 0 1rem;
        }

        .form-group {
          margin-bottom: 1rem;
        }

        .form-group label {
          display: block;
          margin-bottom: 0.5rem;
          font-size: 0.9rem;
          color: #333;
        }

        .form-group input {
          width: 100%;
          padding: 0.75rem;
          border: 1px solid #ddd;
          border-radius: 8px;
          font-size: 1rem;
          box-sizing: border-box;
        }

        .form-group input:focus {
          outline: none;
          border-color: #2196F3;
          box-shadow: 0 0 0 2px rgba(33, 150, 243, 0.1);
        }

        .error-message {
          color: #d32f2f;
          background: #ffebee;
          padding: 0.75rem;
          border-radius: 6px;
          margin-top: 0.5rem;
          font-size: 0.9rem;
        }

        .success-message {
          color: #2e7d32;
          background: #e8f5e9;
          padding: 0.75rem;
          border-radius: 6px;
          margin-bottom: 1rem;
          font-size: 0.9rem;
        }

        .info-text {
          margin-top: 1rem;
          padding: 0.75rem;
          background: #f5f5f5;
          border-radius: 6px;
          font-size: 0.8rem;
          color: #666;
          text-align: center;
        }

        .test-account-box {
          margin-top: 1.5rem;
          padding: 1rem;
          background: linear-gradient(135deg, #fff8e1 0%, #ffecb3 100%);
          border: 1px solid #ffc107;
          border-radius: 8px;
        }

        .test-account-header {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          margin-bottom: 0.75rem;
          font-weight: 600;
          color: #f57c00;
        }

        .test-badge {
          background: #ff9800;
          color: white;
          padding: 0.2rem 0.5rem;
          border-radius: 4px;
          font-size: 0.7rem;
          font-weight: bold;
        }

        .test-account-content {
          background: white;
          border-radius: 6px;
          padding: 0.75rem;
          margin-bottom: 0.75rem;
        }

        .test-row {
          display: flex;
          justify-content: space-between;
          padding: 0.25rem 0;
          font-size: 0.9rem;
        }

        .test-label {
          color: #666;
        }

        .test-value {
          font-weight: 500;
          color: #333;
        }

        .test-value.pw {
          font-family: monospace;
          font-size: 1rem;
          color: #d32f2f;
          letter-spacing: 0.1rem;
        }

        .btn-fill-test {
          width: 100%;
          padding: 0.6rem;
          background: #ff9800;
          color: white;
          border: none;
          border-radius: 6px;
          font-size: 0.85rem;
          cursor: pointer;
          transition: background 0.2s;
        }

        .btn-fill-test:hover {
          background: #f57c00;
        }
      `}</style>
    </div>
  );
};

export default LoginPage;
