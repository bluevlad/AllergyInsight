/**
 * Papers Management Page
 */
import React, { useState, useEffect } from 'react';
import { adminApi } from '../services/adminApi';

const PapersPage = () => {
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [sourceFilter, setSourceFilter] = useState('');
  const [guidelineOnly, setGuidelineOnly] = useState(false);
  const pageSize = 20;

  useEffect(() => {
    loadPapers();
  }, [page, sourceFilter, guidelineOnly]);

  const loadPapers = async () => {
    try {
      setLoading(true);
      const params = { page, page_size: pageSize };
      if (search) params.search = search;
      if (sourceFilter) params.source = sourceFilter;
      if (guidelineOnly) params.is_guideline = true;

      const response = await adminApi.papers.list(params);
      setPapers(response.items || []);
      setTotal(response.total || 0);
    } catch (err) {
      console.error('Papers load failed:', err);
      setError('논문 목록 로딩 실패');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    loadPapers();
  };

  const handleDelete = async (id) => {
    if (!window.confirm('정말 삭제하시겠습니까?')) return;

    try {
      await adminApi.papers.delete(id);
      loadPapers();
    } catch (err) {
      alert('삭제 실패');
    }
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="papers-page">
      <h2>논문 관리</h2>

      {/* 검색 및 필터 */}
      <div className="toolbar">
        <form onSubmit={handleSearch} className="search-form">
          <input
            type="text"
            placeholder="제목, 저자, 저널 검색..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button type="submit">검색</button>
        </form>
        <select
          value={sourceFilter}
          onChange={(e) => { setSourceFilter(e.target.value); setPage(1); }}
        >
          <option value="">전체 출처</option>
          <option value="pubmed">PubMed</option>
          <option value="semantic_scholar">Semantic Scholar</option>
          <option value="manual">직접 입력</option>
        </select>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={guidelineOnly}
            onChange={(e) => { setGuidelineOnly(e.target.checked); setPage(1); }}
          />
          가이드라인만
        </label>
      </div>

      {/* 논문 목록 */}
      {loading ? (
        <div className="loading">로딩 중...</div>
      ) : error ? (
        <div className="error">{error}</div>
      ) : (
        <>
          <div className="papers-list">
            {papers.map((paper) => (
              <div key={paper.id} className="paper-card">
                <div className="paper-header">
                  <h3 className="paper-title">{paper.title}</h3>
                  <div className="paper-badges">
                    {paper.is_guideline && (
                      <span className="badge guideline">가이드라인</span>
                    )}
                    {paper.evidence_level && (
                      <span className="badge evidence">{paper.evidence_level}</span>
                    )}
                    {paper.source && (
                      <span className="badge source">{getSourceName(paper.source)}</span>
                    )}
                  </div>
                </div>
                <div className="paper-meta">
                  {paper.authors && (
                    <span className="authors">{paper.authors}</span>
                  )}
                  {paper.journal && (
                    <span className="journal">{paper.journal}</span>
                  )}
                  {paper.year && (
                    <span className="year">{paper.year}</span>
                  )}
                </div>
                <div className="paper-actions">
                  <button
                    onClick={() => handleDelete(paper.id)}
                    className="btn-delete"
                  >
                    삭제
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* 페이지네이션 */}
          <div className="pagination">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
            >
              이전
            </button>
            <span>
              {page} / {totalPages} (총 {total}건)
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
            >
              다음
            </button>
          </div>
        </>
      )}

      <style>{`
        .papers-page {
          padding: 1rem;
        }

        .papers-page h2 {
          margin-bottom: 1.5rem;
        }

        .toolbar {
          display: flex;
          gap: 1rem;
          margin-bottom: 1.5rem;
          flex-wrap: wrap;
          align-items: center;
        }

        .search-form {
          display: flex;
          gap: 0.5rem;
          flex: 1;
          min-width: 300px;
        }

        .search-form input {
          flex: 1;
          padding: 0.5rem 1rem;
          border: 1px solid #ddd;
          border-radius: 6px;
        }

        .search-form button {
          padding: 0.5rem 1rem;
          background: #667eea;
          color: white;
          border: none;
          border-radius: 6px;
          cursor: pointer;
        }

        .toolbar select {
          padding: 0.5rem 1rem;
          border: 1px solid #ddd;
          border-radius: 6px;
          background: white;
        }

        .checkbox-label {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          cursor: pointer;
        }

        .papers-list {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .paper-card {
          background: white;
          border-radius: 8px;
          padding: 1.25rem;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .paper-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 1rem;
          margin-bottom: 0.75rem;
        }

        .paper-title {
          margin: 0;
          font-size: 1rem;
          font-weight: 600;
          color: #333;
          flex: 1;
        }

        .paper-badges {
          display: flex;
          gap: 0.5rem;
          flex-shrink: 0;
        }

        .badge {
          padding: 0.25rem 0.5rem;
          border-radius: 4px;
          font-size: 0.75rem;
          font-weight: 500;
        }

        .badge.guideline {
          background: #e8f5e9;
          color: #2e7d32;
        }

        .badge.evidence {
          background: #e3f2fd;
          color: #1565c0;
        }

        .badge.source {
          background: #f3e5f5;
          color: #7b1fa2;
        }

        .paper-meta {
          display: flex;
          flex-wrap: wrap;
          gap: 1rem;
          font-size: 0.875rem;
          color: #666;
          margin-bottom: 0.75rem;
        }

        .paper-meta span::before {
          margin-right: 0.25rem;
        }

        .authors::before {
          content: '👤';
        }

        .journal::before {
          content: '📖';
        }

        .year::before {
          content: '📅';
        }

        .paper-actions {
          display: flex;
          justify-content: flex-end;
          gap: 0.5rem;
        }

        .btn-delete {
          padding: 0.375rem 0.75rem;
          background: #e74c3c;
          color: white;
          border: none;
          border-radius: 4px;
          font-size: 0.75rem;
          cursor: pointer;
        }

        .btn-delete:hover {
          background: #c0392b;
        }

        .pagination {
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 1rem;
          margin-top: 1.5rem;
        }

        .pagination button {
          padding: 0.5rem 1rem;
          border: 1px solid #ddd;
          border-radius: 6px;
          background: white;
          cursor: pointer;
        }

        .pagination button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .loading, .error {
          text-align: center;
          padding: 2rem;
          color: #666;
        }
      `}</style>
    </div>
  );
};

const getSourceName = (source) => {
  const sources = {
    pubmed: 'PubMed',
    semantic_scholar: 'Semantic Scholar',
    manual: '직접 입력',
  };
  return sources[source] || source;
};

export default PapersPage;
