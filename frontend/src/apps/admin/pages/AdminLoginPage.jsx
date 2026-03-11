/**
 * Admin Login Page - Purple themed admin-specific login
 *
 * Provides Google OAuth and name + accessPin login for administrators.
 * Redirects to /admin on success, shows error if not super_admin.
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../../../shared/contexts/AuthContext';

const AdminLoginPage = () => {
  const navigate = useNavigate();
  const { loginWithGoogle, loginEmail, user, isSuperAdmin, isAdmin } = useAuth();

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

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setError('');
  };

  const handleGoogleLogin = () => {
    loginWithGoogle();
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

        {/* Google OAuth */}
        <button className="admin-btn admin-btn-google" onClick={handleGoogleLogin}>
          <svg viewBox="0 0 24 24" width="20" height="20">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Google 계정으로 로그인
        </button>

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

  .admin-btn-google {
    background: white;
    border: 1px solid #ddd;
    color: #333;
  }

  .admin-btn-google:hover {
    background: #f8f8f8;
    border-color: #bbb;
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
