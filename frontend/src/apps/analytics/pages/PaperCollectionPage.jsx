/**
 * 논문 수집정보 페이지 (공개, read-only)
 * 출처별/연도별 수집 현황, 알러젠 연결 TOP15, 최근 수집
 */
import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { analyticsApi } from '../services/analyticsApi';

const COLORS = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22', '#667eea'];

const SOURCE_NAMES = {
  pubmed: 'PubMed',
  semantic_scholar: 'Semantic Scholar',
  manual: '직접 입력',
  unknown: '미분류',
};

const LINK_TYPE_NAMES = {
  symptom: '증상',
  dietary: '식이',
  cross_reactivity: '교차반응',
  substitute: '대체식품',
  emergency: '응급',
  management: '관리',
  general: '일반',
};

const PaperCollectionPage = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await analyticsApi.getPaperStats();
      setData(result);
    } catch (err) {
      setError('논문 수집정보를 불러오지 못했습니다.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <p className="pc-loading">로딩 중...</p>;
  if (error) return <div className="pc-error">{error} <button onClick={loadData} className="pc-retry-btn">재시도</button></div>;
  if (!data) return <p className="pc-empty">논문 수집정보가 없습니다.</p>;

  const sourceChartData = Object.entries(data.by_source || {}).map(([name, value]) => ({
    name: SOURCE_NAMES[name] || name,
    value,
  }));

  const yearEntries = Object.entries(data.by_year || {})
    .filter(([yr]) => yr !== 'None')
    .sort((a, b) => Number(a[0]) - Number(b[0]))
    .slice(-10);
  const yearChartData = yearEntries.map(([year, count]) => ({ year, count }));

  const topAllergenLinks = data.top_allergen_links || [];
  const recentPapers = data.recent_papers || [];
  const linkTypeData = Object.entries(data.by_link_type || {}).map(([name, value]) => ({
    name: LINK_TYPE_NAMES[name] || name,
    value,
  }));

  return (
    <div style={{ padding: '1rem' }}>
      <h2 className="pc-page-title">논문 수집정보</h2>

      {/* 상단 정보 바 */}
      <div className="pc-info-bar">
        <div className="pc-info-items">
          <span className="pc-info-item">전체 논문: <strong>{data.total}건</strong></span>
          <span className="pc-info-item">가이드라인: <strong>{data.guideline_count}건</strong></span>
          <span className="pc-info-item">출처: <strong>{Object.keys(data.by_source || {}).length}종</strong></span>
          <span className="pc-info-item">알러젠 연결: <strong>{topAllergenLinks.length}종</strong></span>
        </div>
        <button onClick={loadData} className="pc-refresh-btn">새로고침</button>
      </div>

      {/* 출처별 / 연도별 차트 */}
      <div className="pc-grid-2col" style={{ marginBottom: '1.5rem' }}>
        {sourceChartData.length > 0 && (
          <div className="pc-card">
            <h4 className="pc-card-title">출처별 수집 현황</h4>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={sourceChartData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} innerRadius={50}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={{ stroke: '#ccc' }}>
                  {sourceChartData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #eee' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {yearChartData.length > 0 && (
          <div className="pc-card">
            <h4 className="pc-card-title">연도별 논문 분포 (최근 10년)</h4>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={yearChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="year" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #eee', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
                <Bar dataKey="count" name="논문 수" fill="#1abc9c" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* 연결 유형별 / 알러젠 연결 TOP 15 */}
      <div className="pc-grid-2col" style={{ marginBottom: '1.5rem' }}>
        {linkTypeData.length > 0 && (
          <div className="pc-card">
            <h4 className="pc-card-title">연결 유형별 분포</h4>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={linkTypeData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} innerRadius={50}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={{ stroke: '#ccc' }}>
                  {linkTypeData.map((_, i) => <Cell key={i} fill={COLORS[(i + 3) % COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #eee' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {topAllergenLinks.length > 0 && (
          <div className="pc-card">
            <h4 className="pc-card-title">알러젠별 논문 연결 현황 (TOP 15)</h4>
            <table className="pc-table">
              <thead><tr><th>순위</th><th>알러젠</th><th>연결 논문 수</th></tr></thead>
              <tbody>
                {topAllergenLinks.map((item, i) => (
                  <tr key={item.allergen_code}>
                    <td><span className={`pc-rank ${i < 3 ? `pc-rank-${i + 1}` : ''}`}>{i + 1}</span></td>
                    <td style={{ fontWeight: 500 }}>{item.allergen_code}</td>
                    <td style={{ fontWeight: 600, color: '#1abc9c' }}>{item.paper_count}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>

      {/* 최근 수집 논문 */}
      <div className="pc-card">
        <h4 className="pc-card-title">최근 수집 논문 (10건)</h4>
        {recentPapers.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {recentPapers.map((paper, i) => (
              <div key={i} className="pc-recent-item">
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: 500, color: '#333', marginBottom: '0.25rem', lineHeight: 1.4 }}>
                    {paper.title}
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', fontSize: '0.75rem', color: '#888' }}>
                    {paper.source && <span className="pc-badge-source">{SOURCE_NAMES[paper.source] || paper.source}</span>}
                    {paper.year && <span>{paper.year}</span>}
                    {paper.is_guideline && <span style={{ color: '#2e7d32', fontWeight: 500 }}>가이드라인</span>}
                    {paper.created_at && <span>수집: {new Date(paper.created_at).toLocaleDateString('ko-KR')}</span>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p className="pc-empty">수집된 논문이 없습니다.</p>
        )}
      </div>

      <style>{`
        .pc-page-title { margin-bottom: 1.25rem; font-size: 1.25rem; font-weight: 700; color: #2c3e50; }
        .pc-loading { padding: 2rem; text-align: center; color: #888; }
        .pc-error { color: #e74c3c; padding: 1rem; }
        .pc-retry-btn { margin-left: 0.5rem; padding: 0.25rem 0.75rem; border: 1px solid #e74c3c; border-radius: 4px; background: white; color: #e74c3c; cursor: pointer; }
        .pc-empty { color: #aaa; font-size: 0.85rem; text-align: center; padding: 2rem 0; }
        .pc-info-bar { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; margin-bottom: 1.5rem; padding: 0.75rem 1rem; background: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
        .pc-info-items { display: flex; gap: 1.5rem; flex-wrap: wrap; }
        .pc-info-item { font-size: 0.85rem; color: #666; }
        .pc-info-item strong { color: #333; }
        .pc-refresh-btn { padding: 0.5rem 1rem; background: linear-gradient(135deg, #1abc9c, #16a085); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.85rem; font-weight: 500; transition: opacity 0.2s; }
        .pc-refresh-btn:hover { opacity: 0.85; }
        .pc-grid-2col { display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 1.5rem; }
        .pc-card { background: white; border-radius: 12px; padding: 1.25rem; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
        .pc-card-title { margin: 0 0 1rem 0; font-size: 0.95rem; font-weight: 600; color: #333; }
        .pc-table { width: 100%; border-collapse: collapse; }
        .pc-table thead tr { background: #f8f9fa; }
        .pc-table th { padding: 0.625rem 0.75rem; text-align: left; font-size: 0.75rem; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }
        .pc-table td { padding: 0.625rem 0.75rem; font-size: 0.85rem; border-bottom: 1px solid #f0f0f0; }
        .pc-table tbody tr:hover { background: #f0faf8; }
        .pc-table tbody tr:last-child td { border-bottom: none; }
        .pc-rank { display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; border-radius: 50%; font-size: 0.7rem; font-weight: 700; background: #eee; color: #666; }
        .pc-rank-1 { background: #ffd700; color: #7a6100; }
        .pc-rank-2 { background: #c0c0c0; color: #555; }
        .pc-rank-3 { background: #cd7f32; color: white; }
        .pc-recent-item { display: flex; align-items: flex-start; padding: 0.75rem; background: #f8f9fa; border-radius: 8px; border-left: 3px solid #1abc9c; }
        .pc-badge-source { padding: 0.1rem 0.4rem; background: #f3e5f5; color: #7b1fa2; border-radius: 4px; font-size: 0.7rem; font-weight: 500; }
        @media (max-width: 640px) { .pc-grid-2col { grid-template-columns: 1fr; } }
      `}</style>
    </div>
  );
};

export default PaperCollectionPage;
