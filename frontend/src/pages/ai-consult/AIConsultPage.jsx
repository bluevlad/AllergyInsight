/**
 * AI Consult Page - 알러지 AI 상담
 *
 * 공개 페이지 (인증 불필요)
 * 사용자가 알러지 관련 질문을 하면 논문 기반 AI 답변을 제공합니다.
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../../shared/services/apiClient';

const CATEGORY_ICONS = {
  symptoms: '🩺',
  severity: '⚠️',
  cross_reactivity: '🔄',
  onset: '⏱️',
  treatment: '💊',
};

function AIConsultPage() {
  const navigate = useNavigate();
  const [allergens, setAllergens] = useState({ food: [], inhalant: [] });
  const [selectedAllergen, setSelectedAllergen] = useState('peanut');
  const [question, setQuestion] = useState('');
  const [quickQuestions, setQuickQuestions] = useState([]);
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [history, setHistory] = useState([]);

  // 알러젠 목록 로드
  useEffect(() => {
    apiClient.get('/ai/consult/allergens')
      .then(data => {
        setAllergens({ food: data.food, inhalant: data.inhalant });
      })
      .catch(() => {});
  }, []);

  // 빠른 질문 로드
  useEffect(() => {
    apiClient.get(`/ai/consult/questions/${selectedAllergen}`)
      .then(data => {
        setQuickQuestions(data.categories || []);
      })
      .catch(() => {});
  }, [selectedAllergen]);

  const handleAsk = async (q) => {
    const questionText = q || question;
    if (!questionText.trim()) return;

    try {
      setLoading(true);
      setError(null);
      setAnswer(null);

      const data = await apiClient.post('/ai/consult/ask', {
        question: questionText,
        allergen: selectedAllergen,
        max_citations: 5,
      });

      setAnswer(data);
      setHistory(prev => [
        { question: questionText, allergen: selectedAllergen, timestamp: new Date().toISOString() },
        ...prev.slice(0, 9),
      ]);
      if (!q) setQuestion('');
    } catch (err) {
      setError(err.response?.data?.detail || '답변 생성에 실패했습니다. 잠시 후 다시 시도해주세요.');
    } finally {
      setLoading(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleAsk();
    }
  };

  const getAllergenName = (code) => {
    const all = [...allergens.food, ...allergens.inhalant];
    const found = all.find(a => a.code === code);
    return found ? found.name_kr : code;
  };

  return (
    <div style={{ minHeight: '100vh', background: '#f5f6fa' }}>
      {/* 헤더 */}
      <div style={{
        background: 'linear-gradient(135deg, #2980b9 0%, #3498db 50%, #2c3e50 100%)',
        padding: '1.25rem 1rem',
        textAlign: 'center',
        color: 'white',
      }}>
        <h1
          style={{ margin: 0, fontSize: '1.5rem', cursor: 'pointer' }}
          onClick={() => navigate('/')}
        >
          AllergyInsight
        </h1>
        <p style={{ margin: '0.25rem 0 0', opacity: 0.85, fontSize: '0.9rem' }}>
          알러지 AI 상담
        </p>
      </div>

      <div style={{ maxWidth: '900px', margin: '0 auto', padding: '1.5rem 1rem' }}>
        {/* 소개 */}
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <h2 style={{ marginTop: 0, marginBottom: '0.5rem' }}>알러지에 대해 궁금한 점을 물어보세요</h2>
          <p style={{ color: '#666', margin: 0, fontSize: '0.9rem' }}>
            수집된 의학 논문을 기반으로 알러지 관련 질문에 답변합니다. 출처 논문과 함께 신뢰도를 표시합니다.
          </p>
        </div>

        {/* 알러젠 선택 */}
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <h4 style={{ marginTop: 0, marginBottom: '0.75rem' }}>관심 알러젠 선택</h4>

          <div style={{ marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.8rem', color: '#999', fontWeight: 600 }}>식품</span>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '0.75rem' }}>
            {allergens.food.map(a => (
              <button
                key={a.code}
                className={`allergen-tag ${selectedAllergen === a.code ? 'selected' : ''}`}
                onClick={() => setSelectedAllergen(a.code)}
              >
                {a.name_kr}
              </button>
            ))}
          </div>

          <div style={{ marginBottom: '0.5rem' }}>
            <span style={{ fontSize: '0.8rem', color: '#999', fontWeight: 600 }}>흡입</span>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {allergens.inhalant.map(a => (
              <button
                key={a.code}
                className={`allergen-tag ${selectedAllergen === a.code ? 'selected' : ''}`}
                onClick={() => setSelectedAllergen(a.code)}
              >
                {a.name_kr}
              </button>
            ))}
          </div>
        </div>

        {/* 빠른 질문 */}
        {quickQuestions.length > 0 && (
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <h4 style={{ marginTop: 0, marginBottom: '0.75rem' }}>
              빠른 질문 — {getAllergenName(selectedAllergen)}
            </h4>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {quickQuestions.map(cat => (
                <React.Fragment key={cat.category}>
                  {cat.questions.slice(0, 1).map((q, i) => (
                    <button
                      key={i}
                      className="quick-q-btn"
                      onClick={() => {
                        setQuestion(q);
                        handleAsk(q);
                      }}
                      disabled={loading}
                    >
                      <span style={{ marginRight: '0.35rem' }}>{CATEGORY_ICONS[cat.category] || '❓'}</span>
                      {q}
                    </button>
                  ))}
                </React.Fragment>
              ))}
            </div>
          </div>
        )}

        {/* 질문 입력 */}
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <div style={{ display: 'flex', gap: '0.75rem' }}>
            <textarea
              value={question}
              onChange={e => setQuestion(e.target.value)}
              onKeyDown={handleKeyDown}
              placeholder={`${getAllergenName(selectedAllergen)} 알러지에 대해 궁금한 점을 입력하세요...`}
              rows={2}
              maxLength={500}
              style={{
                flex: 1,
                padding: '0.75rem',
                border: '1px solid #ddd',
                borderRadius: '8px',
                fontSize: '1rem',
                resize: 'vertical',
                fontFamily: 'inherit',
              }}
            />
            <button
              className="ask-btn"
              onClick={() => handleAsk()}
              disabled={!question.trim() || loading}
            >
              {loading ? '...' : '질문'}
            </button>
          </div>
          <div style={{ fontSize: '0.75rem', color: '#999', marginTop: '0.35rem' }}>
            Enter로 전송 · {question.length}/500
          </div>
        </div>

        {/* 에러 */}
        {error && (
          <div style={{
            padding: '0.75rem 1rem',
            background: '#ffebee',
            color: '#c62828',
            borderRadius: '8px',
            marginBottom: '1rem',
          }}>
            {error}
          </div>
        )}

        {/* 로딩 */}
        {loading && (
          <div className="card" style={{ textAlign: 'center', padding: '2rem', marginBottom: '1.5rem' }}>
            <div className="spinner" />
            <p style={{ color: '#666', marginTop: '1rem' }}>논문을 검색하고 답변을 생성하고 있습니다...</p>
          </div>
        )}

        {/* 답변 */}
        {answer && !loading && (
          <div className="card answer-card" style={{ marginBottom: '1.5rem' }}>
            {/* 신뢰도 + 엔진 */}
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
              <h3 style={{ margin: 0 }}>AI 답변</h3>
              <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
                {answer.engine && (
                  <span style={{
                    padding: '0.2rem 0.6rem',
                    borderRadius: '12px',
                    fontSize: '0.7rem',
                    fontWeight: 600,
                    background: answer.engine === 'rag' ? '#e3f2fd' : '#f3e5f5',
                    color: answer.engine === 'rag' ? '#1565c0' : '#7b1fa2',
                  }}>
                    {answer.engine === 'rag' ? 'RAG' : 'Keyword'}
                  </span>
                )}
                <span className="confidence-badge" data-level={
                  answer.confidence >= 0.7 ? 'high' : answer.confidence >= 0.4 ? 'medium' : 'low'
                }>
                  신뢰도 {Math.round(answer.confidence * 100)}%
                </span>
              </div>
            </div>

            {/* 답변 본문 */}
            <div
              className="answer-body"
              dangerouslySetInnerHTML={{
                __html: formatAnswer(answer.answer),
              }}
            />

            {/* 주의사항 */}
            {answer.warnings && answer.warnings.length > 0 && (
              <div style={{
                marginTop: '1rem',
                padding: '0.75rem',
                background: '#fff3cd',
                border: '1px solid #ffc107',
                borderRadius: '8px',
                fontSize: '0.85rem',
              }}>
                {answer.warnings.map((w, i) => (
                  <p key={i} style={{ margin: i === 0 ? 0 : '0.5rem 0 0', color: '#856404' }}>
                    ⚠️ {w}
                  </p>
                ))}
              </div>
            )}

            {/* 출처 논문 (RAG 엔진) */}
            {answer.sources && answer.sources.length > 0 && (
              <div style={{ marginTop: '1.25rem' }}>
                <h4 style={{ margin: '0 0 0.5rem', fontSize: '0.95rem' }}>
                  참고 논문 ({answer.source_count}건)
                </h4>
                <div className="citations-list">
                  {answer.sources.map((s, i) => (
                    <div key={i} className="citation-item">
                      <div style={{ fontWeight: 500, fontSize: '0.9rem' }}>
                        [{i + 1}] {s.title}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#777', marginTop: '0.25rem' }}>
                        {s.year > 0 && <span>{s.year} · </span>}
                        {s.doi && <span>DOI: {s.doi} · </span>}
                        <span>관련도 {Math.round(s.relevance * 100)}%</span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* 출처 논문 (Keyword 엔진) */}
            {answer.citations && answer.citations.length > 0 && (
              <div style={{ marginTop: '1.25rem' }}>
                <h4 style={{ margin: '0 0 0.5rem', fontSize: '0.95rem' }}>
                  참고 논문 ({answer.citation_count}건)
                </h4>
                <div className="citations-list">
                  {answer.citations.map((c, i) => (
                    <div key={i} className="citation-item">
                      <div style={{ fontWeight: 500, fontSize: '0.9rem' }}>
                        [{i + 1}] {c.paper_title}
                      </div>
                      <div style={{ fontSize: '0.8rem', color: '#777', marginTop: '0.25rem' }}>
                        {c.authors && <span>{c.authors} · </span>}
                        {c.year && <span>{c.year} · </span>}
                        {c.journal && <span>{c.journal}</span>}
                      </div>
                      {c.relevant_text && (
                        <div style={{ fontSize: '0.8rem', color: '#555', marginTop: '0.35rem', fontStyle: 'italic' }}>
                          "{c.relevant_text.slice(0, 150)}..."
                        </div>
                      )}
                    </div>
                  ))}
                </div>
              </div>
            )}
          </div>
        )}

        {/* 질문 히스토리 */}
        {history.length > 0 && (
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <h4 style={{ marginTop: 0, marginBottom: '0.5rem', fontSize: '0.9rem', color: '#999' }}>
              이전 질문
            </h4>
            {history.map((h, i) => (
              <div
                key={i}
                className="history-item"
                onClick={() => {
                  setSelectedAllergen(h.allergen);
                  setQuestion(h.question);
                  handleAsk(h.question);
                }}
              >
                <span style={{ fontSize: '0.85rem' }}>{h.question}</span>
                <span style={{ fontSize: '0.75rem', color: '#aaa' }}>{getAllergenName(h.allergen)}</span>
              </div>
            ))}
          </div>
        )}

        {/* 의학적 고지 */}
        <div style={{
          padding: '1rem',
          background: '#fff3cd',
          border: '1px solid #ffc107',
          borderRadius: '8px',
          fontSize: '0.85rem',
          color: '#856404',
        }}>
          ⚠️ 본 AI 상담은 의학 논문을 기반으로 한 참고 정보이며, 의학적 진단이나 치료를 대체하지 않습니다.
          정확한 진단과 치료는 반드시 전문 의료진과 상담하세요.
        </div>
      </div>

      {/* 푸터 */}
      <footer style={{ textAlign: 'center', padding: '2rem 1rem', color: '#999', fontSize: '0.85rem' }}>
        <a href="/ai/insight" style={{ color: '#2980b9', textDecoration: 'none', marginRight: '1.5rem' }}>
          알러지 인사이트
        </a>
        <a href="/" style={{ color: '#667eea', textDecoration: 'none' }}>
          AllergyInsight 홈으로
        </a>
      </footer>

      <style>{`
        .card {
          background: white;
          border-radius: 12px;
          padding: 1.5rem;
          box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        .allergen-tag {
          padding: 0.4rem 0.85rem;
          border: 1.5px solid #ddd;
          border-radius: 20px;
          background: white;
          cursor: pointer;
          font-size: 0.85rem;
          transition: all 0.15s;
        }
        .allergen-tag:hover {
          border-color: #2980b9;
          color: #2980b9;
        }
        .allergen-tag.selected {
          background: #2980b9;
          color: white;
          border-color: #2980b9;
        }
        .quick-q-btn {
          padding: 0.5rem 0.85rem;
          border: 1px solid #e0e0e0;
          border-radius: 20px;
          background: #f8f9fa;
          cursor: pointer;
          font-size: 0.82rem;
          transition: all 0.15s;
          text-align: left;
        }
        .quick-q-btn:hover:not(:disabled) {
          background: #e3f2fd;
          border-color: #2980b9;
        }
        .quick-q-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .ask-btn {
          padding: 0.75rem 1.5rem;
          background: linear-gradient(135deg, #2980b9, #2c3e50);
          color: white;
          border: none;
          border-radius: 8px;
          font-size: 1rem;
          font-weight: 600;
          cursor: pointer;
          transition: opacity 0.2s;
          white-space: nowrap;
        }
        .ask-btn:hover:not(:disabled) {
          opacity: 0.9;
        }
        .ask-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        .spinner {
          width: 36px;
          height: 36px;
          border: 4px solid #e9ecef;
          border-top: 4px solid #2980b9;
          border-radius: 50%;
          animation: spin 1s linear infinite;
          margin: 0 auto;
        }
        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }
        .confidence-badge {
          padding: 0.3rem 0.75rem;
          border-radius: 16px;
          font-size: 0.8rem;
          font-weight: 600;
        }
        .confidence-badge[data-level="high"] {
          background: #e8f5e9;
          color: #2e7d32;
        }
        .confidence-badge[data-level="medium"] {
          background: #fff8e1;
          color: #f57f17;
        }
        .confidence-badge[data-level="low"] {
          background: #fce4ec;
          color: #c62828;
        }
        .answer-body {
          line-height: 1.7;
          font-size: 0.95rem;
          color: #333;
        }
        .answer-body h2 {
          font-size: 1.15rem;
          margin: 0.75rem 0 0.5rem;
          color: #2c3e50;
        }
        .answer-body h3 {
          font-size: 1rem;
          margin: 0.75rem 0 0.35rem;
          color: #34495e;
        }
        .answer-body ul, .answer-body ol {
          padding-left: 1.25rem;
        }
        .answer-body li {
          margin-bottom: 0.25rem;
        }
        .answer-card {
          border-left: 4px solid #2980b9;
        }
        .citations-list {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }
        .citation-item {
          padding: 0.75rem;
          background: #f8f9fa;
          border-radius: 8px;
          border-left: 3px solid #2980b9;
        }
        .history-item {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 0.5rem 0;
          border-bottom: 1px solid #f0f0f0;
          cursor: pointer;
          transition: background 0.15s;
        }
        .history-item:hover {
          background: #f8f9fa;
        }
        .history-item:last-child {
          border-bottom: none;
        }
        @media (max-width: 600px) {
          .card { padding: 1rem; }
        }
      `}</style>
    </div>
  );
}

function formatAnswer(text) {
  if (!text) return '';
  return text
    .replace(/## (.+)/g, '<h2>$1</h2>')
    .replace(/### (.+)/g, '<h3>$1</h3>')
    .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
    .replace(/^- (.+)$/gm, '<li>$1</li>')
    .replace(/(<li>.*<\/li>\n?)+/g, '<ul>$&</ul>')
    .replace(/\n{2,}/g, '<br/><br/>')
    .replace(/\n/g, '<br/>');
}

export default AIConsultPage;
