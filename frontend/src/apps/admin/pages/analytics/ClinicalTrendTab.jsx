/**
 * 임상 트렌드 탭 - 알러젠 양성률 분석
 */
import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { adminApi } from '../../services/adminApi';

const COLORS = ['#9b59b6', '#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#1abc9c', '#e67e22', '#667eea'];

const ClinicalTrendTab = () => {
  const [overview, setOverview] = useState(null);
  const [selectedAllergen, setSelectedAllergen] = useState('');
  const [trendData, setTrendData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadOverview();
  }, []);

  useEffect(() => {
    if (selectedAllergen) loadTrend(selectedAllergen);
  }, [selectedAllergen]);

  const loadOverview = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await adminApi.analytics.overview();
      setOverview(result);
      if (result.allergens?.length > 0 && !selectedAllergen) {
        setSelectedAllergen(result.allergens[0].allergen_code);
      }
    } catch (err) {
      setError('임상 트렌드 데이터를 불러오지 못했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const loadTrend = async (code) => {
    try {
      const result = await adminApi.analytics.trend(code, { limit: 12 });
      setTrendData(result);
    } catch (err) {
      console.error('Trend load failed:', err);
    }
  };

  if (loading) return <p style={{ padding: '2rem', textAlign: 'center', color: '#888' }}>로딩 중...</p>;
  if (error) return <div style={{ color: '#e74c3c', padding: '1rem' }}>{error} <button onClick={loadOverview} style={{ marginLeft: '0.5rem', padding: '0.25rem 0.75rem', border: '1px solid #e74c3c', borderRadius: '4px', background: 'white', color: '#e74c3c', cursor: 'pointer' }}>재시도</button></div>;
  if (!overview) return <p className="ai-empty-text">데이터가 없습니다. 먼저 집계를 실행해주세요.</p>;

  const allergens = overview.allergens || [];
  const top10 = allergens.slice(0, 10);
  const barData = top10.map(a => ({
    name: a.allergen_code,
    양성률: +(a.positive_rate * 100).toFixed(1),
  }));

  const selectedDetail = allergens.find(a => a.allergen_code === selectedAllergen);
  const trendChartData = (trendData?.trend || []).map(t => ({
    period: t.period?.slice(0, 7),
    양성률: +(t.positive_rate * 100).toFixed(1),
    평균등급: +t.avg_grade?.toFixed(2),
  }));

  const gradeDistData = trendData?.trend?.length > 0
    ? Object.entries(trendData.trend[trendData.trend.length - 1].grade_distribution || {}).map(([grade, count]) => ({
        name: `${grade}등급`,
        value: count,
      }))
    : [];

  const cooccurrence = selectedDetail?.cooccurrence_top5 || [];

  return (
    <div>
      {/* 상단 정보 바 */}
      <div className="ai-info-bar">
        <div className="ai-info-items">
          <span className="ai-info-item">기준: <strong>{overview.latest_period?.slice(0, 7) || '-'}</strong></span>
          <span className="ai-info-item">알러젠: <strong>{overview.total_allergens ?? '-'}종</strong></span>
          <span className="ai-info-item">검사: <strong>{overview.total_tests?.toLocaleString() ?? '-'}건</strong></span>
        </div>
        <button onClick={loadOverview} className="ai-refresh-btn">새로고침</button>
      </div>

      {/* 양성률 TOP 10 차트 */}
      {barData.length > 0 && (
        <div className="ai-card" style={{ marginBottom: '1.5rem' }}>
          <h4 className="ai-card-title">알러젠 양성률 TOP 10</h4>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="name" tick={{ fontSize: 12 }} />
              <YAxis unit="%" tick={{ fontSize: 12 }} />
              <Tooltip
                contentStyle={{ borderRadius: '8px', border: '1px solid #eee', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }}
                formatter={(value) => [`${value}%`, '양성률']}
              />
              <Bar dataKey="양성률" fill="#9b59b6" radius={[6, 6, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* 알러젠 선택 */}
      <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
        <label style={{ fontSize: '0.85rem', color: '#666' }}>알러젠 선택:</label>
        <select
          value={selectedAllergen}
          onChange={e => setSelectedAllergen(e.target.value)}
          style={{ padding: '0.5rem 0.75rem', borderRadius: '6px', border: '1px solid #ddd', fontSize: '0.85rem' }}
        >
          {allergens.map(a => (
            <option key={a.allergen_code} value={a.allergen_code}>{a.allergen_code}</option>
          ))}
        </select>
      </div>

      <div className="ai-grid-2col" style={{ marginBottom: '1.5rem' }}>
        {/* 양성률/평균등급 추이 */}
        {trendChartData.length > 0 && (
          <div className="ai-card">
            <h4 className="ai-card-title">{selectedAllergen} 양성률 / 평균등급 추이</h4>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trendChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="period" tick={{ fontSize: 11 }} />
                <YAxis yAxisId="left" unit="%" tick={{ fontSize: 11 }} />
                <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #eee', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
                <Legend />
                <Line yAxisId="left" type="monotone" dataKey="양성률" stroke="#9b59b6" strokeWidth={2.5} dot={{ r: 4, fill: '#9b59b6' }} activeDot={{ r: 6 }} />
                <Line yAxisId="right" type="monotone" dataKey="평균등급" stroke="#3498db" strokeWidth={2.5} dot={{ r: 4, fill: '#3498db' }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* 등급 분포 파이 차트 */}
        {gradeDistData.length > 0 && (
          <div className="ai-card">
            <h4 className="ai-card-title">등급 분포 (최근 월)</h4>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={gradeDistData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} innerRadius={50}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  labelLine={{ stroke: '#ccc' }}
                >
                  {gradeDistData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #eee' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* 동반 양성 알러젠 */}
      {cooccurrence.length > 0 && (
        <div className="ai-card">
          <h4 className="ai-card-title">동반 양성 알러젠 (TOP 5)</h4>
          <table className="ai-table">
            <thead>
              <tr>
                <th>순위</th>
                <th>알러젠</th>
                <th>동반 건수</th>
                <th>동반률</th>
              </tr>
            </thead>
            <tbody>
              {cooccurrence.map((c, i) => (
                <tr key={i}>
                  <td><span className={`ai-rank ai-rank-${i + 1}`}>{i + 1}</span></td>
                  <td style={{ fontWeight: 500 }}>{c.allergen}</td>
                  <td>{c.count?.toLocaleString()}</td>
                  <td style={{ fontWeight: 600, color: '#9b59b6' }}>{(c.rate * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {allergens.length === 0 && (
        <p className="ai-empty-text">임상 트렌드 데이터가 없습니다. 집계를 먼저 실행해주세요.</p>
      )}

      <style>{`
        .ai-info-bar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          flex-wrap: wrap;
          gap: 1rem;
          margin-bottom: 1.5rem;
          padding: 0.75rem 1rem;
          background: white;
          border-radius: 10px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        .ai-info-items { display: flex; gap: 1.5rem; flex-wrap: wrap; }
        .ai-info-item { font-size: 0.85rem; color: #666; }
        .ai-info-item strong { color: #333; }
        .ai-refresh-btn {
          padding: 0.5rem 1rem;
          background: linear-gradient(135deg, #9b59b6, #8e44ad);
          color: white; border: none; border-radius: 6px;
          cursor: pointer; font-size: 0.85rem; font-weight: 500;
          transition: opacity 0.2s;
        }
        .ai-refresh-btn:hover { opacity: 0.85; }
        .ai-grid-2col {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
          gap: 1.5rem;
        }
        .ai-card {
          background: white; border-radius: 12px; padding: 1.25rem;
          box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        }
        .ai-card-title { margin: 0 0 1rem 0; font-size: 0.95rem; font-weight: 600; color: #333; }
        .ai-table { width: 100%; border-collapse: collapse; }
        .ai-table thead tr { background: #f8f9fa; }
        .ai-table th { padding: 0.625rem 0.75rem; text-align: left; font-size: 0.75rem; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }
        .ai-table td { padding: 0.625rem 0.75rem; font-size: 0.85rem; border-bottom: 1px solid #f0f0f0; }
        .ai-table tbody tr:hover { background: #faf8fc; }
        .ai-table tbody tr:last-child td { border-bottom: none; }
        .ai-rank { display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; border-radius: 50%; font-size: 0.7rem; font-weight: 700; background: #eee; color: #666; }
        .ai-rank-1 { background: #ffd700; color: #7a6100; }
        .ai-rank-2 { background: #c0c0c0; color: #555; }
        .ai-rank-3 { background: #cd7f32; color: white; }
        .ai-empty-text { color: #aaa; font-size: 0.85rem; text-align: center; padding: 2rem 0; margin: 0; }
        @media (max-width: 640px) { .ai-grid-2col { grid-template-columns: 1fr; } }
      `}</style>
    </div>
  );
};

export default ClinicalTrendTab;
