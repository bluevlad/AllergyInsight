/**
 * Allergy Report View - 알러지 리포트 출력 화면
 *
 * 식품가이드, 생활관리, 응급정보를 통합 레포트로 렌더링합니다.
 * 인쇄/PDF 최적화 CSS를 포함합니다.
 */
import React from 'react';

const SEVERITY_COLORS = {
  mild: { bg: '#e8f5e9', color: '#2e7d32', border: '#4CAF50' },
  moderate: { bg: '#fff8e1', color: '#f57c00', border: '#FFC107' },
  severe: { bg: '#ffebee', color: '#c62828', border: '#e74c3c' },
};

const SEVERITY_LABELS = {
  mild: '경미',
  moderate: '중등도',
  severe: '심각',
};

function AllergyReportView({ report, onBack }) {
  const { summary, food_guide, lifestyle, symptoms, emergency, disclaimer, generated_at, name } = report;

  const handlePrint = () => window.print();

  const formatDate = (iso) => {
    const d = new Date(iso);
    return `${d.getFullYear()}년 ${d.getMonth() + 1}월 ${d.getDate()}일`;
  };

  return (
    <div className="report-container">
      {/* 상단 액션 바 (인쇄 시 숨김) */}
      <div className="no-print" style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem' }}>
        <button className="action-btn back-btn" onClick={onBack}>
          ← 다시 입력
        </button>
        <button className="action-btn print-btn" onClick={handlePrint}>
          🖨️ 인쇄 / PDF 저장
        </button>
      </div>

      {/* 리포트 헤더 */}
      <div className="report-header">
        <h1>알러지 리포트</h1>
        <p className="report-subtitle">AllergyInsight</p>
        {name && <p className="report-name">{name}</p>}
        <p className="report-date">생성일: {formatDate(generated_at)}</p>
      </div>

      {/* 면책 문구 */}
      <div className="disclaimer-box">
        ⚠️ {disclaimer}
      </div>

      {/* ============ 1. 요약 ============ */}
      <section className="report-section">
        <h2 className="section-title">1. 검사 결과 요약</h2>

        <div className="summary-cards">
          <div className="summary-card" style={{ borderColor: '#e74c3c' }}>
            <span className="summary-number" style={{ color: '#e74c3c' }}>{summary.high_risk_count}</span>
            <span className="summary-label">고위험 (4-6등급)</span>
          </div>
          <div className="summary-card" style={{ borderColor: '#f39c12' }}>
            <span className="summary-number" style={{ color: '#f39c12' }}>{summary.moderate_risk_count}</span>
            <span className="summary-label">중등도 (2-3등급)</span>
          </div>
          <div className="summary-card" style={{ borderColor: '#27ae60' }}>
            <span className="summary-number" style={{ color: '#27ae60' }}>{summary.low_risk_count}</span>
            <span className="summary-label">저위험 (1등급)</span>
          </div>
          <div className="summary-card" style={{ borderColor: '#667eea' }}>
            <span className="summary-number" style={{ color: '#667eea' }}>{summary.positive_count}</span>
            <span className="summary-label">양성 합계</span>
          </div>
        </div>

        {/* 알러젠 목록 */}
        <div className="allergen-grid">
          {summary.allergens.map(item => {
            const sc = SEVERITY_COLORS[item.severity] || SEVERITY_COLORS.mild;
            return (
              <div key={item.code} className="allergen-badge" style={{
                background: sc.bg,
                borderLeft: `4px solid ${sc.border}`,
              }}>
                <span className="badge-name">{item.name}</span>
                <span className="badge-grade" style={{ color: sc.color }}>
                  {item.grade}등급 ({item.severity_label})
                </span>
              </div>
            );
          })}
        </div>
      </section>

      {/* ============ 2. 식품 가이드 ============ */}
      {(food_guide.avoid_foods.length > 0 || food_guide.substitutes.length > 0) && (
        <section className="report-section">
          <h2 className="section-title">2. 식품 가이드</h2>

          {/* 회피 식품 */}
          {food_guide.avoid_foods.length > 0 && (
            <div className="subsection">
              <h3 style={{ color: '#e74c3c' }}>🚫 회피 식품</h3>
              {food_guide.avoid_foods.map((item, idx) => (
                <div key={idx} className="food-block avoid-block">
                  <h4>{item.allergen}</h4>
                  <div className="tag-wrap">
                    {item.foods.map((food, i) => (
                      <span key={i} className="food-tag avoid">{food}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* 대체 식품 */}
          {food_guide.substitutes.length > 0 && (
            <div className="subsection">
              <h3 style={{ color: '#27ae60' }}>✅ 대체 식품</h3>
              {food_guide.substitutes.map((item, idx) => (
                <div key={idx} className="food-block safe-block">
                  <p>
                    <span style={{ fontWeight: 600 }}>{item.allergen}</span>:
                    <span style={{ color: '#e74c3c', textDecoration: 'line-through', marginLeft: '0.5rem' }}>
                      {item.original}
                    </span>
                  </p>
                  <div className="tag-wrap">
                    {item.alternatives.map((alt, i) => (
                      <span key={i} className="food-tag safe">{alt}</span>
                    ))}
                  </div>
                  {item.notes && (
                    <p style={{ fontSize: '0.85rem', color: '#666', marginTop: '0.5rem' }}>
                      💡 {item.notes}
                    </p>
                  )}
                </div>
              ))}
            </div>
          )}

          {/* 숨겨진 알러젠 */}
          {food_guide.hidden_sources.length > 0 && (
            <div className="subsection">
              <h3 style={{ color: '#f39c12' }}>⚠️ 숨겨진 알러젠 주의</h3>
              {food_guide.hidden_sources.map((item, idx) => (
                <div key={idx} className="food-block warning-block">
                  <h4>{item.allergen}</h4>
                  <div className="tag-wrap">
                    {item.sources.map((source, i) => (
                      <span key={i} className="food-tag warning">{source}</span>
                    ))}
                  </div>
                </div>
              ))}
            </div>
          )}

          {/* 교차반응 */}
          {food_guide.cross_reactivity.length > 0 && (
            <div className="subsection">
              <h3>🔄 교차반응 주의</h3>
              {food_guide.cross_reactivity.map((item, idx) => (
                <div key={idx} className="food-block cross-block">
                  <p>
                    <strong>{item.from_allergen}</strong> → {item.to_allergen}
                    <span style={{ color: '#666', marginLeft: '0.5rem' }}>
                      (확률: {item.probability})
                    </span>
                  </p>
                  {item.related_foods.length > 0 && (
                    <div className="tag-wrap">
                      {item.related_foods.map((food, i) => (
                        <span key={i} className="food-tag cross">{food}</span>
                      ))}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </section>
      )}

      {/* ============ 3. 증상 정보 ============ */}
      {symptoms.length > 0 && (
        <section className="report-section">
          <h2 className="section-title">3. 예상 증상</h2>
          {symptoms.map((item, idx) => {
            const sc = SEVERITY_COLORS[item.severity] || SEVERITY_COLORS.mild;
            return (
              <div key={idx} className="symptom-card" style={{ borderLeft: `4px solid ${sc.border}` }}>
                <h4>
                  {item.allergen}
                  <span style={{ fontWeight: 'normal', color: sc.color, marginLeft: '0.5rem' }}>
                    ({item.grade}등급 - {SEVERITY_LABELS[item.severity] || item.severity})
                  </span>
                </h4>
                {item.symptoms.length > 0 ? (
                  <ul>
                    {item.symptoms.map((s, i) => (
                      <li key={i}>
                        {s.name}
                        {s.probability && <span style={{ color: '#999', marginLeft: '0.5rem' }}>({s.probability})</span>}
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p style={{ color: '#999' }}>상세 증상 정보 없음</p>
                )}
              </div>
            );
          })}
        </section>
      )}

      {/* ============ 4. 생활 관리 ============ */}
      <section className="report-section">
        <h2 className="section-title">4. 생활 관리</h2>

        {lifestyle.allergen_specific.length > 0 && (
          <div className="subsection">
            <h3>알러젠별 관리</h3>
            {lifestyle.allergen_specific.map((item, idx) => (
              <div key={idx} className="tip-block">
                <h4>{item.allergen}</h4>
                <ul>
                  {item.tips.map((tip, i) => (
                    <li key={i}>{tip}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        )}

        <div className="subsection">
          <h3>일반 관리 팁</h3>
          <div className="tips-grid">
            {lifestyle.common_tips.map((section, idx) => (
              <div key={idx} className="common-tip-card">
                <h4>{section.title}</h4>
                <ul>
                  {section.tips.map((tip, i) => (
                    <li key={i}>{tip}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* ============ 5. 응급 대처 ============ */}
      <section className="report-section">
        <h2 className="section-title">5. 응급 대처</h2>

        {/* 긴급 연락처 */}
        <div className="emergency-banner">
          <p style={{ fontSize: '1.1rem', fontWeight: 'bold' }}>
            🚨 응급 상황 시 즉시 119에 연락하세요
          </p>
          <div style={{ display: 'flex', justifyContent: 'center', gap: '2rem', marginTop: '0.5rem' }}>
            {emergency.contacts?.map((c, idx) => (
              <span key={idx} style={{ fontWeight: 600 }}>
                {c.name}
              </span>
            ))}
          </div>
        </div>

        {emergency.primary && (
          <div className="emergency-card">
            <h3>{emergency.primary.condition}</h3>
            <p style={{ color: '#666' }}>{emergency.primary.description}</p>

            <h4>주요 증상</h4>
            <ul>
              {emergency.primary.symptoms?.map((s, idx) => (
                <li key={idx}>{s}</li>
              ))}
            </ul>

            <h4>대처 방법</h4>
            <ol>
              {emergency.primary.immediate_actions?.map((a, idx) => (
                <li key={idx} style={{ marginBottom: '0.5rem' }}>{a}</li>
              ))}
            </ol>

            {emergency.primary.medication_info && (
              <div style={{ padding: '0.75rem', background: '#e3f2fd', borderRadius: '8px', marginTop: '1rem' }}>
                <strong>약물 정보:</strong> {emergency.primary.medication_info}
              </div>
            )}
          </div>
        )}

        {emergency.secondary && (
          <div className="emergency-card" style={{ marginTop: '1rem' }}>
            <h3>{emergency.secondary.condition}</h3>
            <p style={{ color: '#666' }}>{emergency.secondary.description}</p>
            <h4>대처 방법</h4>
            <ol>
              {emergency.secondary.immediate_actions?.map((a, idx) => (
                <li key={idx} style={{ marginBottom: '0.5rem' }}>{a}</li>
              ))}
            </ol>
          </div>
        )}
      </section>

      {/* 하단 면책 + 인쇄 버튼 */}
      <div className="report-footer">
        <div className="disclaimer-box">
          ⚠️ {disclaimer}
        </div>
        <p style={{ textAlign: 'center', color: '#999', fontSize: '0.85rem', marginTop: '1rem' }}>
          AllergyInsight - 알러지 연구 논문 검색/분석 플랫폼 | {formatDate(generated_at)} 생성
        </p>
        <div className="no-print" style={{ textAlign: 'center', marginTop: '1rem' }}>
          <button className="action-btn print-btn" onClick={handlePrint}>
            🖨️ 인쇄 / PDF 저장
          </button>
        </div>
      </div>

      <style>{`
        .report-container {
          max-width: 900px;
          margin: 0 auto;
        }
        .report-header {
          text-align: center;
          padding: 2rem 1rem;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
          border-radius: 16px;
          margin-bottom: 1.5rem;
        }
        .report-header h1 {
          margin: 0;
          font-size: 2rem;
        }
        .report-subtitle {
          margin: 0.25rem 0 0;
          opacity: 0.8;
          font-size: 0.95rem;
        }
        .report-name {
          margin: 1rem 0 0;
          font-size: 1.25rem;
          font-weight: 600;
        }
        .report-date {
          margin: 0.25rem 0 0;
          opacity: 0.7;
          font-size: 0.9rem;
        }
        .disclaimer-box {
          padding: 1rem;
          background: #fff3cd;
          border: 1px solid #ffc107;
          border-radius: 8px;
          font-size: 0.9rem;
          color: #856404;
          margin-bottom: 1.5rem;
        }
        .report-section {
          margin-bottom: 2rem;
          page-break-inside: avoid;
        }
        .section-title {
          font-size: 1.3rem;
          color: #333;
          border-bottom: 2px solid #667eea;
          padding-bottom: 0.5rem;
          margin-bottom: 1rem;
        }
        .subsection {
          margin-bottom: 1.5rem;
        }
        .summary-cards {
          display: grid;
          grid-template-columns: repeat(4, 1fr);
          gap: 1rem;
          margin-bottom: 1.5rem;
        }
        .summary-card {
          text-align: center;
          padding: 1rem;
          background: white;
          border: 1px solid #eee;
          border-top: 3px solid;
          border-radius: 8px;
        }
        .summary-number {
          display: block;
          font-size: 2rem;
          font-weight: 700;
        }
        .summary-label {
          display: block;
          font-size: 0.8rem;
          color: #666;
          margin-top: 0.25rem;
        }
        .allergen-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
          gap: 0.75rem;
        }
        .allergen-badge {
          padding: 0.75rem 1rem;
          border-radius: 8px;
          display: flex;
          justify-content: space-between;
          align-items: center;
        }
        .badge-name {
          font-weight: 600;
        }
        .badge-grade {
          font-size: 0.85rem;
          font-weight: 500;
        }
        .food-block {
          padding: 1rem;
          border-radius: 8px;
          margin-bottom: 0.75rem;
        }
        .food-block h4 {
          margin: 0 0 0.5rem;
        }
        .avoid-block { background: #fff5f5; }
        .safe-block { background: #f0fff4; }
        .warning-block { background: #fff8e1; }
        .cross-block { background: #f3e5f5; }
        .tag-wrap {
          display: flex;
          flex-wrap: wrap;
          gap: 0.4rem;
        }
        .food-tag {
          padding: 0.2rem 0.65rem;
          border-radius: 16px;
          font-size: 0.85rem;
        }
        .food-tag.avoid { background: #ffcdd2; color: #c62828; }
        .food-tag.safe { background: #c8e6c9; color: #2e7d32; }
        .food-tag.warning { background: #ffe082; color: #f57c00; }
        .food-tag.cross { background: #e1bee7; color: #7b1fa2; }
        .symptom-card {
          padding: 1rem;
          margin-bottom: 0.75rem;
          background: white;
          border: 1px solid #eee;
          border-radius: 8px;
        }
        .symptom-card h4 { margin: 0 0 0.5rem; }
        .symptom-card ul { padding-left: 1.25rem; margin: 0; }
        .symptom-card li { margin-bottom: 0.35rem; }
        .tip-block {
          padding: 1rem;
          background: white;
          border: 1px solid #eee;
          border-radius: 8px;
          margin-bottom: 0.75rem;
        }
        .tip-block h4 { margin: 0 0 0.5rem; }
        .tip-block ul { padding-left: 1.25rem; margin: 0; }
        .tip-block li { margin-bottom: 0.35rem; }
        .tips-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
          gap: 1rem;
        }
        .common-tip-card {
          padding: 1rem;
          background: white;
          border: 1px solid #eee;
          border-radius: 8px;
        }
        .common-tip-card h4 { margin: 0 0 0.5rem; }
        .common-tip-card ul { padding-left: 1.25rem; margin: 0; }
        .common-tip-card li { margin-bottom: 0.35rem; color: #555; }
        .emergency-banner {
          padding: 1rem;
          background: #e74c3c;
          color: white;
          border-radius: 12px;
          text-align: center;
          margin-bottom: 1.5rem;
        }
        .emergency-card {
          padding: 1.5rem;
          background: white;
          border: 1px solid #eee;
          border-radius: 8px;
        }
        .emergency-card h3 { margin-top: 0; }
        .emergency-card h4 { margin-bottom: 0.5rem; }
        .emergency-card ul, .emergency-card ol { padding-left: 1.25rem; }
        .emergency-card li { margin-bottom: 0.35rem; }
        .report-footer {
          margin-top: 2rem;
          padding-top: 1rem;
          border-top: 1px solid #eee;
        }
        .action-btn {
          padding: 0.75rem 1.5rem;
          border: none;
          border-radius: 8px;
          font-size: 1rem;
          cursor: pointer;
          transition: opacity 0.2s;
        }
        .action-btn:hover { opacity: 0.85; }
        .back-btn {
          background: #f0f0f0;
          color: #333;
        }
        .print-btn {
          background: linear-gradient(135deg, #667eea, #764ba2);
          color: white;
        }

        @media (max-width: 600px) {
          .summary-cards {
            grid-template-columns: repeat(2, 1fr);
          }
          .allergen-grid {
            grid-template-columns: 1fr;
          }
        }

        @media print {
          .no-print { display: none !important; }
          .report-container { max-width: 100%; }
          .report-header {
            background: #667eea !important;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
          }
          .report-section { page-break-inside: avoid; }
          .emergency-banner {
            background: #e74c3c !important;
            -webkit-print-color-adjust: exact;
            print-color-adjust: exact;
          }
          body { font-size: 11pt; }
        }
      `}</style>
    </div>
  );
}

export default AllergyReportView;
