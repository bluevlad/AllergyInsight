import React, { useState } from 'react';
import { searchApi } from '../services/api';

function PapersPage() {
  const [papers, setPapers] = useState([]);
  const [selectedPaper, setSelectedPaper] = useState(null);
  const [searchQuery, setSearchQuery] = useState('');
  const [loading, setLoading] = useState(false);

  // 로컬 스토리지에서 저장된 논문 불러오기 (선택사항)
  const [savedPapers, setSavedPapers] = useState(() => {
    try {
      const saved = localStorage.getItem('savedPapers');
      return saved ? JSON.parse(saved) : [];
    } catch {
      return [];
    }
  });

  const handleSearch = async () => {
    if (!searchQuery.trim()) return;

    setLoading(true);
    try {
      const result = await searchApi.search(searchQuery, {
        includeCrossReactivity: true,
        maxResults: 50,
      });
      setPapers(result.papers || []);
    } catch (err) {
      console.error('Search failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const handleSavePaper = (paper) => {
    const isAlreadySaved = savedPapers.some((p) => p.source_id === paper.source_id);
    if (isAlreadySaved) {
      // 저장 취소
      const updated = savedPapers.filter((p) => p.source_id !== paper.source_id);
      setSavedPapers(updated);
      localStorage.setItem('savedPapers', JSON.stringify(updated));
    } else {
      // 저장
      const updated = [...savedPapers, paper];
      setSavedPapers(updated);
      localStorage.setItem('savedPapers', JSON.stringify(updated));
    }
  };

  const isPaperSaved = (paper) => {
    return savedPapers.some((p) => p.source_id === paper.source_id);
  };

  const formatAbstract = (abstract) => {
    if (!abstract) return '초록 없음';
    return abstract.length > 300 ? abstract.substring(0, 300) + '...' : abstract;
  };

  return (
    <div>
      <h2 style={{ marginBottom: '1.5rem' }}>📄 논문 목록</h2>

      {/* 검색 바 */}
      <div className="card">
        <div className="input-group" style={{ marginBottom: 0 }}>
          <input
            type="text"
            className="input"
            placeholder="알러지 항원 또는 키워드로 검색 (예: peanut, milk allergy)"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
          />
          <button className="btn btn-primary" onClick={handleSearch} disabled={loading}>
            {loading ? '검색 중...' : '검색'}
          </button>
        </div>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1.5rem' }}>
        {/* 왼쪽: 논문 목록 */}
        <div>
          {/* 저장된 논문 */}
          {savedPapers.length > 0 && (
            <div className="card">
              <div className="card-header">
                <h3 className="card-title">⭐ 저장된 논문 ({savedPapers.length})</h3>
              </div>
              <div style={{ maxHeight: '200px', overflowY: 'auto' }}>
                {savedPapers.map((paper, idx) => (
                  <div
                    key={idx}
                    style={{
                      padding: '0.75rem',
                      borderBottom: '1px solid #eee',
                      cursor: 'pointer',
                      background: selectedPaper?.source_id === paper.source_id ? '#f5f5f5' : 'white',
                    }}
                    onClick={() => setSelectedPaper(paper)}
                  >
                    <div style={{ fontSize: '0.875rem', fontWeight: '500' }}>
                      {paper.title.substring(0, 60)}...
                    </div>
                    <div style={{ fontSize: '0.75rem', color: '#666' }}>
                      {paper.year || 'N/A'} | {paper.source}
                    </div>
                  </div>
                ))}
              </div>
            </div>
          )}

          {/* 검색 결과 */}
          <div className="card">
            <div className="card-header">
              <h3 className="card-title">검색 결과 ({papers.length})</h3>
            </div>

            {papers.length === 0 && !loading && (
              <div style={{ textAlign: 'center', padding: '2rem', color: '#666' }}>
                <div style={{ fontSize: '2rem', marginBottom: '0.5rem' }}>🔍</div>
                <p>검색어를 입력하고 검색 버튼을 클릭하세요.</p>
              </div>
            )}

            {loading && (
              <div className="loading">
                <div className="spinner"></div>
              </div>
            )}

            <div style={{ maxHeight: '500px', overflowY: 'auto' }}>
              {papers.map((paper, idx) => (
                <div
                  key={idx}
                  style={{
                    padding: '1rem',
                    borderBottom: '1px solid #eee',
                    cursor: 'pointer',
                    background: selectedPaper?.source_id === paper.source_id ? '#f0f7ff' : 'white',
                  }}
                  onClick={() => setSelectedPaper(paper)}
                >
                  <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                    <div style={{ flex: 1 }}>
                      <div style={{ fontWeight: '500', marginBottom: '0.25rem' }}>
                        {paper.title}
                      </div>
                      <div style={{ fontSize: '0.75rem', color: '#666' }}>
                        {paper.authors?.slice(0, 2).join(', ')}
                        {paper.authors?.length > 2 && ' et al.'}
                        {paper.year && ` (${paper.year})`}
                      </div>
                    </div>
                    <button
                      className="btn btn-secondary"
                      style={{ padding: '0.25rem 0.5rem', fontSize: '0.75rem' }}
                      onClick={(e) => {
                        e.stopPropagation();
                        handleSavePaper(paper);
                      }}
                    >
                      {isPaperSaved(paper) ? '⭐' : '☆'}
                    </button>
                  </div>
                  <div style={{ marginTop: '0.5rem', display: 'flex', gap: '0.5rem' }}>
                    <span className={`badge ${paper.source === 'pubmed' ? 'badge-info' : 'badge-success'}`}>
                      {paper.source === 'pubmed' ? 'PubMed' : 'S2'}
                    </span>
                    {paper.pdf_url && <span className="badge badge-warning">PDF</span>}
                    {paper.citation_count && (
                      <span className="badge badge-secondary">인용 {paper.citation_count}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        </div>

        {/* 오른쪽: 논문 상세 */}
        <div className="card" style={{ position: 'sticky', top: '1rem', height: 'fit-content' }}>
          {selectedPaper ? (
            <div>
              <div className="card-header">
                <h3 className="card-title">논문 상세</h3>
                <button
                  className="btn btn-secondary"
                  style={{ padding: '0.25rem 0.5rem' }}
                  onClick={() => handleSavePaper(selectedPaper)}
                >
                  {isPaperSaved(selectedPaper) ? '⭐ 저장됨' : '☆ 저장'}
                </button>
              </div>

              <h4 style={{ marginBottom: '1rem', lineHeight: '1.4' }}>{selectedPaper.title}</h4>

              <div style={{ marginBottom: '1rem' }}>
                <div style={{ fontSize: '0.75rem', color: '#666', marginBottom: '0.25rem' }}>저자</div>
                <div style={{ fontSize: '0.875rem' }}>
                  {selectedPaper.authors?.join(', ') || '저자 정보 없음'}
                </div>
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem', marginBottom: '1rem' }}>
                <div>
                  <div style={{ fontSize: '0.75rem', color: '#666', marginBottom: '0.25rem' }}>연도</div>
                  <div>{selectedPaper.year || 'N/A'}</div>
                </div>
                <div>
                  <div style={{ fontSize: '0.75rem', color: '#666', marginBottom: '0.25rem' }}>출처</div>
                  <span className={`badge ${selectedPaper.source === 'pubmed' ? 'badge-info' : 'badge-success'}`}>
                    {selectedPaper.source === 'pubmed' ? 'PubMed' : 'Semantic Scholar'}
                  </span>
                </div>
              </div>

              {selectedPaper.journal && (
                <div style={{ marginBottom: '1rem' }}>
                  <div style={{ fontSize: '0.75rem', color: '#666', marginBottom: '0.25rem' }}>저널</div>
                  <div style={{ fontSize: '0.875rem' }}>{selectedPaper.journal}</div>
                </div>
              )}

              <div style={{ marginBottom: '1rem' }}>
                <div style={{ fontSize: '0.75rem', color: '#666', marginBottom: '0.25rem' }}>초록</div>
                <div style={{ fontSize: '0.875rem', lineHeight: '1.6', color: '#444' }}>
                  {selectedPaper.abstract || '초록 없음'}
                </div>
              </div>

              {selectedPaper.keywords?.length > 0 && (
                <div style={{ marginBottom: '1rem' }}>
                  <div style={{ fontSize: '0.75rem', color: '#666', marginBottom: '0.25rem' }}>키워드</div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.25rem' }}>
                    {selectedPaper.keywords.slice(0, 10).map((kw, i) => (
                      <span key={i} className="badge badge-secondary" style={{ background: '#f0f0f0', color: '#666' }}>
                        {kw}
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* 링크 */}
              <div style={{ display: 'flex', gap: '0.5rem', marginTop: '1.5rem' }}>
                {selectedPaper.doi && (
                  <a
                    href={`https://doi.org/${selectedPaper.doi}`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-primary"
                  >
                    DOI 링크
                  </a>
                )}
                {selectedPaper.source_id && selectedPaper.source === 'pubmed' && (
                  <a
                    href={`https://pubmed.ncbi.nlm.nih.gov/${selectedPaper.source_id}/`}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-secondary"
                  >
                    PubMed
                  </a>
                )}
                {selectedPaper.pdf_url && (
                  <a
                    href={selectedPaper.pdf_url}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="btn btn-secondary"
                  >
                    PDF 다운로드
                  </a>
                )}
              </div>
            </div>
          ) : (
            <div style={{ textAlign: 'center', padding: '3rem', color: '#666' }}>
              <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📖</div>
              <p>논문을 선택하면 상세 정보가 표시됩니다.</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default PapersPage;
