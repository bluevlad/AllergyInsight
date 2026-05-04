/**
 * MAST Result View
 *
 * 입력된 알러젠 + 등급에 대한 매칭 정보 표시.
 * 섹션: 알러젠 카드 → 응급 알림(Class 3+) → 식이 제한 → 예상 증상 →
 *       교차반응 → 응급 가이드 → 의료 권고 → 면책 + citations
 */
import React from 'react';
import GradeBadge from './GradeBadge';
import MedicalDisclaimer from '../../shared/components/MedicalDisclaimer';

const MastResultView = ({ result, onBack }) => {
  const { allergen, grade, is_positive, has_detailed_data } = result;
  const showEmergency = result.emergency_required;

  return (
    <div>
      {/* 알러젠 카드 */}
      <div style={cardStyle}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.75rem' }}>
          <div>
            <div style={{ color: '#999', fontSize: '0.8rem' }}>알러젠</div>
            <h2 style={{ margin: '0.25rem 0', fontSize: '1.5rem' }}>{allergen.name_kr}</h2>
            <div style={{ color: '#666', fontSize: '0.9rem' }}>
              {allergen.name_en} · [{allergen.code}] · {allergen.category} / {allergen.type}
            </div>
          </div>
          <GradeBadge
            value={grade.value}
            level={grade.level}
            levelEn={grade.level_en}
            color={grade.color}
            size="lg"
          />
        </div>
        <p style={{ marginTop: '0.75rem', color: '#444' }}>{grade.description}</p>
        <p style={{ margin: 0, color: '#1976d2', fontWeight: 500 }}>{grade.action}</p>
      </div>

      {/* 응급 알림 (Class 3+) */}
      {showEmergency && (
        <div
          role="alert"
          style={{
            padding: '1rem',
            background: '#ffebee',
            border: '2px solid #c62828',
            borderRadius: '8px',
            marginBottom: '1rem',
          }}
        >
          <h3 style={{ margin: '0 0 0.5rem', color: '#c62828' }}>🚨 응급 정보 우선 확인</h3>
          <ul style={{ margin: 0, paddingLeft: '1.25rem', color: '#5d1717', lineHeight: 1.7 }}>
            <li>호흡곤란, 입술/혀 부종, 의식저하 등 아나필락시스 의심 증상 시 <strong>즉시 119</strong></li>
            <li>에피네프린 자가주사기(에피펜)가 있다면 즉시 사용 후 119 호출</li>
            <li>증상이 경미하더라도 의료진 평가가 필요합니다</li>
          </ul>
        </div>
      )}

      {/* 음성/약양성 안내 */}
      {!is_positive && (
        <div style={{ ...cardStyle, background: '#e8f5e9', borderLeft: '4px solid #2e7d32' }}>
          <p style={{ margin: 0, color: '#1b5e20' }}>
            현재 등급 기준 알러지 반응이 확인되지 않았습니다. 정기 검사를 통한 추적 관찰을 권장합니다.
          </p>
        </div>
      )}

      {/* 시드 데이터 부족 안내 */}
      {is_positive && !has_detailed_data && (
        <div style={{ ...cardStyle, background: '#fff8e1', borderLeft: '4px solid #ffc107' }}>
          <p style={{ margin: 0, color: '#5d4037' }}>
            이 알러젠에 대한 상세 식이/증상 정보는 현재 정비 중입니다.
            일반 알러지 관리 가이드를 참고하시고, 자세한 정보는 의료진과 상담하세요.
          </p>
        </div>
      )}

      {/* 식이 제한 */}
      {result.food_restriction && (
        <Section title="🍽️ 식이 관리">
          {result.food_restriction.avoid_foods?.length > 0 && (
            <Subsection title="회피 식품">
              <Tags items={result.food_restriction.avoid_foods} color="#c62828" />
            </Subsection>
          )}
          {result.food_restriction.hidden_sources?.length > 0 && (
            <Subsection title="숨겨진 알러젠 (가공식품)">
              <Tags items={result.food_restriction.hidden_sources} color="#e65100" />
            </Subsection>
          )}
          {result.food_restriction.substitutes?.length > 0 && (
            <Subsection title="대체 식품">
              <ul style={listStyle}>
                {result.food_restriction.substitutes.map((s, i) => (
                  <li key={i}>
                    <strong>{s.original}</strong>
                    {s.substitutes?.length > 0 && ' → '}
                    {s.substitutes?.join(', ')}
                    {s.notes && <span style={{ color: '#666', marginLeft: '0.5rem' }}>({s.notes})</span>}
                  </li>
                ))}
              </ul>
            </Subsection>
          )}
          {result.food_restriction.label_keywords?.length > 0 && (
            <Subsection title="라벨 확인 키워드">
              <Tags items={result.food_restriction.label_keywords} color="#1976d2" />
            </Subsection>
          )}
          <MedicalDisclaimer variant="inline" />
        </Section>
      )}

      {/* 예상 증상 */}
      {result.predicted_symptoms?.length > 0 && (
        <Section title="⚠️ 예상 증상 / 위험도">
          <ul style={{ ...listStyle, paddingLeft: 0, listStyle: 'none' }}>
            {result.predicted_symptoms.map((s, i) => (
              <li key={i} style={{ padding: '0.5rem 0', borderBottom: '1px solid #f0f0f0' }}>
                <strong>{s.symptom_kr}</strong>
                <span style={{ color: '#999', marginLeft: '0.4rem', fontSize: '0.85rem' }}>
                  ({s.symptom})
                </span>
                <div style={{ color: '#666', fontSize: '0.85rem', marginTop: '0.2rem' }}>
                  {s.probability && `발생 확률: ${s.probability} · `}
                  {s.onset_time && `발현: ${s.onset_time} · `}
                  {s.severity && `심각도: ${s.severity}`}
                </div>
              </li>
            ))}
          </ul>
          <MedicalDisclaimer variant="inline" />
        </Section>
      )}

      {/* 교차반응 */}
      {result.cross_reactivity_alerts?.length > 0 && (
        <Section title="🔁 교차반응 주의">
          <ul style={listStyle}>
            {result.cross_reactivity_alerts.map((c, i) => (
              <li key={i}>
                <strong>{c.related_allergen_kr}</strong>
                {c.probability && ` (${c.probability})`}
                {c.common_protein && (
                  <span style={{ color: '#666' }}> — 공통 단백질: {c.common_protein}</span>
                )}
                {c.recommendation && (
                  <div style={{ color: '#666', fontSize: '0.85rem', marginTop: '0.2rem' }}>
                    {c.recommendation}
                  </div>
                )}
              </li>
            ))}
          </ul>
        </Section>
      )}

      {/* 응급 가이드 */}
      {result.emergency_guidelines?.length > 0 && (
        <Section title="🚨 응급 대처 가이드">
          {result.emergency_guidelines.map((g, i) => (
            <div key={i} style={{ marginBottom: '1rem', paddingBottom: '0.75rem', borderBottom: '1px solid #f0f0f0' }}>
              <h4 style={{ margin: '0 0 0.4rem', color: '#c62828' }}>
                {g.condition} <span style={{ color: '#999', fontSize: '0.85rem' }}>({g.condition_en})</span>
              </h4>
              {g.symptoms?.length > 0 && (
                <div style={{ marginBottom: '0.4rem' }}>
                  <strong style={{ fontSize: '0.85rem' }}>증상:</strong> {g.symptoms.join(', ')}
                </div>
              )}
              {g.immediate_actions?.length > 0 && (
                <div>
                  <strong style={{ fontSize: '0.85rem' }}>즉각 대처:</strong>
                  <ol style={{ margin: '0.25rem 0', paddingLeft: '1.25rem' }}>
                    {g.immediate_actions.map((a, j) => <li key={j}>{a}</li>)}
                  </ol>
                </div>
              )}
              {g.when_to_call_119 && (
                <p style={{ margin: '0.4rem 0 0', color: '#c62828', fontSize: '0.9rem' }}>
                  📞 <strong>119 호출:</strong> {g.when_to_call_119}
                </p>
              )}
            </div>
          ))}
        </Section>
      )}

      {/* 의료 권고 */}
      {result.medical_recommendation && (
        <Section title="🏥 의료 권고">
          <ul style={listStyle}>
            {result.medical_recommendation.consultation_needed && (
              <li>
                {result.medical_recommendation.specialist_type} 상담 권장
                {result.medical_recommendation.consultation_urgency === 'urgent' && ' (긴급)'}
              </li>
            )}
            {result.medical_recommendation.epinephrine_recommended && (
              <li>에피네프린 자가주사기(에피펜) 처방 검토 권장</li>
            )}
            {result.medical_recommendation.follow_up_period && (
              <li>추적 검사 주기: {result.medical_recommendation.follow_up_period}</li>
            )}
            {result.medical_recommendation.additional_tests?.map((t, i) => (
              <li key={`t-${i}`}>{t}</li>
            ))}
            {result.medical_recommendation.notes?.map((n, i) => (
              <li key={`n-${i}`} style={{ color: '#666' }}>{n}</li>
            ))}
          </ul>
        </Section>
      )}

      {/* citations placeholder (Phase 4) */}
      <Section title="📚 출처">
        <p style={{ margin: 0, color: '#999', fontSize: '0.85rem' }}>
          {result.citations?.length > 0
            ? `${result.citations.length}건의 논문 · 전문기관 출처`
            : '논문 출처 시스템은 Phase 4에서 활성화될 예정입니다. 시드 콘텐츠는 학회 가이드 및 PubMed 자료를 기반으로 합니다.'}
        </p>
      </Section>

      <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1.5rem' }}>
        <button
          onClick={onBack}
          style={{
            flex: 1,
            padding: '0.85rem',
            border: '1px solid #1976d2',
            borderRadius: '8px',
            background: 'white',
            color: '#1976d2',
            fontSize: '1rem',
            fontWeight: 600,
            cursor: 'pointer',
          }}
        >
          다른 알러젠 조회
        </button>
      </div>

      <div style={{ marginTop: '1rem' }}>
        <MedicalDisclaimer variant="banner" />
      </div>
    </div>
  );
};

const Section = ({ title, children }) => (
  <section style={{ ...cardStyle, marginBottom: '1rem' }}>
    <h3 style={{ margin: '0 0 0.75rem', fontSize: '1.05rem' }}>{title}</h3>
    {children}
  </section>
);

const Subsection = ({ title, children }) => (
  <div style={{ marginBottom: '0.75rem' }}>
    <h4 style={{ margin: '0 0 0.4rem', fontSize: '0.9rem', color: '#555' }}>{title}</h4>
    {children}
  </div>
);

const Tags = ({ items, color = '#1976d2' }) => (
  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
    {items.map((t, i) => (
      <span
        key={i}
        style={{
          padding: '0.25rem 0.6rem',
          background: `${color}15`,
          color,
          borderRadius: '4px',
          fontSize: '0.85rem',
        }}
      >
        {t}
      </span>
    ))}
  </div>
);

const cardStyle = {
  padding: '1rem',
  background: 'white',
  border: '1px solid #e0e0e0',
  borderRadius: '8px',
  marginBottom: '1rem',
};

const listStyle = {
  margin: 0,
  paddingLeft: '1.25rem',
  lineHeight: 1.7,
};

export default MastResultView;
