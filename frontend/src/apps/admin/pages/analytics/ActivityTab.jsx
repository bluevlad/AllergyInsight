/**
 * 활동 통계 탭 - 사용자 행동 로그 분석
 */
import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { adminApi } from '../../services/adminApi';

const COLORS = ['#9b59b6', '#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#1abc9c', '#e67e22', '#667eea'];

const ActivityTab = () => {
  const [days, setDays] = useState(30);
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, [days]);

  const loadData = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await adminApi.analytics.activityStats({ days });
      setData(result);
    } catch (err) {
      setError('활동 통계를 불러오지 못했습니다.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <p>로딩 중...</p>;
  if (error) return <div style={{ color: '#e74c3c', padding: '1rem' }}>{error} <button onClick={loadData}>재시도</button></div>;
  if (!data) return <p style={{ color: '#888', padding: '1rem' }}>데이터가 없습니다.</p>;

  const actionData = data.by_action ? Object.entries(data.by_action).map(([name, value]) => ({ name, value })) : [];
  const resourceData = data.by_resource ? Object.entries(data.by_resource).map(([name, value]) => ({ name, value })) : [];
  const dailyData = data.daily_trend || [];

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        <label>기간: </label>
        <select value={days} onChange={e => setDays(Number(e.target.value))} style={{ padding: '0.5rem', borderRadius: '6px', border: '1px solid #ddd' }}>
          <option value={7}>7일</option>
          <option value={14}>14일</option>
          <option value={30}>30일</option>
          <option value={90}>90일</option>
        </select>
        <button onClick={loadData} style={{ padding: '0.5rem 1rem', background: '#9b59b6', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>
          새로고침
        </button>
      </div>

      {/* KPI 카드 */}
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        <KpiCard label="총 활동 수" value={data.total_logs?.toLocaleString() ?? '-'} />
        <KpiCard label="고유 사용자" value={data.unique_users?.toLocaleString() ?? '-'} color="#3498db" />
      </div>

      {/* 일별 활동 추이 */}
      {dailyData.length > 0 && (
        <div style={{ background: 'white', borderRadius: '8px', padding: '1rem', marginBottom: '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}>
          <h4 style={{ margin: '0 0 1rem 0' }}>일별 활동 추이</h4>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={dailyData}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" tickFormatter={v => v?.slice(5)} />
              <YAxis />
              <Tooltip />
              <Legend />
              <Line type="monotone" dataKey="count" name="활동 수" stroke="#9b59b6" strokeWidth={2} dot={{ r: 3 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem' }}>
        {/* 행동 유형별 분포 */}
        {actionData.length > 0 && (
          <div style={{ background: 'white', borderRadius: '8px', padding: '1rem', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}>
            <h4 style={{ margin: '0 0 1rem 0' }}>행동 유형별 분포</h4>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={actionData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}>
                  {actionData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* 리소스 유형별 */}
        {resourceData.length > 0 && (
          <div style={{ background: 'white', borderRadius: '8px', padding: '1rem', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}>
            <h4 style={{ margin: '0 0 1rem 0' }}>리소스 유형별</h4>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={resourceData} layout="vertical" margin={{ left: 80 }}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis type="number" />
                <YAxis dataKey="name" type="category" width={70} />
                <Tooltip />
                <Bar dataKey="value" name="건수" fill="#3498db" radius={[0, 4, 4, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {actionData.length === 0 && resourceData.length === 0 && dailyData.length === 0 && (
        <p style={{ color: '#888', textAlign: 'center', padding: '2rem' }}>해당 기간에 활동 데이터가 없습니다.</p>
      )}
    </div>
  );
};

const KpiCard = ({ label, value, color }) => (
  <div style={{ background: 'white', padding: '0.75rem 1.25rem', borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}>
    <span style={{ fontSize: '0.85rem', color: '#888' }}>{label} </span>
    <span style={{ fontSize: '1.1rem', fontWeight: 700, color: color || '#333' }}>{value}</span>
  </div>
);

export default ActivityTab;
