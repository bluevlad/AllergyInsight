/**
 * Professional Patients Page - 환자 관리
 */
import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate, useParams } from 'react-router-dom';
import { proApi } from '../services/proApi';

function PatientsPage() {
  const navigate = useNavigate();
  const { id: selectedPatientId } = useParams();

  const [patients, setPatients] = useState([]);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [patientDiagnoses, setPatientDiagnoses] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState('');
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 20;

  const loadPatients = useCallback(async () => {
    try {
      setLoading(true);
      const params = {
        page,
        page_size: pageSize,
      };
      if (searchQuery) params.query = searchQuery;
      if (statusFilter) params.status = statusFilter;

      const response = await proApi.patients.list(params);
      setPatients(response.items || []);
      setTotalCount(response.total || 0);
    } catch (err) {
      setError('환자 목록을 불러오는데 실패했습니다.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [page, searchQuery, statusFilter]);

  const loadPatientDetail = useCallback(async (patientId) => {
    try {
      const [patient, diagnoses] = await Promise.all([
        proApi.patients.get(patientId),
        proApi.patients.getDiagnoses(patientId).catch(() => ({ items: [] })),
      ]);
      setSelectedPatient(patient);
      setPatientDiagnoses(diagnoses.items || []);
    } catch (err) {
      console.error('환자 상세 조회 실패:', err);
    }
  }, []);

  useEffect(() => {
    loadPatients();
  }, [loadPatients]);

  useEffect(() => {
    if (selectedPatientId) {
      loadPatientDetail(selectedPatientId);
    } else {
      setSelectedPatient(null);
      setPatientDiagnoses([]);
    }
  }, [selectedPatientId, loadPatientDetail]);

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    loadPatients();
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      active: { label: '활성', class: 'badge-success' },
      pending_consent: { label: '동의 대기', class: 'badge-warning' },
      inactive: { label: '비활성', class: 'badge-secondary' },
    };
    const info = statusMap[status] || { label: status, class: 'badge-secondary' };
    return <span className={`badge ${info.class}`}>{info.label}</span>;
  };

  if (loading && patients.length === 0) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div style={{ display: 'grid', gridTemplateColumns: selectedPatientId ? '1fr 1fr' : '1fr', gap: '1.5rem' }}>
      {/* 환자 목록 */}
      <div>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h2>환자 관리</h2>
          <button className="btn btn-primary" onClick={() => navigate('/pro/patients/new')}>
            + 신규 환자
          </button>
        </div>

        {/* 검색/필터 */}
        <form onSubmit={handleSearch} className="card" style={{ marginBottom: '1rem' }}>
          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <input
              type="text"
              placeholder="환자명, 전화번호, 환자번호 검색..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="form-control"
              style={{ flex: 1 }}
            />
            <select
              value={statusFilter}
              onChange={(e) => setStatusFilter(e.target.value)}
              className="form-control"
              style={{ width: '120px' }}
            >
              <option value="">전체 상태</option>
              <option value="active">활성</option>
              <option value="pending_consent">동의 대기</option>
              <option value="inactive">비활성</option>
            </select>
            <button type="submit" className="btn btn-primary">검색</button>
          </div>
        </form>

        {error && (
          <div className="card" style={{ marginBottom: '1rem' }}>
            <p style={{ color: '#c62828' }}>{error}</p>
            <button className="btn btn-primary" onClick={loadPatients}>다시 시도</button>
          </div>
        )}

        {/* 환자 목록 테이블 */}
        <div className="card">
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th>환자명</th>
                  <th>환자번호</th>
                  <th>연락처</th>
                  <th>상태</th>
                  <th>진단 수</th>
                  <th></th>
                </tr>
              </thead>
              <tbody>
                {patients.map((patient) => (
                  <tr
                    key={patient.id}
                    style={{
                      cursor: 'pointer',
                      background: selectedPatientId == patient.id ? '#e3f2fd' : 'inherit',
                    }}
                    onClick={() => navigate(`/pro/patients/${patient.id}`)}
                  >
                    <td>{patient.patient_name}</td>
                    <td>{patient.patient_number || '-'}</td>
                    <td>{patient.patient_phone || '-'}</td>
                    <td>{getStatusBadge(patient.status)}</td>
                    <td>{patient.diagnosis_count || 0}건</td>
                    <td>
                      <button
                        className="btn btn-sm btn-secondary"
                        onClick={(e) => {
                          e.stopPropagation();
                          navigate(`/pro/diagnosis?patient=${patient.id}`);
                        }}
                      >
                        진단 입력
                      </button>
                    </td>
                  </tr>
                ))}
                {patients.length === 0 && (
                  <tr>
                    <td colSpan={6} style={{ textAlign: 'center', color: '#666' }}>
                      등록된 환자가 없습니다.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>

          {/* 페이지네이션 */}
          {totalCount > pageSize && (
            <div style={{ display: 'flex', justifyContent: 'center', gap: '0.5rem', marginTop: '1rem' }}>
              <button
                className="btn btn-secondary"
                disabled={page === 1}
                onClick={() => setPage(p => p - 1)}
              >
                이전
              </button>
              <span style={{ padding: '0.5rem 1rem' }}>
                {page} / {Math.ceil(totalCount / pageSize)}
              </span>
              <button
                className="btn btn-secondary"
                disabled={page >= Math.ceil(totalCount / pageSize)}
                onClick={() => setPage(p => p + 1)}
              >
                다음
              </button>
            </div>
          )}
        </div>
      </div>

      {/* 환자 상세 (선택 시) */}
      {selectedPatient && (
        <div>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h2>환자 상세</h2>
            <button className="btn btn-secondary" onClick={() => navigate('/pro/patients')}>
              닫기
            </button>
          </div>

          {/* 기본 정보 */}
          <div className="card" style={{ marginBottom: '1rem' }}>
            <h3>기본 정보</h3>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <p style={{ color: '#666', fontSize: '0.875rem' }}>환자명</p>
                <p style={{ fontWeight: '600' }}>{selectedPatient.patient_name}</p>
              </div>
              <div>
                <p style={{ color: '#666', fontSize: '0.875rem' }}>환자번호</p>
                <p style={{ fontWeight: '600' }}>{selectedPatient.patient_number || '-'}</p>
              </div>
              <div>
                <p style={{ color: '#666', fontSize: '0.875rem' }}>연락처</p>
                <p style={{ fontWeight: '600' }}>{selectedPatient.patient_phone || '-'}</p>
              </div>
              <div>
                <p style={{ color: '#666', fontSize: '0.875rem' }}>생년월일</p>
                <p style={{ fontWeight: '600' }}>{selectedPatient.patient_birth_date || '-'}</p>
              </div>
              <div>
                <p style={{ color: '#666', fontSize: '0.875rem' }}>담당의</p>
                <p style={{ fontWeight: '600' }}>{selectedPatient.assigned_doctor_name || '-'}</p>
              </div>
              <div>
                <p style={{ color: '#666', fontSize: '0.875rem' }}>상태</p>
                <p>{getStatusBadge(selectedPatient.status)}</p>
              </div>
            </div>

            <div style={{ marginTop: '1rem' }}>
              <button
                className="btn btn-primary"
                onClick={() => navigate(`/pro/diagnosis?patient=${selectedPatient.id}`)}
              >
                새 진단 입력
              </button>
            </div>
          </div>

          {/* 진단 이력 */}
          <div className="card">
            <h3>진단 이력 ({patientDiagnoses.length}건)</h3>
            {patientDiagnoses.length > 0 ? (
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>진단일</th>
                      <th>양성 항목</th>
                      <th>입력자</th>
                    </tr>
                  </thead>
                  <tbody>
                    {patientDiagnoses.map((diag) => {
                      const positiveCount = Object.values(diag.results || {}).filter(v => v > 0).length;
                      return (
                        <tr key={diag.id}>
                          <td>{diag.diagnosis_date}</td>
                          <td>{positiveCount}개</td>
                          <td>{diag.entered_by_name || '-'}</td>
                        </tr>
                      );
                    })}
                  </tbody>
                </table>
              </div>
            ) : (
              <p style={{ color: '#666', textAlign: 'center', padding: '2rem' }}>
                진단 이력이 없습니다.
              </p>
            )}
          </div>
        </div>
      )}

      <style>{`
        .btn-sm {
          padding: 0.25rem 0.5rem;
          font-size: 0.875rem;
        }
      `}</style>
    </div>
  );
}

export default PatientsPage;
