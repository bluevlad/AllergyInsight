/**
 * Professional Papers Page - 논문 목록/관리
 */
import React, { useState, useEffect, useCallback } from 'react';
import { proApi } from '../services/proApi';

function PapersPage() {
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 20;

  // Filters
  const [filters, setFilters] = useState({
    allergen: '',
    link_type: '',
    paper_type: '',
    year: '',
    search: '',
    verified_only: false,
  });

  // Modal state
  const [showAddModal, setShowAddModal] = useState(false);
  const [selectedPaper, setSelectedPaper] = useState(null);

  const loadPapers = useCallback(async () => {
    try {
      setLoading(true);
      const params = {
        page,
        size: pageSize,
        verified_only: filters.verified_only,
      };
      if (filters.allergen) params.allergen = filters.allergen;
      if (filters.link_type) params.link_type = filters.link_type;
      if (filters.paper_type) params.paper_type = filters.paper_type;
      if (filters.year) params.year = parseInt(filters.year);
      if (filters.search) params.search = filters.search;

      const response = await proApi.research.listPapers(params);
      setPapers(response.items || []);
      setTotalCount(response.total || 0);
    } catch (err) {
      setError('논문 목록을 불러오는데 실패했습니다.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [page, filters]);

  useEffect(() => {
    loadPapers();
  }, [loadPapers]);

  const handleFilterChange = (key, value) => {
    setFilters(prev => ({ ...prev, [key]: value }));
    setPage(1);
  };

  const handleViewPaper = async (paperId) => {
    try {
      const paper = await proApi.research.getPaper(paperId);
      setSelectedPaper(paper);
    } catch (err) {
      console.error('논문 상세 조회 실패:', err);
      alert('논문 정보를 불러오는데 실패했습니다.');
    }
  };

  const getPaperTypeBadge = (type) => {
    const types = {
      research: { label: '연구', class: 'badge-info' },
      review: { label: '리뷰', class: 'badge-secondary' },
      guideline: { label: '가이드라인', class: 'badge-success' },
      meta_analysis: { label: '메타분석', class: 'badge-warning' },
    };
    const info = types[type] || { label: type, class: 'badge-secondary' };
    return <span className={`badge ${info.class}`}>{info.label}</span>;
  };

  return (
    <div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
        <h2>논문 목록</h2>
        <button className="btn btn-primary" onClick={() => setShowAddModal(true)}>
          + 논문 추가
        </button>
      </div>

      {/* 필터 */}
      <div className="card" style={{ marginBottom: '1rem' }}>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '0.5rem' }}>
          <input
            type="text"
            placeholder="검색..."
            value={filters.search}
            onChange={(e) => handleFilterChange('search', e.target.value)}
            className="form-control"
          />
          <select
            value={filters.allergen}
            onChange={(e) => handleFilterChange('allergen', e.target.value)}
            className="form-control"
          >
            <option value="">알러젠</option>
            <option value="peanut">땅콩</option>
            <option value="milk">우유</option>
            <option value="egg">계란</option>
            <option value="wheat">밀</option>
            <option value="soy">대두</option>
          </select>
          <select
            value={filters.paper_type}
            onChange={(e) => handleFilterChange('paper_type', e.target.value)}
            className="form-control"
          >
            <option value="">유형</option>
            <option value="research">연구</option>
            <option value="review">리뷰</option>
            <option value="guideline">가이드라인</option>
            <option value="meta_analysis">메타분석</option>
          </select>
          <input
            type="number"
            placeholder="연도"
            value={filters.year}
            onChange={(e) => handleFilterChange('year', e.target.value)}
            className="form-control"
            min="1990"
            max="2030"
          />
          <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
            <input
              type="checkbox"
              checked={filters.verified_only}
              onChange={(e) => handleFilterChange('verified_only', e.target.checked)}
            />
            검증된 논문만
          </label>
          <button className="btn btn-secondary" onClick={() => {
            setFilters({
              allergen: '', link_type: '', paper_type: '', year: '', search: '', verified_only: false
            });
            setPage(1);
          }}>
            초기화
          </button>
        </div>
      </div>

      {error && (
        <div className="card" style={{ marginBottom: '1rem' }}>
          <p style={{ color: '#c62828' }}>{error}</p>
          <button className="btn btn-primary" onClick={loadPapers}>다시 시도</button>
        </div>
      )}

      {/* 논문 목록 */}
      <div className="card">
        <div style={{ marginBottom: '1rem', color: '#666' }}>
          총 {totalCount}개의 논문
        </div>

        {loading ? (
          <div style={{ textAlign: 'center', padding: '2rem' }}>
            <div className="spinner"></div>
          </div>
        ) : (
          <>
            <div className="table-container">
              <table className="table">
                <thead>
                  <tr>
                    <th style={{ width: '40%' }}>제목</th>
                    <th>저자</th>
                    <th>저널</th>
                    <th>연도</th>
                    <th>유형</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {papers.map((paper) => (
                    <tr key={paper.id}>
                      <td>
                        <div>
                          {paper.title}
                          {paper.is_verified && (
                            <span className="badge badge-success" style={{ marginLeft: '0.5rem' }}>검증</span>
                          )}
                        </div>
                        {paper.title_kr && (
                          <div style={{ fontSize: '0.875rem', color: '#666' }}>{paper.title_kr}</div>
                        )}
                      </td>
                      <td style={{ fontSize: '0.875rem' }}>{paper.authors?.substring(0, 30)}...</td>
                      <td style={{ fontSize: '0.875rem' }}>{paper.journal}</td>
                      <td>{paper.year}</td>
                      <td>{getPaperTypeBadge(paper.paper_type)}</td>
                      <td>
                        <button className="btn btn-sm btn-secondary" onClick={() => handleViewPaper(paper.id)}>
                          상세
                        </button>
                      </td>
                    </tr>
                  ))}
                  {papers.length === 0 && (
                    <tr>
                      <td colSpan={6} style={{ textAlign: 'center', color: '#666' }}>
                        논문이 없습니다.
                      </td>
                    </tr>
                  )}
                </tbody>
              </table>
            </div>

            {/* 페이지네이션 */}
            {totalCount > pageSize && (
              <div style={{ display: 'flex', justifyContent: 'center', gap: '0.5rem', marginTop: '1rem' }}>
                <button className="btn btn-secondary" disabled={page === 1} onClick={() => setPage(p => p - 1)}>
                  이전
                </button>
                <span style={{ padding: '0.5rem 1rem' }}>
                  {page} / {Math.ceil(totalCount / pageSize)}
                </span>
                <button className="btn btn-secondary" disabled={page >= Math.ceil(totalCount / pageSize)} onClick={() => setPage(p => p + 1)}>
                  다음
                </button>
              </div>
            )}
          </>
        )}
      </div>

      {/* 논문 상세 모달 */}
      {selectedPaper && (
        <div className="modal-overlay" onClick={() => setSelectedPaper(null)}>
          <div className="modal-content" onClick={e => e.stopPropagation()}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
              <h3>{selectedPaper.title}</h3>
              <button className="btn btn-secondary" onClick={() => setSelectedPaper(null)}>닫기</button>
            </div>
            {selectedPaper.title_kr && (
              <p style={{ color: '#666' }}>{selectedPaper.title_kr}</p>
            )}
            <hr />
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
              <div>
                <p style={{ color: '#888', fontSize: '0.875rem' }}>저자</p>
                <p>{selectedPaper.authors}</p>
              </div>
              <div>
                <p style={{ color: '#888', fontSize: '0.875rem' }}>저널</p>
                <p>{selectedPaper.journal} ({selectedPaper.year})</p>
              </div>
              {selectedPaper.pmid && (
                <div>
                  <p style={{ color: '#888', fontSize: '0.875rem' }}>PMID</p>
                  <p>{selectedPaper.pmid}</p>
                </div>
              )}
              {selectedPaper.doi && (
                <div>
                  <p style={{ color: '#888', fontSize: '0.875rem' }}>DOI</p>
                  <p>{selectedPaper.doi}</p>
                </div>
              )}
            </div>
            {selectedPaper.abstract && (
              <>
                <hr />
                <p style={{ color: '#888', fontSize: '0.875rem' }}>초록</p>
                <p style={{ whiteSpace: 'pre-wrap' }}>{selectedPaper.abstract}</p>
              </>
            )}
            {selectedPaper.allergen_links?.length > 0 && (
              <>
                <hr />
                <p style={{ color: '#888', fontSize: '0.875rem' }}>알러젠 연결</p>
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {selectedPaper.allergen_links.map((link, idx) => (
                    <span key={idx} className="badge badge-info">
                      {link.allergen_code} - {link.link_type}
                      {link.specific_item && `: ${link.specific_item}`}
                    </span>
                  ))}
                </div>
              </>
            )}
            {selectedPaper.url && (
              <div style={{ marginTop: '1rem' }}>
                <a href={selectedPaper.url} target="_blank" rel="noopener noreferrer" className="btn btn-primary">
                  원문 보기
                </a>
              </div>
            )}
          </div>
        </div>
      )}

      <style>{`
        .btn-sm {
          padding: 0.25rem 0.5rem;
          font-size: 0.875rem;
        }
        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          justify-content: center;
          align-items: center;
          z-index: 1000;
        }
        .modal-content {
          background: white;
          padding: 2rem;
          border-radius: 12px;
          max-width: 800px;
          max-height: 80vh;
          overflow-y: auto;
          width: 90%;
        }
      `}</style>
    </div>
  );
}

export default PapersPage;
