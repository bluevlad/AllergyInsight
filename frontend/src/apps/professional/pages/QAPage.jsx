/**
 * Professional Q&A Page - 질문/답변
 */
import React, { useState } from 'react';
import { proApi } from '../services/proApi';

function QAPage() {
  const [question, setQuestion] = useState('');
  const [contextAllergens, setContextAllergens] = useState([]);
  const [answer, setAnswer] = useState(null);
  const [loading, setLoading] = useState(false);
  const [history, setHistory] = useState([]);

  const allergenOptions = [
    { code: 'peanut', label: '땅콩' },
    { code: 'milk', label: '우유' },
    { code: 'egg', label: '계란' },
    { code: 'wheat', label: '밀' },
    { code: 'soy', label: '대두' },
    { code: 'fish', label: '생선' },
    { code: 'shellfish', label: '갑각류' },
    { code: 'tree_nuts', label: '견과류' },
    { code: 'sesame', label: '참깨' },
    { code: 'dust_mite', label: '집먼지진드기' },
    { code: 'pollen', label: '꽃가루' },
    { code: 'mold', label: '곰팡이' },
    { code: 'pet_dander', label: '반려동물' },
  ];

  const toggleAllergen = (code) => {
    setContextAllergens(prev =>
      prev.includes(code)
        ? prev.filter(c => c !== code)
        : [...prev, code]
    );
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!question.trim()) {
      alert('질문을 입력해주세요.');
      return;
    }

    try {
      setLoading(true);
      const response = await proApi.research.askQuestion({
        question: question,
        context_allergens: contextAllergens.length > 0 ? contextAllergens : null,
      });
      setAnswer(response);

      // 히스토리에 추가
      setHistory(prev => [
        { question, answer: response, timestamp: new Date() },
        ...prev.slice(0, 9), // 최근 10개만 유지
      ]);
    } catch (err) {
      console.error('Q&A 실패:', err);
      alert('질문 처리에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleQuickQuestion = (q) => {
    setQuestion(q);
  };

  const quickQuestions = [
    '땅콩 알러지 환자의 식이 주의사항은?',
    '우유 알러지와 유당불내증의 차이점은?',
    '교차반응이 발생하는 알러젠 조합은?',
    '아나필락시스 응급 대처법은?',
    '알러지 검사 결과 해석 방법은?',
  ];

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto' }}>
      <h2>Q&A</h2>
      <p style={{ color: '#666', marginBottom: '1.5rem' }}>
        알러지 관련 질문을 입력하면 관련 논문을 기반으로 답변을 제공합니다.
      </p>

      {/* 질문 폼 */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>질문</label>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              className="form-control"
              rows={3}
              placeholder="알러지 관련 질문을 입력하세요..."
            />
          </div>

          {/* 알러젠 컨텍스트 */}
          <div className="form-group">
            <label>관련 알러젠 선택 (선택사항)</label>
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {allergenOptions.map((opt) => (
                <button
                  key={opt.code}
                  type="button"
                  className={`btn btn-sm ${contextAllergens.includes(opt.code) ? 'btn-primary' : 'btn-secondary'}`}
                  onClick={() => toggleAllergen(opt.code)}
                >
                  {opt.label}
                </button>
              ))}
            </div>
          </div>

          <button type="submit" className="btn btn-primary" disabled={loading}>
            {loading ? '처리 중...' : '질문하기'}
          </button>
        </form>
      </div>

      {/* 빠른 질문 */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h4>자주 묻는 질문</h4>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          {quickQuestions.map((q, idx) => (
            <button
              key={idx}
              className="btn btn-secondary btn-sm"
              onClick={() => handleQuickQuestion(q)}
            >
              {q}
            </button>
          ))}
        </div>
      </div>

      {/* 답변 */}
      {answer && (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <h3>답변</h3>
          <div style={{
            padding: '1rem',
            background: '#f8f9fa',
            borderRadius: '8px',
            marginBottom: '1rem'
          }}>
            <p>{answer.answer}</p>
            {answer.confidence && (
              <p style={{ color: '#666', fontSize: '0.875rem', marginTop: '0.5rem' }}>
                신뢰도: {(answer.confidence * 100).toFixed(0)}%
              </p>
            )}
          </div>

          {/* 관련 논문 */}
          {answer.related_papers?.length > 0 && (
            <>
              <h4>참고 논문</h4>
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
                {answer.related_papers.map((paper) => (
                  <div key={paper.id} style={{
                    padding: '0.75rem',
                    border: '1px solid #eee',
                    borderRadius: '6px'
                  }}>
                    <p style={{ fontWeight: '600', marginBottom: '0.25rem' }}>{paper.title}</p>
                    <p style={{ fontSize: '0.875rem', color: '#666' }}>
                      {paper.authors} | {paper.journal} ({paper.year})
                    </p>
                    {paper.url && (
                      <a href={paper.url} target="_blank" rel="noopener noreferrer" style={{ fontSize: '0.875rem' }}>
                        원문 보기
                      </a>
                    )}
                  </div>
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* 질문 히스토리 */}
      {history.length > 0 && (
        <div className="card">
          <h3>최근 질문</h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
            {history.map((item, idx) => (
              <div key={idx} style={{
                padding: '1rem',
                border: '1px solid #eee',
                borderRadius: '8px'
              }}>
                <p style={{ fontWeight: '600', marginBottom: '0.5rem' }}>
                  Q: {item.question}
                </p>
                <p style={{ color: '#666', fontSize: '0.9rem' }}>
                  A: {item.answer.answer.substring(0, 200)}...
                </p>
                <p style={{ fontSize: '0.75rem', color: '#888', marginTop: '0.5rem' }}>
                  {item.timestamp.toLocaleString('ko-KR')}
                </p>
              </div>
            ))}
          </div>
        </div>
      )}

      <style>{`
        .btn-sm {
          padding: 0.25rem 0.75rem;
          font-size: 0.875rem;
        }
      `}</style>
    </div>
  );
}

export default QAPage;
