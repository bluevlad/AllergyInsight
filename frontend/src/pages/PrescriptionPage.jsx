import React, { useState } from 'react';
import { useLocation, useNavigate } from 'react-router-dom';

// 등급별 색상
const gradeColors = {
  0: '#4CAF50', 1: '#8BC34A', 2: '#FFEB3B',
  3: '#FFC107', 4: '#FF9800', 5: '#F44336', 6: '#B71C1C',
};

// 위험도별 색상
const riskColors = {
  none: '#4CAF50',
  low: '#8BC34A',
  moderate: '#FFC107',
  high: '#FF9800',
  critical: '#F44336',
};

// 위험도 한글 변환
const riskLabels = {
  none: '없음',
  low: '낮음',
  moderate: '중간',
  high: '높음',
  critical: '매우 높음',
};

// 제한 수준 한글 변환
const restrictionLabels = {
  none: '제한 없음',
  monitor: '모니터링',
  caution: '주의',
  limit: '제한',
  avoid: '회피',
  strict_avoid: '완전 회피',
};

function PrescriptionPage() {
  const location = useLocation();
  const navigate = useNavigate();
  const prescription = location.state?.prescription;

  const [activeTab, setActiveTab] = useState('symptoms');

  if (!prescription) {
    return (
      <div style={{ textAlign: 'center', padding: '48px' }}>
        <h2>처방 정보가 없습니다</h2>
        <p>진단 결과를 먼저 입력해주세요.</p>
        <button
          onClick={() => navigate('/diagnosis')}
          style={{
            marginTop: '16px',
            padding: '12px 24px',
            backgroundColor: '#1976D2',
            color: 'white',
            border: 'none',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          진단 결과 입력하기
        </button>
      </div>
    );
  }

  const { summary, diagnosis_results, food_restrictions, cross_reactivity_alerts,
    predicted_symptoms, emergency_guidelines, medical_recommendation,
    general_recommendations, lifestyle_tips } = prescription;

  // 양성 결과만 필터링
  const positiveResults = diagnosis_results?.filter(r => r.is_positive) || [];

  // 탭 컴포넌트
  const TabButton = ({ id, label }) => (
    <button
      onClick={() => setActiveTab(id)}
      style={{
        padding: '12px 20px',
        border: 'none',
        borderBottom: activeTab === id ? '3px solid #1976D2' : '3px solid transparent',
        backgroundColor: activeTab === id ? '#E3F2FD' : 'transparent',
        cursor: 'pointer',
        fontWeight: activeTab === id ? 'bold' : 'normal',
        fontSize: '0.95rem',
      }}
    >
      {label}
    </button>
  );

  return (
    <div style={{ maxWidth: '1000px', margin: '0 auto' }}>
      <h2>처방 권고 결과</h2>

      {/* 요약 카드 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(4, 1fr)',
        gap: '16px',
        marginBottom: '24px',
      }}>
        <div style={{
          backgroundColor: '#E3F2FD',
          padding: '20px',
          borderRadius: '8px',
          textAlign: 'center',
        }}>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#1976D2' }}>
            {summary?.positive_count || 0}
          </div>
          <div style={{ color: '#666', fontSize: '0.9rem' }}>양성 항원</div>
        </div>
        <div style={{
          backgroundColor: '#FFF3E0',
          padding: '20px',
          borderRadius: '8px',
          textAlign: 'center',
        }}>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#F57C00' }}>
            {summary?.highest_grade || 0}
          </div>
          <div style={{ color: '#666', fontSize: '0.9rem' }}>최고 등급</div>
        </div>
        <div style={{
          backgroundColor: riskColors[summary?.risk_level] ? `${riskColors[summary?.risk_level]}22` : '#f5f5f5',
          padding: '20px',
          borderRadius: '8px',
          textAlign: 'center',
        }}>
          <div style={{
            fontSize: '1.2rem',
            fontWeight: 'bold',
            color: riskColors[summary?.risk_level] || '#666',
          }}>
            {riskLabels[summary?.risk_level] || '알 수 없음'}
          </div>
          <div style={{ color: '#666', fontSize: '0.9rem' }}>위험도</div>
        </div>
        <div style={{
          backgroundColor: '#F3E5F5',
          padding: '20px',
          borderRadius: '8px',
          textAlign: 'center',
        }}>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#7B1FA2' }}>
            {food_restrictions?.length || 0}
          </div>
          <div style={{ color: '#666', fontSize: '0.9rem' }}>식이 제한</div>
        </div>
      </div>

      {/* 고위험 경고 */}
      {summary?.critical_allergens?.length > 0 && (
        <div style={{
          backgroundColor: '#FFEBEE',
          border: '2px solid #F44336',
          borderRadius: '8px',
          padding: '16px',
          marginBottom: '24px',
        }}>
          <h4 style={{ color: '#C62828', margin: '0 0 8px 0' }}>
            고위험 알러젠 경고
          </h4>
          <p style={{ margin: 0 }}>
            다음 항원에 대해 특별한 주의가 필요합니다: {' '}
            <strong>{summary.critical_allergens.join(', ')}</strong>
          </p>
        </div>
      )}

      {/* 탭 네비게이션 - 3가지 카테고리 */}
      <div style={{
        display: 'flex',
        borderBottom: '1px solid #ddd',
        marginBottom: '24px',
        overflowX: 'auto',
      }}>
        <TabButton id="symptoms" label="🔴 증상 및 위험도" />
        <TabButton id="diet" label="🍽️ 식이 관리" />
        <TabButton id="emergency" label="🏥 응급 및 의료" />
      </div>

      {/* 탭 컨텐츠 */}
      <div style={{ minHeight: '400px' }}>
        {/* 카테고리 1: 증상 및 위험도 */}
        {activeTab === 'symptoms' && (
          <div>
            {/* 진단 결과 요약 섹션 */}
            <div style={{
              backgroundColor: '#FAFAFA',
              borderRadius: '12px',
              padding: '24px',
              marginBottom: '32px',
            }}>
              <h3 style={{ marginTop: 0, borderBottom: '2px solid #1976D2', paddingBottom: '8px' }}>
                📋 진단 결과 요약
              </h3>
              {positiveResults.length === 0 ? (
                <p style={{ color: '#4CAF50' }}>모든 항목이 음성입니다. 특별한 제한이 필요하지 않습니다.</p>
              ) : (
                <div style={{ display: 'grid', gap: '12px' }}>
                  {positiveResults.map((result, idx) => (
                    <div
                      key={idx}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '12px 16px',
                        backgroundColor: `${gradeColors[result.grade]}22`,
                        borderLeft: `4px solid ${gradeColors[result.grade]}`,
                        borderRadius: '4px',
                      }}
                    >
                      <div>
                        <strong>{result.allergen_kr}</strong>
                        <span style={{ color: '#666', marginLeft: '8px' }}>({result.allergen})</span>
                      </div>
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
                        <span style={{ fontWeight: 'bold' }}>{result.grade}등급</span>
                        <span style={{
                          padding: '4px 8px',
                          backgroundColor: gradeColors[result.grade],
                          color: 'white',
                          borderRadius: '4px',
                          fontSize: '0.8rem',
                        }}>
                          {restrictionLabels[result.restriction_level]}
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 예상 증상 섹션 */}
            <div style={{
              backgroundColor: '#FFF8E1',
              borderRadius: '12px',
              padding: '24px',
              marginBottom: '32px',
            }}>
              <h3 style={{ marginTop: 0, borderBottom: '2px solid #FF9800', paddingBottom: '8px' }}>
                ⚠️ 예상 증상
              </h3>
              {predicted_symptoms?.length === 0 ? (
                <p>예상 증상이 없습니다.</p>
              ) : (
                <div style={{ display: 'grid', gap: '12px' }}>
                  {predicted_symptoms?.map((symptom, idx) => (
                    <div
                      key={idx}
                      style={{
                        display: 'flex',
                        justifyContent: 'space-between',
                        alignItems: 'center',
                        padding: '12px 16px',
                        backgroundColor: 'white',
                        borderRadius: '4px',
                        borderLeft: `4px solid ${
                          symptom.severity === 'severe' ? '#F44336' :
                          symptom.severity === 'moderate' ? '#FF9800' : '#4CAF50'
                        }`,
                      }}
                    >
                      <div>
                        <strong>{symptom.symptom_kr}</strong>
                        <span style={{ color: '#666', marginLeft: '8px', fontSize: '0.9rem' }}>
                          ({symptom.symptom})
                        </span>
                      </div>
                      <div style={{ textAlign: 'right' }}>
                        <div style={{ fontSize: '0.9rem' }}>
                          발생 확률: <strong>{symptom.probability}</strong>
                        </div>
                        <div style={{ fontSize: '0.85rem', color: '#666' }}>
                          발현 시간: {symptom.onset_time}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>

            {/* 일반 권고사항 & 생활 팁 */}
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
              {general_recommendations?.length > 0 && (
                <div style={{
                  backgroundColor: '#E8F5E9',
                  borderRadius: '12px',
                  padding: '24px',
                }}>
                  <h4 style={{ marginTop: 0, color: '#2E7D32' }}>💡 일반 권고사항</h4>
                  <ul style={{ lineHeight: '1.8', margin: 0, paddingLeft: '20px' }}>
                    {general_recommendations.map((rec, idx) => (
                      <li key={idx}>{rec}</li>
                    ))}
                  </ul>
                </div>
              )}
              {lifestyle_tips?.length > 0 && (
                <div style={{
                  backgroundColor: '#E3F2FD',
                  borderRadius: '12px',
                  padding: '24px',
                }}>
                  <h4 style={{ marginTop: 0, color: '#1565C0' }}>🏃 생활 관리 팁</h4>
                  <ul style={{ lineHeight: '1.8', margin: 0, paddingLeft: '20px' }}>
                    {lifestyle_tips.map((tip, idx) => (
                      <li key={idx}>{tip}</li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          </div>
        )}

        {/* 카테고리 2: 식이 관리 (음식 제한 + 교차반응 통합) */}
        {activeTab === 'diet' && (
          <div>
            {/* 음식 섭취 제한 섹션 */}
            <div style={{
              backgroundColor: '#FAFAFA',
              borderRadius: '12px',
              padding: '24px',
              marginBottom: '32px',
            }}>
              <h3 style={{ marginTop: 0, borderBottom: '2px solid #F44336', paddingBottom: '8px' }}>
                🚫 음식 섭취 제한
              </h3>
              {food_restrictions?.length === 0 ? (
                <p style={{ color: '#4CAF50' }}>식이 제한이 필요하지 않습니다.</p>
              ) : (
                food_restrictions?.map((restriction, idx) => (
                  <div
                    key={idx}
                    style={{
                      border: '1px solid #ddd',
                      borderRadius: '8px',
                      marginBottom: '16px',
                      overflow: 'hidden',
                      backgroundColor: 'white',
                    }}
                  >
                    <div style={{
                      backgroundColor: `${gradeColors[restriction.grade]}22`,
                      borderBottom: '1px solid #ddd',
                      padding: '16px',
                    }}>
                      <h4 style={{ margin: 0 }}>
                        {restriction.allergen_kr}
                        <span style={{
                          marginLeft: '8px',
                          padding: '4px 8px',
                          backgroundColor: gradeColors[restriction.grade],
                          color: 'white',
                          borderRadius: '4px',
                          fontSize: '0.8rem',
                        }}>
                          {restriction.grade}등급 - {restrictionLabels[restriction.restriction_level]}
                        </span>
                      </h4>
                    </div>
                    <div style={{ padding: '16px' }}>
                      {/* 회피 식품 */}
                      {restriction.avoid_foods?.length > 0 && (
                        <div style={{ marginBottom: '16px' }}>
                          <h5 style={{ color: '#C62828', marginBottom: '8px' }}>🔴 회피해야 할 식품</h5>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                            {restriction.avoid_foods.map((food, i) => (
                              <span key={i} style={{
                                padding: '4px 12px',
                                backgroundColor: '#FFEBEE',
                                borderRadius: '16px',
                                fontSize: '0.9rem',
                              }}>
                                {food}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* 숨겨진 알러젠 */}
                      {restriction.hidden_sources?.length > 0 && (
                        <div style={{ marginBottom: '16px' }}>
                          <h5 style={{ color: '#FF9800', marginBottom: '8px' }}>⚠️ 숨겨진 알러젠 주의</h5>
                          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '8px' }}>
                            {restriction.hidden_sources.map((food, i) => (
                              <span key={i} style={{
                                padding: '4px 12px',
                                backgroundColor: '#FFF3E0',
                                borderRadius: '16px',
                                fontSize: '0.9rem',
                              }}>
                                {food}
                              </span>
                            ))}
                          </div>
                        </div>
                      )}

                      {/* 대체 식품 */}
                      {restriction.substitutes?.length > 0 && (
                        <div style={{ marginBottom: '16px' }}>
                          <h5 style={{ color: '#4CAF50', marginBottom: '8px' }}>✅ 대체 식품</h5>
                          {restriction.substitutes.map((sub, i) => (
                            <div key={i} style={{
                              padding: '8px 12px',
                              backgroundColor: '#E8F5E9',
                              borderRadius: '4px',
                              marginBottom: '8px',
                            }}>
                              <strong>{sub.original}</strong> → {sub.substitutes.join(', ')}
                              {sub.notes && <span style={{ color: '#666', marginLeft: '8px' }}>({sub.notes})</span>}
                            </div>
                          ))}
                        </div>
                      )}

                      {/* 외식 주의 & 라벨 키워드 */}
                      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                        {restriction.restaurant_cautions?.length > 0 && (
                          <div>
                            <h5 style={{ color: '#7B1FA2', marginBottom: '8px' }}>🍴 외식 시 주의</h5>
                            <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '0.9rem' }}>
                              {restriction.restaurant_cautions.map((caution, i) => (
                                <li key={i}>{caution}</li>
                              ))}
                            </ul>
                          </div>
                        )}
                        {restriction.label_keywords?.length > 0 && (
                          <div>
                            <h5 style={{ color: '#1976D2', marginBottom: '8px' }}>🏷️ 성분표 키워드</h5>
                            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '4px' }}>
                              {restriction.label_keywords.map((keyword, i) => (
                                <span key={i} style={{
                                  padding: '2px 8px',
                                  backgroundColor: '#E3F2FD',
                                  borderRadius: '12px',
                                  fontSize: '0.8rem',
                                  fontFamily: 'monospace',
                                }}>
                                  {keyword}
                                </span>
                              ))}
                              {restriction.label_keywords_en?.map((keyword, i) => (
                                <span key={`en-${i}`} style={{
                                  padding: '2px 8px',
                                  backgroundColor: '#E3F2FD',
                                  borderRadius: '12px',
                                  fontSize: '0.8rem',
                                  fontFamily: 'monospace',
                                }}>
                                  {keyword}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </div>
                  </div>
                ))
              )}
            </div>

            {/* 교차반응 섹션 */}
            <div style={{
              backgroundColor: '#FFF8E1',
              borderRadius: '12px',
              padding: '24px',
            }}>
              <h3 style={{ marginTop: 0, borderBottom: '2px solid #FF9800', paddingBottom: '8px' }}>
                🔄 교차반응 주의
              </h3>
              {cross_reactivity_alerts?.length === 0 ? (
                <p>교차반응 경고가 없습니다.</p>
              ) : (
                <div style={{ display: 'grid', gap: '12px' }}>
                  {cross_reactivity_alerts?.map((alert, idx) => (
                    <div
                      key={idx}
                      style={{
                        border: '1px solid #FFB74D',
                        borderRadius: '8px',
                        padding: '16px',
                        backgroundColor: 'white',
                      }}
                    >
                      <div style={{ display: 'flex', alignItems: 'center', gap: '8px', marginBottom: '8px' }}>
                        <strong>{alert.primary_allergen_kr}</strong>
                        <span style={{ color: '#FF9800' }}>→</span>
                        <strong style={{ color: '#F57C00' }}>{alert.related_allergen_kr}</strong>
                        <span style={{
                          padding: '2px 8px',
                          backgroundColor: '#FF9800',
                          color: 'white',
                          borderRadius: '4px',
                          fontSize: '0.8rem',
                        }}>
                          {alert.probability}
                        </span>
                      </div>
                      {alert.common_protein && (
                        <p style={{ margin: '4px 0', color: '#666', fontSize: '0.9rem' }}>
                          🧬 공통 단백질: {alert.common_protein}
                        </p>
                      )}
                      {alert.related_foods?.length > 0 && (
                        <div style={{ marginTop: '8px' }}>
                          <span style={{ fontSize: '0.9rem', color: '#666' }}>관련 식품: </span>
                          <span style={{ fontSize: '0.9rem' }}>{alert.related_foods.join(', ')}</span>
                        </div>
                      )}
                      {alert.recommendation && (
                        <p style={{ margin: '8px 0 0 0', fontStyle: 'italic', color: '#5D4037', fontSize: '0.9rem' }}>
                          💡 {alert.recommendation}
                        </p>
                      )}
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}

        {/* 카테고리 3: 응급 및 의료 (응급 대처 + 의료 권고 통합) */}
        {activeTab === 'emergency' && (
          <div>
            {/* 응급 대처 가이드 섹션 */}
            <div style={{
              backgroundColor: '#FFEBEE',
              borderRadius: '12px',
              padding: '24px',
              marginBottom: '32px',
            }}>
              <h3 style={{ marginTop: 0, borderBottom: '2px solid #F44336', paddingBottom: '8px' }}>
                🚨 응급 대처 가이드
              </h3>
              {emergency_guidelines?.map((guide, idx) => (
                <div
                  key={idx}
                  style={{
                    border: guide.condition.includes('아나필락시스') ? '2px solid #F44336' : '1px solid #ddd',
                    borderRadius: '8px',
                    marginBottom: '16px',
                    overflow: 'hidden',
                    backgroundColor: 'white',
                  }}
                >
                  <div style={{
                    backgroundColor: guide.condition.includes('아나필락시스') ? '#D32F2F' :
                      guide.condition.includes('중등도') ? '#FF9800' : '#4CAF50',
                    color: 'white',
                    padding: '12px 16px',
                  }}>
                    <h4 style={{ margin: 0 }}>
                      {guide.condition.includes('아나필락시스') && '⚠️ '}
                      {guide.condition}
                    </h4>
                  </div>
                  <div style={{ padding: '16px' }}>
                    {/* 증상 & 대처법 2단 레이아웃 */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px', marginBottom: '16px' }}>
                      <div>
                        <h5 style={{ color: '#C62828', marginBottom: '8px' }}>🔍 증상</h5>
                        <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '0.9rem' }}>
                          {guide.symptoms.map((s, i) => <li key={i}>{s}</li>)}
                        </ul>
                      </div>
                      <div>
                        <h5 style={{ color: '#1565C0', marginBottom: '8px' }}>⚡ 즉각 대처법</h5>
                        <ol style={{ margin: 0, paddingLeft: '20px', fontSize: '0.9rem' }}>
                          {guide.immediate_actions.map((action, i) => (
                            <li key={i} style={{ marginBottom: '4px' }}>{action}</li>
                          ))}
                        </ol>
                      </div>
                    </div>

                    {/* 약물 정보 & 119 호출 기준 */}
                    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '12px' }}>
                      {guide.medication_info && (
                        <div style={{
                          backgroundColor: '#E3F2FD',
                          padding: '12px',
                          borderRadius: '8px',
                        }}>
                          <strong>💊 약물 정보:</strong>
                          <p style={{ margin: '4px 0 0 0', fontSize: '0.9rem' }}>{guide.medication_info}</p>
                        </div>
                      )}
                      {guide.when_to_call_119 && (
                        <div style={{
                          backgroundColor: '#FFEBEE',
                          padding: '12px',
                          borderRadius: '8px',
                          border: '1px solid #F44336',
                        }}>
                          <strong>📞 119 호출 기준:</strong>
                          <p style={{ margin: '4px 0 0 0', fontSize: '0.9rem' }}>{guide.when_to_call_119}</p>
                        </div>
                      )}
                    </div>
                  </div>
                </div>
              ))}
            </div>

            {/* 의료 권고사항 섹션 */}
            <div style={{
              backgroundColor: '#E3F2FD',
              borderRadius: '12px',
              padding: '24px',
            }}>
              <h3 style={{ marginTop: 0, borderBottom: '2px solid #1976D2', paddingBottom: '8px' }}>
                🏥 의료 권고사항
              </h3>
              {medical_recommendation && (
                <div style={{
                  backgroundColor: 'white',
                  borderRadius: '8px',
                  padding: '20px',
                }}>
                  {/* 전문의 상담 & 추적 관찰 */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px', marginBottom: '24px' }}>
                    <div style={{
                      backgroundColor: '#F3E5F5',
                      padding: '16px',
                      borderRadius: '8px',
                    }}>
                      <h4 style={{ marginTop: 0, color: '#7B1FA2' }}>👨‍⚕️ 전문의 상담</h4>
                      <div style={{ fontSize: '0.95rem' }}>
                        <p style={{ margin: '8px 0' }}>
                          <strong>필요 여부:</strong>{' '}
                          <span style={{
                            padding: '2px 8px',
                            backgroundColor: medical_recommendation.consultation_needed ? '#F44336' : '#4CAF50',
                            color: 'white',
                            borderRadius: '4px',
                          }}>
                            {medical_recommendation.consultation_needed ? '필요' : '선택'}
                          </span>
                        </p>
                        <p style={{ margin: '8px 0' }}>
                          <strong>긴급도:</strong>{' '}
                          {medical_recommendation.consultation_urgency === 'urgent' ? '🔴 긴급' :
                           medical_recommendation.consultation_urgency === 'recommended' ? '🟡 권장' : '🟢 일반'}
                        </p>
                        <p style={{ margin: '8px 0' }}>
                          <strong>전문의:</strong> {medical_recommendation.specialist_type}
                        </p>
                      </div>
                    </div>
                    <div style={{
                      backgroundColor: '#E8F5E9',
                      padding: '16px',
                      borderRadius: '8px',
                    }}>
                      <h4 style={{ marginTop: 0, color: '#2E7D32' }}>📅 추적 관찰</h4>
                      <div style={{ fontSize: '0.95rem' }}>
                        <p style={{ margin: '8px 0' }}>
                          <strong>추적 검사 주기:</strong> {medical_recommendation.follow_up_period}
                        </p>
                        <p style={{ margin: '8px 0' }}>
                          <strong>에피네프린 처방:</strong>{' '}
                          <span style={{
                            padding: '2px 8px',
                            backgroundColor: medical_recommendation.epinephrine_recommended ? '#FF9800' : '#9E9E9E',
                            color: 'white',
                            borderRadius: '4px',
                          }}>
                            {medical_recommendation.epinephrine_recommended ? '권고됨' : '해당 없음'}
                          </span>
                        </p>
                      </div>
                    </div>
                  </div>

                  {/* 추가 검사 & 참고사항 */}
                  <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
                    {medical_recommendation.additional_tests?.length > 0 && (
                      <div style={{
                        backgroundColor: '#FFF3E0',
                        padding: '16px',
                        borderRadius: '8px',
                      }}>
                        <h4 style={{ marginTop: 0, color: '#E65100' }}>🔬 권고 추가 검사</h4>
                        <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '0.9rem' }}>
                          {medical_recommendation.additional_tests.map((test, i) => (
                            <li key={i}>{test}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                    {medical_recommendation.notes?.length > 0 && (
                      <div style={{
                        backgroundColor: '#ECEFF1',
                        padding: '16px',
                        borderRadius: '8px',
                      }}>
                        <h4 style={{ marginTop: 0, color: '#455A64' }}>📝 참고사항</h4>
                        <ul style={{ margin: 0, paddingLeft: '20px', fontSize: '0.9rem' }}>
                          {medical_recommendation.notes.map((note, i) => (
                            <li key={i}>{note}</li>
                          ))}
                        </ul>
                      </div>
                    )}
                  </div>
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* 하단 버튼 */}
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        gap: '16px',
        marginTop: '32px',
        paddingBottom: '32px',
      }}>
        <button
          onClick={() => navigate('/diagnosis')}
          style={{
            padding: '12px 24px',
            border: '1px solid #1976D2',
            backgroundColor: 'white',
            color: '#1976D2',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          새 진단 입력
        </button>
        <button
          onClick={() => window.print()}
          style={{
            padding: '12px 24px',
            border: 'none',
            backgroundColor: '#1976D2',
            color: 'white',
            borderRadius: '4px',
            cursor: 'pointer',
          }}
        >
          인쇄하기
        </button>
      </div>
    </div>
  );
}

export default PrescriptionPage;
