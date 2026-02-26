/**
 * 공개 구독 신청 페이지
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { subscribeApi } from '../../services/subscribeApi';

const KEYWORD_OPTIONS = [
  { value: 'regulatory', label: '규제/인허가' },
  { value: 'market', label: '시장/산업' },
  { value: 'technology', label: '기술/R&D' },
  { value: 'competitor', label: '경쟁사' },
  { value: 'product', label: '제품/서비스' },
];

const SubscribePage = () => {
  const navigate = useNavigate();
  const [email, setEmail] = useState('');
  const [name, setName] = useState('');
  const [keywords, setKeywords] = useState([]);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [error, setError] = useState(null);

  const toggleKeyword = (value) => {
    setKeywords(prev =>
      prev.includes(value) ? prev.filter(k => k !== value) : [...prev, value]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!email) return;

    try {
      setLoading(true);
      setError(null);
      const result = await subscribeApi.subscribe({ email, name, keywords });
      setMessage(result.message);
      if (result.status === 'created' || result.status === 'reactivated') {
        setTimeout(() => navigate(`/subscribe/verify?email=${encodeURIComponent(email)}`), 2000);
      }
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="subscribe-page">
      <div className="subscribe-container">
        <h1>AllergyInsight 뉴스 구독</h1>
        <p className="subtitle">알러지 진단/체외진단 업계 최신 뉴스를 매일 이메일로 받아보세요.</p>

        {message && <div className="alert success">{message}</div>}
        {error && <div className="alert error">{error}</div>}

        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label htmlFor="email">이메일 *</label>
            <input
              id="email"
              type="email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              placeholder="your@email.com"
              required
            />
          </div>
          <div className="form-group">
            <label htmlFor="name">이름 (선택)</label>
            <input
              id="name"
              type="text"
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="홍길동"
            />
          </div>
          <div className="form-group">
            <label>관심 분야 (선택)</label>
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
          <button type="submit" className="btn-submit" disabled={loading || !email}>
            {loading ? '처리 중...' : '구독 신청'}
          </button>
        </form>

        <p className="login-link">
          이미 구독 중이신가요? <a href="/subscribe/manage">구독 관리</a>
        </p>
      </div>

      <style>{`
        .subscribe-page {
          min-height: 100vh;
          display: flex;
          align-items: center;
          justify-content: center;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          padding: 2rem;
        }
        .subscribe-container {
          background: white;
          border-radius: 12px;
          padding: 2.5rem;
          max-width: 480px;
          width: 100%;
          box-shadow: 0 20px 60px rgba(0,0,0,0.15);
        }
        .subscribe-container h1 {
          text-align: center;
          color: #333;
          margin-bottom: 0.5rem;
        }
        .subtitle {
          text-align: center;
          color: #666;
          margin-bottom: 2rem;
          font-size: 0.95rem;
        }
        .form-group {
          margin-bottom: 1.25rem;
        }
        .form-group label {
          display: block;
          margin-bottom: 0.5rem;
          font-weight: 500;
          color: #333;
        }
        .form-group input {
          width: 100%;
          padding: 0.75rem 1rem;
          border: 1px solid #ddd;
          border-radius: 8px;
          font-size: 1rem;
          box-sizing: border-box;
        }
        .form-group input:focus {
          border-color: #667eea;
          outline: none;
          box-shadow: 0 0 0 3px rgba(102,126,234,0.1);
        }
        .keyword-chips {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
        }
        .chip {
          padding: 0.5rem 1rem;
          border: 1px solid #ddd;
          border-radius: 20px;
          background: white;
          cursor: pointer;
          font-size: 0.9rem;
          transition: all 0.2s;
        }
        .chip:hover { border-color: #667eea; }
        .chip.selected {
          background: #667eea;
          color: white;
          border-color: #667eea;
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
          margin-top: 0.5rem;
        }
        .btn-submit:hover { background: #5a6fd6; }
        .btn-submit:disabled { opacity: 0.6; cursor: not-allowed; }
        .alert {
          padding: 0.75rem 1rem;
          border-radius: 8px;
          margin-bottom: 1rem;
          font-size: 0.9rem;
        }
        .alert.success { background: #d4edda; color: #155724; }
        .alert.error { background: #f8d7da; color: #721c24; }
        .login-link {
          text-align: center;
          margin-top: 1.5rem;
          font-size: 0.9rem;
          color: #666;
        }
        .login-link a { color: #667eea; }
      `}</style>
    </div>
  );
};

export default SubscribePage;
