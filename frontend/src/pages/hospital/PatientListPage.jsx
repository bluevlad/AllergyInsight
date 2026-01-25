import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { hospitalApi } from '../../services/api';

const PatientListPage = () => {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();

  const [patients, setPatients] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  const [searchQuery, setSearchQuery] = useState(searchParams.get('query') || '');
  const [statusFilter, setStatusFilter] = useState(searchParams.get('status') || '');
  const [page, setPage] = useState(parseInt(searchParams.get('page')) || 1);
  const pageSize = 20;

  useEffect(() => {
    loadPatients();
  }, [page, statusFilter]);

  const loadPatients = async () => {
    try {
      setLoading(true);
      const params = {
        page,
        page_size: pageSize,
      };
      if (searchQuery) params.query = searchQuery;
      if (statusFilter) params.status = statusFilter;

      const data = await hospitalApi.getPatients(params);
      setPatients(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error('Patient list error:', err);
      setError(err.response?.data?.detail || '환자 목록을 불러올 수 없습니다');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    loadPatients();
  };

  const handleStatusChange = (e) => {
    setStatusFilter(e.target.value);
    setPage(1);
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div style={{ padding: '1.5rem' }}>
      <div style={{ marginBottom: '2rem', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
        <div>
          <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
            환자 목록
          </h2>
          <p style={{ color: '#666' }}>총 {total}명의 환자</p>
        </div>
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
      </div>

      {/* 검색 및 필터 */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: '12px',
        padding: '1rem',
        marginBottom: '1.5rem',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
      }}>
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '1rem', flexWrap: 'wrap' }}>
          <input
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="이름, 전화번호, 환자번호 검색..."
            style={{
              flex: '1',
              minWidth: '200px',
              padding: '0.75rem',
              border: '1px solid #d1d5db',
              borderRadius: '8px',
              fontSize: '0.875rem'
            }}
          />
          <select
            value={statusFilter}
            onChange={handleStatusChange}
            style={{
              padding: '0.75rem',
              border: '1px solid #d1d5db',
              borderRadius: '8px',
              fontSize: '0.875rem',
              backgroundColor: 'white'
            }}
          >
            <option value="">전체 상태</option>
            <option value="active">활성</option>
            <option value="pending_consent">동의 대기</option>
            <option value="inactive">비활성</option>
            <option value="transferred">전원</option>
          </select>
          <button
            type="submit"
            style={{
              padding: '0.75rem 1.5rem',
              backgroundColor: '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: 'pointer'
            }}
          >
            검색
          </button>
        </form>
      </div>

      {/* 에러 표시 */}
      {error && (
        <div style={{
          backgroundColor: '#fee2e2',
          border: '1px solid #fecaca',
          borderRadius: '8px',
          padding: '1rem',
          marginBottom: '1rem',
          color: '#dc2626'
        }}>
          {error}
        </div>
      )}

      {/* 환자 목록 테이블 */}
      <div style={{
        backgroundColor: 'white',
        borderRadius: '12px',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
        overflow: 'hidden'
      }}>
        {loading ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: '#666' }}>
            로딩 중...
          </div>
        ) : patients.length === 0 ? (
          <div style={{ padding: '3rem', textAlign: 'center', color: '#666' }}>
            등록된 환자가 없습니다
          </div>
        ) : (
          <table style={{ width: '100%', borderCollapse: 'collapse' }}>
            <thead>
              <tr style={{ backgroundColor: '#f9fafb' }}>
                <th style={thStyle}>환자번호</th>
                <th style={thStyle}>이름</th>
                <th style={thStyle}>연락처</th>
                <th style={thStyle}>담당의</th>
                <th style={thStyle}>상태</th>
                <th style={thStyle}>진단 횟수</th>
                <th style={thStyle}>최근 진단일</th>
              </tr>
            </thead>
            <tbody>
              {patients.map((patient) => (
                <tr
                  key={patient.id}
                  onClick={() => navigate(`/hospital/patients/${patient.id}`)}
                  style={{ cursor: 'pointer' }}
                  onMouseOver={(e) => e.currentTarget.style.backgroundColor = '#f9fafb'}
                  onMouseOut={(e) => e.currentTarget.style.backgroundColor = 'transparent'}
                >
                  <td style={tdStyle}>{patient.patient_number || '-'}</td>
                  <td style={tdStyle}>
                    <span style={{ fontWeight: '500' }}>{patient.patient_name || '이름 없음'}</span>
                  </td>
                  <td style={tdStyle}>{patient.patient_phone || '-'}</td>
                  <td style={tdStyle}>{patient.assigned_doctor_name || '-'}</td>
                  <td style={tdStyle}>
                    <StatusBadge status={patient.status} />
                  </td>
                  <td style={tdStyle}>{patient.diagnosis_count || 0}회</td>
                  <td style={tdStyle}>{patient.last_diagnosis_date || '-'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        )}

        {/* 페이지네이션 */}
        {totalPages > 1 && (
          <div style={{
            display: 'flex',
            justifyContent: 'center',
            gap: '0.5rem',
            padding: '1rem',
            borderTop: '1px solid #e5e7eb'
          }}>
            <button
              onClick={() => setPage(p => Math.max(1, p - 1))}
              disabled={page === 1}
              style={paginationBtnStyle}
            >
              이전
            </button>
            <span style={{ padding: '0.5rem 1rem', color: '#666' }}>
              {page} / {totalPages}
            </span>
            <button
              onClick={() => setPage(p => Math.min(totalPages, p + 1))}
              disabled={page === totalPages}
              style={paginationBtnStyle}
            >
              다음
            </button>
          </div>
        )}
      </div>
    </div>
  );
};

const thStyle = {
  padding: '0.75rem 1rem',
  textAlign: 'left',
  fontSize: '0.75rem',
  fontWeight: '600',
  color: '#6b7280',
  textTransform: 'uppercase',
  borderBottom: '1px solid #e5e7eb'
};

const tdStyle = {
  padding: '0.75rem 1rem',
  borderBottom: '1px solid #e5e7eb',
  fontSize: '0.875rem'
};

const paginationBtnStyle = {
  padding: '0.5rem 1rem',
  border: '1px solid #d1d5db',
  borderRadius: '6px',
  backgroundColor: 'white',
  cursor: 'pointer'
};

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

export default PatientListPage;
