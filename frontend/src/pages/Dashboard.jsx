import React, { useState, useEffect } from 'react';
import { statsApi } from '../services/api';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const COLORS = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe'];

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [summary, setSummary] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [statsData, summaryData] = await Promise.all([
        statsApi.getStats(),
        statsApi.getSummary(),
      ]);
      setStats(statsData);
      setSummary(summaryData);
    } catch (err) {
      setError('데이터를 불러오는데 실패했습니다.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleReset = async () => {
    if (window.confirm('통계를 초기화하시겠습니까?')) {
      await statsApi.reset();
      loadData();
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <p style={{ color: '#c62828' }}>{error}</p>
        <button className="btn btn-primary" onClick={loadData} style={{ marginTop: '1rem' }}>
          다시 시도
        </button>
      </div>
    );
  }

  const overview = summary?.overview || {};
  const byAllergen = summary?.by_allergen || {};

  // 차트 데이터 준비
  const allergenChartData = Object.entries(byAllergen).map(([name, data]) => ({
    name,
    papers: data.papers,
    searches: data.searches,
  }));

  const pieData = [
    { name: '검색 수', value: overview.total_searches || 0 },
    { name: '논문 수', value: overview.total_papers || 0 },
    { name: '질문 수', value: overview.total_questions || 0 },
  ].filter(d => d.value > 0);

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2>📊 수집 현황 대시보드</h2>
        <div style={{ display: 'flex', gap: '0.5rem' }}>
          <button className="btn btn-secondary" onClick={loadData}>
            🔄 새로고침
          </button>
          <button className="btn btn-secondary" onClick={handleReset}>
            🗑️ 초기화
          </button>
        </div>
      </div>

      {/* 통계 카드 */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon blue">🔍</div>
          <div className="stat-info">
            <h3>{overview.total_searches || 0}</h3>
            <p>총 검색 수</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon green">📄</div>
          <div className="stat-info">
            <h3>{overview.total_papers || 0}</h3>
            <p>수집된 논문</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon purple">❓</div>
          <div className="stat-info">
            <h3>{overview.total_questions || 0}</h3>
            <p>Q&A 질문 수</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon orange">🏷️</div>
          <div className="stat-info">
            <h3>{overview.unique_allergens || 0}</h3>
            <p>검색된 알러지 항원</p>
          </div>
        </div>
      </div>

      {/* 차트 영역 */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem' }}>
        {/* 알러지별 논문 수 */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">📈 알러지 항원별 수집 현황</h3>
          </div>
          {allergenChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={allergenChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="papers" fill="#667eea" name="논문 수" />
                <Bar dataKey="searches" fill="#f093fb" name="검색 수" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ textAlign: 'center', padding: '3rem', color: '#666' }}>
              아직 수집된 데이터가 없습니다.
            </div>
          )}
        </div>

        {/* 활동 비율 */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">📊 활동 비율</h3>
          </div>
          {pieData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={pieData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {pieData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ textAlign: 'center', padding: '3rem', color: '#666' }}>
              아직 활동 데이터가 없습니다.
            </div>
          )}
        </div>
      </div>

      {/* 최근 검색 이력 */}
      <div className="card" style={{ marginTop: '1.5rem' }}>
        <div className="card-header">
          <h3 className="card-title">🕐 최근 검색 이력</h3>
        </div>
        {stats?.recent_searches?.length > 0 ? (
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>알러지 항원</th>
                  <th>발견된 논문</th>
                  <th>검색 시간</th>
                </tr>
              </thead>
              <tbody>
                {stats.recent_searches.slice().reverse().map((search, idx) => (
                  <tr key={idx}>
                    <td>
                      <span className="badge badge-info">{search.allergen}</span>
                    </td>
                    <td>{search.papers_found}개</td>
                    <td>{new Date(search.timestamp).toLocaleString('ko-KR')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
            검색 이력이 없습니다. 논문 검색을 시작해보세요!
          </div>
        )}
      </div>

      {/* 캐시 정보 */}
      <div className="card" style={{ marginTop: '1.5rem' }}>
        <div className="card-header">
          <h3 className="card-title">💾 캐시 상태</h3>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
          <div>
            <p style={{ color: '#666', fontSize: '0.875rem' }}>캐시 항목</p>
            <p style={{ fontSize: '1.25rem', fontWeight: '600' }}>{stats?.cache?.valid_entries || 0}개</p>
          </div>
          <div>
            <p style={{ color: '#666', fontSize: '0.875rem' }}>총 항목</p>
            <p style={{ fontSize: '1.25rem', fontWeight: '600' }}>{stats?.cache?.total_entries || 0}개</p>
          </div>
          <div>
            <p style={{ color: '#666', fontSize: '0.875rem' }}>TTL</p>
            <p style={{ fontSize: '1.25rem', fontWeight: '600' }}>{stats?.cache?.ttl_hours || 24}시간</p>
          </div>
        </div>
      </div>

      {/* 마지막 활동 */}
      {summary?.last_activity && (
        <div style={{ marginTop: '1rem', textAlign: 'center', color: '#666', fontSize: '0.875rem' }}>
          마지막 활동: {new Date(summary.last_activity).toLocaleString('ko-KR')}
        </div>
      )}
    </div>
  );
}

export default Dashboard;
