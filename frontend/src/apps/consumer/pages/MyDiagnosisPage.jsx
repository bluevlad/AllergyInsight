/**
 * Consumer My Diagnosis Page - 내 검사 결과 목록
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { consumerApi } from '../services/consumerApi';

function MyDiagnosisPage() {
  const navigate = useNavigate();
  const [diagnoses, setDiagnoses] = useState([]);
  const [latestDiagnosis, setLatestDiagnosis] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [diagList, latest] = await Promise.all([
        consumerApi.my.getDiagnoses(),
        consumerApi.my.getLatest().catch(() => null),
      ]);
      setDiagnoses(diagList.items || []);
      setLatestDiagnosis(latest);
    } catch (err) {
      if (err.response?.status === 404) {
        setDiagnoses([]);
        setLatestDiagnosis(null);
      } else {
        setError('데이터를 불러오는데 실패했습니다.');
        console.error(err);
      }
    } finally {
      setLoading(false);
    }
  };

  const getRiskBadge = (riskList, type) => {
    if (!riskList || riskList.length === 0) return null;
    const color = type === 'high' ? '#e74c3c' : '#f39c12';
    return (
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
        {riskList.map((item, idx) => (
          <span key={idx} style={{
            padding: '0.25rem 0.5rem',
            background: color,
            color: 'white',
            borderRadius: '12px',
            fontSize: '0.75rem',
          }}>
            {item}
          </span>
        ))}
      </div>
    );
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto' }}>
      <h2>내 검사 결과</h2>

      {error && (
        <div className="card" style={{ marginBottom: '1rem' }}>
          <p style={{ color: '#c62828' }}>{error}</p>
          <button className="btn btn-primary" onClick={loadData}>다시 시도</button>
        </div>
      )}

      {/* 최신 진단 요약 */}
      {latestDiagnosis && (
        <div className="card summary-card" style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
            <div>
              <h3 style={{ marginBottom: '0.5rem' }}>최신 검사 결과 요약</h3>
              <p style={{ color: '#666', fontSize: '0.875rem' }}>
                {new Date(latestDiagnosis.diagnosis_date).toLocaleDateString('ko-KR')} 검사
              </p>
            </div>
            <button
              className="btn btn-primary"
              onClick={() => navigate(`/app/my-diagnosis/${latestDiagnosis.id}`)}
            >
              상세 보기
            </button>
          </div>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginTop: '1rem' }}>
            <div style={{ textAlign: 'center', padding: '1rem', background: '#fee', borderRadius: '8px' }}>
              <p style={{ fontSize: '2rem', fontWeight: 'bold', color: '#e74c3c' }}>
                {latestDiagnosis.high_risk?.length || 0}
              </p>
              <p style={{ color: '#666' }}>고위험 알러젠</p>
            </div>
            <div style={{ textAlign: 'center', padding: '1rem', background: '#ffeebb', borderRadius: '8px' }}>
              <p style={{ fontSize: '2rem', fontWeight: 'bold', color: '#f39c12' }}>
                {latestDiagnosis.moderate_risk?.length || 0}
              </p>
              <p style={{ color: '#666' }}>주의 알러젠</p>
            </div>
            <div style={{ textAlign: 'center', padding: '1rem', background: '#eef', borderRadius: '8px' }}>
              <p style={{ fontSize: '2rem', fontWeight: 'bold', color: '#3498db' }}>
                {latestDiagnosis.total_positive || 0}
              </p>
              <p style={{ color: '#666' }}>양성 항목</p>
            </div>
          </div>

          {latestDiagnosis.high_risk?.length > 0 && (
            <div style={{ marginTop: '1rem' }}>
              <p style={{ fontWeight: '600', color: '#e74c3c', marginBottom: '0.5rem' }}>
                주의가 필요한 알러젠:
              </p>
              {getRiskBadge(latestDiagnosis.high_risk, 'high')}
            </div>
          )}
        </div>
      )}

      {/* 빠른 액션 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
        <button className="quick-action" onClick={() => navigate('/app/food-guide')}>
          <span className="action-icon">🍽️</span>
          <span>식품 가이드</span>
        </button>
        <button className="quick-action" onClick={() => navigate('/app/lifestyle')}>
          <span className="action-icon">🏠</span>
          <span>생활 관리</span>
        </button>
        <button className="quick-action" onClick={() => navigate('/app/emergency')}>
          <span className="action-icon">🚨</span>
          <span>응급 대처</span>
        </button>
        <button className="quick-action" onClick={() => navigate('/app/kit-register')}>
          <span className="action-icon">📦</span>
          <span>키트 등록</span>
        </button>
        <button className="quick-action report-action" onClick={() => window.open('/report', '_blank')}>
          <span className="action-icon">📄</span>
          <span>알러지 리포트</span>
        </button>
      </div>

      {/* 검사 이력 */}
      <div className="card">
        <h3>검사 이력</h3>
        {diagnoses.length > 0 ? (
          <div className="diagnosis-list">
            {diagnoses.map((diag) => (
              <div
                key={diag.id}
                className="diagnosis-item"
                onClick={() => navigate(`/app/my-diagnosis/${diag.id}`)}
              >
                <div style={{ flex: 1 }}>
                  <p style={{ fontWeight: '600' }}>
                    {new Date(diag.diagnosis_date).toLocaleDateString('ko-KR')}
                    {diag.kit_serial && (
                      <span style={{ color: '#666', fontWeight: 'normal', marginLeft: '0.5rem', fontSize: '0.875rem' }}>
                        키트: {diag.kit_serial}
                      </span>
                    )}
                  </p>
                  <div style={{ marginTop: '0.5rem' }}>
                    {getRiskBadge(diag.high_risk, 'high')}
                    {diag.high_risk?.length > 0 && diag.moderate_risk?.length > 0 && <div style={{ height: '0.25rem' }} />}
                    {getRiskBadge(diag.moderate_risk, 'moderate')}
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <p style={{ fontSize: '1.5rem', fontWeight: 'bold', color: '#3498db' }}>
                    {diag.total_positive}
                  </p>
                  <p style={{ color: '#666', fontSize: '0.875rem' }}>양성 항목</p>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <div style={{ textAlign: 'center', padding: '3rem', color: '#666' }}>
            <p style={{ fontSize: '3rem', marginBottom: '1rem' }}>📋</p>
            <p>아직 검사 결과가 없습니다.</p>
            <button
              className="btn btn-primary"
              style={{ marginTop: '1rem' }}
              onClick={() => navigate('/app/kit-register')}
            >
              키트 등록하기
            </button>
          </div>
        )}
      </div>

      <style>{`
        .summary-card {
          background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        }
        .quick-action {
          display: flex;
          flex-direction: column;
          align-items: center;
          gap: 0.5rem;
          padding: 1.5rem 1rem;
          background: white;
          border: 1px solid #eee;
          border-radius: 12px;
          cursor: pointer;
          transition: all 0.2s;
        }
        .quick-action:hover {
          background: #f8f9fa;
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .action-icon {
          font-size: 2rem;
        }
        .report-action {
          border-color: #e74c3c;
          background: #fff5f5;
        }
        .report-action:hover {
          background: #ffebee !important;
        }
        .diagnosis-list {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }
        .diagnosis-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 1rem;
          background: #f8f9fa;
          border-radius: 8px;
          cursor: pointer;
          transition: background 0.2s;
        }
        .diagnosis-item:hover {
          background: #e9ecef;
        }
      `}</style>
    </div>
  );
}

export default MyDiagnosisPage;
