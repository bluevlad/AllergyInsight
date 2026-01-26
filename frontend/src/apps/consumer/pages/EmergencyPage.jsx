/**
 * Consumer Emergency Page - 응급 대처
 */
import React, { useState, useEffect } from 'react';
import { consumerApi } from '../services/consumerApi';

function EmergencyPage() {
  const [guidelines, setGuidelines] = useState(null);
  const [actionPlan, setActionPlan] = useState(null);
  const [epinephrineGuide, setEpinephrineGuide] = useState(null);
  const [loading, setLoading] = useState(true);
  const [activeSection, setActiveSection] = useState('overview');

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [guidelinesData, actionData, epiData] = await Promise.all([
        consumerApi.emergency.getGuidelines(),
        consumerApi.emergency.getActionPlan(),
        consumerApi.emergency.getEpinephrineGuide(),
      ]);
      setGuidelines(guidelinesData);
      setActionPlan(actionData.action_plans);
      setEpinephrineGuide(epiData);
    } catch (err) {
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

  const sections = [
    { id: 'overview', label: '개요', icon: '📋' },
    { id: 'mild', label: '경미한 증상', icon: '🟢' },
    { id: 'moderate', label: '중등도 증상', icon: '🟡' },
    { id: 'severe', label: '심각한 증상', icon: '🔴' },
    { id: 'epinephrine', label: '에피펜 사용법', icon: '💉' },
  ];

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto' }}>
      {/* 긴급 연락처 배너 */}
      <div style={{
        padding: '1rem',
        background: '#e74c3c',
        color: 'white',
        borderRadius: '12px',
        marginBottom: '1.5rem',
        textAlign: 'center',
      }}>
        <p style={{ fontSize: '1.25rem', fontWeight: 'bold' }}>
          🚨 응급 상황 시 즉시 119에 연락하세요
        </p>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '2rem', marginTop: '0.5rem' }}>
          <a href="tel:119" style={{ color: 'white', fontWeight: '600' }}>
            🚑 119 (응급)
          </a>
          <a href="tel:1339" style={{ color: 'white', fontWeight: '600' }}>
            ☎️ 1339 (독극물)
          </a>
        </div>
      </div>

      <h2>응급 대처 가이드</h2>

      {/* 섹션 네비게이션 */}
      <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', marginBottom: '1.5rem' }}>
        {sections.map(section => (
          <button
            key={section.id}
            className={`section-btn ${activeSection === section.id ? 'active' : ''}`}
            onClick={() => setActiveSection(section.id)}
          >
            {section.icon} {section.label}
          </button>
        ))}
      </div>

      {/* 개요 */}
      {activeSection === 'overview' && (
        <div className="card">
          <h3>알러지 반응 단계별 대처</h3>
          <div style={{ display: 'grid', gap: '1rem' }}>
            <div style={{ padding: '1rem', background: '#e8f5e9', borderRadius: '8px', borderLeft: '4px solid #4CAF50' }}>
              <h4 style={{ color: '#2e7d32' }}>🟢 경미한 증상</h4>
              <p>피부 가려움, 국소 두드러기, 콧물 → 항히스타민제 복용 및 관찰</p>
            </div>
            <div style={{ padding: '1rem', background: '#fff8e1', borderRadius: '8px', borderLeft: '4px solid #FFC107' }}>
              <h4 style={{ color: '#f57c00' }}>🟡 중등도 증상</h4>
              <p>전신 두드러기, 복통, 구토 → 항히스타민제 + 응급실 방문 고려</p>
            </div>
            <div style={{ padding: '1rem', background: '#ffebee', borderRadius: '8px', borderLeft: '4px solid #e74c3c' }}>
              <h4 style={{ color: '#c62828' }}>🔴 심각한 증상 (아나필락시스)</h4>
              <p>호흡곤란, 혈압저하, 의식저하 → 에피펜 즉시 사용 + 119 신고</p>
            </div>
          </div>

          {guidelines?.important_notes && (
            <div style={{ marginTop: '1.5rem' }}>
              <h4>중요 사항</h4>
              <ul style={{ paddingLeft: '1.25rem' }}>
                {guidelines.important_notes.map((note, idx) => (
                  <li key={idx} style={{ marginBottom: '0.5rem' }}>{note}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {/* 경미한 증상 */}
      {activeSection === 'mild' && actionPlan?.mild && (
        <div className="card">
          <h3>{actionPlan.mild.title}</h3>

          <div style={{ marginBottom: '1.5rem' }}>
            <h4>증상</h4>
            <ul>
              {actionPlan.mild.symptoms.map((s, idx) => (
                <li key={idx}>{s}</li>
              ))}
            </ul>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <h4>대처 방법</h4>
            <ol>
              {actionPlan.mild.actions.map((a, idx) => (
                <li key={idx} style={{ marginBottom: '0.5rem' }}>{a}</li>
              ))}
            </ol>
          </div>

          <div style={{ padding: '1rem', background: '#fff8e1', borderRadius: '8px' }}>
            <p><strong>🏥 병원 방문이 필요한 경우:</strong></p>
            <p>{actionPlan.mild.when_to_call_doctor}</p>
          </div>
        </div>
      )}

      {/* 중등도 증상 */}
      {activeSection === 'moderate' && actionPlan?.moderate && (
        <div className="card">
          <h3>{actionPlan.moderate.title}</h3>

          <div style={{ marginBottom: '1.5rem' }}>
            <h4>증상</h4>
            <ul>
              {actionPlan.moderate.symptoms.map((s, idx) => (
                <li key={idx}>{s}</li>
              ))}
            </ul>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <h4>대처 방법</h4>
            <ol>
              {actionPlan.moderate.actions.map((a, idx) => (
                <li key={idx} style={{ marginBottom: '0.5rem' }}>{a}</li>
              ))}
            </ol>
          </div>

          <div style={{ padding: '1rem', background: '#ffebee', borderRadius: '8px' }}>
            <p><strong>🚑 119 호출이 필요한 경우:</strong></p>
            <p>{actionPlan.moderate.when_to_call_119}</p>
          </div>
        </div>
      )}

      {/* 심각한 증상 */}
      {activeSection === 'severe' && actionPlan?.severe && (
        <div className="card" style={{ border: '2px solid #e74c3c' }}>
          <h3 style={{ color: '#e74c3c' }}>{actionPlan.severe.title}</h3>

          <div style={{ padding: '1rem', background: '#ffebee', borderRadius: '8px', marginBottom: '1.5rem' }}>
            <p style={{ fontWeight: 'bold', color: '#c62828' }}>⚠️ 즉각적인 대응이 필요합니다!</p>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <h4>증상</h4>
            <ul>
              {actionPlan.severe.symptoms.map((s, idx) => (
                <li key={idx} style={{ color: '#c62828' }}>{s}</li>
              ))}
            </ul>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <h4>즉시 실행할 것</h4>
            <ol>
              {actionPlan.severe.actions.map((a, idx) => (
                <li key={idx} style={{ marginBottom: '0.5rem', fontWeight: idx === 0 || idx === 1 ? '600' : 'normal' }}>{a}</li>
              ))}
            </ol>
          </div>

          {actionPlan.severe.epinephrine_instructions && (
            <div style={{ padding: '1rem', background: '#e3f2fd', borderRadius: '8px' }}>
              <h4>💉 에피펜 사용법</h4>
              <ol>
                {actionPlan.severe.epinephrine_instructions.map((inst, idx) => (
                  <li key={idx}>{inst}</li>
                ))}
              </ol>
            </div>
          )}
        </div>
      )}

      {/* 에피펜 사용법 */}
      {activeSection === 'epinephrine' && epinephrineGuide && (
        <div className="card">
          <h3>💉 에피네프린(에피펜) 사용 가이드</h3>

          <div style={{ marginBottom: '1.5rem' }}>
            <h4>에피네프린이란?</h4>
            <p>{epinephrineGuide.what_is_epinephrine?.description}</p>
            <p style={{ marginTop: '0.5rem' }}>
              <strong>처방 필요:</strong> {epinephrineGuide.what_is_epinephrine?.prescription_required ? '예' : '아니오'}
            </p>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <h4>언제 사용하나요?</h4>
            <ul>
              {epinephrineGuide.when_to_use?.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <h4>사용 방법</h4>
            <div style={{ display: 'grid', gap: '1rem' }}>
              <div style={{ padding: '1rem', background: '#e3f2fd', borderRadius: '8px' }}>
                <h5>1. 준비</h5>
                <ul>
                  {epinephrineGuide.how_to_use?.preparation?.map((step, idx) => (
                    <li key={idx}>{step}</li>
                  ))}
                </ul>
              </div>
              <div style={{ padding: '1rem', background: '#fff3e0', borderRadius: '8px' }}>
                <h5>2. 주사</h5>
                <ul>
                  {epinephrineGuide.how_to_use?.injection?.map((step, idx) => (
                    <li key={idx}>{step}</li>
                  ))}
                </ul>
              </div>
              <div style={{ padding: '1rem', background: '#e8f5e9', borderRadius: '8px' }}>
                <h5>3. 주사 후</h5>
                <ul>
                  {epinephrineGuide.how_to_use?.after_injection?.map((step, idx) => (
                    <li key={idx}>{step}</li>
                  ))}
                </ul>
              </div>
            </div>
          </div>

          <div style={{ marginBottom: '1.5rem' }}>
            <h4>보관 방법</h4>
            <ul>
              {epinephrineGuide.storage?.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>
          </div>

          <div style={{ padding: '1rem', background: '#fffde7', borderRadius: '8px' }}>
            <h4>중요 알림</h4>
            <ul>
              {epinephrineGuide.important_reminders?.map((item, idx) => (
                <li key={idx}>{item}</li>
              ))}
            </ul>
          </div>
        </div>
      )}

      <style>{`
        .section-btn {
          padding: 0.5rem 1rem;
          border: 1px solid #ddd;
          background: white;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s;
        }
        .section-btn:hover {
          background: #f8f9fa;
        }
        .section-btn.active {
          background: #667eea;
          color: white;
          border-color: #667eea;
        }
      `}</style>
    </div>
  );
}

export default EmergencyPage;
