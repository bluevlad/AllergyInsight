/**
 * Analytics Dashboard - 공개 분석 대시보드
 */
import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { analyticsApi } from '../services/analyticsApi';

const COLORS = ['#1abc9c', '#3498db', '#9b59b6', '#e74c3c', '#f39c12', '#2ecc71', '#e67e22', '#1abc9c'];

const CATEGORY_COLORS = {
  company: '#9b59b6',
  technology: '#3498db',
  regulation: '#e74c3c',
  product: '#2ecc71',
  allergen: '#f39c12',
};

const AnalyticsDashboard = () => {
  const [summary, setSummary] = useState(null);
  const [overview, setOverview] = useState(null);
  const [keywords, setKeywords] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError(null);
      const [s, o, k] = await Promise.allSettled([
        analyticsApi.getSummary(),
        analyticsApi.getOverview(),
        analyticsApi.getKeywordsOverview(),
      ]);
      if (s.status === 'fulfilled') setSummary(s.value);
      if (o.status === 'fulfilled') setOverview(o.value);
      if (k.status === 'fulfilled') setKeywords(k.value);
      if ([s, o, k].every(r => r.status === 'rejected')) setError('데이터를 불러올 수 없습니다.');
    } catch {
      setError('대시보드 로딩 실패');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="pub-loading">
        <div className="pub-spinner" />
        <p>대시보드 로딩 중...</p>
      </div>
    );
  }

  if (error && !summary && !overview && !keywords) {
    return (
      <div className="pub-error">
        <p>{error}</p>
        <button onClick={loadDashboard} className="pub-retry-btn">다시 시도</button>
      </div>
    );
  }

  // Allergen chart data
  const allergens = Array.isArray(overview) ? overview : (overview?.allergens || []);
  const top10 = allergens.slice(0, 10);
  const barData = top10.map(a => ({
    name: a.allergen_code,
    양성률: +(( a.positive_rate || 0) * 100).toFixed(1),
  }));

  // Keyword data
  const keywordList = Array.isArray(keywords) ? keywords : [];
  const risingKeywords = keywords?.rising_keywords || keywordList.filter(k => k.trend_direction === 'up' || k.trend_direction === 'rising');
  const categories = keywords?.categories || {};

  return (
    <div className="pub-dashboard">
      <h2 className="pub-page-title">분석 대시보드</h2>

      {/* KPI Cards */}
      {summary && (
        <div className="pub-kpi-grid">
          <KpiCard icon="👥" label="사용자" value={summary.total_users ?? '-'} color="#1abc9c" />
          <KpiCard icon="🔬" label="진단 건수" value={summary.total_diagnoses?.toLocaleString() ?? '-'} color="#3498db" />
          <KpiCard icon="📄" label="연구 논문" value={summary.total_papers?.toLocaleString() ?? '-'} color="#9b59b6" />
          <KpiCard icon="🧬" label="분석 알러젠" value={allergens.length || '-'} color="#e74c3c" />
        </div>
      )}

      {/* Allergen Chart + Table */}
      {barData.length > 0 && (
        <div className="pub-card">
          <div className="pub-card-header">
            <h3 className="pub-card-title">알러젠 양성률 TOP 10</h3>
            <a href="/analytics/allergen-trends" className="pub-card-link">상세 보기 &rarr;</a>
          </div>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis unit="%" tick={{ fontSize: 11 }} />
              <Tooltip
                contentStyle={{ borderRadius: '8px', border: '1px solid #eee', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                formatter={(value) => [`${value}%`, '양성률']}
              />
              <Bar dataKey="양성률" radius={[6, 6, 0, 0]}>
                {barData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="pub-grid-2col">
        {/* Rising Keywords */}
        <div className="pub-card">
          <div className="pub-card-header">
            <h3 className="pub-card-title">상승 키워드</h3>
            <a href="/analytics/keyword-trends" className="pub-card-link">전체 보기 &rarr;</a>
          </div>
          {risingKeywords.length > 0 ? (
            <div className="pub-keyword-tags">
              {risingKeywords.slice(0, 12).map((kw, i) => (
                <span key={i} className="pub-keyword-tag" style={{
                  background: CATEGORY_COLORS[kw.category] || '#1abc9c',
                }}>
                  {kw.keyword}
                  <span className="pub-keyword-rate">
                    {kw.change_rate != null ? `+${(typeof kw.change_rate === 'number' && kw.change_rate < 1 ? kw.change_rate * 100 : kw.change_rate).toFixed(0)}%` : 'NEW'}
                  </span>
                </span>
              ))}
            </div>
          ) : keywordList.length > 0 ? (
            <div className="pub-keyword-tags">
              {keywordList.slice(0, 12).map((kw, i) => (
                <span key={i} className="pub-keyword-tag" style={{ background: CATEGORY_COLORS[kw.category] || '#1abc9c' }}>
                  {kw.keyword}
                  <span className="pub-keyword-count">{kw.mention_count ?? 0}</span>
                </span>
              ))}
            </div>
          ) : (
            <p className="pub-empty">키워드 데이터가 없습니다.</p>
          )}
        </div>

        {/* Allergen Ranking Table */}
        {top10.length > 0 && (
          <div className="pub-card">
            <div className="pub-card-header">
              <h3 className="pub-card-title">양성률 랭킹</h3>
            </div>
            <table className="pub-table">
              <thead>
                <tr>
                  <th>순위</th>
                  <th>알러젠</th>
                  <th>양성률</th>
                  <th>검사 수</th>
                </tr>
              </thead>
              <tbody>
                {top10.slice(0, 8).map((a, i) => (
                  <tr key={i}>
                    <td><span className={`pub-rank pub-rank-${i + 1}`}>{i + 1}</span></td>
                    <td className="pub-allergen-name">{a.allergen_name || a.allergen_code}</td>
                    <td><span className="pub-rate-badge">{((a.positive_rate || 0) * 100).toFixed(1)}%</span></td>
                    <td className="pub-muted">{a.total_tests?.toLocaleString() ?? '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      <style>{`
        .pub-dashboard { padding: 1rem; }
        .pub-page-title { margin-bottom: 1.25rem; font-size: 1.25rem; font-weight: 700; color: #2c3e50; }

        .pub-loading { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px; gap: 1rem; color: #888; }
        .pub-spinner { width: 40px; height: 40px; border: 4px solid #e9ecef; border-top: 4px solid #1abc9c; border-radius: 50%; animation: pub-spin 1s linear infinite; }
        @keyframes pub-spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .pub-error { display: flex; flex-direction: column; align-items: center; min-height: 200px; justify-content: center; gap: 1rem; color: #e74c3c; }
        .pub-retry-btn { padding: 0.5rem 1.25rem; background: #1abc9c; color: white; border: none; border-radius: 8px; cursor: pointer; font-size: 0.85rem; }

        .pub-kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
        .pub-kpi-card { background: white; border-radius: 12px; padding: 1.25rem; box-shadow: 0 2px 12px rgba(0,0,0,0.06); display: flex; align-items: center; gap: 1rem; transition: transform 0.2s, box-shadow 0.2s; }
        .pub-kpi-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.1); }
        .pub-kpi-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.25rem; flex-shrink: 0; }
        .pub-kpi-label { font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.25rem; }
        .pub-kpi-value { font-size: 1.5rem; font-weight: 700; line-height: 1.2; }

        .pub-card { background: white; border-radius: 12px; padding: 1.25rem; box-shadow: 0 2px 12px rgba(0,0,0,0.06); margin-bottom: 1.5rem; }
        .pub-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
        .pub-card-title { margin: 0; font-size: 0.95rem; font-weight: 600; color: #333; }
        .pub-card-link { font-size: 0.8rem; color: #1abc9c; text-decoration: none; font-weight: 500; }
        .pub-card-link:hover { text-decoration: underline; }

        .pub-grid-2col { display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 1.5rem; }

        .pub-keyword-tags { display: flex; flex-wrap: wrap; gap: 0.5rem; }
        .pub-keyword-tag { display: inline-flex; align-items: center; gap: 0.375rem; padding: 0.4rem 0.75rem; color: white; border-radius: 20px; font-size: 0.8rem; font-weight: 500; }
        .pub-keyword-rate { font-size: 0.65rem; background: rgba(255,255,255,0.25); padding: 0.1rem 0.35rem; border-radius: 8px; }
        .pub-keyword-count { font-size: 0.65rem; background: rgba(255,255,255,0.25); padding: 0.1rem 0.35rem; border-radius: 8px; }

        .pub-table { width: 100%; border-collapse: collapse; }
        .pub-table thead tr { background: #f8f9fa; }
        .pub-table th { padding: 0.625rem 0.75rem; text-align: left; font-size: 0.75rem; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }
        .pub-table td { padding: 0.625rem 0.75rem; font-size: 0.85rem; border-bottom: 1px solid #f0f0f0; }
        .pub-table tbody tr:hover { background: #f0faf8; }
        .pub-table tbody tr:last-child td { border-bottom: none; }

        .pub-rank { display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; border-radius: 50%; font-size: 0.7rem; font-weight: 700; background: #eee; color: #666; }
        .pub-rank-1 { background: #ffd700; color: #7a6100; }
        .pub-rank-2 { background: #c0c0c0; color: #555; }
        .pub-rank-3 { background: #cd7f32; color: white; }
        .pub-allergen-name { font-weight: 500; }
        .pub-rate-badge { display: inline-block; padding: 0.2rem 0.5rem; background: #e8f8f5; color: #16a085; border-radius: 12px; font-weight: 600; font-size: 0.8rem; }
        .pub-muted { color: #888; }
        .pub-empty { color: #aaa; font-size: 0.85rem; text-align: center; padding: 1.5rem 0; margin: 0; }

        @media (max-width: 1024px) { .pub-kpi-grid { grid-template-columns: repeat(2, 1fr); } }
        @media (max-width: 640px) {
          .pub-kpi-grid { grid-template-columns: 1fr; }
          .pub-grid-2col { grid-template-columns: 1fr; }
        }
      `}</style>
    </div>
  );
};

const KpiCard = ({ icon, label, value, color = '#333' }) => (
  <div className="pub-kpi-card">
    <div className="pub-kpi-icon" style={{ background: `${color}15`, color }}>{icon}</div>
    <div>
      <div className="pub-kpi-label">{label}</div>
      <div className="pub-kpi-value" style={{ color }}>{value}</div>
    </div>
  </div>
);

export default AnalyticsDashboard;
