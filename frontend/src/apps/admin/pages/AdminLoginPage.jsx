/**
 * Admin Login Page - Purple themed admin-specific login
 *
 * Provides Google OAuth (ID 토큰 방식) and email + password login for administrators.
 * Redirects to /admin on success, shows error if not super_admin.
 */
import React, { useState, useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../shared/contexts/AuthContext';

const GOOGLE_CLIENT_ID = import.meta.env.VITE_GOOGLE_CLIENT_ID;

const AdminLoginPage = () => {
  const navigate = useNavigate();
  const { verifyGoogleToken, loginEmail, user, isSuperAdmin, isAdmin } = useAuth();
  const googleBtnRef = useRef(null);

  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');
  const [formData, setFormData] = useState({
    email: '',
    password: '',
  });

  // If already logged in, check role
  if (user) {
    if (isSuperAdmin || isAdmin) {
      navigate('/admin', { replace: true });
      return null;
    }
    return (
      <div className="admin-login-container">
        <div className="admin-login-card">
          <div className="admin-login-icon">
            <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#d32f2f" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <circle cx="12" cy="12" r="10"/>
              <line x1="15" y1="9" x2="9" y2="15"/>
              <line x1="9" y1="9" x2="15" y2="15"/>
            </svg>
          </div>
          <h1 className="admin-login-title">AllergyInsight 관리자</h1>
          <div className="admin-login-error">
            관리자 권한이 필요합니다
          </div>
          <p className="admin-login-subtext">
            현재 로그인된 계정({user.name || user.email})은 관리자 권한이 없습니다.
          </p>
          <button
            className="admin-btn admin-btn-secondary"
            onClick={() => {
              localStorage.removeItem('access_token');
              window.location.reload();
            }}
          >
            다른 계정으로 로그인
          </button>
        </div>
        <style>{adminStyles}</style>
      </div>
    );
  }

  // Google Identity Services 초기화
  useEffect(() => {
    if (!GOOGLE_CLIENT_ID || !window.google?.accounts) return;

    window.google.accounts.id.initialize({
      client_id: GOOGLE_CLIENT_ID,
      callback: handleGoogleCredential,
    });

    if (googleBtnRef.current) {
      window.google.accounts.id.renderButton(
        googleBtnRef.current,
        { theme: 'outline', size: 'large', width: '100%', text: 'signin_with', locale: 'ko' }
      );
    }
  }, []);

  const handleGoogleCredential = async (response) => {
    setLoading(true);
    setError('');
    try {
      const result = await verifyGoogleToken(response.credential);
      const role = result.user?.role;
      if (role === 'super_admin' || role === 'admin') {
        navigate('/admin', { replace: true });
      } else {
        setError('관리자 권한이 필요합니다');
      }
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

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const result = await loginEmail({
        email: formData.email,
        password: formData.password,
      });

      const role = result.user?.role;
      if (role === 'super_admin' || role === 'admin') {
        navigate('/admin', { replace: true });
      } else {
        setError('관리자 권한이 필요합니다');
      }
    } catch (err) {
      const message = err.response?.data?.detail || '로그인에 실패했습니다.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="admin-login-container">
      <div className="admin-login-card">
        <div className="admin-login-icon">
          <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
            <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/>
          </svg>
        </div>
        <h1 className="admin-login-title">AllergyInsight 관리자</h1>
        <p className="admin-login-subtitle">관리자 전용 로그인</p>

        {/* Google OAuth (ID 토큰 방식) */}
        <div ref={googleBtnRef} className="admin-google-btn-wrapper" />

        <div className="admin-login-divider">
          <span>또는</span>
        </div>

        {/* Email + Password form */}
        <form onSubmit={handleLogin}>
          <div className="admin-form-group">
            <label>이메일</label>
            <input
              type="email"
              name="email"
              value={formData.email}
              onChange={handleChange}
              placeholder="admin@email.com"
              required
            />
          </div>

          <div className="admin-form-group">
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

          {error && <div className="admin-login-error">{error}</div>}

          <button
            type="submit"
            className="admin-btn admin-btn-primary"
            disabled={loading}
          >
            {loading ? '인증 중...' : '관리자 로그인'}
          </button>
        </form>

        <div className="admin-login-footer">
          <a href="/login" className="admin-login-link">
            일반 사용자 로그인으로 돌아가기
          </a>
        </div>
      </div>

      <style>{adminStyles}</style>
    </div>
  );
};

const adminStyles = `
  .admin-login-container {
    display: flex;
    justify-content: center;
    align-items: center;
    min-height: 100vh;
    background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%);
    padding: 1rem;
  }

  .admin-login-card {
    background: white;
    border-radius: 16px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    padding: 2.5rem;
    width: 100%;
    max-width: 420px;
    text-align: center;
  }

  .admin-login-icon {
    width: 72px;
    height: 72px;
    background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%);
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    margin: 0 auto 1.25rem;
  }

  .admin-login-title {
    margin: 0;
    color: #2c2c2c;
    font-size: 1.6rem;
    font-weight: 700;
  }

  .admin-login-subtitle {
    color: #8e44ad;
    margin: 0.4rem 0 1.75rem;
    font-size: 0.9rem;
    font-weight: 500;
  }

  .admin-btn {
    width: 100%;
    padding: 0.8rem 1rem;
    border: none;
    border-radius: 8px;
    font-size: 1rem;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 0.5rem;
    transition: all 0.2s;
    font-weight: 500;
  }

  .admin-google-btn-wrapper {
    display: flex;
    justify-content: center;
  }

  .admin-btn-primary {
    background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%);
    color: white;
    margin-top: 0.5rem;
  }

  .admin-btn-primary:hover:not(:disabled) {
    background: linear-gradient(135deg, #8e44ad 0%, #7d3c98 100%);
    box-shadow: 0 2px 8px rgba(142, 68, 173, 0.4);
  }

  .admin-btn-primary:disabled {
    opacity: 0.6;
    cursor: not-allowed;
  }

  .admin-btn-secondary {
    background: #f5f5f5;
    color: #333;
    margin-top: 1rem;
  }

  .admin-btn-secondary:hover {
    background: #e8e8e8;
  }

  .admin-login-divider {
    display: flex;
    align-items: center;
    margin: 1.5rem 0;
    color: #aaa;
    font-size: 0.85rem;
  }

  .admin-login-divider::before,
  .admin-login-divider::after {
    content: '';
    flex: 1;
    border-bottom: 1px solid #e0e0e0;
  }

  .admin-login-divider span {
    padding: 0 1rem;
  }

  .admin-form-group {
    margin-bottom: 1rem;
    text-align: left;
  }

  .admin-form-group label {
    display: block;
    margin-bottom: 0.4rem;
    font-size: 0.9rem;
    color: #555;
    font-weight: 500;
  }

  .admin-form-group input {
    width: 100%;
    padding: 0.75rem;
    border: 1px solid #ddd;
    border-radius: 8px;
    font-size: 1rem;
    box-sizing: border-box;
    transition: border-color 0.2s, box-shadow 0.2s;
  }

  .admin-form-group input:focus {
    outline: none;
    border-color: #9b59b6;
    box-shadow: 0 0 0 3px rgba(155, 89, 182, 0.15);
  }

  .admin-login-error {
    color: #d32f2f;
    background: #ffebee;
    padding: 0.75rem;
    border-radius: 8px;
    margin: 0.75rem 0;
    font-size: 0.9rem;
    font-weight: 500;
  }

  .admin-login-subtext {
    color: #777;
    font-size: 0.85rem;
    margin: 0.5rem 0 0.5rem;
  }

  .admin-login-footer {
    margin-top: 1.5rem;
    padding-top: 1rem;
    border-top: 1px solid #eee;
  }

  .admin-login-link {
    color: #9b59b6;
    text-decoration: none;
    font-size: 0.85rem;
  }

  .admin-login-link:hover {
    text-decoration: underline;
    color: #8e44ad;
  }
`;

export default AdminLoginPage;
