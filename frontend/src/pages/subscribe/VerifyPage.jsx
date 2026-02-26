/**
 * 구독 인증 페이지
 */
import React, { useState } from 'react';
import { useSearchParams } from 'react-router-dom';
import { subscribeApi } from '../../services/subscribeApi';

const VerifyPage = () => {
  const [searchParams] = useSearchParams();
  const [email, setEmail] = useState(searchParams.get('email') || '');
  const [code, setCode] = useState('');
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);
  const [verified, setVerified] = useState(false);

  const handleVerify = async (e) => {
    e.preventDefault();
    if (!email || !code) return;

    try {
      setLoading(true);
      setError(null);
      const result = await subscribeApi.verify({ email, code });
      if (result.success) {
        setMessage(result.message);
        setVerified(true);
      } else {
        setError(result.message);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleResend = async () => {
    if (!email) return;
    try {
      setLoading(true);
      setError(null);
      const result = await subscribeApi.resendVerification({ email });
      setMessage(result.message);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="verify-page">
      <div className="verify-container">
        <h1>구독 인증</h1>

        {verified ? (
          <div className="verified-box">
            <div className="check-icon">&#10003;</div>
            <p>{message}</p>
            <p className="sub-text">뉴스 브리핑이 매일 이메일로 발송됩니다.</p>
            <a href="/subscribe/manage" className="btn-manage">구독 관리</a>
          </div>
        ) : (
          <>
            <p className="subtitle">이메일로 전송된 6자리 인증 코드를 입력하세요.</p>

            {message && <div className="alert success">{message}</div>}
            {error && <div className="alert error">{error}</div>}

            <form onSubmit={handleVerify}>
              <div className="form-group">
                <label htmlFor="email">이메일</label>
                <input
                  id="email"
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  required
                />
              </div>
              <div className="form-group">
                <label htmlFor="code">인증 코드</label>
                <input
                  id="code"
                  type="text"
                  value={code}
                  onChange={(e) => setCode(e.target.value)}
                  placeholder="6자리 코드"
                  maxLength={6}
                  required
                  className="code-input"
                />
              </div>
              <button type="submit" className="btn-submit" disabled={loading}>
                {loading ? '확인 중...' : '인증 확인'}
              </button>
            </form>
            <button className="btn-resend" onClick={handleResend} disabled={loading || !email}>
              인증 코드 재발송
            </button>
          </>
        )}
      </div>

      <style>{`
        .verify-page {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          padding: 2rem;
        }
        .verify-container {
          background: white;
          border-radius: 12px;
          padding: 2.5rem;
          max-width: 420px;
          width: 100%;
          box-shadow: 0 20px 60px rgba(0,0,0,0.15);
          text-align: center;
        }
        .verify-container h1 { color: #333; margin-bottom: 0.5rem; }
        .subtitle { color: #666; margin-bottom: 1.5rem; }
        .form-group {
          margin-bottom: 1.25rem;
          text-align: left;
        }
        .form-group label {
          display: block;
          margin-bottom: 0.5rem;
          font-weight: 500;
        }
        .form-group input {
          width: 100%;
          padding: 0.75rem 1rem;
          border: 1px solid #ddd;
          border-radius: 8px;
          font-size: 1rem;
          box-sizing: border-box;
        }
        .code-input {
          text-align: center;
          letter-spacing: 8px;
          font-size: 1.5rem !important;
          font-weight: bold;
        }
        .btn-submit {
          width: 100%;
          padding: 0.85rem;
          background: #667eea;
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
        }
        .btn-submit:disabled { opacity: 0.6; }
        .btn-resend {
          margin-top: 1rem;
          background: none;
          border: none;
          color: #667eea;
          cursor: pointer;
          font-size: 0.9rem;
        }
        .verified-box { padding: 1rem 0; }
        .check-icon {
          width: 60px;
          height: 60px;
          background: #d4edda;
          color: #28a745;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 2rem;
          margin: 0 auto 1rem;
        }
        .sub-text { color: #666; font-size: 0.9rem; }
        .btn-manage {
          display: inline-block;
          margin-top: 1rem;
          padding: 0.6rem 1.5rem;
          background: #667eea;
          color: white;
          border-radius: 8px;
          text-decoration: none;
        }
        .alert {
          padding: 0.75rem;
          border-radius: 8px;
          margin-bottom: 1rem;
          font-size: 0.9rem;
        }
        .alert.success { background: #d4edda; color: #155724; }
        .alert.error { background: #f8d7da; color: #721c24; }
      `}</style>
    </div>
  );
};

export default VerifyPage;
