/**
 * Consumer Diagnosis Detail Page - 진단 상세
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
import { consumerApi } from '../services/consumerApi';

function DiagnosisDetailPage() {
  const { id } = useParams();
  const navigate = useNavigate();

  const [diagnosis, setDiagnosis] = useState(null);
  const [guide, setGuide] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeTab, setActiveTab] = useState('summary');

  useEffect(() => {
    loadData();
  }, [id]);

  const loadData = async () => {
    try {
      setLoading(true);
      const [diagData, guideData] = await Promise.all([
        consumerApi.my.getDiagnosis(id),
        consumerApi.my.getGuide(id),
      ]);
      setDiagnosis(diagData);
      setGuide(guideData);
    } catch (err) {
      console.error(err);
      alert('진단 정보를 불러오는데 실패했습니다.');
      navigate('/app/my-diagnosis');
    } finally {
      setLoading(false);
    }
  };

  const getGradeColor = (grade) => {
    const colors = {
      0: '#4CAF50', 1: '#8BC34A', 2: '#FFEB3B',
      3: '#FFC107', 4: '#FF9800', 5: '#F44336', 6: '#B71C1C'
    };
    return colors[grade] || '#ccc';
  };

  const getGradeLabel = (grade) => {
    const labels = {
      0: '음성', 1: '약양성', 2: '양성',
      3: '양성', 4: '강양성', 5: '강양성', 6: '최강양성'
    };
    return labels[grade] || '-';
  };

  const allergenNames = {
    peanut: '땅콩', milk: '우유', egg: '계란',
    wheat: '밀', soy: '대두', fish: '생선',
    shellfish: '갑각류', tree_nuts: '견과류', sesame: '참깨',
    dust_mite: '집먼지진드기', pollen: '꽃가루',
    mold: '곰팡이', pet_dander: '반려동물',
    cockroach: '바퀴벌레', latex: '라텍스', bee_venom: '벌독'
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    );
  }

  if (!diagnosis) return null;

  const tabs = [
    { id: 'summary', label: '요약', icon: '📋' },
    { id: 'dietary', label: '식이 관리', icon: '🍽️' },
    { id: 'symptoms', label: '증상/위험도', icon: '⚠️' },
    { id: 'emergency', label: '응급 정보', icon: '🚨' },
  ];

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto' }}>
      <button className="btn btn-secondary" onClick={() => navigate('/app/my-diagnosis')} style={{ marginBottom: '1rem' }}>
        ← 목록으로
      </button>

      <div className="card" style={{ marginBottom: '1rem' }}>
        <h2>검사 결과 상세</h2>
        <p style={{ color: '#666' }}>
          검사일: {new Date(diagnosis.diagnosis_date).toLocaleDateString('ko-KR')}
          {diagnosis.kit_serial && ` | 키트: ${diagnosis.kit_serial}`}
        </p>
      </div>

      {/* 탭 네비게이션 */}
      <div className="tab-nav" style={{ marginBottom: '1rem' }}>
        {tabs.map(tab => (
          <button
            key={tab.id}
            className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.id)}
          >
            <span>{tab.icon}</span> {tab.label}
          </button>
        ))}
      </div>

      {/* 요약 탭 */}
      {activeTab === 'summary' && (
        <div className="card">
          <h3>검사 결과 요약</h3>

          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
            <div style={{ textAlign: 'center', padding: '1rem', background: '#fee', borderRadius: '8px' }}>
              <p style={{ fontSize: '2rem', fontWeight: 'bold', color: '#e74c3c' }}>
                {diagnosis.summary?.high_risk?.length || 0}
              </p>
              <p style={{ color: '#666' }}>고위험</p>
            </div>
            <div style={{ textAlign: 'center', padding: '1rem', background: '#ffeebb', borderRadius: '8px' }}>
              <p style={{ fontSize: '2rem', fontWeight: 'bold', color: '#f39c12' }}>
                {diagnosis.summary?.moderate_risk?.length || 0}
              </p>
              <p style={{ color: '#666' }}>주의</p>
            </div>
            <div style={{ textAlign: 'center', padding: '1rem', background: '#eef', borderRadius: '8px' }}>
              <p style={{ fontSize: '2rem', fontWeight: 'bold', color: '#3498db' }}>
                {diagnosis.summary?.total_positive || 0}
              </p>
              <p style={{ color: '#666' }}>양성</p>
            </div>
          </div>

          <h4>알러젠별 등급</h4>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.5rem' }}>
            {Object.entries(diagnosis.results || {})
              .filter(([, grade]) => grade > 0)
              .sort((a, b) => b[1] - a[1])
              .map(([code, grade]) => (
                <div key={code} style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '0.75rem',
                  background: '#f8f9fa',
                  borderRadius: '8px',
                  borderLeft: `4px solid ${getGradeColor(grade)}`,
                }}>
                  <span>{allergenNames[code] || code}</span>
                  <span style={{
                    padding: '0.25rem 0.75rem',
                    background: getGradeColor(grade),
                    color: grade >= 4 ? 'white' : 'inherit',
                    borderRadius: '12px',
                    fontWeight: '600',
                  }}>
                    {grade}등급 ({getGradeLabel(grade)})
                  </span>
                </div>
              ))}
          </div>
        </div>
      )}

      {/* 식이 관리 탭 */}
      {activeTab === 'dietary' && guide && (
        <div className="card">
          <h3>식이 관리 가이드</h3>

          {guide.dietary_management?.avoid_foods?.length > 0 && (
            <div style={{ marginBottom: '1.5rem' }}>
              <h4 style={{ color: '#e74c3c' }}>🚫 회피해야 할 식품</h4>
              {guide.dietary_management.avoid_foods.map((item, idx) => (
                <div key={idx} style={{ marginBottom: '1rem', padding: '1rem', background: '#fff5f5', borderRadius: '8px' }}>
                  <p style={{ fontWeight: '600', marginBottom: '0.5rem' }}>{item.allergen}</p>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                    {item.foods.map((food, i) => (
                      <span key={i} style={{
                        padding: '0.25rem 0.5rem',
                        background: '#ffcdd2',
                        borderRadius: '4px',
                        fontSize: '0.875rem',
                      }}>
                        {food}
                      </span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {guide.dietary_management?.substitutes?.length > 0 && (
            <div style={{ marginBottom: '1.5rem' }}>
              <h4 style={{ color: '#27ae60' }}>✅ 대체 식품</h4>
              {guide.dietary_management.substitutes.map((item, idx) => (
                <div key={idx} style={{ marginBottom: '0.75rem', padding: '1rem', background: '#f0fff4', borderRadius: '8px' }}>
                  <p>
                    <span style={{ color: '#e74c3c', textDecoration: 'line-through' }}>{item.original}</span>
                    {' → '}
                    <span style={{ color: '#27ae60', fontWeight: '600' }}>{item.alternatives.join(', ')}</span>
                  </p>
                  {item.notes && <p style={{ fontSize: '0.875rem', color: '#666', marginTop: '0.25rem' }}>{item.notes}</p>}
                </div>
              ))}
            </div>
          )}

          {guide.dietary_management?.hidden_sources?.length > 0 && (
            <div>
              <h4 style={{ color: '#f39c12' }}>⚠️ 숨겨진 알러젠 주의</h4>
              {guide.dietary_management.hidden_sources.map((item, idx) => (
                <div key={idx} style={{ marginBottom: '0.75rem', padding: '1rem', background: '#fff8e1', borderRadius: '8px' }}>
                  <p style={{ fontWeight: '600', marginBottom: '0.5rem' }}>{item.allergen}</p>
                  <p style={{ fontSize: '0.875rem' }}>{item.sources.join(', ')}</p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 증상/위험도 탭 */}
      {activeTab === 'symptoms' && guide && (
        <div className="card">
          <h3>예상 증상 및 위험도</h3>

          {guide.symptoms_risk?.high_risk?.length > 0 && (
            <div style={{ marginBottom: '1.5rem' }}>
              <h4 style={{ color: '#e74c3c' }}>🔴 고위험 (4등급 이상)</h4>
              {guide.symptoms_risk.high_risk.map((item, idx) => (
                <div key={idx} style={{ marginBottom: '1rem', padding: '1rem', background: '#fff5f5', borderRadius: '8px', borderLeft: '4px solid #e74c3c' }}>
                  <p style={{ fontWeight: '600' }}>{item.allergen} ({item.grade}등급)</p>
                  <p style={{ fontSize: '0.875rem', color: '#666', marginTop: '0.5rem' }}>
                    예상 증상: {item.symptoms?.map(s => typeof s === 'string' ? s : s.name).join(', ')}
                  </p>
                </div>
              ))}
            </div>
          )}

          {guide.symptoms_risk?.moderate_risk?.length > 0 && (
            <div style={{ marginBottom: '1.5rem' }}>
              <h4 style={{ color: '#f39c12' }}>🟡 주의 (2-3등급)</h4>
              {guide.symptoms_risk.moderate_risk.map((item, idx) => (
                <div key={idx} style={{ marginBottom: '1rem', padding: '1rem', background: '#fff8e1', borderRadius: '8px', borderLeft: '4px solid #f39c12' }}>
                  <p style={{ fontWeight: '600' }}>{item.allergen} ({item.grade}등급)</p>
                  <p style={{ fontSize: '0.875rem', color: '#666', marginTop: '0.5rem' }}>
                    예상 증상: {item.symptoms?.map(s => typeof s === 'string' ? s : s.name).join(', ')}
                  </p>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 응급 정보 탭 */}
      {activeTab === 'emergency' && guide && (
        <div className="card">
          <h3>응급 대처 정보</h3>

          {guide.emergency_medical?.has_severe_allergy && (
            <div style={{
              padding: '1rem',
              background: '#ffebee',
              borderRadius: '8px',
              marginBottom: '1.5rem',
              border: '2px solid #e74c3c',
            }}>
              <p style={{ fontWeight: 'bold', color: '#e74c3c' }}>
                ⚠️ 아나필락시스 위험이 있습니다
              </p>
              <p style={{ marginTop: '0.5rem' }}>
                에피펜 처방을 받고 항상 휴대하시기 바랍니다.
              </p>
            </div>
          )}

          <div style={{ marginBottom: '1.5rem' }}>
            <h4>응급 연락처</h4>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
              <div style={{ textAlign: 'center', padding: '1rem', background: '#f8f9fa', borderRadius: '8px' }}>
                <p style={{ fontSize: '1.5rem' }}>🚑</p>
                <p style={{ fontWeight: '600' }}>119</p>
                <p style={{ fontSize: '0.875rem', color: '#666' }}>응급</p>
              </div>
              <div style={{ textAlign: 'center', padding: '1rem', background: '#f8f9fa', borderRadius: '8px' }}>
                <p style={{ fontSize: '1.5rem' }}>☎️</p>
                <p style={{ fontWeight: '600' }}>1339</p>
                <p style={{ fontSize: '0.875rem', color: '#666' }}>독극물</p>
              </div>
              <div style={{ textAlign: 'center', padding: '1rem', background: '#f8f9fa', borderRadius: '8px' }}>
                <p style={{ fontSize: '1.5rem' }}>🏥</p>
                <p style={{ fontWeight: '600' }}>1577-1234</p>
                <p style={{ fontSize: '0.875rem', color: '#666' }}>병원 안내</p>
              </div>
            </div>
          </div>

          <button
            className="btn btn-primary"
            style={{ width: '100%' }}
            onClick={() => navigate('/app/emergency')}
          >
            응급 대처 가이드 전체 보기
          </button>
        </div>
      )}

      <style>{`
        .tab-nav {
          display: flex;
          gap: 0.5rem;
          overflow-x: auto;
        }
        .tab-btn {
          padding: 0.75rem 1.5rem;
          border: none;
          background: #f8f9fa;
          border-radius: 8px;
          cursor: pointer;
          white-space: nowrap;
          transition: all 0.2s;
        }
        .tab-btn:hover {
          background: #e9ecef;
        }
        .tab-btn.active {
          background: #667eea;
          color: white;
        }
      `}</style>
    </div>
  );
}

export default DiagnosisDetailPage;
