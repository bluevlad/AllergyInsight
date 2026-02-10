/**
 * Login Page - Google OAuth & Simple Registration/Login
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../shared/contexts/AuthContext';

const LoginPage = () => {
  const navigate = useNavigate();
  const { loginWithGoogle, registerSimple, loginSimple, accessPin, clearAccessPin, getDefaultApp } = useAuth();

  const [mode, setMode] = useState('login'); // 'login', 'register'
  const [identifyMethod, setIdentifyMethod] = useState('phone'); // 'phone', 'birthdate'
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  // Form data
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    birthDate: '',
    serialNumber: '',
    pin: '',
    accessPin: '',
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    setError('');
  };

  const handleGoogleLogin = () => {
    loginWithGoogle();
  };

  const handleRegister = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const data = {
        name: formData.name,
        serialNumber: formData.serialNumber,
        pin: formData.pin,
      };

      if (identifyMethod === 'phone') {
        data.phone = formData.phone;
      } else {
        data.birthDate = formData.birthDate;
      }

      await registerSimple(data);
      // accessPin will be shown after registration
    } catch (err) {
      const message = err.response?.data?.detail || '등록에 실패했습니다.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  // 역할 기반 리다이렉트 결정
  const PROFESSIONAL_ROLES = ['doctor', 'nurse', 'lab_tech', 'hospital_admin', 'admin', 'super_admin'];
  const ADMIN_ROLES = ['admin', 'super_admin'];

  const getRedirectPath = (role) => {
    if (ADMIN_ROLES.includes(role)) return '/admin';
    if (PROFESSIONAL_ROLES.includes(role)) return '/pro';
    return '/app';
  };

  const handleLogin = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      const data = {
        name: formData.name,
        accessPin: formData.accessPin,
      };

      if (identifyMethod === 'phone') {
        data.phone = formData.phone;
      } else {
        data.birthDate = formData.birthDate;
      }

      const result = await loginSimple(data);
      // 반환된 user 정보로 직접 리다이렉트 결정 (상태 업데이트 대기 없이)
      navigate(getRedirectPath(result.user?.role));
    } catch (err) {
      const message = err.response?.data?.detail || '로그인에 실패했습니다.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  const handlePinConfirm = () => {
    clearAccessPin();
    const defaultApp = getDefaultApp();
    const appRoutes = { admin: '/admin', professional: '/pro', consumer: '/app' };
    navigate(appRoutes[defaultApp] || '/app');
  };

  // Show access PIN after registration
  if (accessPin) {
    return (
      <div className="login-container">
        <div className="login-card pin-display">
          <h2>등록 완료!</h2>
          <div className="pin-box">
            <p>아래 접속 PIN을 반드시 메모해두세요.</p>
            <p>다음 로그인 시 필요합니다.</p>
            <div className="access-pin">{accessPin}</div>
          </div>
          <button className="btn btn-primary" onClick={handlePinConfirm}>
            확인했습니다
          </button>
        </div>

        <style>{`
          .pin-display {
            text-align: center;
          }
          .pin-box {
            background: #fff3cd;
            border: 1px solid #ffc107;
            border-radius: 8px;
            padding: 1.5rem;
            margin: 1.5rem 0;
          }
          .access-pin {
            font-size: 2.5rem;
            font-weight: bold;
            color: #d63384;
            letter-spacing: 0.5rem;
            margin-top: 1rem;
            font-family: monospace;
          }
        `}</style>
      </div>
    );
  }

  return (
    <div className="login-container">
      <div className="login-card">
        <h1>AllergyInsight</h1>
        <p className="subtitle">알러지 검사 결과 조회 서비스</p>

        {/* Mode Tabs */}
        <div className="mode-tabs">
          <button
            className={`mode-tab ${mode === 'login' ? 'active' : ''}`}
            onClick={() => setMode('login')}
          >
            로그인
          </button>
          <button
            className={`mode-tab ${mode === 'register' ? 'active' : ''}`}
            onClick={() => setMode('register')}
          >
            회원가입
          </button>
        </div>

        {/* Google Login */}
        <button className="btn btn-google" onClick={handleGoogleLogin}>
          <svg viewBox="0 0 24 24" width="20" height="20">
            <path fill="#4285F4" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
            <path fill="#34A853" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
            <path fill="#FBBC05" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
            <path fill="#EA4335" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
          </svg>
          Google로 계속하기
        </button>

        <div className="divider">
          <span>또는</span>
        </div>

        {/* Simple Registration / Login Form */}
        <form onSubmit={mode === 'register' ? handleRegister : handleLogin}>
          <div className="form-group">
            <label>이름</label>
            <input
              type="text"
              name="name"
              value={formData.name}
              onChange={handleChange}
              placeholder="홍길동"
              required
            />
          </div>

          {/* Identify Method Toggle */}
          <div className="identify-toggle">
            <button
              type="button"
              className={`toggle-btn ${identifyMethod === 'phone' ? 'active' : ''}`}
              onClick={() => setIdentifyMethod('phone')}
            >
              전화번호
            </button>
            <button
              type="button"
              className={`toggle-btn ${identifyMethod === 'birthdate' ? 'active' : ''}`}
              onClick={() => setIdentifyMethod('birthdate')}
            >
              생년월일
            </button>
          </div>

          {identifyMethod === 'phone' ? (
            <div className="form-group">
              <label>전화번호</label>
              <input
                type="tel"
                name="phone"
                value={formData.phone}
                onChange={handleChange}
                placeholder="010-1234-5678"
                required
              />
            </div>
          ) : (
            <div className="form-group">
              <label>생년월일</label>
              <input
                type="date"
                name="birthDate"
                value={formData.birthDate}
                onChange={handleChange}
                required
              />
            </div>
          )}

          {mode === 'register' ? (
            <>
              <div className="form-group">
                <label>검사키트 시리얼번호</label>
                <input
                  type="text"
                  name="serialNumber"
                  value={formData.serialNumber}
                  onChange={handleChange}
                  placeholder="SGT-2024-XXXXX-XXXX"
                  required
                />
              </div>
              <div className="form-group">
                <label>검사키트 PIN</label>
                <input
                  type="password"
                  name="pin"
                  value={formData.pin}
                  onChange={handleChange}
                  placeholder="6자리 PIN"
                  maxLength={6}
                  required
                />
              </div>
            </>
          ) : (
            <div className="form-group">
              <label>접속 PIN</label>
              <input
                type="password"
                name="accessPin"
                value={formData.accessPin}
                onChange={handleChange}
                placeholder="6자리 접속 PIN"
                maxLength={6}
                required
              />
            </div>
          )}

          {error && <div className="error-message">{error}</div>}

          <button
            type="submit"
            className="btn btn-primary"
            disabled={loading}
          >
            {loading ? '처리 중...' : mode === 'register' ? '회원가입' : '로그인'}
          </button>
        </form>

        {mode === 'register' && (
          <p className="info-text">
            회원가입 시 검사키트의 시리얼번호와 PIN이 필요합니다.
            <br />
            검사 결과지에서 확인하실 수 있습니다.
          </p>
        )}

        {/* Test Account Info */}
        <div className="test-account-box">
          <div className="test-account-header">
            <span className="test-badge">TEST</span>
            <span>테스트 계정</span>
          </div>
          <div className="test-account-content">
            <div className="test-row">
              <span className="test-label">이름:</span>
              <span className="test-value">김철수</span>
            </div>
            <div className="test-row">
              <span className="test-label">전화번호:</span>
              <span className="test-value">010-9999-8888</span>
            </div>
            <div className="test-row">
              <span className="test-label">접속 PIN:</span>
              <span className="test-value pin">715302</span>
            </div>
          </div>
          <button
            type="button"
            className="btn-fill-test"
            onClick={() => {
              setMode('login');
              setIdentifyMethod('phone');
              setFormData({
                ...formData,
                name: '김철수',
                phone: '010-9999-8888',
                accessPin: '715302',
              });
            }}
          >
            테스트 계정으로 채우기
          </button>
        </div>
      </div>

      <style>{`
        .login-container {
          display: flex;
          justify-content: center;
          align-items: center;
          min-height: 80vh;
          padding: 1rem;
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

        .btn-google {
          background: white;
          border: 1px solid #ddd;
          color: #333;
        }

        .btn-google:hover {
          background: #f5f5f5;
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

        .identify-toggle {
          display: flex;
          gap: 0.5rem;
          margin-bottom: 1rem;
        }

        .toggle-btn {
          flex: 1;
          padding: 0.5rem;
          border: 1px solid #ddd;
          border-radius: 6px;
          background: white;
          cursor: pointer;
          font-size: 0.85rem;
          transition: all 0.2s;
        }

        .toggle-btn.active {
          border-color: #2196F3;
          background: #E3F2FD;
          color: #2196F3;
        }

        .error-message {
          color: #d32f2f;
          background: #ffebee;
          padding: 0.75rem;
          border-radius: 6px;
          margin-top: 1rem;
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

        .test-value.pin {
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
