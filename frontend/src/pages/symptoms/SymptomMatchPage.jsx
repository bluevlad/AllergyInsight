/**
 * Symptom Match Page (Phase 2)
 *
 * 비회원 공개 — 증상 자유 텍스트 입력 → 매칭 알러젠 후보 표시.
 * "진단" 표현 금지, "유사 사례 매칭" 표현 일관 유지.
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../../shared/services/apiClient';
import EmergencyAlert from '../../shared/components/EmergencyAlert';
import MedicalDisclaimer from '../../shared/components/MedicalDisclaimer';
import BackToHomeBar from '../../shared/components/BackToHomeBar';

const SEVERITY_LABEL = {
  mild: '경미',
  moderate: '중등도',
  severe: '심각',
  anaphylaxis: '응급',
};

const SEVERITY_COLOR = {
  mild: '#10b981',
  moderate: '#f59e0b',
  severe: '#ef4444',
  anaphylaxis: '#7f1d1d',
};

const EXAMPLE_INPUTS = [
  '입술이 부어서 따끔거리고 두드러기가 났어요',
  '재채기와 콧물이 너무 많이 나요',
  '복통과 구토 증상이 있어요',
  '목이 가렵고 발진이 생겼어요',
];

const SymptomMatchPage = () => {
  const navigate = useNavigate();
  const [text, setText] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async (overrideText) => {
    const input = overrideText ?? text;
    if (!input.trim()) return;

    try {
      setLoading(true);
      setError(null);
      setResult(null);
      const data = await apiClient.post('/public/symptom/match', {
        text: input,
        top_k: 5,
      });
      setResult(data);
      window.scrollTo({ top: 200, behavior: 'smooth' });
    } catch (err) {
      setError(err.response?.data?.detail || '증상 매칭에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey && (e.metaKey || e.ctrlKey)) {
      e.preventDefault();
      handleSubmit();
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: '#f5f6fa' }}>
      <BackToHomeBar />
      <div
        style={{
          background: 'linear-gradient(135deg, #2980b9 0%, #3498db 50%, #2c3e50 100%)',
          padding: '1.25rem 1rem',
          textAlign: 'center',
          color: 'white',
        }}
      >
        <h1
          style={{ margin: 0, fontSize: '1.5rem', cursor: 'pointer' }}
          onClick={() => navigate('/')}
        >
          AllergyInsight
        </h1>
        <p style={{ margin: '0.25rem 0 0', opacity: 0.85, fontSize: '0.9rem' }}>
          증상 → 관련 알러젠 매칭
        </p>
      </div>

      <div style={{ maxWidth: '900px', margin: '0 auto', padding: '1.5rem 1rem' }}>
        <div style={{ marginBottom: '1rem' }}>
          <MedicalDisclaimer variant="banner" />
        </div>

        <div style={cardStyle}>
          <h2 style={{ margin: '0 0 0.5rem' }}>증상을 입력해 보세요</h2>
          <p style={{ color: '#666', margin: 0, fontSize: '0.9rem', lineHeight: 1.6 }}>
            증상을 자유롭게 한국어로 입력하시면, 논문 · 전문기관에 보고된 알러지 증상 패턴과 <strong>유사 사례를 매칭</strong>해서 보여드립니다.
            본 서비스는 진단을 내리지 않으며, 정확한 진단은 의료진과 상담하세요.
          </p>
        </div>

        <div style={cardStyle}>
          <textarea
            value={text}
            onChange={(e) => setText(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder="예: 입술이 부어서 따끔거리고 두드러기가 났어요"
            rows={3}
            maxLength={500}
            style={{
              width: '100%',
              padding: '0.75rem',
              border: '1px solid #e0e0e0',
              borderRadius: '8px',
              fontSize: '1rem',
              resize: 'vertical',
              fontFamily: 'inherit',
              boxSizing: 'border-box',
            }}
          />
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '0.4rem' }}>
            <span style={{ fontSize: '0.75rem', color: '#999' }}>
              {text.length}/500 · ⌘/Ctrl+Enter 로 전송
            </span>
          </div>

          <div style={{ marginTop: '0.75rem' }}>
            <div style={{ fontSize: '0.85rem', color: '#666', marginBottom: '0.4rem' }}>예시 입력:</div>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.4rem' }}>
              {EXAMPLE_INPUTS.map((ex, i) => (
                <button
                  key={i}
                  type="button"
                  onClick={() => { setText(ex); handleSubmit(ex); }}
                  style={exampleBtnStyle}
                  disabled={loading}
                >
                  {ex}
                </button>
              ))}
            </div>
          </div>

          <button
            onClick={() => handleSubmit()}
            disabled={!text.trim() || loading}
            style={{
              width: '100%',
              padding: '0.85rem',
              marginTop: '1rem',
              border: 'none',
              borderRadius: '8px',
              background: text.trim() && !loading ? '#1976d2' : '#bdbdbd',
              color: 'white',
              fontSize: '1rem',
              fontWeight: 600,
              cursor: text.trim() && !loading ? 'pointer' : 'not-allowed',
            }}
          >
            {loading ? '매칭 중...' : '증상 매칭하기'}
          </button>
        </div>

        {error && (
          <div role="alert" style={{ ...cardStyle, background: '#ffebee', color: '#c62828' }}>
            {error}
          </div>
        )}

        {result && result.safety && (
          <EmergencyAlert safety={result.safety} />
        )}

        {result && (
          <div style={cardStyle}>
            <h3 style={{ margin: '0 0 0.6rem' }}>매칭 결과</h3>
            <p style={{ margin: '0 0 1rem', color: '#444', lineHeight: 1.6 }}>
              {result.message}
            </p>

            {result.matches?.length > 0 ? (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
                {result.matches.map((m, i) => (
                  <MatchCard key={m.allergen_code} index={i + 1} match={m} />
                ))}
              </div>
            ) : (
              <p style={{ color: '#999', margin: 0, fontStyle: 'italic' }}>
                매칭된 알러젠 후보가 없습니다.
              </p>
            )}

            <div
              style={{
                marginTop: '1rem',
                padding: '0.6rem 0.85rem',
                background: '#f5f5f5',
                borderLeft: '3px solid #ffc107',
                color: '#5d4037',
                fontSize: '0.8rem',
                lineHeight: 1.5,
              }}
            >
              {result.disclaimer}
            </div>
          </div>
        )}
      </div>

      <footer style={{ textAlign: 'center', padding: '2rem 1rem', color: '#999', fontSize: '0.85rem' }}>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          <a href="/help/medical-disclaimer.html" target="_blank" rel="noopener" style={linkStyle}>
            의료 정보 면책 안내
          </a>
          <span style={{ color: '#ddd' }}>·</span>
          <a href="/mast" style={linkStyle}>MAST 등급 매칭</a>
          <span style={{ color: '#ddd' }}>·</span>
          <a href="/ai/consult" style={linkStyle}>알러지 AI 상담</a>
          <span style={{ color: '#ddd' }}>·</span>
          <a href="/" style={linkStyle}>AllergyInsight 홈으로</a>
        </div>
      </footer>
    </div>
  );
};

const MatchCard = ({ index, match }) => (
  <div
    style={{
      padding: '0.85rem 1rem',
      border: '1px solid #e0e0e0',
      borderRadius: '8px',
      background: 'white',
    }}
  >
    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.5rem' }}>
      <div>
        <span style={{ color: '#999', fontSize: '0.85rem' }}>#{index}</span>
        <span style={{ marginLeft: '0.4rem', fontWeight: 600, fontSize: '1.05rem' }}>
          {match.name_kr}
        </span>
        <span style={{ marginLeft: '0.4rem', color: '#666', fontSize: '0.85rem' }}>
          {match.name_en}
        </span>
        <span style={{ marginLeft: '0.5rem', color: '#aaa', fontSize: '0.8rem' }}>
          [{match.allergen_code}] · {match.category}
        </span>
      </div>
      <span
        style={{
          padding: '0.2rem 0.6rem',
          background: '#e3f2fd',
          color: '#1565c0',
          borderRadius: '999px',
          fontSize: '0.8rem',
          fontWeight: 600,
        }}
      >
        score {match.score}
      </span>
    </div>

    {match.matched_symptoms?.length > 0 && (
      <div style={{ marginTop: '0.6rem' }}>
        <div style={{ fontSize: '0.8rem', color: '#666', marginBottom: '0.3rem' }}>
          매칭된 보고 사례:
        </div>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.35rem' }}>
          {match.matched_symptoms.map((s, i) => (
            <span
              key={i}
              style={{
                padding: '0.2rem 0.55rem',
                background: `${SEVERITY_COLOR[s.severity] ?? '#666'}15`,
                color: SEVERITY_COLOR[s.severity] ?? '#666',
                borderRadius: '4px',
                fontSize: '0.8rem',
              }}
            >
              {s.symptom}
              <span style={{ opacity: 0.6, marginLeft: '0.3rem' }}>
                ({SEVERITY_LABEL[s.severity] ?? s.severity})
              </span>
            </span>
          ))}
        </div>
      </div>
    )}

    <div style={{ marginTop: '0.6rem', fontSize: '0.8rem', color: '#999' }}>
      <a href={`/mast?allergen=${match.allergen_code}`} style={{ color: '#1976d2', textDecoration: 'none' }}>
        → 이 알러젠의 MAST 등급별 정보 보기
      </a>
    </div>
  </div>
);

const cardStyle = {
  padding: '1rem 1.25rem',
  background: 'white',
  border: '1px solid #e0e0e0',
  borderRadius: '8px',
  marginBottom: '1rem',
};

const exampleBtnStyle = {
  padding: '0.4rem 0.7rem',
  border: '1px solid #e0e0e0',
  borderRadius: '999px',
  background: '#f5f5f5',
  color: '#444',
  fontSize: '0.8rem',
  cursor: 'pointer',
};

const linkStyle = {
  color: '#1976d2',
  textDecoration: 'none',
};

export default SymptomMatchPage;
