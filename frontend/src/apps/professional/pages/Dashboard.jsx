/**
 * Professional Dashboard Page
 */
import React, { useState, useEffect } from 'react';
import { proApi } from '../services/proApi';
import { BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer, PieChart, Pie, Cell } from 'recharts';

const COLORS = ['#667eea', '#764ba2', '#f093fb', '#f5576c', '#4facfe', '#00f2fe'];

function Dashboard() {
  const [stats, setStats] = useState(null);
  const [doctorStats, setDoctorStats] = useState([]);
  const [allergenStats, setAllergenStats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [dashStats, doctors, allergens] = await Promise.all([
        proApi.dashboard.getStats(),
        proApi.dashboard.getDoctorStats().catch(() => []),
        proApi.dashboard.getAllergenStats('month').catch(() => []),
      ]);
      setStats(dashStats);
      setDoctorStats(doctors);
      setAllergenStats(allergens);
    } catch (err) {
      setError('데이터를 불러오는데 실패했습니다.');
      console.error(err);
    } finally {
      setLoading(false);
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

  // 환자 상태 파이 차트 데이터
  const patientStatusData = [
    { name: '활성 환자', value: stats?.active_patients || 0 },
    { name: '동의 대기', value: stats?.pending_consent || 0 },
  ].filter(d => d.value > 0);

  // 알러젠 차트 데이터
  const allergenChartData = allergenStats.slice(0, 10).map(a => ({
    name: a.allergen_name,
    positive: a.positive_count,
    highRisk: a.high_risk_count,
  }));

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem' }}>
        <h2>병원 대시보드</h2>
        <button className="btn btn-secondary" onClick={loadData}>
          새로고침
        </button>
      </div>

      {/* 통계 카드 */}
      <div className="stats-grid">
        <div className="stat-card">
          <div className="stat-icon blue">👥</div>
          <div className="stat-info">
            <h3>{stats?.total_patients || 0}</h3>
            <p>전체 환자</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon green">✅</div>
          <div className="stat-info">
            <h3>{stats?.active_patients || 0}</h3>
            <p>활성 환자</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon orange">⏳</div>
          <div className="stat-info">
            <h3>{stats?.pending_consent || 0}</h3>
            <p>동의 대기</p>
          </div>
        </div>

        <div className="stat-card">
          <div className="stat-icon purple">📋</div>
          <div className="stat-info">
            <h3>{stats?.today_diagnoses || 0}</h3>
            <p>오늘 진단</p>
          </div>
        </div>
      </div>

      {/* 진단 통계 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginTop: '1rem' }}>
        <div className="card" style={{ textAlign: 'center', padding: '1rem' }}>
          <p style={{ color: '#666', fontSize: '0.875rem' }}>이번 주 진단</p>
          <p style={{ fontSize: '1.5rem', fontWeight: '600', color: '#3498db' }}>
            {stats?.this_week_diagnoses || 0}건
          </p>
        </div>
        <div className="card" style={{ textAlign: 'center', padding: '1rem' }}>
          <p style={{ color: '#666', fontSize: '0.875rem' }}>이번 달 진단</p>
          <p style={{ fontSize: '1.5rem', fontWeight: '600', color: '#9b59b6' }}>
            {stats?.this_month_diagnoses || 0}건
          </p>
        </div>
        <div className="card" style={{ textAlign: 'center', padding: '1rem' }}>
          <p style={{ color: '#666', fontSize: '0.875rem' }}>의사 수</p>
          <p style={{ fontSize: '1.5rem', fontWeight: '600', color: '#27ae60' }}>
            {doctorStats.length}명
          </p>
        </div>
      </div>

      {/* 차트 영역 */}
      <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '1.5rem', marginTop: '1.5rem' }}>
        {/* 알러젠별 양성 현황 */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">알러젠별 양성 현황 (이번 달)</h3>
          </div>
          {allergenChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <BarChart data={allergenChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis />
                <Tooltip />
                <Bar dataKey="positive" fill="#667eea" name="양성" />
                <Bar dataKey="highRisk" fill="#e74c3c" name="고위험" />
              </BarChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ textAlign: 'center', padding: '3rem', color: '#666' }}>
              진단 데이터가 없습니다.
            </div>
          )}
        </div>

        {/* 환자 상태 분포 */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">환자 상태 분포</h3>
          </div>
          {patientStatusData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <PieChart>
                <Pie
                  data={patientStatusData}
                  cx="50%"
                  cy="50%"
                  labelLine={false}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  outerRadius={80}
                  fill="#8884d8"
                  dataKey="value"
                >
                  {patientStatusData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                  ))}
                </Pie>
                <Tooltip />
              </PieChart>
            </ResponsiveContainer>
          ) : (
            <div style={{ textAlign: 'center', padding: '3rem', color: '#666' }}>
              환자 데이터가 없습니다.
            </div>
          )}
        </div>
      </div>

      {/* 의사별 통계 */}
      {doctorStats.length > 0 && (
        <div className="card" style={{ marginTop: '1.5rem' }}>
          <div className="card-header">
            <h3 className="card-title">의사별 환자 현황</h3>
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>의사명</th>
                  <th>담당 환자</th>
                  <th>이번 달 진단</th>
                </tr>
              </thead>
              <tbody>
                {doctorStats.map((doc) => (
                  <tr key={doc.doctor_id}>
                    <td>{doc.doctor_name}</td>
                    <td>{doc.total_patients}명</td>
                    <td>{doc.this_month_diagnoses}건</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 최근 환자 */}
      {stats?.recent_patients?.length > 0 && (
        <div className="card" style={{ marginTop: '1.5rem' }}>
          <div className="card-header">
            <h3 className="card-title">최근 등록 환자</h3>
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>환자명</th>
                  <th>환자번호</th>
                  <th>상태</th>
                  <th>등록일</th>
                </tr>
              </thead>
              <tbody>
                {stats.recent_patients.map((patient, idx) => (
                  <tr key={idx}>
                    <td>{patient.patient_name}</td>
                    <td>{patient.patient_number || '-'}</td>
                    <td>
                      <span className={`badge ${patient.status === 'active' ? 'badge-success' : 'badge-warning'}`}>
                        {patient.status === 'active' ? '활성' : '대기'}
                      </span>
                    </td>
                    <td>{new Date(patient.created_at).toLocaleDateString('ko-KR')}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 최근 진단 */}
      {stats?.recent_diagnoses?.length > 0 && (
        <div className="card" style={{ marginTop: '1.5rem' }}>
          <div className="card-header">
            <h3 className="card-title">최근 진단</h3>
          </div>
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>환자명</th>
                  <th>양성 항목</th>
                  <th>진단일</th>
                </tr>
              </thead>
              <tbody>
                {stats.recent_diagnoses.map((diag, idx) => (
                  <tr key={idx}>
                    <td>{diag.patient_name}</td>
                    <td>{diag.positive_count}개</td>
                    <td>{diag.diagnosis_date}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}
    </div>
  );
}

export default Dashboard;
