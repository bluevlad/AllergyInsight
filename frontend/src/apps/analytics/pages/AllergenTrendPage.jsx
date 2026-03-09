/**
 * Allergen Trend Page - 알러젠 트렌드 분석
 */
import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, LineChart, Line, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { analyticsApi } from '../services/analyticsApi';

const COLORS = ['#1abc9c', '#3498db', '#9b59b6', '#e74c3c', '#f39c12', '#2ecc71', '#e67e22', '#667eea'];

const AllergenTrendPage = () => {
  const [allergens, setAllergens] = useState([]);
  const [selectedAllergen, setSelectedAllergen] = useState('');
  const [trendData, setTrendData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [trendLoading, setTrendLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => { loadOverview(); }, []);

  const loadOverview = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await analyticsApi.getOverview();
      const items = Array.isArray(data) ? data : (data?.allergens || []);
      setAllergens(items);
      if (items.length > 0 && !selectedAllergen) {
        setSelectedAllergen(items[0].allergen_code);
        loadTrend(items[0].allergen_code);
      }
    } catch {
      setError('알러젠 목록을 불러올 수 없습니다.');
    } finally {
      setLoading(false);
    }
  };

  const loadTrend = async (code) => {
    if (!code) { setTrendData([]); return; }
    try {
      setTrendLoading(true);
      const data = await analyticsApi.getAllergenTrend(code, 12);
      setTrendData(Array.isArray(data) ? data : (data?.trend || []));
    } catch {
      setTrendData([]);
    } finally {
      setTrendLoading(false);
    }
  };

  const handleSelect = (code) => {
    setSelectedAllergen(code);
    loadTrend(code);
  };

  if (loading) {
    return <div className="pub-loading"><div className="pub-spinner" /><p>로딩 중...</p></div>;
  }

  const top10 = allergens.slice(0, 10);
  const barData = top10.map(a => ({
    name: a.allergen_code,
    양성률: +((a.positive_rate || 0) * 100).toFixed(1),
  }));

  const trendChartData = trendData.map(t => ({
    period: (t.period || '').slice(0, 7),
    양성률: +((t.positive_rate || 0) * 100).toFixed(1),
    평균등급: +(t.avg_grade || 0).toFixed(2),
  }));

  const latestTrend = trendData.length > 0 ? trendData[trendData.length - 1] : null;
  const gradeDistData = latestTrend?.grade_distribution
    ? Object.entries(latestTrend.grade_distribution).map(([grade, count]) => ({ name: `${grade}등급`, value: count }))
    : [];

  const selectedDetail = allergens.find(a => a.allergen_code === selectedAllergen);
  const cooccurrence = selectedDetail?.cooccurrence_top5 || [];

  return (
    <div className="pub-page">
      <h2 className="pub-page-title">알러젠 트렌드 분석</h2>

      {error && (
        <div className="pub-error-banner">{error} <button onClick={loadOverview} className="pub-retry-sm">재시도</button></div>
      )}

      {/* TOP 10 Chart */}
      {barData.length > 0 && (
        <div className="pub-card">
          <h3 className="pub-card-title">알러젠 양성률 TOP 10</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="name" tick={{ fontSize: 11 }} />
              <YAxis unit="%" tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #eee', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} formatter={(v) => [`${v}%`, '양성률']} />
              <Bar dataKey="양성률" radius={[6, 6, 0, 0]}>
                {barData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
              </Bar>
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Allergen Selector */}
      {allergens.length > 0 && (
        <div className="pub-card">
          <h3 className="pub-card-title">알러젠별 상세 분석</h3>
          <div className="pub-allergen-pills">
            {allergens.map(a => (
              <button
                key={a.allergen_code}
                onClick={() => handleSelect(a.allergen_code)}
                className={`pub-pill ${selectedAllergen === a.allergen_code ? 'active' : ''}`}
              >
                {a.allergen_name || a.allergen_code}
                <span className="pub-pill-rate">{((a.positive_rate || 0) * 100).toFixed(0)}%</span>
              </button>
            ))}
          </div>
        </div>
      )}

      {/* Trend Charts */}
      {trendLoading && <div className="pub-loading-inline"><div className="pub-spinner-sm" /><span>트렌드 로딩 중...</span></div>}

      {!trendLoading && selectedAllergen && trendChartData.length > 0 && (
        <div className="pub-grid-2col">
          <div className="pub-card">
            <h3 className="pub-card-title">{selectedAllergen} 양성률 / 평균등급 추이</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trendChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="period" tick={{ fontSize: 11 }} />
                <YAxis yAxisId="left" unit="%" tick={{ fontSize: 11 }} />
                <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #eee', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
                <Legend />
                <Line yAxisId="left" type="monotone" dataKey="양성률" stroke="#1abc9c" strokeWidth={2.5} dot={{ r: 4, fill: '#1abc9c' }} activeDot={{ r: 6 }} />
                <Line yAxisId="right" type="monotone" dataKey="평균등급" stroke="#3498db" strokeWidth={2.5} dot={{ r: 4, fill: '#3498db' }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>

          {gradeDistData.length > 0 && (
            <div className="pub-card">
              <h3 className="pub-card-title">등급 분포 (최근 월)</h3>
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie data={gradeDistData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} innerRadius={50}
                    label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={{ stroke: '#ccc' }}>
                    {gradeDistData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                  </Pie>
                  <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #eee' }} />
                </PieChart>
              </ResponsiveContainer>
            </div>
          )}
        </div>
      )}

      {/* Co-occurrence */}
      {cooccurrence.length > 0 && (
        <div className="pub-card">
          <h3 className="pub-card-title">동반 양성 알러젠 (TOP 5)</h3>
          <table className="pub-table">
            <thead><tr><th>순위</th><th>알러젠</th><th>동반 건수</th><th>동반률</th></tr></thead>
            <tbody>
              {cooccurrence.map((c, i) => (
                <tr key={i}>
                  <td><span className={`pub-rank pub-rank-${i+1}`}>{i+1}</span></td>
                  <td className="pub-allergen-name">{c.allergen}</td>
                  <td>{c.count?.toLocaleString()}</td>
                  <td><span className="pub-rate-badge">{(c.rate * 100).toFixed(1)}%</span></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {!trendLoading && selectedAllergen && trendChartData.length === 0 && !error && (
        <div className="pub-card"><p className="pub-empty">선택한 알러젠에 대한 트렌드 데이터가 없습니다.</p></div>
      )}

      {allergens.length === 0 && !error && (
        <div className="pub-card"><p className="pub-empty">알러젠 데이터가 없습니다. 집계가 실행되면 표시됩니다.</p></div>
      )}

      <style>{`
        .pub-page { padding: 1rem; }
        .pub-page-title { margin-bottom: 1.25rem; font-size: 1.25rem; font-weight: 700; color: #2c3e50; }
        .pub-loading { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px; gap: 1rem; color: #888; }
        .pub-spinner { width: 40px; height: 40px; border: 4px solid #e9ecef; border-top: 4px solid #1abc9c; border-radius: 50%; animation: pub-spin 1s linear infinite; }
        @keyframes pub-spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .pub-loading-inline { display: flex; align-items: center; gap: 0.75rem; padding: 1.5rem; background: white; border-radius: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.06); color: #888; margin-bottom: 1.5rem; }
        .pub-spinner-sm { width: 24px; height: 24px; border: 3px solid #e9ecef; border-top: 3px solid #1abc9c; border-radius: 50%; animation: pub-spin 1s linear infinite; }
        .pub-error-banner { display: flex; align-items: center; gap: 1rem; padding: 0.75rem 1rem; background: #fdecea; color: #c0392b; border-radius: 8px; margin-bottom: 1rem; font-size: 0.9rem; }
        .pub-retry-sm { padding: 0.3rem 0.7rem; background: #e74c3c; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.8rem; margin-left: auto; }

        .pub-card { background: white; border-radius: 12px; padding: 1.25rem; box-shadow: 0 2px 12px rgba(0,0,0,0.06); margin-bottom: 1.5rem; }
        .pub-card-title { margin: 0 0 1rem 0; font-size: 0.95rem; font-weight: 600; color: #333; }
        .pub-grid-2col { display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 1.5rem; margin-bottom: 1.5rem; }

        .pub-allergen-pills { display: flex; flex-wrap: wrap; gap: 0.375rem; }
        .pub-pill { display: inline-flex; align-items: center; gap: 0.35rem; padding: 0.4rem 0.75rem; border: 1px solid #ddd; border-radius: 20px; background: white; cursor: pointer; font-size: 0.8rem; color: #555; transition: all 0.2s; }
        .pub-pill:hover { border-color: #1abc9c; color: #1abc9c; }
        .pub-pill.active { background: #1abc9c; color: white; border-color: #1abc9c; }
        .pub-pill-rate { font-size: 0.65rem; opacity: 0.75; }

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
        .pub-empty { color: #aaa; font-size: 0.85rem; text-align: center; padding: 1.5rem 0; margin: 0; }

        @media (max-width: 640px) { .pub-grid-2col { grid-template-columns: 1fr; } }
      `}</style>
    </div>
  );
};

export default AllergenTrendPage;
