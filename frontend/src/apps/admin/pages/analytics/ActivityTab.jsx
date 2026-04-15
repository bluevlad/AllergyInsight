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

  if (loading) return <p style={{ padding: '2rem', textAlign: 'center', color: '#888' }}>로딩 중...</p>;
  if (error) return <div style={{ color: '#e74c3c', padding: '1rem' }}>{error} <button onClick={loadData} style={{ marginLeft: '0.5rem', padding: '0.25rem 0.75rem', border: '1px solid #e74c3c', borderRadius: '4px', background: 'white', color: '#e74c3c', cursor: 'pointer' }}>재시도</button></div>;
  if (!data) return <p className="ai-empty-text">데이터가 없습니다.</p>;

  const actionData = data.by_action ? Object.entries(data.by_action).map(([name, value]) => ({ name, value })) : [];
  const resourceData = data.by_resource ? Object.entries(data.by_resource).map(([name, value]) => ({ name, value })) : [];
  const dailyData = data.daily_trend || [];

  const hasData = actionData.length > 0 || resourceData.length > 0 || dailyData.length > 0;

  return (
    <div>
      {/* 상단 컨트롤 */}
      <div className="ai-info-bar">
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <label style={{ fontSize: '0.85rem', color: '#666' }}>기간:</label>
          <div className="at-period-tabs">
            {[
              { value: 7, label: '7일' },
              { value: 14, label: '14일' },
              { value: 30, label: '30일' },
              { value: 90, label: '90일' },
            ].map(opt => (
              <button
                key={opt.value}
                onClick={() => setDays(opt.value)}
                className={`at-period-tab ${days === opt.value ? 'active' : ''}`}
              >
                {opt.label}
              </button>
            ))}
          </div>
        </div>
        <button onClick={loadData} className="ai-refresh-btn">새로고침</button>
      </div>

      {/* KPI 카드 */}
      <div className="at-kpi-row">
        <div className="ai-kpi-card">
          <div className="ai-kpi-icon" style={{ background: '#9b59b615', color: '#9b59b6' }}>📊</div>
          <div className="ai-kpi-info">
            <div className="ai-kpi-label">총 활동 수</div>
            <div className="ai-kpi-value" style={{ color: '#9b59b6' }}>{data.total_logs?.toLocaleString() ?? '-'}</div>
            <div className="ai-kpi-sub">최근 {days}일</div>
          </div>
        </div>
        <div className="ai-kpi-card">
          <div className="ai-kpi-icon" style={{ background: '#3498db15', color: '#3498db' }}>👤</div>
          <div className="ai-kpi-info">
            <div className="ai-kpi-label">고유 사용자</div>
            <div className="ai-kpi-value" style={{ color: '#3498db' }}>{data.unique_users?.toLocaleString() ?? '-'}</div>
            <div className="ai-kpi-sub">활성 사용자</div>
          </div>
        </div>
      </div>

      {/* 일별 활동 추이 */}
      {dailyData.length > 0 && (
        <div className="ai-card" style={{ marginBottom: '1.5rem' }}>
          <h4 className="ai-card-title">일별 활동 추이</h4>
          <ResponsiveContainer width="100%" height={300}>
            <LineChart data={dailyData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
              <XAxis dataKey="date" tickFormatter={v => v?.slice(5)} tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #eee', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
              <Legend />
              <Line type="monotone" dataKey="count" name="활동 수" stroke="#9b59b6" strokeWidth={2.5} dot={{ r: 3, fill: '#9b59b6' }} activeDot={{ r: 6 }} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      <div className="ai-grid-2col">
        {/* 행동 유형별 분포 */}
        {actionData.length > 0 && (
          <div className="ai-card">
            <h4 className="ai-card-title">행동 유형별 분포</h4>
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie data={actionData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} innerRadius={50}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  labelLine={{ stroke: '#ccc' }}
                >
                  {actionData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #eee' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* 리소스 유형별 */}
        {resourceData.length > 0 && (
          <div className="ai-card">
            <h4 className="ai-card-title">리소스 유형별</h4>
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={resourceData} layout="vertical" margin={{ left: 80 }}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis type="number" tick={{ fontSize: 11 }} />
                <YAxis dataKey="name" type="category" width={70} tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #eee', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
                <Bar dataKey="value" name="건수" fill="#3498db" radius={[0, 6, 6, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {!hasData && (
        <p className="ai-empty-text">해당 기간에 활동 데이터가 없습니다.</p>
      )}

      <style>{`
        .ai-info-bar { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; margin-bottom: 1.5rem; padding: 0.75rem 1rem; background: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
        .ai-refresh-btn { padding: 0.5rem 1rem; background: linear-gradient(135deg, #9b59b6, #8e44ad); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.85rem; font-weight: 500; transition: opacity 0.2s; }
        .ai-refresh-btn:hover { opacity: 0.85; }

        .at-period-tabs { display: flex; gap: 0; border: 1px solid #ddd; border-radius: 8px; overflow: hidden; }
        .at-period-tab {
          padding: 0.4rem 0.875rem; border: none; background: white;
          font-size: 0.8rem; cursor: pointer; color: #666;
          transition: all 0.15s;
        }
        .at-period-tab:not(:last-child) { border-right: 1px solid #ddd; }
        .at-period-tab.active { background: #9b59b6; color: white; font-weight: 600; }
        .at-period-tab:hover:not(.active) { background: #f8f9fa; }

        .at-kpi-row { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1rem; margin-bottom: 1.5rem; }

        .ai-kpi-card {
          background: white; border-radius: 12px; padding: 1.25rem;
          box-shadow: 0 2px 12px rgba(0,0,0,0.06);
          display: flex; align-items: center; gap: 1rem;
          transition: transform 0.2s, box-shadow 0.2s;
        }
        .ai-kpi-card:hover { transform: translateY(-2px); box-shadow: 0 4px 16px rgba(0,0,0,0.1); }
        .ai-kpi-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.25rem; flex-shrink: 0; }
        .ai-kpi-info { flex: 1; }
        .ai-kpi-label { font-size: 0.75rem; color: #888; text-transform: uppercase; letter-spacing: 0.5px; margin-bottom: 0.25rem; }
        .ai-kpi-value { font-size: 1.5rem; font-weight: 700; line-height: 1.2; }
        .ai-kpi-sub { font-size: 0.7rem; color: #aaa; margin-top: 0.2rem; }

        .ai-grid-2col { display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 1.5rem; }
        .ai-card { background: white; border-radius: 12px; padding: 1.25rem; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
        .ai-card-title { margin: 0 0 1rem 0; font-size: 0.95rem; font-weight: 600; color: #333; }
        .ai-empty-text { color: #aaa; font-size: 0.85rem; text-align: center; padding: 2rem 0; margin: 0; }

        @media (max-width: 640px) {
          .at-kpi-row { grid-template-columns: 1fr; }
          .ai-grid-2col { grid-template-columns: 1fr; }
        }
      `}</style>
    </div>
  );
};

export default ActivityTab;
