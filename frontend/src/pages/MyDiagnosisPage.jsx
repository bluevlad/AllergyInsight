/**
 * My Diagnosis Page - User's diagnosis history and results
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { myDiagnosisApi } from '../services/api';

// Citation Badge Component - 출처 표시 컴포넌트
const CitationBadge = ({ citations, small = false, showCount = true }) => {
  const [showTooltip, setShowTooltip] = useState(false);

  if (!citations || citations.length === 0) return null;

  const citation = citations[0]; // 첫 번째 출처만 표시
  const count = citations.length;

  return (
    <span
      className={`citation-badge ${small ? 'small' : ''}`}
      onMouseEnter={() => setShowTooltip(true)}
      onMouseLeave={() => setShowTooltip(false)}
      onClick={() => citation.url && window.open(citation.url, '_blank')}
    >
      <span className="citation-icon">📄</span>
      {showCount && count > 1 && <span className="citation-count">{count}</span>}
      {showTooltip && (
        <div className="citation-tooltip">
          <div className="citation-tooltip-title">
            {citation.title_kr || citation.title}
          </div>
          <div className="citation-tooltip-meta">
            {citation.authors && <span>{citation.authors.split(',')[0]} 외</span>}
            {citation.year && <span>{citation.year}</span>}
            {citation.journal && <span>{citation.journal}</span>}
          </div>
          {citation.url && <div className="citation-tooltip-link">클릭하여 원문 보기</div>}
          {count > 1 && <div className="citation-tooltip-more">외 {count - 1}건의 출처</div>}
        </div>
      )}
    </span>
  );
};

// No Citation Badge - 출처 없음 표시 컴포넌트
const NoCitationBadge = ({ small = false }) => {
  return (
    <span className={`no-citation-badge ${small ? 'small' : ''}`} title="일반 정보 (출처 준비중)">
      <span className="no-citation-icon">ℹ️</span>
    </span>
  );
};

const MyDiagnosisPage = () => {
  const navigate = useNavigate();
  const { user, registerKit, logout } = useAuth();
  const [diagnoses, setDiagnoses] = useState([]);
  const [selectedDiagnosis, setSelectedDiagnosis] = useState(null);
  const [allergenInfo, setAllergenInfo] = useState(null);
  const [patientGuide, setPatientGuide] = useState(null);
  const [activeTab, setActiveTab] = useState('results'); // 'results', 'symptoms', 'dietary', 'emergency', 'citations'
  const [loading, setLoading] = useState(true);
  const [guideLoading, setGuideLoading] = useState(false);
  const [error, setError] = useState('');

  // Kit registration modal
  const [showKitModal, setShowKitModal] = useState(false);
  const [kitForm, setKitForm] = useState({ serialNumber: '', pin: '' });
  const [kitError, setKitError] = useState('');
  const [kitLoading, setKitLoading] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  useEffect(() => {
    if (selectedDiagnosis?.id) {
      fetchPatientGuide(selectedDiagnosis.id);
    }
  }, [selectedDiagnosis?.id]);

  const fetchPatientGuide = async (diagnosisId) => {
    setGuideLoading(true);
    try {
      const guideData = await myDiagnosisApi.getPatientGuide(diagnosisId);
      setPatientGuide(guideData);
    } catch (err) {
      console.error('Failed to fetch patient guide:', err);
    } finally {
      setGuideLoading(false);
    }
  };

  const fetchData = async () => {
    try {
      const [diagnosesData, allergenData] = await Promise.all([
        myDiagnosisApi.getAll(),
        myDiagnosisApi.getAllergenInfo(),
      ]);
      setDiagnoses(diagnosesData);
      setAllergenInfo(allergenData);
      if (diagnosesData.length > 0) {
        setSelectedDiagnosis(diagnosesData[0]);
      }
    } catch (err) {
      console.error('Failed to fetch data:', err);
      setError('데이터를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleKitRegister = async (e) => {
    e.preventDefault();
    setKitLoading(true);
    setKitError('');

    try {
      await registerKit(kitForm.serialNumber, kitForm.pin);
      setShowKitModal(false);
      setKitForm({ serialNumber: '', pin: '' });
      await fetchData();
    } catch (err) {
      const message = err.response?.data?.detail || '키트 등록에 실패했습니다.';
      setKitError(message);
    } finally {
      setKitLoading(false);
    }
  };

  const getGradeColor = (grade) => {
    if (!allergenInfo?.grades) return '#666';
    return allergenInfo.grades[grade]?.color || '#666';
  };

  const getGradeLabel = (grade) => {
    if (!allergenInfo?.grades) return `등급 ${grade}`;
    return allergenInfo.grades[grade]?.label || `등급 ${grade}`;
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>로딩 중...</p>
      </div>
    );
  }

  return (
    <div className="my-diagnosis-container">
      {/* User Header */}
      <div className="user-header">
        <div className="user-info">
          {user?.profile_image && (
            <img src={user.profile_image} alt="" className="profile-image" />
          )}
          <div>
            <h2>{user?.name}님</h2>
            <p>{user?.email || '간편 로그인'}</p>
          </div>
        </div>
        <div className="header-actions">
          <button className="btn btn-outline" onClick={() => setShowKitModal(true)}>
            + 키트 등록
          </button>
          <button className="btn btn-text" onClick={handleLogout}>
            로그아웃
          </button>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      {diagnoses.length === 0 ? (
        <div className="empty-state">
          <h3>등록된 검사 결과가 없습니다</h3>
          <p>검사키트를 등록하여 알러지 검사 결과를 확인하세요.</p>
          <button className="btn btn-primary" onClick={() => setShowKitModal(true)}>
            검사키트 등록하기
          </button>
        </div>
      ) : (
        <div className="diagnosis-content">
          {/* Diagnosis List */}
          <div className="diagnosis-list">
            <h3>검사 이력</h3>
            {diagnoses.map((diag) => (
              <div
                key={diag.id}
                className={`diagnosis-item ${selectedDiagnosis?.id === diag.id ? 'selected' : ''}`}
                onClick={() => setSelectedDiagnosis(diag)}
              >
                <div className="diag-date">{formatDate(diag.diagnosis_date)}</div>
                {diag.kit_serial && (
                  <div className="diag-serial">{diag.kit_serial}</div>
                )}
              </div>
            ))}
          </div>

          {/* Diagnosis Detail */}
          {selectedDiagnosis && (
            <div className="diagnosis-detail">
              <h3>{formatDate(selectedDiagnosis.diagnosis_date)} 검사 결과</h3>

              {/* Tab Navigation */}
              <div className="tab-navigation">
                <button
                  className={`tab-btn ${activeTab === 'results' ? 'active' : ''}`}
                  onClick={() => setActiveTab('results')}
                >
                  검사 결과
                </button>
                <button
                  className={`tab-btn ${activeTab === 'symptoms' ? 'active' : ''}`}
                  onClick={() => setActiveTab('symptoms')}
                >
                  증상/위험도
                </button>
                <button
                  className={`tab-btn ${activeTab === 'dietary' ? 'active' : ''}`}
                  onClick={() => setActiveTab('dietary')}
                >
                  식이 관리
                </button>
                <button
                  className={`tab-btn ${activeTab === 'emergency' ? 'active' : ''}`}
                  onClick={() => setActiveTab('emergency')}
                >
                  응급/의료
                </button>
                <button
                  className={`tab-btn ${activeTab === 'citations' ? 'active' : ''}`}
                  onClick={() => setActiveTab('citations')}
                >
                  출처 {patientGuide?.total_citations > 0 && `(${patientGuide.total_citations})`}
                </button>
              </div>

              {/* Tab: Results */}
              {activeTab === 'results' && (
                <>
                  <div className="allergen-section">
                    <h4>식품 알러젠</h4>
                    <div className="allergen-grid">
                      {allergenInfo?.food?.map((allergen) => {
                        const grade = selectedDiagnosis.results[allergen.code] ?? 0;
                        return (
                          <div key={allergen.code} className="allergen-card">
                            <div className="allergen-name">{allergen.name_kr}</div>
                            <div
                              className="allergen-grade"
                              style={{ backgroundColor: getGradeColor(grade) }}
                            >
                              {grade}
                            </div>
                            <div className="allergen-label">{getGradeLabel(grade)}</div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                  <div className="allergen-section">
                    <h4>흡입 알러젠</h4>
                    <div className="allergen-grid">
                      {allergenInfo?.inhalant?.map((allergen) => {
                        const grade = selectedDiagnosis.results[allergen.code] ?? 0;
                        return (
                          <div key={allergen.code} className="allergen-card">
                            <div className="allergen-name">{allergen.name_kr}</div>
                            <div
                              className="allergen-grade"
                              style={{ backgroundColor: getGradeColor(grade) }}
                            >
                              {grade}
                            </div>
                            <div className="allergen-label">{getGradeLabel(grade)}</div>
                          </div>
                        );
                      })}
                    </div>
                  </div>
                </>
              )}

              {/* Tab: Symptoms & Risk */}
              {activeTab === 'symptoms' && (
                <div className="patient-guide-section">
                  {guideLoading ? (
                    <div className="loading-small">로딩 중...</div>
                  ) : patientGuide ? (
                    <>
                      <div className="guide-intro">
                        <p>검사 결과에 따른 예상 증상과 위험도입니다.</p>
                      </div>

                      {/* High Risk */}
                      {patientGuide.symptoms_risk.high_risk.length > 0 && (
                        <div className="risk-group high-risk">
                          <h4><span className="risk-badge danger">고위험</span> 강한 반응 예상</h4>
                          {patientGuide.symptoms_risk.high_risk.map((item, idx) => (
                            <div key={idx} className="symptom-card">
                              <div className="symptom-header">
                                <span className="allergen-badge">{item.allergen}</span>
                                <span className="grade-badge">등급 {item.grade}</span>
                              </div>
                              <ul className="symptom-list">
                                {item.symptoms.map((s, i) => (
                                  <li key={i} className="symptom-item-with-citation">
                                    <div className="symptom-content">
                                      <strong>{s.name}</strong>
                                      <span className="symptom-detail">발생확률 {s.probability}, {s.onset}</span>
                                    </div>
                                    {s.citations && s.citations.length > 0 ? (
                                      <CitationBadge citations={s.citations} />
                                    ) : (
                                      <NoCitationBadge />
                                    )}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Moderate Risk */}
                      {patientGuide.symptoms_risk.moderate_risk.length > 0 && (
                        <div className="risk-group moderate-risk">
                          <h4><span className="risk-badge warning">주의</span> 중등도 반응 예상</h4>
                          {patientGuide.symptoms_risk.moderate_risk.map((item, idx) => (
                            <div key={idx} className="symptom-card">
                              <div className="symptom-header">
                                <span className="allergen-badge">{item.allergen}</span>
                                <span className="grade-badge">등급 {item.grade}</span>
                              </div>
                              <ul className="symptom-list">
                                {item.symptoms.map((s, i) => (
                                  <li key={i} className="symptom-item-with-citation">
                                    <div className="symptom-content">
                                      <strong>{s.name}</strong>
                                      <span className="symptom-detail">발생확률 {s.probability}, {s.onset}</span>
                                    </div>
                                    {s.citations && s.citations.length > 0 ? (
                                      <CitationBadge citations={s.citations} />
                                    ) : (
                                      <NoCitationBadge />
                                    )}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Low Risk */}
                      {patientGuide.symptoms_risk.low_risk.length > 0 && (
                        <div className="risk-group low-risk">
                          <h4><span className="risk-badge info">경미</span> 약한 반응 예상</h4>
                          {patientGuide.symptoms_risk.low_risk.map((item, idx) => (
                            <div key={idx} className="symptom-card">
                              <div className="symptom-header">
                                <span className="allergen-badge">{item.allergen}</span>
                                <span className="grade-badge">등급 {item.grade}</span>
                              </div>
                              <ul className="symptom-list">
                                {item.symptoms.map((s, i) => (
                                  <li key={i} className="symptom-item-with-citation">
                                    <div className="symptom-content">
                                      <strong>{s.name}</strong>
                                      <span className="symptom-detail">발생확률 {s.probability}, {s.onset}</span>
                                    </div>
                                    {s.citations && s.citations.length > 0 ? (
                                      <CitationBadge citations={s.citations} />
                                    ) : (
                                      <NoCitationBadge />
                                    )}
                                  </li>
                                ))}
                              </ul>
                            </div>
                          ))}
                        </div>
                      )}
                    </>
                  ) : (
                    <p>데이터를 불러오지 못했습니다.</p>
                  )}
                </div>
              )}

              {/* Tab: Dietary Management */}
              {activeTab === 'dietary' && (
                <div className="patient-guide-section">
                  {guideLoading ? (
                    <div className="loading-small">로딩 중...</div>
                  ) : patientGuide ? (
                    <>
                      <div className="guide-intro">
                        <p>무엇을 먹으면 안 되는지, 어떤 음식에 주의해야 하는지 안내합니다.</p>
                      </div>

                      {/* Avoid Foods */}
                      {patientGuide.dietary_management.avoid_foods.length > 0 && (
                        <div className="dietary-group">
                          <h4>회피해야 할 식품</h4>
                          {patientGuide.dietary_management.avoid_foods.map((item, idx) => (
                            <div key={idx} className="dietary-card">
                              <div className="dietary-header">
                                <span className="allergen-badge danger">{item.allergen}</span>
                              </div>
                              <div className="food-tags">
                                {item.foods.map((food, i) => (
                                  <span key={i} className="food-tag-with-citation">
                                    <span className="food-tag danger">
                                      {typeof food === 'object' ? food.name : food}
                                    </span>
                                    {food.citations && food.citations.length > 0 ? (
                                      <CitationBadge citations={food.citations} small />
                                    ) : (
                                      <NoCitationBadge small />
                                    )}
                                  </span>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Hidden Sources */}
                      {patientGuide.dietary_management.hidden_sources.length > 0 && (
                        <div className="dietary-group">
                          <h4>숨겨진 알러젠 주의</h4>
                          {patientGuide.dietary_management.hidden_sources.map((item, idx) => (
                            <div key={idx} className="dietary-card">
                              <div className="dietary-header">
                                <span className="allergen-badge warning">{item.allergen}</span>
                              </div>
                              <div className="food-tags">
                                {item.sources.map((source, i) => (
                                  <span key={i} className="food-tag-with-citation">
                                    <span className="food-tag warning">
                                      {typeof source === 'object' ? source.name : source}
                                    </span>
                                    {source.citations && source.citations.length > 0 ? (
                                      <CitationBadge citations={source.citations} small />
                                    ) : (
                                      <NoCitationBadge small />
                                    )}
                                  </span>
                                ))}
                              </div>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Cross Reactivity */}
                      {patientGuide.dietary_management.cross_reactivity.length > 0 && (
                        <div className="dietary-group">
                          <h4>교차반응 주의</h4>
                          <div className="cross-reaction-list">
                            {patientGuide.dietary_management.cross_reactivity.map((item, idx) => (
                              <div key={idx} className="cross-card">
                                <span className="cross-from">{item.from_allergen}</span>
                                <span className="cross-arrow">→</span>
                                <span className="cross-to">{item.to_allergen}</span>
                                <span className="cross-prob">{item.probability}</span>
                                {item.citations && item.citations.length > 0 ? (
                                  <CitationBadge citations={item.citations} small />
                                ) : (
                                  <NoCitationBadge small />
                                )}
                              </div>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* Substitutes */}
                      {patientGuide.dietary_management.substitutes.length > 0 && (
                        <div className="dietary-group">
                          <h4>대체 식품</h4>
                          {patientGuide.dietary_management.substitutes.map((item, idx) => (
                            <div key={idx} className="substitute-card">
                              <div className="substitute-original">
                                <span className="allergen-small">{item.allergen}</span>
                                <strong>{item.original}</strong>
                              </div>
                              <div className="substitute-arrow">→</div>
                              <div className="substitute-alternatives">
                                {item.alternatives.map((alt, i) => (
                                  <span key={i} className="alt-tag">{alt}</span>
                                ))}
                              </div>
                              {item.citations && item.citations.length > 0 ? (
                                <CitationBadge citations={item.citations} small />
                              ) : (
                                <NoCitationBadge small />
                              )}
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Restaurant Cautions */}
                      {patientGuide.dietary_management.restaurant_cautions.length > 0 && (
                        <div className="dietary-group">
                          <h4>외식 시 주의</h4>
                          <ul className="caution-list">
                            {patientGuide.dietary_management.restaurant_cautions.map((caution, idx) => (
                              <li key={idx}>{caution}</li>
                            ))}
                          </ul>
                        </div>
                      )}
                    </>
                  ) : (
                    <p>데이터를 불러오지 못했습니다.</p>
                  )}
                </div>
              )}

              {/* Tab: Emergency & Medical */}
              {activeTab === 'emergency' && (
                <div className="patient-guide-section">
                  {guideLoading ? (
                    <div className="loading-small">로딩 중...</div>
                  ) : patientGuide ? (
                    <>
                      <div className="guide-intro">
                        <p>문제 발생 시 어떻게 대처해야 하는지 안내합니다.</p>
                      </div>

                      {/* Severe Allergy Warning */}
                      {patientGuide.emergency_medical.has_severe_allergy && (
                        <div className="emergency-alert">
                          <h4>아나필락시스 위험</h4>
                          <p>고등급 알러지가 있습니다. 에피네프린 자가주사기(에피펜) 처방을 의사와 상담하세요.</p>
                        </div>
                      )}

                      {/* Emergency Guidelines */}
                      <div className="emergency-group">
                        <h4>응급 대처법</h4>

                        {/* Anaphylaxis */}
                        <div className="emergency-card severe">
                          <h5>{patientGuide.emergency_medical.emergency_guidelines.anaphylaxis.condition}</h5>
                          <p className="emergency-desc">
                            {patientGuide.emergency_medical.emergency_guidelines.anaphylaxis.description}
                          </p>
                          <div className="emergency-symptoms">
                            <strong>증상:</strong>
                            <ul>
                              {patientGuide.emergency_medical.emergency_guidelines.anaphylaxis.symptoms.slice(0, 5).map((s, i) => (
                                <li key={i}>{s}</li>
                              ))}
                            </ul>
                          </div>
                          <div className="emergency-actions">
                            <strong>즉시 조치:</strong>
                            <ol>
                              {patientGuide.emergency_medical.emergency_guidelines.anaphylaxis.immediate_actions.slice(0, 4).map((a, i) => (
                                <li key={i}>{a}</li>
                              ))}
                            </ol>
                          </div>
                        </div>

                        {/* Mild Reaction */}
                        <div className="emergency-card mild">
                          <h5>{patientGuide.emergency_medical.emergency_guidelines.mild_reaction.condition}</h5>
                          <div className="emergency-actions">
                            <strong>조치:</strong>
                            <ol>
                              {patientGuide.emergency_medical.emergency_guidelines.mild_reaction.immediate_actions.map((a, i) => (
                                <li key={i}>{a}</li>
                              ))}
                            </ol>
                          </div>
                        </div>
                      </div>

                      {/* Management Tips (for inhalant allergies) */}
                      {patientGuide.emergency_medical.management_tips.length > 0 && (
                        <div className="management-group">
                          <h4>환경 관리 권고</h4>
                          {patientGuide.emergency_medical.management_tips.map((item, idx) => (
                            <div key={idx} className="management-card">
                              <div className="management-header">
                                <span className="allergen-badge info">{item.allergen}</span>
                              </div>
                              <ul className="management-list">
                                {item.tips.map((tip, i) => (
                                  <li key={i}>{tip}</li>
                                ))}
                              </ul>
                            </div>
                          ))}
                        </div>
                      )}

                      {/* Medical Consultation */}
                      <div className="medical-note">
                        <h4>의료 상담 권고</h4>
                        <ul>
                          <li>알러지 전문의 상담을 통해 정확한 진단을 받으세요.</li>
                          <li>필요시 추가 검사(피부단자검사, 유발검사)를 고려하세요.</li>
                          <li>심한 알러지는 면역치료(탈감작)를 상담해 보세요.</li>
                        </ul>
                      </div>
                    </>
                  ) : (
                    <p>데이터를 불러오지 못했습니다.</p>
                  )}
                </div>
              )}

              {/* Tab: Citations */}
              {activeTab === 'citations' && (
                <div className="patient-guide-section">
                  {guideLoading ? (
                    <div className="loading-small">로딩 중...</div>
                  ) : patientGuide?.citations ? (
                    <>
                      <div className="guide-intro">
                        <p>의학 정보의 근거가 되는 논문 및 가이드라인 출처입니다.</p>
                      </div>

                      {patientGuide.total_citations === 0 ? (
                        <div className="no-citations">
                          <p>아직 등록된 출처가 없습니다.</p>
                          <p className="no-citations-sub">논문 정보는 점차 추가될 예정입니다.</p>
                        </div>
                      ) : (
                        <>
                          {/* Symptoms Citations */}
                          {patientGuide.citations.symptoms?.length > 0 && (
                            <div className="citation-group">
                              <h4>증상 관련 문헌</h4>
                              <div className="citation-list">
                                {patientGuide.citations.symptoms.map((paper, idx) => (
                                  <div key={idx} className="citation-card">
                                    <div className="citation-type">
                                      <span className={`type-badge ${paper.paper_type}`}>
                                        {paper.paper_type === 'guideline' ? '가이드라인' :
                                         paper.paper_type === 'review' ? '리뷰' :
                                         paper.paper_type === 'meta_analysis' ? '메타분석' : '연구'}
                                      </span>
                                    </div>
                                    <div className="citation-title">
                                      {paper.title_kr || paper.title}
                                    </div>
                                    <div className="citation-meta">
                                      {paper.authors && <span>{paper.authors}</span>}
                                      {paper.journal && <span>{paper.journal}</span>}
                                      {paper.year && <span>{paper.year}</span>}
                                    </div>
                                    {paper.url && (
                                      <a href={paper.url} target="_blank" rel="noopener noreferrer" className="citation-link">
                                        원문 보기 →
                                      </a>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Dietary Citations */}
                          {patientGuide.citations.dietary?.length > 0 && (
                            <div className="citation-group">
                              <h4>식이 관리 관련 문헌</h4>
                              <div className="citation-list">
                                {patientGuide.citations.dietary.map((paper, idx) => (
                                  <div key={idx} className="citation-card">
                                    <div className="citation-type">
                                      <span className={`type-badge ${paper.paper_type}`}>
                                        {paper.paper_type === 'guideline' ? '가이드라인' :
                                         paper.paper_type === 'review' ? '리뷰' :
                                         paper.paper_type === 'meta_analysis' ? '메타분석' : '연구'}
                                      </span>
                                    </div>
                                    <div className="citation-title">
                                      {paper.title_kr || paper.title}
                                    </div>
                                    <div className="citation-meta">
                                      {paper.authors && <span>{paper.authors}</span>}
                                      {paper.journal && <span>{paper.journal}</span>}
                                      {paper.year && <span>{paper.year}</span>}
                                    </div>
                                    {paper.url && (
                                      <a href={paper.url} target="_blank" rel="noopener noreferrer" className="citation-link">
                                        원문 보기 →
                                      </a>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Cross Reactivity Citations */}
                          {patientGuide.citations.cross_reactivity?.length > 0 && (
                            <div className="citation-group">
                              <h4>교차반응 관련 문헌</h4>
                              <div className="citation-list">
                                {patientGuide.citations.cross_reactivity.map((paper, idx) => (
                                  <div key={idx} className="citation-card">
                                    <div className="citation-type">
                                      <span className={`type-badge ${paper.paper_type}`}>
                                        {paper.paper_type === 'guideline' ? '가이드라인' :
                                         paper.paper_type === 'review' ? '리뷰' :
                                         paper.paper_type === 'meta_analysis' ? '메타분석' : '연구'}
                                      </span>
                                    </div>
                                    <div className="citation-title">
                                      {paper.title_kr || paper.title}
                                    </div>
                                    <div className="citation-meta">
                                      {paper.authors && <span>{paper.authors}</span>}
                                      {paper.journal && <span>{paper.journal}</span>}
                                      {paper.year && <span>{paper.year}</span>}
                                    </div>
                                    {paper.url && (
                                      <a href={paper.url} target="_blank" rel="noopener noreferrer" className="citation-link">
                                        원문 보기 →
                                      </a>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}

                          {/* Emergency Citations */}
                          {patientGuide.citations.emergency?.length > 0 && (
                            <div className="citation-group">
                              <h4>응급 대처 관련 문헌</h4>
                              <div className="citation-list">
                                {patientGuide.citations.emergency.map((paper, idx) => (
                                  <div key={idx} className="citation-card">
                                    <div className="citation-type">
                                      <span className={`type-badge ${paper.paper_type}`}>
                                        {paper.paper_type === 'guideline' ? '가이드라인' :
                                         paper.paper_type === 'review' ? '리뷰' :
                                         paper.paper_type === 'meta_analysis' ? '메타분석' : '연구'}
                                      </span>
                                    </div>
                                    <div className="citation-title">
                                      {paper.title_kr || paper.title}
                                    </div>
                                    <div className="citation-meta">
                                      {paper.authors && <span>{paper.authors}</span>}
                                      {paper.journal && <span>{paper.journal}</span>}
                                      {paper.year && <span>{paper.year}</span>}
                                    </div>
                                    {paper.url && (
                                      <a href={paper.url} target="_blank" rel="noopener noreferrer" className="citation-link">
                                        원문 보기 →
                                      </a>
                                    )}
                                  </div>
                                ))}
                              </div>
                            </div>
                          )}
                        </>
                      )}

                      <div className="citation-note">
                        <p>출처는 지속적으로 업데이트됩니다. 의학적 결정은 반드시 전문의와 상담하세요.</p>
                      </div>
                    </>
                  ) : (
                    <p>데이터를 불러오지 못했습니다.</p>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      )}

      {/* Kit Registration Modal */}
      {showKitModal && (
        <div className="modal-overlay" onClick={() => setShowKitModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>검사키트 등록</h3>
            <form onSubmit={handleKitRegister}>
              <div className="form-group">
                <label>시리얼번호</label>
                <input
                  type="text"
                  value={kitForm.serialNumber}
                  onChange={(e) => setKitForm({ ...kitForm, serialNumber: e.target.value })}
                  placeholder="SGT-2024-XXXXX-XXXX"
                  required
                />
              </div>
              <div className="form-group">
                <label>PIN</label>
                <input
                  type="password"
                  value={kitForm.pin}
                  onChange={(e) => setKitForm({ ...kitForm, pin: e.target.value })}
                  placeholder="6자리 PIN"
                  maxLength={6}
                  required
                />
              </div>
              {kitError && <div className="error-message">{kitError}</div>}
              <div className="modal-actions">
                <button type="button" className="btn btn-outline" onClick={() => setShowKitModal(false)}>
                  취소
                </button>
                <button type="submit" className="btn btn-primary" disabled={kitLoading}>
                  {kitLoading ? '등록 중...' : '등록'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <style>{`
        .my-diagnosis-container {
          max-width: 1200px;
          margin: 0 auto;
          padding: 1rem;
        }

        .user-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          background: white;
          padding: 1rem 1.5rem;
          border-radius: 12px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
          margin-bottom: 1.5rem;
        }

        .user-info {
          display: flex;
          align-items: center;
          gap: 1rem;
        }

        .profile-image {
          width: 48px;
          height: 48px;
          border-radius: 50%;
        }

        .user-info h2 {
          margin: 0;
          font-size: 1.25rem;
        }

        .user-info p {
          margin: 0;
          color: #666;
          font-size: 0.9rem;
        }

        .header-actions {
          display: flex;
          gap: 0.5rem;
        }

        .btn {
          padding: 0.5rem 1rem;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-size: 0.9rem;
          transition: all 0.2s;
        }

        .btn-outline {
          background: white;
          border: 1px solid #2196F3;
          color: #2196F3;
        }

        .btn-text {
          background: transparent;
          color: #666;
        }

        .btn-primary {
          background: #2196F3;
          color: white;
        }

        .btn-primary:hover {
          background: #1976D2;
        }

        .btn-large {
          padding: 0.75rem 1.5rem;
          font-size: 1rem;
          width: 100%;
          margin-top: 1.5rem;
        }

        .loading-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          min-height: 50vh;
        }

        .spinner {
          width: 40px;
          height: 40px;
          border: 4px solid #f3f3f3;
          border-top: 4px solid #2196F3;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .error-message {
          color: #d32f2f;
          background: #ffebee;
          padding: 0.75rem;
          border-radius: 6px;
          margin-bottom: 1rem;
        }

        .empty-state {
          text-align: center;
          padding: 3rem;
          background: white;
          border-radius: 12px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .empty-state h3 {
          color: #333;
        }

        .empty-state p {
          color: #666;
          margin-bottom: 1.5rem;
        }

        .diagnosis-content {
          display: grid;
          grid-template-columns: 300px 1fr;
          gap: 1.5rem;
        }

        @media (max-width: 768px) {
          .diagnosis-content {
            grid-template-columns: 1fr;
          }
        }

        .diagnosis-list {
          background: white;
          border-radius: 12px;
          padding: 1rem;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .diagnosis-list h3 {
          margin: 0 0 1rem;
          font-size: 1rem;
          color: #666;
        }

        .diagnosis-item {
          padding: 0.75rem;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s;
          margin-bottom: 0.5rem;
        }

        .diagnosis-item:hover {
          background: #f5f5f5;
        }

        .diagnosis-item.selected {
          background: #E3F2FD;
          border-left: 3px solid #2196F3;
        }

        .diag-date {
          font-weight: 500;
        }

        .diag-serial {
          font-size: 0.8rem;
          color: #666;
        }

        .diagnosis-detail {
          background: white;
          border-radius: 12px;
          padding: 1.5rem;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .diagnosis-detail h3 {
          margin: 0 0 1.5rem;
        }

        .allergen-section {
          margin-bottom: 1.5rem;
        }

        .allergen-section h4 {
          margin: 0 0 0.75rem;
          color: #666;
          font-size: 0.9rem;
        }

        .allergen-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
          gap: 0.75rem;
        }

        .allergen-card {
          text-align: center;
          padding: 0.75rem;
          background: #f5f5f5;
          border-radius: 8px;
        }

        .allergen-name {
          font-size: 0.85rem;
          margin-bottom: 0.5rem;
        }

        .allergen-grade {
          width: 36px;
          height: 36px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          margin: 0 auto;
          color: white;
          font-weight: bold;
          font-size: 1.1rem;
        }

        .allergen-label {
          font-size: 0.75rem;
          color: #666;
          margin-top: 0.25rem;
        }

        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0,0,0,0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .modal-content {
          background: white;
          border-radius: 12px;
          padding: 1.5rem;
          width: 90%;
          max-width: 400px;
        }

        .modal-content h3 {
          margin: 0 0 1.5rem;
        }

        .form-group {
          margin-bottom: 1rem;
        }

        .form-group label {
          display: block;
          margin-bottom: 0.5rem;
          font-size: 0.9rem;
        }

        .form-group input {
          width: 100%;
          padding: 0.75rem;
          border: 1px solid #ddd;
          border-radius: 8px;
          font-size: 1rem;
          box-sizing: border-box;
        }

        .modal-actions {
          display: flex;
          gap: 0.5rem;
          margin-top: 1.5rem;
        }

        .modal-actions .btn {
          flex: 1;
        }

        /* Tab Navigation */
        .tab-navigation {
          display: flex;
          gap: 0.25rem;
          margin-bottom: 1.5rem;
          border-bottom: 2px solid #e0e0e0;
          padding-bottom: 0;
          overflow-x: auto;
        }

        .tab-btn {
          padding: 0.75rem 1rem;
          border: none;
          background: transparent;
          cursor: pointer;
          font-size: 0.9rem;
          color: #666;
          border-bottom: 3px solid transparent;
          margin-bottom: -2px;
          transition: all 0.2s;
          white-space: nowrap;
        }

        .tab-btn:hover {
          color: #2196F3;
          background: #f5f5f5;
        }

        .tab-btn.active {
          color: #2196F3;
          border-bottom-color: #2196F3;
          font-weight: 600;
        }

        /* Patient Guide Section */
        .patient-guide-section {
          padding: 0.5rem 0;
        }

        .guide-intro {
          background: #e3f2fd;
          padding: 1rem;
          border-radius: 8px;
          margin-bottom: 1.5rem;
        }

        .guide-intro p {
          margin: 0;
          color: #1565c0;
          font-size: 0.95rem;
        }

        .loading-small {
          text-align: center;
          color: #666;
          padding: 2rem;
        }

        /* Risk Groups */
        .risk-group {
          margin-bottom: 1.5rem;
          padding: 1rem;
          border-radius: 10px;
        }

        .risk-group h4 {
          margin: 0 0 1rem;
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .risk-group.high-risk {
          background: #ffebee;
          border-left: 4px solid #f44336;
        }

        .risk-group.moderate-risk {
          background: #fff8e1;
          border-left: 4px solid #ff9800;
        }

        .risk-group.low-risk {
          background: #e8f5e9;
          border-left: 4px solid #4caf50;
        }

        /* Badges */
        .risk-badge {
          padding: 0.25rem 0.6rem;
          border-radius: 4px;
          font-size: 0.75rem;
          font-weight: bold;
          color: white;
        }

        .risk-badge.danger {
          background: #f44336;
        }

        .risk-badge.warning {
          background: #ff9800;
        }

        .risk-badge.info {
          background: #4caf50;
        }

        .allergen-badge {
          padding: 0.25rem 0.5rem;
          border-radius: 4px;
          font-size: 0.85rem;
          font-weight: 500;
          background: #e0e0e0;
          color: #333;
        }

        .allergen-badge.danger {
          background: #ffcdd2;
          color: #c62828;
        }

        .allergen-badge.warning {
          background: #ffe0b2;
          color: #e65100;
        }

        .allergen-badge.info {
          background: #b3e5fc;
          color: #01579b;
        }

        .grade-badge {
          padding: 0.2rem 0.5rem;
          border-radius: 4px;
          font-size: 0.8rem;
          background: #424242;
          color: white;
        }

        /* Symptom Cards */
        .symptom-card {
          background: white;
          padding: 1rem;
          border-radius: 8px;
          margin-bottom: 0.75rem;
          box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .symptom-header {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          margin-bottom: 0.75rem;
        }

        .symptom-list {
          margin: 0;
          padding-left: 1.2rem;
        }

        .symptom-list li {
          margin-bottom: 0.5rem;
        }

        .symptom-detail {
          display: block;
          font-size: 0.8rem;
          color: #666;
          margin-top: 0.1rem;
        }

        /* Dietary Groups */
        .dietary-group {
          margin-bottom: 1.5rem;
        }

        .dietary-group h4 {
          margin: 0 0 0.75rem;
          color: #333;
          font-size: 1rem;
          padding-bottom: 0.5rem;
          border-bottom: 1px solid #e0e0e0;
        }

        .dietary-card {
          background: #fafafa;
          padding: 1rem;
          border-radius: 8px;
          margin-bottom: 0.75rem;
        }

        .dietary-header {
          margin-bottom: 0.75rem;
        }

        .food-tags {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
        }

        .food-tag {
          padding: 0.35rem 0.7rem;
          border-radius: 20px;
          font-size: 0.85rem;
          background: #e0e0e0;
        }

        .food-tag.danger {
          background: #ffcdd2;
          color: #c62828;
        }

        .food-tag.warning {
          background: #ffe0b2;
          color: #e65100;
        }

        /* Cross Reactivity */
        .cross-reaction-list {
          display: flex;
          flex-direction: column;
          gap: 0.5rem;
        }

        .cross-card {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.75rem;
          background: #f5f5f5;
          border-radius: 8px;
        }

        .cross-from {
          font-weight: 500;
          color: #d32f2f;
        }

        .cross-arrow {
          color: #999;
        }

        .cross-to {
          font-weight: 500;
          color: #f57c00;
        }

        .cross-prob {
          margin-left: auto;
          font-size: 0.8rem;
          color: #666;
          background: #e0e0e0;
          padding: 0.2rem 0.5rem;
          border-radius: 4px;
        }

        /* Substitutes */
        .substitute-card {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.75rem;
          background: #f5f5f5;
          border-radius: 8px;
          margin-bottom: 0.5rem;
          flex-wrap: wrap;
        }

        .substitute-original {
          display: flex;
          align-items: center;
          gap: 0.5rem;
        }

        .allergen-small {
          font-size: 0.7rem;
          background: #e0e0e0;
          padding: 0.15rem 0.4rem;
          border-radius: 3px;
        }

        .substitute-arrow {
          color: #4caf50;
          font-weight: bold;
        }

        .substitute-alternatives {
          display: flex;
          flex-wrap: wrap;
          gap: 0.4rem;
        }

        .alt-tag {
          padding: 0.25rem 0.5rem;
          background: #c8e6c9;
          color: #2e7d32;
          border-radius: 4px;
          font-size: 0.85rem;
        }

        /* Caution List */
        .caution-list {
          margin: 0;
          padding-left: 1.2rem;
          color: #666;
        }

        .caution-list li {
          margin-bottom: 0.5rem;
        }

        /* Emergency Section */
        .emergency-alert {
          background: linear-gradient(135deg, #ffebee, #ffcdd2);
          border: 2px solid #f44336;
          border-radius: 10px;
          padding: 1.25rem;
          margin-bottom: 1.5rem;
        }

        .emergency-alert h4 {
          margin: 0 0 0.5rem;
          color: #c62828;
        }

        .emergency-alert p {
          margin: 0;
          color: #d32f2f;
        }

        .emergency-group {
          margin-bottom: 1.5rem;
        }

        .emergency-group h4 {
          margin: 0 0 1rem;
          color: #333;
          font-size: 1rem;
        }

        .emergency-card {
          padding: 1rem;
          border-radius: 8px;
          margin-bottom: 1rem;
        }

        .emergency-card.severe {
          background: #ffebee;
          border-left: 4px solid #f44336;
        }

        .emergency-card.mild {
          background: #f5f5f5;
          border-left: 4px solid #9e9e9e;
        }

        .emergency-card h5 {
          margin: 0 0 0.75rem;
          color: #333;
        }

        .emergency-desc {
          font-size: 0.9rem;
          color: #666;
          margin-bottom: 0.75rem;
        }

        .emergency-symptoms ul,
        .emergency-actions ol {
          margin: 0.5rem 0;
          padding-left: 1.2rem;
        }

        .emergency-symptoms li,
        .emergency-actions li {
          margin-bottom: 0.3rem;
          font-size: 0.9rem;
        }

        /* Management Section */
        .management-group {
          margin-bottom: 1.5rem;
        }

        .management-group h4 {
          margin: 0 0 1rem;
          color: #333;
        }

        .management-card {
          background: #e3f2fd;
          padding: 1rem;
          border-radius: 8px;
          margin-bottom: 0.75rem;
        }

        .management-header {
          margin-bottom: 0.75rem;
        }

        .management-list {
          margin: 0;
          padding-left: 1.2rem;
        }

        .management-list li {
          margin-bottom: 0.4rem;
          font-size: 0.9rem;
          color: #333;
        }

        /* Medical Note */
        .medical-note {
          background: #f3e5f5;
          border-left: 4px solid #9c27b0;
          padding: 1rem;
          border-radius: 8px;
        }

        .medical-note h4 {
          margin: 0 0 0.75rem;
          color: #6a1b9a;
        }

        .medical-note ul {
          margin: 0;
          padding-left: 1.2rem;
        }

        .medical-note li {
          margin-bottom: 0.4rem;
          color: #333;
        }

        /* Citation Section */
        .no-citations {
          text-align: center;
          padding: 3rem 1rem;
          color: #666;
        }

        .no-citations p {
          margin: 0;
        }

        .no-citations-sub {
          font-size: 0.85rem;
          margin-top: 0.5rem !important;
          color: #999;
        }

        .citation-group {
          margin-bottom: 1.5rem;
        }

        .citation-group h4 {
          margin: 0 0 0.75rem;
          color: #333;
          font-size: 1rem;
          padding-bottom: 0.5rem;
          border-bottom: 1px solid #e0e0e0;
        }

        .citation-list {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .citation-card {
          background: #fafafa;
          border: 1px solid #e0e0e0;
          border-radius: 8px;
          padding: 1rem;
        }

        .citation-type {
          margin-bottom: 0.5rem;
        }

        .type-badge {
          display: inline-block;
          padding: 0.2rem 0.5rem;
          border-radius: 4px;
          font-size: 0.7rem;
          font-weight: 600;
          text-transform: uppercase;
        }

        .type-badge.research {
          background: #e3f2fd;
          color: #1565c0;
        }

        .type-badge.review {
          background: #f3e5f5;
          color: #7b1fa2;
        }

        .type-badge.guideline {
          background: #e8f5e9;
          color: #2e7d32;
        }

        .type-badge.meta_analysis {
          background: #fff3e0;
          color: #e65100;
        }

        .citation-title {
          font-weight: 500;
          color: #333;
          margin-bottom: 0.5rem;
          line-height: 1.4;
        }

        .citation-meta {
          display: flex;
          flex-wrap: wrap;
          gap: 0.5rem;
          font-size: 0.8rem;
          color: #666;
          margin-bottom: 0.5rem;
        }

        .citation-meta span:not(:last-child)::after {
          content: '·';
          margin-left: 0.5rem;
        }

        .citation-link {
          display: inline-block;
          color: #1976d2;
          font-size: 0.85rem;
          text-decoration: none;
        }

        .citation-link:hover {
          text-decoration: underline;
        }

        .citation-note {
          margin-top: 1.5rem;
          padding: 0.75rem 1rem;
          background: #f5f5f5;
          border-radius: 6px;
          font-size: 0.85rem;
          color: #666;
          text-align: center;
        }

        .citation-note p {
          margin: 0;
        }

        /* Citation Badge Styles */
        .citation-badge {
          display: inline-flex;
          align-items: center;
          position: relative;
          cursor: pointer;
          margin-left: 0.5rem;
        }

        .citation-badge.small {
          margin-left: 0.25rem;
        }

        .citation-icon {
          font-size: 0.9rem;
          opacity: 0.7;
          transition: opacity 0.2s;
        }

        .citation-badge.small .citation-icon {
          font-size: 0.75rem;
        }

        .citation-badge:hover .citation-icon {
          opacity: 1;
        }

        .citation-count {
          font-size: 0.65rem;
          font-weight: bold;
          color: #1976d2;
          margin-left: 1px;
          vertical-align: super;
        }

        .citation-badge.small .citation-count {
          font-size: 0.55rem;
        }

        .citation-tooltip-more {
          font-size: 0.7rem;
          color: #1976d2;
          margin-top: 0.5rem;
          font-style: italic;
        }

        /* No Citation Badge */
        .no-citation-badge {
          display: inline-flex;
          align-items: center;
          margin-left: 0.5rem;
          opacity: 0.4;
        }

        .no-citation-badge.small {
          margin-left: 0.25rem;
        }

        .no-citation-icon {
          font-size: 0.75rem;
        }

        .no-citation-badge.small .no-citation-icon {
          font-size: 0.6rem;
        }

        .citation-tooltip {
          position: absolute;
          bottom: 100%;
          left: 50%;
          transform: translateX(-50%);
          background: white;
          border: 1px solid #e0e0e0;
          border-radius: 8px;
          padding: 0.75rem;
          width: 280px;
          box-shadow: 0 4px 12px rgba(0,0,0,0.15);
          z-index: 1000;
          margin-bottom: 0.5rem;
        }

        .citation-tooltip::after {
          content: '';
          position: absolute;
          top: 100%;
          left: 50%;
          transform: translateX(-50%);
          border: 6px solid transparent;
          border-top-color: white;
        }

        .citation-tooltip-title {
          font-size: 0.85rem;
          font-weight: 500;
          color: #333;
          margin-bottom: 0.5rem;
          line-height: 1.4;
        }

        .citation-tooltip-meta {
          display: flex;
          flex-wrap: wrap;
          gap: 0.25rem;
          font-size: 0.75rem;
          color: #666;
          margin-bottom: 0.5rem;
        }

        .citation-tooltip-meta span:not(:last-child)::after {
          content: ' · ';
        }

        .citation-tooltip-link {
          font-size: 0.75rem;
          color: #1976d2;
          margin-top: 0.25rem;
        }

        /* Symptom item with citation */
        .symptom-item-with-citation {
          display: flex;
          align-items: flex-start;
          justify-content: space-between;
          gap: 0.5rem;
        }

        .symptom-content {
          flex: 1;
        }

        /* Food tag with citation */
        .food-tag-with-citation {
          display: inline-flex;
          align-items: center;
          margin-right: 0.5rem;
          margin-bottom: 0.5rem;
        }

        @media (max-width: 600px) {
          .tab-navigation {
            gap: 0;
          }

          .tab-btn {
            padding: 0.6rem 0.75rem;
            font-size: 0.8rem;
          }

          .symptom-header {
            flex-wrap: wrap;
          }

          .substitute-card {
            flex-direction: column;
            align-items: flex-start;
          }

          .citation-tooltip {
            width: 220px;
            left: auto;
            right: 0;
            transform: none;
          }
        }
      `}</style>
    </div>
  );
};

export default MyDiagnosisPage;
