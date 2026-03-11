/**
 * 주간 브리핑 탭 - 플랫폼 현황 + 키워드 + 임상 하이라이트
 */
import React, { useState, useEffect } from 'react';
import { adminApi } from '../../services/adminApi';

const BriefingTab = () => {
  const [days, setDays] = useState(7);
  const [keywords, setKeywords] = useState(null);
  const [clinical, setClinical] = useState(null);
  const [dashboard, setDashboard] = useState(null);
  const [newsStats, setNewsStats] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadAll();
  }, [days]);

  const loadAll = async () => {
    try {
      setLoading(true);
      setError(null);
      const [kw, cl, dash, ns] = await Promise.all([
        adminApi.analytics.keywordsOverview().catch(() => null),
        adminApi.analytics.overview().catch(() => null),
        adminApi.dashboard.get().catch(() => null),
        adminApi.news.stats().catch(() => null),
      ]);
      setKeywords(kw);
      setClinical(cl);
      setDashboard(dash);
      setNewsStats(ns);
    } catch (err) {
      setError('브리핑 데이터를 불러오지 못했습니다.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <p style={{ padding: '2rem', textAlign: 'center', color: '#888' }}>로딩 중...</p>;
  if (error) return <div style={{ color: '#e74c3c', padding: '1rem' }}>{error} <button onClick={loadAll} style={{ marginLeft: '0.5rem', padding: '0.25rem 0.75rem', border: '1px solid #e74c3c', borderRadius: '4px', background: 'white', color: '#e74c3c', cursor: 'pointer' }}>재시도</button></div>;

  const risingKeywords = keywords?.rising_keywords || [];
  const allergens = clinical?.allergens || [];
  const top5 = allergens.slice(0, 5);
  const paperStats = dashboard?.stats?.papers || {};
  const userStats = dashboard?.stats?.users || {};

  return (
    <div>
      {/* 기간 선택 + 새로고침 */}
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        <label style={{ fontSize: '0.85rem', color: '#666' }}>기간:</label>
        <select value={days} onChange={e => setDays(Number(e.target.value))} style={{ padding: '0.5rem 0.75rem', borderRadius: '6px', border: '1px solid #ddd', fontSize: '0.85rem' }}>
          <option value={1}>1일</option>
          <option value={3}>3일</option>
          <option value={7}>7일</option>
        </select>
        <button onClick={loadAll} className="ai-refresh-btn">새로고침</button>
      </div>

      {/* KPI 요약 카드 */}
      <div className="ai-kpi-grid">
        <KpiCard icon="📄" label="논문 수" value={paperStats.total ?? '-'} sub={`가이드라인 ${paperStats.guidelines ?? 0}건`} color="#9b59b6" />
        <KpiCard icon="📰" label="수집 뉴스" value={newsStats?.total_news ?? '-'} sub={`최근 7일 ${newsStats?.recent_7days ?? 0}건`} color="#3498db" />
        <KpiCard icon="👥" label="사용자" value={userStats.total ?? '-'} sub={`최근 가입 ${userStats.recent_signups ?? 0}명`} color="#2ecc71" />
        <KpiCard icon="🔬" label="임상 검사" value={clinical?.total_tests?.toLocaleString() ?? '-'} sub={`알러젠 ${clinical?.total_allergens ?? 0}종`} color="#e74c3c" />
      </div>

      <div className="ai-grid-2col">
        {/* 키워드 핫 토픽 */}
        <div className="ai-card">
          <div className="ai-card-header">
            <h4 className="ai-card-title">키워드 핫 토픽</h4>
            <span className="ai-card-badge">{risingKeywords.length}건</span>
          </div>
          {risingKeywords.length > 0 ? (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {risingKeywords.map((kw, i) => (
                <span key={i} className="ai-keyword-tag">
                  {kw.keyword}
                  <span className="ai-keyword-change">
                    {kw.change_rate != null ? `+${kw.change_rate.toFixed(0)}%` : 'NEW'}
                  </span>
                </span>
              ))}
            </div>
          ) : (
            <p className="ai-empty-text">상승 키워드가 없습니다.</p>
          )}
        </div>

        {/* 임상 하이라이트 */}
        <div className="ai-card">
          <div className="ai-card-header">
            <h4 className="ai-card-title">임상 하이라이트 (양성률 TOP 5)</h4>
          </div>
          {top5.length > 0 ? (
            <table className="ai-table">
              <thead>
                <tr>
                  <th>순위</th>
                  <th>알러젠</th>
                  <th>양성률</th>
                  <th>검사 수</th>
                </tr>
              </thead>
              <tbody>
                {top5.map((a, i) => (
                  <tr key={i}>
                    <td>
                      <span className={`ai-rank ai-rank-${i + 1}`}>{i + 1}</span>
                    </td>
                    <td style={{ fontWeight: 500 }}>{a.allergen_code}</td>
                    <td style={{ fontWeight: 600, color: '#9b59b6' }}>{(a.positive_rate * 100).toFixed(1)}%</td>
                    <td style={{ color: '#888' }}>{a.total_tests?.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p className="ai-empty-text">임상 데이터가 없습니다.</p>
          )}
        </div>
      </div>

      {/* 플랫폼 수집 현황 */}
      <div className="ai-card" style={{ marginTop: '1.5rem' }}>
        <div className="ai-card-header">
          <h4 className="ai-card-title">플랫폼 수집 현황</h4>
        </div>
        <div className="ai-status-grid">
          <StatusItem icon="📄" label="논문 (전체)" value={`${paperStats.total ?? 0}건`} />
          <StatusItem icon="📋" label="가이드라인" value={`${paperStats.guidelines ?? 0}건`} />
          <StatusItem icon="🔬" label="임상 진술" value={`${paperStats.clinical_statements ?? 0}건`} />
          <StatusItem icon="📰" label="뉴스 (전체)" value={`${newsStats?.total_news ?? 0}건`} />
          <StatusItem icon="🆕" label="뉴스 (7일)" value={`${newsStats?.recent_7days ?? 0}건`} />
          <StatusItem icon="⭐" label="중요 뉴스" value={`${newsStats?.important_count ?? 0}건`} />
        </div>
      </div>

      <style>{`
        .ai-refresh-btn {
          padding: 0.5rem 1rem;
          background: linear-gradient(135deg, #9b59b6, #8e44ad);
          color: white;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-size: 0.85rem;
          font-weight: 500;
          transition: opacity 0.2s;
        }
        .ai-refresh-btn:hover { opacity: 0.85; }

        .ai-kpi-grid {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 1rem;
          margin-bottom: 1.5rem;
        }

        .ai-kpi-card {
          background: white;
          border-radius: 12px;
          padding: 1.25rem;
          box-shadow: 0 2px 12px rgba(0,0,0,0.06);
          display: flex;
          align-items: center;
          gap: 1rem;
          transition: transform 0.2s, box-shadow 0.2s;
        }
        .ai-kpi-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 16px rgba(0,0,0,0.1);
        }

        .ai-kpi-icon {
          width: 48px;
          height: 48px;
          border-radius: 12px;
          display: flex;
          align-items: center;
          justify-content: center;
          font-size: 1.25rem;
          flex-shrink: 0;
        }

        .ai-kpi-info {
          flex: 1;
          min-width: 0;
        }

        .ai-kpi-label {
          font-size: 0.75rem;
          color: #888;
          text-transform: uppercase;
          letter-spacing: 0.5px;
          margin-bottom: 0.25rem;
        }

        .ai-kpi-value {
          font-size: 1.5rem;
          font-weight: 700;
          line-height: 1.2;
        }

        .ai-kpi-sub {
          font-size: 0.7rem;
          color: #aaa;
          margin-top: 0.2rem;
        }

        .ai-grid-2col {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
          gap: 1.5rem;
        }

        .ai-card {
          background: white;
          border-radius: 12px;
          padding: 1.25rem;
          box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        }

        .ai-card-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1rem;
        }

        .ai-card-title {
          margin: 0;
          font-size: 0.95rem;
          font-weight: 600;
          color: #333;
        }

        .ai-card-badge {
          background: #f0e6f6;
          color: #9b59b6;
          padding: 0.2rem 0.6rem;
          border-radius: 12px;
          font-size: 0.7rem;
          font-weight: 600;
        }

        .ai-keyword-tag {
          display: inline-flex;
          align-items: center;
          gap: 0.375rem;
          padding: 0.4rem 0.75rem;
          background: linear-gradient(135deg, #9b59b6, #8e44ad);
          color: white;
          border-radius: 20px;
          font-size: 0.8rem;
          font-weight: 500;
        }

        .ai-keyword-change {
          font-size: 0.65rem;
          background: rgba(255,255,255,0.25);
          padding: 0.1rem 0.35rem;
          border-radius: 8px;
        }

        .ai-table {
          width: 100%;
          border-collapse: collapse;
        }

        .ai-table thead tr {
          background: #f8f9fa;
        }

        .ai-table th {
          padding: 0.625rem 0.75rem;
          text-align: left;
          font-size: 0.75rem;
          font-weight: 600;
          color: #888;
          text-transform: uppercase;
          letter-spacing: 0.5px;
        }

        .ai-table td {
          padding: 0.625rem 0.75rem;
          font-size: 0.85rem;
          border-bottom: 1px solid #f0f0f0;
        }

        .ai-table tbody tr:hover {
          background: #faf8fc;
        }

        .ai-table tbody tr:last-child td {
          border-bottom: none;
        }

        .ai-rank {
          display: inline-flex;
          align-items: center;
          justify-content: center;
          width: 24px;
          height: 24px;
          border-radius: 50%;
          font-size: 0.7rem;
          font-weight: 700;
          background: #eee;
          color: #666;
        }
        .ai-rank-1 { background: #ffd700; color: #7a6100; }
        .ai-rank-2 { background: #c0c0c0; color: #555; }
        .ai-rank-3 { background: #cd7f32; color: white; }

        .ai-empty-text {
          color: #aaa;
          font-size: 0.85rem;
          text-align: center;
          padding: 1.5rem 0;
          margin: 0;
        }

        .ai-status-grid {
          display: grid;
          grid-template-columns: repeat(3, 1fr);
          gap: 0.75rem;
        }

        .ai-status-item {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.75rem;
          background: #f8f9fa;
          border-radius: 8px;
        }

        .ai-status-icon {
          font-size: 1.25rem;
        }

        .ai-status-label {
          font-size: 0.75rem;
          color: #888;
        }

        .ai-status-value {
          font-size: 0.95rem;
          font-weight: 600;
          color: #333;
        }

        @media (max-width: 1024px) {
          .ai-kpi-grid { grid-template-columns: repeat(2, 1fr); }
          .ai-status-grid { grid-template-columns: repeat(2, 1fr); }
        }

        @media (max-width: 640px) {
          .ai-kpi-grid { grid-template-columns: 1fr; }
          .ai-grid-2col { grid-template-columns: 1fr; }
          .ai-status-grid { grid-template-columns: 1fr; }
        }
      `}</style>
    </div>
  );
};

const KpiCard = ({ icon, label, value, sub, color = '#333' }) => (
  <div className="ai-kpi-card">
    <div className="ai-kpi-icon" style={{ background: `${color}15`, color }}>
      {icon}
    </div>
    <div className="ai-kpi-info">
      <div className="ai-kpi-label">{label}</div>
      <div className="ai-kpi-value" style={{ color }}>{value}</div>
      {sub && <div className="ai-kpi-sub">{sub}</div>}
    </div>
  </div>
);

const StatusItem = ({ icon, label, value }) => (
  <div className="ai-status-item">
    <span className="ai-status-icon">{icon}</span>
    <div>
      <div className="ai-status-label">{label}</div>
      <div className="ai-status-value">{value}</div>
    </div>
  </div>
);

export default BriefingTab;
