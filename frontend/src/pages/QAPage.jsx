import React, { useState, useEffect, useRef } from 'react';
import { qaApi, allergenApi } from '../services/api';

function QAPage() {
  const [allergens, setAllergens] = useState({ food: [], inhalant: [] });
  const [selectedAllergen, setSelectedAllergen] = useState('peanut');
  const [question, setQuestion] = useState('');
  const [messages, setMessages] = useState([]);
  const [loading, setLoading] = useState(false);
  const [predefinedQuestions, setPredefinedQuestions] = useState({});
  const messagesEndRef = useRef(null);

  useEffect(() => {
    loadAllergens();
    loadQuestions('peanut');
  }, []);

  useEffect(() => {
    loadQuestions(selectedAllergen);
  }, [selectedAllergen]);

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadAllergens = async () => {
    try {
      const data = await allergenApi.getAll();
      setAllergens(data);
    } catch (err) {
      console.error('Failed to load allergens:', err);
    }
  };

  const loadQuestions = async (allergen) => {
    try {
      const data = await qaApi.getQuestions(allergen);
      setPredefinedQuestions(data.questions || {});
    } catch (err) {
      console.error('Failed to load questions:', err);
    }
  };

  const handleAsk = async (q = question) => {
    if (!q.trim()) return;

    const userMessage = { role: 'user', content: q };
    setMessages((prev) => [...prev, userMessage]);
    setQuestion('');
    setLoading(true);

    try {
      const response = await qaApi.ask(q, selectedAllergen);

      const assistantMessage = {
        role: 'assistant',
        content: response.answer,
        citations: response.citations,
        confidence: response.confidence,
        warnings: response.warnings,
      };

      setMessages((prev) => [...prev, assistantMessage]);
    } catch (err) {
      const errorMessage = {
        role: 'assistant',
        content: '죄송합니다. 응답을 생성하는 중 오류가 발생했습니다.',
        isError: true,
      };
      setMessages((prev) => [...prev, errorMessage]);
    } finally {
      setLoading(false);
    }
  };

  const handleKeyPress = (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleAsk();
    }
  };

  const handleQuickQuestion = (q) => {
    handleAsk(q);
  };

  const getAllergenKorean = (name) => {
    const all = [...allergens.food, ...allergens.inhalant];
    const found = all.find((a) => a.name === name);
    return found ? found.name_kr : name;
  };

  return (
    <div>
      <h2 style={{ marginBottom: '1.5rem' }}>❓ 논문 기반 Q&A</h2>

      <div className="qa-container">
        {/* 왼쪽: 채팅 영역 */}
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">💬 {getAllergenKorean(selectedAllergen)} 알러지 Q&A</h3>
            <select
              className="select"
              value={selectedAllergen}
              onChange={(e) => setSelectedAllergen(e.target.value)}
              style={{ width: 'auto' }}
            >
              <optgroup label="식품 알러지">
                {allergens.food.map((a) => (
                  <option key={a.name} value={a.name}>
                    {a.name_kr}
                  </option>
                ))}
              </optgroup>
              <optgroup label="흡입성 알러지">
                {allergens.inhalant.map((a) => (
                  <option key={a.name} value={a.name}>
                    {a.name_kr}
                  </option>
                ))}
              </optgroup>
            </select>
          </div>

          {/* 빠른 질문 */}
          <div className="quick-questions">
            {predefinedQuestions.symptoms?.slice(0, 1).map((q, i) => (
              <button key={i} className="quick-btn" onClick={() => handleQuickQuestion(q)}>
                증상
              </button>
            ))}
            {predefinedQuestions.severity?.slice(0, 1).map((q, i) => (
              <button key={i} className="quick-btn" onClick={() => handleQuickQuestion(q)}>
                위험성
              </button>
            ))}
            {predefinedQuestions.cross_reactivity?.slice(0, 1).map((q, i) => (
              <button key={i} className="quick-btn" onClick={() => handleQuickQuestion(q)}>
                교차반응
              </button>
            ))}
            {predefinedQuestions.treatment?.slice(0, 1).map((q, i) => (
              <button key={i} className="quick-btn" onClick={() => handleQuickQuestion(q)}>
                치료
              </button>
            ))}
          </div>

          {/* 메시지 목록 */}
          <div className="chat-messages">
            {messages.length === 0 && (
              <div style={{ textAlign: 'center', color: '#666', padding: '2rem' }}>
                <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🔬</div>
                <p>논문 기반으로 알러지에 대해 질문해보세요!</p>
                <p style={{ fontSize: '0.875rem' }}>모든 답변에 출처가 포함됩니다.</p>
              </div>
            )}

            {messages.map((msg, idx) => (
              <div key={idx} className={`message ${msg.role}`}>
                <div className="message-header">
                  {msg.role === 'user' ? '👤 질문' : '🤖 답변'}
                </div>
                <div style={{ whiteSpace: 'pre-wrap' }}>{msg.content}</div>

                {/* 인용 정보 */}
                {msg.citations && msg.citations.length > 0 && (
                  <div style={{ marginTop: '1rem' }}>
                    <div style={{ fontSize: '0.75rem', fontWeight: '600', color: '#666', marginBottom: '0.5rem' }}>
                      📚 출처 ({msg.citations.length}개)
                    </div>
                    {msg.citations.slice(0, 3).map((citation, cidx) => (
                      <div key={cidx} className="citation">
                        <div className="citation-title">{citation.paper_title}</div>
                        <div className="citation-meta">
                          {citation.format_short}
                          {citation.doi && (
                            <a
                              href={`https://doi.org/${citation.doi}`}
                              target="_blank"
                              rel="noopener noreferrer"
                              className="citation-link"
                              style={{ marginLeft: '0.5rem' }}
                            >
                              DOI 링크
                            </a>
                          )}
                        </div>
                      </div>
                    ))}
                  </div>
                )}

                {/* 신뢰도 */}
                {msg.confidence !== undefined && (
                  <div style={{ marginTop: '0.5rem', fontSize: '0.75rem', color: '#666' }}>
                    신뢰도: {(msg.confidence * 100).toFixed(0)}%
                  </div>
                )}

                {/* 주의사항 */}
                {msg.warnings && msg.warnings.length > 0 && (
                  <div style={{ marginTop: '0.5rem', padding: '0.5rem', background: '#fff3e0', borderRadius: '4px', fontSize: '0.75rem' }}>
                    {msg.warnings.map((w, widx) => (
                      <div key={widx}>⚠️ {w}</div>
                    ))}
                  </div>
                )}
              </div>
            ))}

            {loading && (
              <div className="message assistant">
                <div className="message-header">🤖 답변</div>
                <div className="loading" style={{ justifyContent: 'flex-start', padding: '0.5rem 0' }}>
                  <div className="spinner" style={{ width: '20px', height: '20px' }}></div>
                  <span style={{ marginLeft: '0.5rem', color: '#666' }}>논문 검색 중...</span>
                </div>
              </div>
            )}

            <div ref={messagesEndRef} />
          </div>

          {/* 입력 영역 */}
          <div className="input-group" style={{ marginTop: '1rem', marginBottom: 0 }}>
            <input
              type="text"
              className="input"
              placeholder="질문을 입력하세요..."
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              onKeyPress={handleKeyPress}
              disabled={loading}
            />
            <button
              className="btn btn-primary"
              onClick={() => handleAsk()}
              disabled={loading || !question.trim()}
            >
              전송
            </button>
          </div>
        </div>

        {/* 오른쪽: 정보 패널 */}
        <div>
          {/* 알러지 정보 */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">ℹ️ {getAllergenKorean(selectedAllergen)} 알러지</h3>
            </div>
            <p style={{ color: '#666', fontSize: '0.875rem' }}>
              {selectedAllergen === 'peanut' && '땅콩 알러지는 가장 흔한 식품 알러지 중 하나로, 아나필락시스를 유발할 수 있습니다.'}
              {selectedAllergen === 'milk' && '우유 알러지는 영유아에서 가장 흔하며, 대부분 성장하면서 호전됩니다.'}
              {selectedAllergen === 'egg' && '계란 알러지는 소아에서 두 번째로 흔한 식품 알러지입니다.'}
              {selectedAllergen === 'wheat' && '밀 알러지는 글루텐 불내증과 다르며, 면역 반응을 일으킵니다.'}
              {!['peanut', 'milk', 'egg', 'wheat'].includes(selectedAllergen) &&
                `${getAllergenKorean(selectedAllergen)} 알러지에 대한 정보를 검색해보세요.`}
            </p>
          </div>

          {/* 질문 예시 */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">💡 질문 예시</h3>
            </div>
            <ul style={{ listStyle: 'none', fontSize: '0.875rem' }}>
              <li style={{ padding: '0.5rem 0', borderBottom: '1px solid #eee' }}>
                "주요 증상은 무엇인가요?"
              </li>
              <li style={{ padding: '0.5rem 0', borderBottom: '1px solid #eee' }}>
                "얼마나 위험한가요?"
              </li>
              <li style={{ padding: '0.5rem 0', borderBottom: '1px solid #eee' }}>
                "교차 반응이 있는 음식은?"
              </li>
              <li style={{ padding: '0.5rem 0', borderBottom: '1px solid #eee' }}>
                "응급 상황 대처 방법은?"
              </li>
              <li style={{ padding: '0.5rem 0' }}>
                "증상 발현 시간은?"
              </li>
            </ul>
          </div>

          {/* 안내 */}
          <div className="card" style={{ background: '#e3f2fd' }}>
            <p style={{ fontSize: '0.75rem', color: '#1565c0' }}>
              ℹ️ 모든 답변은 PubMed 및 Semantic Scholar의 학술 논문을 기반으로 합니다.
              정확한 진단과 치료는 반드시 전문 의료진과 상담하세요.
            </p>
          </div>
        </div>
      </div>
    </div>
  );
}

export default QAPage;
