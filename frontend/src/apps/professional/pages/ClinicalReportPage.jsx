/**
 * ClinicalReportPage - 의사 전용 임상 보고서 페이지
 *
 * 환자의 알레르기 검사 결과를 의료 문서 형식으로 표시합니다.
 * GRADE 기반 근거 수준 및 논문 인용 포함.
 */
import React, { useState, useEffect } from 'react';
import { useParams, useSearchParams } from 'react-router-dom';
import { proApi } from '../services/proApi';

// GRADE 표시 컴포넌트
const GradeBadge = ({ level, grade }) => {
  const gradeDisplay = {
    A: { symbol: '⊕⊕⊕⊕', label: 'High', color: '#22c55e' },
    B: { symbol: '⊕⊕⊕◯', label: 'Moderate', color: '#3b82f6' },
    C: { symbol: '⊕⊕◯◯', label: 'Low', color: '#f59e0b' },
    D: { symbol: '⊕◯◯◯', label: 'Very Low', color: '#ef4444' },
  };

  const display = gradeDisplay[level] || gradeDisplay['D'];

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '4px',
        fontSize: '12px',
        padding: '2px 8px',
        borderRadius: '4px',
        backgroundColor: `${display.color}20`,
        color: display.color,
        fontFamily: 'monospace',
      }}
    >
      <span>{display.symbol}</span>
      {grade && <span style={{ fontWeight: 'bold' }}>{grade}</span>}
    </span>
  );
};

// 위험도 뱃지 컴포넌트
const RiskBadge = ({ level }) => {
  const colors = {
    High: { bg: '#fef2f2', border: '#ef4444', text: '#b91c1c' },
    Moderate: { bg: '#fffbeb', border: '#f59e0b', text: '#b45309' },
    Low: { bg: '#f0fdf4', border: '#22c55e', text: '#15803d' },
  };
  const style = colors[level] || colors['Low'];

  return (
    <span
      style={{
        padding: '4px 12px',
        borderRadius: '9999px',
        fontSize: '14px',
        fontWeight: 'bold',
        backgroundColor: style.bg,
        border: `1px solid ${style.border}`,
        color: style.text,
      }}
    >
      {level === 'High' && '⚠️ '}{level}
    </span>
  );
};

// 인용 컴포넌트
const Citation = ({ citation }) => {
  if (!citation) return null;

  return (
    <div
      style={{
        fontSize: '12px',
        color: '#6b7280',
        marginTop: '8px',
        padding: '8px',
        backgroundColor: '#f9fafb',
        borderRadius: '4px',
        borderLeft: '3px solid #3b82f6',
      }}
    >
      <div style={{ fontWeight: 'bold', color: '#374151' }}>
        {citation.title}
      </div>
      <div style={{ marginTop: '4px' }}>
        {citation.authors && <span>{citation.authors}</span>}
        {citation.journal && <span> {citation.journal}</span>}
        {citation.year && <span> ({citation.year})</span>}
      </div>
      {citation.pmid && (
        <a
          href={citation.url || `https://pubmed.ncbi.nlm.nih.gov/${citation.pmid}/`}
          target="_blank"
          rel="noopener noreferrer"
          style={{ color: '#3b82f6', textDecoration: 'none' }}
        >
          PMID: {citation.pmid}
        </a>
      )}
      {citation.is_guideline && (
        <span
          style={{
            marginLeft: '8px',
            padding: '2px 6px',
            backgroundColor: '#dbeafe',
            color: '#1e40af',
            borderRadius: '4px',
            fontSize: '10px',
          }}
        >
          {citation.guideline_org} Guideline
        </span>
      )}
    </div>
  );
};

// 임상 진술문 컴포넌트
const ClinicalStatement = ({ statement }) => {
  const [showCitation, setShowCitation] = useState(false);

  return (
    <div
      style={{
        padding: '12px',
        marginBottom: '12px',
        backgroundColor: '#fff',
        border: '1px solid #e5e7eb',
        borderRadius: '8px',
      }}
    >
      <div style={{ display: 'flex', alignItems: 'flex-start', gap: '12px' }}>
        <div style={{ flex: 1 }}>
          <p style={{ margin: 0, color: '#1f2937', lineHeight: 1.6 }}>
            {statement.statement_kr || statement.statement_en}
          </p>
          {statement.statement_kr && (
            <p
              style={{
                margin: '8px 0 0',
                fontSize: '13px',
                color: '#6b7280',
                fontStyle: 'italic',
              }}
            >
              {statement.statement_en}
            </p>
          )}
        </div>
        {statement.evidence_level && (
          <GradeBadge
            level={statement.evidence_level}
            grade={statement.recommendation_grade}
          />
        )}
      </div>
      {statement.citation && (
        <>
          <button
            onClick={() => setShowCitation(!showCitation)}
            style={{
              marginTop: '8px',
              padding: '4px 8px',
              fontSize: '12px',
              color: '#3b82f6',
              backgroundColor: 'transparent',
              border: 'none',
              cursor: 'pointer',
            }}
          >
            {showCitation ? '출처 숨기기' : '출처 보기'} ▸
          </button>
          {showCitation && <Citation citation={statement.citation} />}
        </>
      )}
    </div>
  );
};

// 알러젠 결과 테이블
const AllergenResultsTable = ({ results }) => {
  const getGradeColor = (grade) => {
    if (grade === 0) return '#9ca3af';
    if (grade <= 2) return '#f59e0b';
    if (grade <= 4) return '#ef4444';
    return '#7c2d12';
  };

  return (
    <table style={{ width: '100%', borderCollapse: 'collapse' }}>
      <thead>
        <tr style={{ backgroundColor: '#f3f4f6' }}>
          <th style={thStyle}>알러젠</th>
          <th style={thStyle}>등급</th>
          <th style={thStyle}>해석</th>
          <th style={thStyle}>임상적 의의</th>
        </tr>
      </thead>
      <tbody>
        {results.map((r, i) => (
          <tr
            key={i}
            style={{
              backgroundColor: r.grade > 0 ? '#fef2f2' : '#fff',
              borderBottom: '1px solid #e5e7eb',
            }}
          >
            <td style={tdStyle}>
              <strong>{r.allergen_name_kr}</strong>
              <span style={{ color: '#9ca3af', marginLeft: '8px', fontSize: '12px' }}>
                ({r.allergen_name_en})
              </span>
            </td>
            <td style={{ ...tdStyle, textAlign: 'center' }}>
              <span
                style={{
                  display: 'inline-block',
                  width: '28px',
                  height: '28px',
                  lineHeight: '28px',
                  borderRadius: '50%',
                  backgroundColor: getGradeColor(r.grade),
                  color: '#fff',
                  fontWeight: 'bold',
                }}
              >
                {r.grade}
              </span>
            </td>
            <td style={tdStyle}>
              <span style={{ fontSize: '12px', color: '#6b7280' }}>
                {r.grade_class}
              </span>
              <br />
              {r.grade_interpretation}
            </td>
            <td style={tdStyle}>{r.clinical_significance}</td>
          </tr>
        ))}
      </tbody>
    </table>
  );
};

const thStyle = {
  padding: '12px 16px',
  textAlign: 'left',
  fontSize: '14px',
  fontWeight: 'bold',
  color: '#374151',
  borderBottom: '2px solid #e5e7eb',
};

const tdStyle = {
  padding: '12px 16px',
  fontSize: '14px',
  color: '#1f2937',
};

// 섹션 컴포넌트
const Section = ({ title, children, icon }) => (
  <div
    style={{
      marginBottom: '24px',
      backgroundColor: '#fff',
      borderRadius: '12px',
      boxShadow: '0 1px 3px rgba(0,0,0,0.1)',
      overflow: 'hidden',
    }}
  >
    <div
      style={{
        padding: '16px 20px',
        backgroundColor: '#f8fafc',
        borderBottom: '1px solid #e5e7eb',
      }}
    >
      <h2 style={{ margin: 0, fontSize: '18px', color: '#1f2937' }}>
        {icon} {title}
      </h2>
    </div>
    <div style={{ padding: '20px' }}>{children}</div>
  </div>
);

// 메인 컴포넌트
export default function ClinicalReportPage() {
  const { patientId } = useParams();
  const [searchParams] = useSearchParams();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [searchMode, setSearchMode] = useState('patient');
  const [searchValue, setSearchValue] = useState('');

  useEffect(() => {
    // URL 파라미터에서 조회
    const kitSerial = searchParams.get('kit');
    const diagId = searchParams.get('diagnosis');

    if (patientId) {
      fetchReport({ patient_id: patientId });
    } else if (kitSerial) {
      fetchReport({ kit_serial_number: kitSerial });
    } else if (diagId) {
      fetchReport({ diagnosis_id: diagId });
    } else {
      setLoading(false);
    }
  }, [patientId, searchParams]);

  const fetchReport = async (params) => {
    setLoading(true);
    setError(null);
    try {
      const response = await proApi.clinicalReport.get(params);
      setReport(response.data);
    } catch (err) {
      console.error('Failed to fetch report:', err);
      setError(err.response?.data?.detail || '보고서를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    if (!searchValue.trim()) return;

    const params = {};
    if (searchMode === 'patient') {
      params.patient_id = searchValue;
    } else if (searchMode === 'kit') {
      params.kit_serial_number = searchValue;
    } else if (searchMode === 'diagnosis') {
      params.diagnosis_id = searchValue;
    }
    fetchReport(params);
  };

  if (loading) {
    return (
      <div style={{ padding: '40px', textAlign: 'center' }}>
        <div
          style={{
            display: 'inline-block',
            width: '40px',
            height: '40px',
            border: '3px solid #e5e7eb',
            borderTopColor: '#3b82f6',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
          }}
        />
        <style>
          {`@keyframes spin { to { transform: rotate(360deg); } }`}
        </style>
        <p style={{ marginTop: '16px', color: '#6b7280' }}>
          임상 보고서를 불러오는 중...
        </p>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '1200px', margin: '0 auto', padding: '24px' }}>
      {/* 검색 폼 */}
      {!report && (
        <Section title="임상 보고서 조회" icon="🔍">
          <form onSubmit={handleSearch}>
            <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
              <select
                value={searchMode}
                onChange={(e) => setSearchMode(e.target.value)}
                style={{
                  padding: '10px 16px',
                  borderRadius: '8px',
                  border: '1px solid #d1d5db',
                  fontSize: '14px',
                }}
              >
                <option value="patient">환자 ID</option>
                <option value="kit">키트 시리얼</option>
                <option value="diagnosis">진단 ID</option>
              </select>
              <input
                type="text"
                value={searchValue}
                onChange={(e) => setSearchValue(e.target.value)}
                placeholder={
                  searchMode === 'kit'
                    ? 'SGT-2024-XXXXX-XXXX'
                    : searchMode === 'patient'
                    ? '환자 ID 입력'
                    : '진단 ID 입력'
                }
                style={{
                  flex: 1,
                  padding: '10px 16px',
                  borderRadius: '8px',
                  border: '1px solid #d1d5db',
                  fontSize: '14px',
                }}
              />
              <button
                type="submit"
                style={{
                  padding: '10px 24px',
                  backgroundColor: '#3b82f6',
                  color: '#fff',
                  border: 'none',
                  borderRadius: '8px',
                  fontSize: '14px',
                  fontWeight: 'bold',
                  cursor: 'pointer',
                }}
              >
                조회
              </button>
            </div>
          </form>
          {error && (
            <div
              style={{
                padding: '12px 16px',
                backgroundColor: '#fef2f2',
                color: '#b91c1c',
                borderRadius: '8px',
              }}
            >
              {error}
            </div>
          )}
        </Section>
      )}

      {report && (
        <>
          {/* 헤더: 보고서 메타 정보 */}
          <div
            style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              marginBottom: '24px',
              padding: '16px 24px',
              backgroundColor: '#1e40af',
              color: '#fff',
              borderRadius: '12px',
            }}
          >
            <div>
              <h1 style={{ margin: 0, fontSize: '24px' }}>
                알레르기 임상 보고서
              </h1>
              <p style={{ margin: '4px 0 0', opacity: 0.9, fontSize: '14px' }}>
                Clinical Allergy Assessment Report (Physician Only)
              </p>
            </div>
            <div style={{ textAlign: 'right', fontSize: '14px' }}>
              <div>보고서 버전: {report.report_version}</div>
              <div>
                생성일시:{' '}
                {new Date(report.report_generated_at).toLocaleString('ko-KR')}
              </div>
            </div>
          </div>

          {/* 환자 정보 + 진단 요약 */}
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
            <Section title="환자 정보" icon="👤">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div>
                  <label style={labelStyle}>환자명</label>
                  <div style={valueStyle}>{report.patient.name}</div>
                </div>
                <div>
                  <label style={labelStyle}>환자 ID</label>
                  <div style={valueStyle}>{report.patient.patient_id}</div>
                </div>
                {report.patient.birth_date && (
                  <div>
                    <label style={labelStyle}>생년월일</label>
                    <div style={valueStyle}>{report.patient.birth_date}</div>
                  </div>
                )}
                {report.patient.age && (
                  <div>
                    <label style={labelStyle}>나이</label>
                    <div style={valueStyle}>{report.patient.age}세</div>
                  </div>
                )}
              </div>
            </Section>

            <Section title="진단 요약" icon="📋">
              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '16px' }}>
                <div>
                  <label style={labelStyle}>검사 일자</label>
                  <div style={valueStyle}>{report.diagnosis.diagnosis_date}</div>
                </div>
                <div>
                  <label style={labelStyle}>키트 시리얼</label>
                  <div style={valueStyle}>{report.diagnosis.kit_serial || '-'}</div>
                </div>
                <div>
                  <label style={labelStyle}>양성 항원</label>
                  <div style={valueStyle}>
                    {report.diagnosis.positive_count} / {report.diagnosis.total_tested}
                  </div>
                </div>
                <div>
                  <label style={labelStyle}>위험도</label>
                  <div style={valueStyle}>
                    <RiskBadge level={report.assessment.risk_level} />
                  </div>
                </div>
              </div>
              {report.assessment.anaphylaxis_risk && (
                <div
                  style={{
                    marginTop: '16px',
                    padding: '12px',
                    backgroundColor: '#fef2f2',
                    borderRadius: '8px',
                    border: '1px solid #ef4444',
                    color: '#b91c1c',
                    fontWeight: 'bold',
                  }}
                >
                  ⚠️ 아나필락시스 위험: 에피네프린 자가주사기 처방 권장
                </div>
              )}
            </Section>
          </div>

          {/* ICD-10 진단 코드 */}
          {report.icd10_codes?.length > 0 && (
            <Section title="진단 코드 (ICD-10)" icon="🏷️">
              <div style={{ display: 'flex', gap: '8px', flexWrap: 'wrap' }}>
                {report.icd10_codes.map((code, i) => (
                  <span
                    key={i}
                    style={{
                      padding: '6px 12px',
                      backgroundColor: '#eff6ff',
                      color: '#1e40af',
                      borderRadius: '6px',
                      fontSize: '14px',
                      fontFamily: 'monospace',
                    }}
                  >
                    {code}
                  </span>
                ))}
              </div>
            </Section>
          )}

          {/* Objective: 검사 결과 */}
          <Section title="검사 결과 (Objective)" icon="🔬">
            <AllergenResultsTable results={report.allergen_results} />
          </Section>

          {/* Assessment: 임상 평가 */}
          <Section title="임상 평가 (Assessment)" icon="📊">
            {/* 교차반응 */}
            {report.assessment.cross_reactivity_concerns?.length > 0 && (
              <div style={{ marginBottom: '24px' }}>
                <h3 style={{ fontSize: '16px', color: '#374151', marginBottom: '12px' }}>
                  교차반응 고려사항
                </h3>
                {report.assessment.cross_reactivity_concerns.map((cr, i) => (
                  <div
                    key={i}
                    style={{
                      padding: '16px',
                      backgroundColor: '#fefce8',
                      border: '1px solid #fcd34d',
                      borderRadius: '8px',
                      marginBottom: '12px',
                    }}
                  >
                    <div style={{ fontWeight: 'bold', color: '#92400e' }}>
                      관련 알러젠: {cr.related_allergens.join(', ')}
                    </div>
                    {cr.mechanism && (
                      <div style={{ marginTop: '8px', color: '#78350f' }}>
                        기전: {cr.mechanism}
                      </div>
                    )}
                    {cr.statements?.map((stmt, j) => (
                      <ClinicalStatement key={j} statement={stmt} />
                    ))}
                  </div>
                ))}
              </div>
            )}

            {/* 임상 진술문 */}
            {report.assessment.clinical_statements?.length > 0 && (
              <div>
                <h3 style={{ fontSize: '16px', color: '#374151', marginBottom: '12px' }}>
                  근거 기반 임상 진술
                </h3>
                {report.assessment.clinical_statements.map((stmt, i) => (
                  <ClinicalStatement key={i} statement={stmt} />
                ))}
              </div>
            )}
          </Section>

          {/* Plan: 관리 계획 */}
          <Section title="관리 계획 (Plan)" icon="📝">
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
              {/* 회피 식품 */}
              <div>
                <h4 style={{ color: '#ef4444', marginBottom: '12px' }}>🚫 회피 식품</h4>
                <ul style={{ margin: 0, paddingLeft: '20px' }}>
                  {report.management.avoidance_items.map((item, i) => (
                    <li key={i} style={{ marginBottom: '4px' }}>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>

              {/* 숨겨진 알러젠 */}
              <div>
                <h4 style={{ color: '#f59e0b', marginBottom: '12px' }}>
                  ⚠️ 숨겨진 알러젠 주의
                </h4>
                <ul style={{ margin: 0, paddingLeft: '20px' }}>
                  {report.management.hidden_allergens.map((item, i) => (
                    <li key={i} style={{ marginBottom: '4px' }}>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>

              {/* 대체 식품 */}
              <div>
                <h4 style={{ color: '#22c55e', marginBottom: '12px' }}>✅ 권장 대체 식품</h4>
                <ul style={{ margin: 0, paddingLeft: '20px' }}>
                  {report.management.substitutes.map((item, i) => (
                    <li key={i} style={{ marginBottom: '4px' }}>
                      {item}
                    </li>
                  ))}
                </ul>
              </div>

              {/* 추가 권고 */}
              <div>
                <h4 style={{ color: '#3b82f6', marginBottom: '12px' }}>📋 추가 권고사항</h4>
                <ul style={{ margin: 0, paddingLeft: '20px' }}>
                  {report.management.emergency_plan && (
                    <li style={{ marginBottom: '4px', fontWeight: 'bold', color: '#ef4444' }}>
                      응급 대처 계획 수립 필요
                    </li>
                  )}
                  {report.management.follow_up_recommended && (
                    <li style={{ marginBottom: '4px' }}>추적 관찰 권장</li>
                  )}
                </ul>
              </div>
            </div>

            {/* 관리 관련 진술문 */}
            {report.management.statements?.length > 0 && (
              <div style={{ marginTop: '24px' }}>
                <h3 style={{ fontSize: '16px', color: '#374151', marginBottom: '12px' }}>
                  관리 지침 (근거 기반)
                </h3>
                {report.management.statements.map((stmt, i) => (
                  <ClinicalStatement key={i} statement={stmt} />
                ))}
              </div>
            )}
          </Section>

          {/* References */}
          {report.references?.length > 0 && (
            <Section title="참고문헌" icon="📚">
              <div style={{ fontSize: '14px' }}>
                {report.references.map((ref, i) => (
                  <div
                    key={i}
                    style={{
                      padding: '12px',
                      marginBottom: '8px',
                      backgroundColor: '#f9fafb',
                      borderRadius: '8px',
                    }}
                  >
                    <div style={{ fontWeight: 'bold', color: '#1f2937' }}>
                      [{i + 1}] {ref.title}
                    </div>
                    <div style={{ color: '#6b7280', marginTop: '4px' }}>
                      {ref.authors && <span>{ref.authors}</span>}
                      {ref.journal && <span>. {ref.journal}</span>}
                      {ref.year && <span>. {ref.year}</span>}
                      {ref.pmid && (
                        <a
                          href={ref.url || `https://pubmed.ncbi.nlm.nih.gov/${ref.pmid}/`}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{ color: '#3b82f6', marginLeft: '8px' }}
                        >
                          [PubMed]
                        </a>
                      )}
                    </div>
                    {ref.evidence_level && (
                      <div style={{ marginTop: '4px' }}>
                        <GradeBadge level={ref.evidence_level} />
                      </div>
                    )}
                  </div>
                ))}
              </div>
            </Section>
          )}

          {/* 새로운 검색 버튼 */}
          <div style={{ textAlign: 'center', marginTop: '24px' }}>
            <button
              onClick={() => setReport(null)}
              style={{
                padding: '12px 24px',
                backgroundColor: '#6b7280',
                color: '#fff',
                border: 'none',
                borderRadius: '8px',
                fontSize: '14px',
                cursor: 'pointer',
              }}
            >
              다른 환자 조회
            </button>
          </div>
        </>
      )}
    </div>
  );
}

const labelStyle = {
  display: 'block',
  fontSize: '12px',
  color: '#6b7280',
  marginBottom: '4px',
};

const valueStyle = {
  fontSize: '16px',
  fontWeight: '500',
  color: '#1f2937',
};
