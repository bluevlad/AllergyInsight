/**
 * Admin 뉴스레터 관리 페이지
 */
import React, { useState, useEffect } from 'react';
import { adminApi } from '../services/adminApi';

const NewsletterPage = () => {
  const [activeTab, setActiveTab] = useState('preview');
  const [previewHtml, setPreviewHtml] = useState('');
  const [history, setHistory] = useState([]);
  const [stats, setStats] = useState(null);
  const [recipients, setRecipients] = useState('');
  const [days, setDays] = useState(1);
  const [loading, setLoading] = useState(false);
  const [message, setMessage] = useState(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);

  useEffect(() => {
    loadStats();
  }, []);

  useEffect(() => {
    if (activeTab === 'preview') loadPreview();
    if (activeTab === 'history') loadHistory();
  }, [activeTab, days, page]);

  const loadPreview = async () => {
    try {
      setLoading(true);
      const html = await adminApi.newsletter.preview({ days });
      setPreviewHtml(html);
    } catch (err) {
      console.error('Preview failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadHistory = async () => {
    try {
      const result = await adminApi.newsletter.history({ page, page_size: 20 });
      setHistory(result.items || []);
      setTotal(result.total || 0);
    } catch (err) {
      console.error('History load failed:', err);
    }
  };

  const loadStats = async () => {
    try {
      const result = await adminApi.newsletter.stats();
      setStats(result);
    } catch (err) {
      console.error('Stats load failed:', err);
    }
  };

  const handleSend = async () => {
    const recipientList = recipients.split(',').map(e => e.trim()).filter(Boolean);
    if (recipientList.length === 0) {
      alert('수신자 이메일을 입력하세요.');
      return;
    }
    if (!window.confirm(`${recipientList.length}명에게 뉴스레터를 발송하시겠습니까?`)) return;

    try {
      setLoading(true);
      const result = await adminApi.newsletter.send({
        recipients: recipientList,
        days,
      });
      setMessage(`${result.message} (기사 ${result.article_count}건)`);
      loadStats();
    } catch (err) {
      setMessage('발송 실패: ' + err.message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="newsletter-page" style={{ padding: '1rem' }}>
      <h2>뉴스레터 관리</h2>

      {stats && (
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
          <StatCard label="전체 발송" value={stats.total_sent} />
          <StatCard label="성공" value={stats.success_count} color="#27ae60" />
          <StatCard label="실패" value={stats.failed_count} color="#e74c3c" />
          <StatCard label="최근 7일" value={stats.recent_7days} />
        </div>
      )}

      {message && (
        <div style={{ padding: '0.75rem', background: '#d4edda', borderRadius: '6px', marginBottom: '1rem' }}>
          {message}
        </div>
      )}

      <div style={{ display: 'flex', gap: 0, borderBottom: '2px solid #eee', marginBottom: '1rem' }}>
        {['preview', 'send', 'history'].map(tab => (
          <button
            key={tab}
            onClick={() => setActiveTab(tab)}
            style={{
              padding: '0.75rem 1.5rem',
              background: 'none',
              border: 'none',
              borderBottom: activeTab === tab ? '2px solid #9b59b6' : '2px solid transparent',
              color: activeTab === tab ? '#9b59b6' : '#888',
              fontWeight: activeTab === tab ? 600 : 400,
              cursor: 'pointer',
              marginBottom: '-2px',
            }}
          >
            {{ preview: '미리보기', send: '수동 발송', history: '발송 이력' }[tab]}
          </button>
        ))}
      </div>

      {activeTab === 'preview' && (
        <div>
          <div style={{ marginBottom: '1rem' }}>
            <label>기간: </label>
            <select value={days} onChange={e => setDays(Number(e.target.value))}>
              <option value={1}>1일</option>
              <option value={3}>3일</option>
              <option value={7}>7일</option>
            </select>
          </div>
          {loading ? (
            <p>로딩 중...</p>
          ) : (
            <div
              style={{ background: 'white', borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)', overflow: 'hidden' }}
              dangerouslySetInnerHTML={{ __html: previewHtml }}
            />
          )}
        </div>
      )}

      {activeTab === 'send' && (
        <div style={{ maxWidth: '600px' }}>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: 500 }}>수신자 이메일 (쉼표 구분)</label>
            <textarea
              value={recipients}
              onChange={e => setRecipients(e.target.value)}
              placeholder="user1@example.com, user2@example.com"
              rows={3}
              style={{ width: '100%', padding: '0.75rem', border: '1px solid #ddd', borderRadius: '6px', boxSizing: 'border-box' }}
            />
          </div>
          <div style={{ marginBottom: '1rem' }}>
            <label style={{ marginRight: '0.5rem' }}>기간:</label>
            <select value={days} onChange={e => setDays(Number(e.target.value))}>
              <option value={1}>1일</option>
              <option value={3}>3일</option>
              <option value={7}>7일</option>
            </select>
          </div>
          <button
            onClick={handleSend}
            disabled={loading}
            style={{ padding: '0.75rem 2rem', background: '#9b59b6', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer', fontWeight: 600 }}
          >
            {loading ? '발송 중...' : '뉴스레터 발송'}
          </button>
        </div>
      )}

      {activeTab === 'history' && (
        <div>
          <table style={{ width: '100%', borderCollapse: 'collapse', background: 'white', borderRadius: '8px', overflow: 'hidden' }}>
            <thead>
              <tr style={{ background: '#f8f9fa', textAlign: 'left' }}>
                <th style={{ padding: '0.75rem' }}>수신자</th>
                <th style={{ padding: '0.75rem' }}>제목</th>
                <th style={{ padding: '0.75rem' }}>기사수</th>
                <th style={{ padding: '0.75rem' }}>결과</th>
                <th style={{ padding: '0.75rem' }}>발송일</th>
              </tr>
            </thead>
            <tbody>
              {history.map(item => (
                <tr key={item.id} style={{ borderBottom: '1px solid #eee' }}>
                  <td style={{ padding: '0.75rem' }}>{item.recipient_email}</td>
                  <td style={{ padding: '0.75rem', maxWidth: '200px', overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{item.subject}</td>
                  <td style={{ padding: '0.75rem' }}>{item.article_count}</td>
                  <td style={{ padding: '0.75rem' }}>
                    <span style={{ color: item.is_success ? '#27ae60' : '#e74c3c' }}>
                      {item.is_success ? '성공' : '실패'}
                    </span>
                  </td>
                  <td style={{ padding: '0.75rem', fontSize: '0.85rem', color: '#888' }}>
                    {item.sent_at ? new Date(item.sent_at).toLocaleString('ko-KR') : '-'}
                  </td>
                </tr>
              ))}
              {history.length === 0 && (
                <tr><td colSpan={5} style={{ padding: '2rem', textAlign: 'center', color: '#888' }}>발송 이력이 없습니다.</td></tr>
              )}
            </tbody>
          </table>
          {total > 20 && (
            <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginTop: '1rem' }}>
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1}>이전</button>
              <span>{page} / {Math.ceil(total / 20)}</span>
              <button onClick={() => setPage(p => p + 1)} disabled={page * 20 >= total}>다음</button>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const StatCard = ({ label, value, color }) => (
  <div style={{ background: 'white', padding: '0.75rem 1.25rem', borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}>
    <span style={{ fontSize: '0.85rem', color: '#888' }}>{label} </span>
    <span style={{ fontSize: '1.1rem', fontWeight: 700, color: color || '#333' }}>{value}</span>
  </div>
);

export default NewsletterPage;
