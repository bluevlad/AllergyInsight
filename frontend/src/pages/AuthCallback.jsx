/**
 * OAuth Callback Page
 */
import React, { useEffect, useState } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';

const AuthCallback = () => {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const { handleOAuthCallback } = useAuth();
  const [error, setError] = useState('');

  useEffect(() => {
    const processCallback = async () => {
      const token = searchParams.get('token');
      const errorParam = searchParams.get('error');

      if (errorParam) {
        setError('인증에 실패했습니다. 다시 시도해주세요.');
        setTimeout(() => navigate('/login'), 3000);
        return;
      }

      if (token) {
        try {
          await handleOAuthCallback(token);
          navigate('/my-diagnosis');
        } catch (err) {
          setError('인증 처리 중 오류가 발생했습니다.');
          setTimeout(() => navigate('/login'), 3000);
        }
      } else {
        setError('유효하지 않은 인증 요청입니다.');
        setTimeout(() => navigate('/login'), 3000);
      }
    };

    processCallback();
  }, [searchParams, handleOAuthCallback, navigate]);

  return (
    <div className="callback-container">
      {error ? (
        <div className="error-box">
          <p>{error}</p>
          <p>잠시 후 로그인 페이지로 이동합니다...</p>
        </div>
      ) : (
        <div className="loading-box">
          <div className="spinner"></div>
          <p>로그인 처리 중...</p>
        </div>
      )}

      <style>{`
        .callback-container {
          display: flex;
          justify-content: center;
          align-items: center;
          min-height: 80vh;
        }

        .loading-box, .error-box {
          text-align: center;
          padding: 2rem;
        }

        .spinner {
          width: 40px;
          height: 40px;
          border: 4px solid #f3f3f3;
          border-top: 4px solid #2196F3;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin: 0 auto 1rem;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .error-box {
          color: #d32f2f;
        }
      `}</style>
    </div>
  );
};

export default AuthCallback;
