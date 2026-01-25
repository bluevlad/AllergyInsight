import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { hospitalApi } from '../../services/api';

const HospitalDashboard = () => {
  const navigate = useNavigate();
  const [stats, setStats] = useState(null);
  const [doctorStats, setDoctorStats] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const [dashboardData, doctorsData] = await Promise.all([
        hospitalApi.getDashboard(),
        hospitalApi.getDoctorStats()
      ]);
      setStats(dashboardData);
      setDoctorStats(doctorsData);
    } catch (err) {
      console.error('Dashboard load error:', err);
      setError(err.response?.data?.detail || '대시보드를 불러올 수 없습니다');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', padding: '3rem' }}>
        <p>로딩 중...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div style={{ padding: '2rem' }}>
        <div style={{
          backgroundColor: '#fee2e2',
          border: '1px solid #fecaca',
          borderRadius: '8px',
          padding: '1rem',
          color: '#dc2626'
        }}>
          {error}
        </div>
      </div>
    );
  }

  return (
    <div style={{ padding: '1.5rem' }}>
      <div style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
          병원 대시보드
        </h2>
        <p style={{ color: '#666' }}>환자 관리 및 진단 현황</p>
      </div>

      {/* 통계 카드 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '1rem',
        marginBottom: '2rem'
      }}>
        <StatCard
          title="전체 환자"
          value={stats?.total_patients || 0}
          color="#3b82f6"
          onClick={() => navigate('/hospital/patients')}
        />
        <StatCard
          title="활성 환자"
          value={stats?.active_patients || 0}
          color="#10b981"
        />
        <StatCard
          title="동의 대기"
          value={stats?.pending_consent || 0}
          color="#f59e0b"
        />
        <StatCard
          title="오늘 진단"
          value={stats?.today_diagnoses || 0}
          color="#8b5cf6"
        />
        <StatCard
          title="이번 달 진단"
          value={stats?.this_month_diagnoses || 0}
          color="#ec4899"
        />
      </div>

      {/* 빠른 작업 버튼 */}
      <div style={{
        display: 'flex',
        gap: '1rem',
        marginBottom: '2rem',
        flexWrap: 'wrap'
      }}>
        <button
          onClick={() => navigate('/hospital/patients/new')}
          style={{
            padding: '0.75rem 1.5rem',
            backgroundColor: '#3b82f6',
            color: 'white',
            border: 'none',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: '500'
          }}
        >
          + 신규 환자 등록
        </button>
        <button
          onClick={() => navigate('/hospital/patients')}
          style={{
            padding: '0.75rem 1.5rem',
            backgroundColor: '#f3f4f6',
            color: '#374151',
            border: '1px solid #d1d5db',
            borderRadius: '8px',
            cursor: 'pointer',
            fontWeight: '500'
          }}
        >
          환자 목록
        </button>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '1.5rem' }}>
        {/* 최근 등록 환자 */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: '12px',
          padding: '1.5rem',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem' }}>
            최근 등록 환자
          </h3>
          {stats?.recent_patients?.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {stats.recent_patients.map((patient) => (
                <div
                  key={patient.id}
                  onClick={() => navigate(`/hospital/patients/${patient.id}`)}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '0.75rem',
                    backgroundColor: '#f9fafb',
                    borderRadius: '8px',
                    cursor: 'pointer'
                  }}
                >
                  <div>
                    <div style={{ fontWeight: '500' }}>{patient.patient_name || '이름 없음'}</div>
                    <div style={{ fontSize: '0.875rem', color: '#666' }}>
                      {patient.patient_number || '-'}
                    </div>
                  </div>
                  <StatusBadge status={patient.status} />
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: '#666', textAlign: 'center', padding: '2rem' }}>
              등록된 환자가 없습니다
            </p>
          )}
        </div>

        {/* 의사별 통계 */}
        <div style={{
          backgroundColor: 'white',
          borderRadius: '12px',
          padding: '1.5rem',
          boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
        }}>
          <h3 style={{ fontSize: '1.125rem', fontWeight: '600', marginBottom: '1rem' }}>
            의사별 환자 현황
          </h3>
          {doctorStats?.length > 0 ? (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              {doctorStats.map((doctor) => (
                <div
                  key={doctor.doctor_id}
                  style={{
                    display: 'flex',
                    justifyContent: 'space-between',
                    alignItems: 'center',
                    padding: '0.75rem',
                    backgroundColor: '#f9fafb',
                    borderRadius: '8px'
                  }}
                >
                  <div style={{ fontWeight: '500' }}>{doctor.doctor_name}</div>
                  <div style={{ display: 'flex', gap: '1rem', fontSize: '0.875rem' }}>
                    <span>환자 {doctor.total_patients}명</span>
                    <span style={{ color: '#666' }}>
                      이번달 {doctor.this_month_diagnoses}건
                    </span>
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p style={{ color: '#666', textAlign: 'center', padding: '2rem' }}>
              등록된 의사가 없습니다
            </p>
          )}
        </div>
      </div>
    </div>
  );
};

const StatCard = ({ title, value, color, onClick }) => (
  <div
    onClick={onClick}
    style={{
      backgroundColor: 'white',
      borderRadius: '12px',
      padding: '1.5rem',
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
      cursor: onClick ? 'pointer' : 'default',
      borderLeft: `4px solid ${color}`
    }}
  >
    <div style={{ fontSize: '0.875rem', color: '#666', marginBottom: '0.5rem' }}>
      {title}
    </div>
    <div style={{ fontSize: '2rem', fontWeight: 'bold', color }}>
      {value}
    </div>
  </div>
);

const StatusBadge = ({ status }) => {
  const statusConfig = {
    active: { label: '활성', bg: '#dcfce7', color: '#16a34a' },
    pending_consent: { label: '동의 대기', bg: '#fef3c7', color: '#d97706' },
    inactive: { label: '비활성', bg: '#f3f4f6', color: '#6b7280' },
    transferred: { label: '전원', bg: '#dbeafe', color: '#2563eb' },
  };

  const config = statusConfig[status] || statusConfig.inactive;

  return (
    <span style={{
      padding: '0.25rem 0.75rem',
      borderRadius: '9999px',
      fontSize: '0.75rem',
      fontWeight: '500',
      backgroundColor: config.bg,
      color: config.color
    }}>
      {config.label}
    </span>
  );
};

export default HospitalDashboard;
