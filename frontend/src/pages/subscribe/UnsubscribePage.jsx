/**
 * 간편 구독 해지 페이지 (URL 파라미터: email, key)
 */
import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { subscribeApi } from '../../services/subscribeApi';

const UnsubscribePage = () => {
  const [searchParams] = useSearchParams();
  const email = searchParams.get('email') || '';
  const key = searchParams.get('key') || '';
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [error, setError] = useState(null);

  const handleUnsubscribe = async () => {
    if (!email || !key) {
      setError('유효하지 않은 해지 링크입니다.');
      return;
    }
    try {
      setLoading(true);
      const res = await subscribeApi.unsubscribe({ email, subscription_key: key });
      setResult(res);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="unsub-page">
      <div className="unsub-container">
        <h1>구독 해지</h1>

        {result?.success ? (
          <div className="result-box">
            <p>{result.message}</p>
            <p className="sub-text">구독이 해지되었습니다. 다시 구독하시려면 아래 링크를 이용하세요.</p>
            <a href="/subscribe" className="btn-resubscribe">다시 구독하기</a>
          </div>
        ) : (
          <>
            {error && <div className="alert error">{error}</div>}
            <p>아래 이메일의 뉴스 구독을 해지하시겠습니까?</p>
            <p className="email-display">{email || '(이메일 없음)'}</p>
            <button
              className="btn-unsub"
              onClick={handleUnsubscribe}
              disabled={loading || !email || !key}
            >
              {loading ? '처리 중...' : '구독 해지'}
            </button>
          </>
        )}
      </div>

      <style>{`
        .unsub-page {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: #f5f5f5;
          padding: 2rem;
        }
        .unsub-container {
          background: white;
          border-radius: 12px;
          padding: 2.5rem;
          max-width: 420px;
          width: 100%;
          text-align: center;
          box-shadow: 0 4px 20px rgba(0,0,0,0.1);
        }
        .unsub-container h1 { color: #333; margin-bottom: 1rem; }
        .email-display {
          font-size: 1.1rem;
          font-weight: 600;
          color: #667eea;
          margin: 1rem 0;
        }
        .btn-unsub {
          padding: 0.85rem 2rem;
          background: #dc3545;
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
        }
        .btn-unsub:disabled { opacity: 0.6; }
        .result-box { padding: 1rem 0; }
        .sub-text { color: #666; font-size: 0.9rem; margin-top: 0.5rem; }
        .btn-resubscribe {
          display: inline-block;
          margin-top: 1rem;
          padding: 0.6rem 1.5rem;
          background: #667eea;
          color: white;
          border-radius: 8px;
          text-decoration: none;
        }
        .alert { padding: 0.75rem; border-radius: 8px; margin-bottom: 1rem; }
        .alert.error { background: #f8d7da; color: #721c24; }
      `}</style>
    </div>
  );
};

export default UnsubscribePage;
