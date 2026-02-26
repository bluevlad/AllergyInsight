/**
 * 구독 관리 페이지
 */
import React, { useState, useEffect } from 'react';
import { useSearchParams } from 'react-router-dom';
import { subscribeApi } from '../../services/subscribeApi';

const KEYWORD_OPTIONS = [
  { value: 'regulatory', label: '규제/인허가' },
  { value: 'market', label: '시장/산업' },
  { value: 'technology', label: '기술/R&D' },
  { value: 'competitor', label: '경쟁사' },
  { value: 'product', label: '제품/서비스' },
];

const ManagePage = () => {
  const [searchParams] = useSearchParams();
  const [email, setEmail] = useState(searchParams.get('email') || '');
  const [subscriptionKey, setSubscriptionKey] = useState(searchParams.get('key') || '');
  const [status, setStatus] = useState(null);
  const [keywords, setKeywords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (email) loadStatus();
  }, []);

  const loadStatus = async () => {
    try {
      const result = await subscribeApi.getStatus(email);
      setStatus(result);
      setKeywords(result.keywords || []);
    } catch (err) {
      setError(err.message);
    }
  };

  const handleLookup = async (e) => {
    e.preventDefault();
    if (!email) return;
    setError(null);
    setMessage(null);
    await loadStatus();
  };

  const toggleKeyword = (value) => {
    setKeywords(prev =>
      prev.includes(value) ? prev.filter(k => k !== value) : [...prev, value]
    );
  };

  const handleSaveKeywords = async () => {
    if (!email || !subscriptionKey) {
      setError('이메일과 구독 키가 필요합니다.');
      return;
    }
    try {
      setLoading(true);
      const result = await subscribeApi.updateKeywords({ email, subscription_key: subscriptionKey, keywords });
      setMessage(result.message);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  const handleUnsubscribe = async () => {
    if (!email || !subscriptionKey) {
      setError('이메일과 구독 키가 필요합니다.');
      return;
    }
    if (!window.confirm('정말 구독을 해지하시겠습니까?')) return;
    try {
      setLoading(true);
      const result = await subscribeApi.unsubscribe({ email, subscription_key: subscriptionKey });
      setMessage(result.message);
      setStatus(null);
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="manage-page">
      <div className="manage-container">
        <h1>구독 관리</h1>

        {message && <div className="alert success">{message}</div>}
        {error && <div className="alert error">{error}</div>}

        {!status ? (
          <form onSubmit={handleLookup}>
            <p className="subtitle">이메일을 입력하여 구독 상태를 확인하세요.</p>
            <div className="form-group">
              <input
                type="email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                placeholder="your@email.com"
                required
              />
            </div>
            <button type="submit" className="btn-submit">조회</button>
          </form>
        ) : (
          <div className="status-info">
            <div className="status-card">
              <div className="status-row">
                <span className="label">이메일</span>
                <span>{email}</span>
              </div>
              <div className="status-row">
                <span className="label">상태</span>
                <span className={`badge ${status.is_active ? 'active' : 'inactive'}`}>
                  {status.is_active ? (status.is_verified ? '활성' : '인증 대기') : '비활성'}
                </span>
              </div>
              <div className="status-row">
                <span className="label">구독일</span>
                <span>{status.subscribed_at ? new Date(status.subscribed_at).toLocaleDateString('ko-KR') : '-'}</span>
              </div>
            </div>

            <div className="form-group">
              <label>관심 분야</label>
              <div className="keyword-chips">
                {KEYWORD_OPTIONS.map((opt) => (
                  <button
                    key={opt.value}
                    type="button"
                    className={`chip ${keywords.includes(opt.value) ? 'selected' : ''}`}
                    onClick={() => toggleKeyword(opt.value)}
                  >
                    {opt.label}
                  </button>
                ))}
              </div>
            </div>

            <div className="form-group">
              <label>구독 키 (키워드 수정 시 필요)</label>
              <input
                type="text"
                value={subscriptionKey}
                onChange={(e) => setSubscriptionKey(e.target.value)}
                placeholder="구독 인증 시 받은 키"
              />
            </div>

            <div className="btn-group">
              <button className="btn-submit" onClick={handleSaveKeywords} disabled={loading}>
                키워드 저장
              </button>
              <button className="btn-danger" onClick={handleUnsubscribe} disabled={loading}>
                구독 해지
              </button>
            </div>
          </div>
        )}
      </div>

      <style>{`
        .manage-page {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          padding: 2rem;
        }
        .manage-container {
          background: white;
          border-radius: 12px;
          padding: 2.5rem;
          max-width: 500px;
          width: 100%;
          box-shadow: 0 20px 60px rgba(0,0,0,0.15);
        }
        .manage-container h1 { text-align: center; color: #333; margin-bottom: 1rem; }
        .subtitle { text-align: center; color: #666; margin-bottom: 1.5rem; }
        .form-group { margin-bottom: 1.25rem; }
        .form-group label { display: block; margin-bottom: 0.5rem; font-weight: 500; }
        .form-group input {
          width: 100%;
          padding: 0.75rem 1rem;
          border: 1px solid #ddd;
          border-radius: 8px;
          font-size: 1rem;
          box-sizing: border-box;
        }
        .keyword-chips { display: flex; flex-wrap: wrap; gap: 0.5rem; }
        .chip {
          padding: 0.5rem 1rem;
          border: 1px solid #ddd;
          border-radius: 20px;
          background: white;
          cursor: pointer;
          transition: all 0.2s;
        }
        .chip.selected { background: #667eea; color: white; border-color: #667eea; }
        .status-card {
          background: #f8f9fa;
          border-radius: 8px;
          padding: 1rem;
          margin-bottom: 1.5rem;
        }
        .status-row {
          display: flex;
          justify-content: space-between;
          padding: 0.5rem 0;
          border-bottom: 1px solid #eee;
        }
        .status-row:last-child { border-bottom: none; }
        .status-row .label { color: #666; }
        .badge {
          padding: 0.2rem 0.6rem;
          border-radius: 4px;
          font-size: 0.85rem;
          font-weight: 500;
        }
        .badge.active { background: #d4edda; color: #155724; }
        .badge.inactive { background: #f8d7da; color: #721c24; }
        .btn-group { display: flex; gap: 0.75rem; }
        .btn-submit {
          flex: 1;
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
        .btn-danger {
          padding: 0.85rem 1.5rem;
          background: #dc3545;
          color: white;
          border: none;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 600;
        }
        .btn-danger:disabled { opacity: 0.6; }
        .alert { padding: 0.75rem; border-radius: 8px; margin-bottom: 1rem; font-size: 0.9rem; }
        .alert.success { background: #d4edda; color: #155724; }
        .alert.error { background: #f8d7da; color: #721c24; }
      `}</style>
    </div>
  );
};

export default ManagePage;
