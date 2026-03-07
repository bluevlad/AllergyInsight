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

  if (loading) return <p>로딩 중...</p>;
  if (error) return <div style={{ color: '#e74c3c', padding: '1rem' }}>{error} <button onClick={loadOverview}>재시도</button></div>;
  if (!overview) return <p style={{ color: '#888', padding: '1rem' }}>데이터가 없습니다. 먼저 집계를 실행해주세요.</p>;

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
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        <span style={{ fontSize: '0.85rem', color: '#888' }}>기준 기간: {overview.latest_period?.slice(0, 7) || '-'}</span>
        <span style={{ fontSize: '0.85rem', color: '#888' }}>총 알러젠: {overview.total_allergens ?? '-'}</span>
        <span style={{ fontSize: '0.85rem', color: '#888' }}>총 검사: {overview.total_tests?.toLocaleString() ?? '-'}</span>
        <button onClick={loadOverview} style={{ padding: '0.5rem 1rem', background: '#9b59b6', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>
          새로고침
        </button>
      </div>

      {/* 알러젠 양성률 TOP 10 */}
      {barData.length > 0 && (
        <div style={{ background: 'white', borderRadius: '8px', padding: '1rem', marginBottom: '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}>
          <h4 style={{ margin: '0 0 1rem 0' }}>알러젠 양성률 TOP 10 (%)</h4>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={barData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="name" />
              <YAxis unit="%" />
              <Tooltip />
              <Legend />
              <Bar dataKey="양성률" fill="#9b59b6" radius={[4, 4, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* 알러젠 선택 + 추이 */}
      <div style={{ marginBottom: '1rem' }}>
        <label>알러젠 선택: </label>
        <select value={selectedAllergen} onChange={e => setSelectedAllergen(e.target.value)} style={{ padding: '0.5rem', borderRadius: '6px', border: '1px solid #ddd' }}>
          {allergens.map(a => (
            <option key={a.allergen_code} value={a.allergen_code}>{a.allergen_code}</option>
          ))}
        </select>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem', marginBottom: '1.5rem' }}>
        {/* 양성률/평균등급 추이 */}
        {trendChartData.length > 0 && (
          <div style={{ background: 'white', borderRadius: '8px', padding: '1rem', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}>
            <h4 style={{ margin: '0 0 1rem 0' }}>{selectedAllergen} 양성률/평균등급 추이</h4>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trendChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="period" />
                <YAxis yAxisId="left" unit="%" />
                <YAxis yAxisId="right" orientation="right" />
                <Tooltip />
                <Legend />
                <Line yAxisId="left" type="monotone" dataKey="양성률" stroke="#9b59b6" strokeWidth={2} dot={{ r: 3 }} />
                <Line yAxisId="right" type="monotone" dataKey="평균등급" stroke="#3498db" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* 등급 분포 */}
        {gradeDistData.length > 0 && (
          <div style={{ background: 'white', borderRadius: '8px', padding: '1rem', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}>
            <h4 style={{ margin: '0 0 1rem 0' }}>등급 분포 (최근 월)</h4>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={gradeDistData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                  {gradeDistData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* 동반 양성 알러젠 테이블 */}
      {cooccurrence.length > 0 && (
        <div style={{ background: 'white', borderRadius: '8px', padding: '1rem', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}>
          <h4 style={{ margin: '0 0 1rem 0' }}>동반 양성 알러젠 (TOP 5)</h4>
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ background: '#f8f9fa', textAlign: 'left' }}>
                <th style={{ padding: '0.75rem' }}>알러젠</th>
                <th style={{ padding: '0.75rem' }}>동반 건수</th>
                <th style={{ padding: '0.75rem' }}>동반률</th>
              </tr>
            </thead>
            <tbody>
              {cooccurrence.map((c, i) => (
                <tr key={i} style={{ borderBottom: '1px solid #eee' }}>
                  <td style={{ padding: '0.75rem' }}>{c.allergen}</td>
                  <td style={{ padding: '0.75rem' }}>{c.count}</td>
                  <td style={{ padding: '0.75rem' }}>{(c.rate * 100).toFixed(1)}%</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {allergens.length === 0 && (
        <p style={{ color: '#888', textAlign: 'center', padding: '2rem' }}>임상 트렌드 데이터가 없습니다. 집계를 먼저 실행해주세요.</p>
      )}
    </div>
  );
};

export default ClinicalTrendTab;
