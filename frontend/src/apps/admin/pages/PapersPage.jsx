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
                  {paper.created_at && (
                    <span className="collected">수집: {formatDateTime(paper.created_at)}</span>
                  )}
                </div>

                {/* 원본 링크 */}
                {(paper.pmid || paper.doi || paper.url) && (
                  <div className="paper-links">
                    {paper.pmid && (
                      <a href={`https://pubmed.ncbi.nlm.nih.gov/${paper.pmid}`} target="_blank" rel="noopener noreferrer" className="link-btn pubmed">
                        PubMed
                      </a>
                    )}
                    {paper.doi && (
                      <a href={`https://doi.org/${paper.doi}`} target="_blank" rel="noopener noreferrer" className="link-btn doi">
                        DOI
                      </a>
                    )}
                    {paper.url && !paper.pmid && !paper.doi && (
                      <a href={paper.url} target="_blank" rel="noopener noreferrer" className="link-btn url">
                        원본 보기
                      </a>
                    )}
                  </div>
                )}

                {/* 수집 근거 */}
                {(paper.collection_reason || (paper.allergen_links && paper.allergen_links.length > 0)) && (
                  <div className="paper-collection-info">
                    {paper.allergen_links && paper.allergen_links.length > 0 && (
                      <div className="allergen-tags">
                        {paper.allergen_links.map((link, idx) => (
                          <span key={idx} className={`allergen-tag ${link.link_type}`}>
                            {link.allergen_name || link.allergen_code}
                            <span className="link-type">{getLinkTypeName(link.link_type)}</span>
                          </span>
                        ))}
                      </div>
                    )}
                    {paper.collection_reason && (
                      <div className="collection-reason">{paper.collection_reason}</div>
                    )}
                  </div>
                )}

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

        .collected {
          color: #999;
          font-size: 0.8rem;
        }

        .collected::before {
          content: '🕐';
        }

        .paper-links {
          display: flex;
          gap: 0.5rem;
          margin-bottom: 0.75rem;
        }

        .link-btn {
          display: inline-block;
          padding: 0.25rem 0.625rem;
          border-radius: 4px;
          font-size: 0.75rem;
          font-weight: 500;
          text-decoration: none;
          transition: opacity 0.2s;
        }

        .link-btn:hover {
          opacity: 0.8;
        }

        .link-btn.pubmed {
          background: #1a5276;
          color: white;
        }

        .link-btn.doi {
          background: #f39c12;
          color: white;
        }

        .link-btn.url {
          background: #7f8c8d;
          color: white;
        }

        .paper-collection-info {
          background: #f8f9fa;
          border-radius: 6px;
          padding: 0.625rem 0.875rem;
          margin-bottom: 0.75rem;
          border-left: 3px solid #667eea;
        }

        .allergen-tags {
          display: flex;
          flex-wrap: wrap;
          gap: 0.375rem;
          margin-bottom: 0.375rem;
        }

        .allergen-tag {
          display: inline-flex;
          align-items: center;
          gap: 0.25rem;
          padding: 0.2rem 0.5rem;
          border-radius: 12px;
          font-size: 0.7rem;
          font-weight: 500;
          background: #e8eaf6;
          color: #283593;
        }

        .allergen-tag.cross_reactivity {
          background: #fce4ec;
          color: #c62828;
        }

        .allergen-tag.symptom {
          background: #fff3e0;
          color: #e65100;
        }

        .allergen-tag.dietary {
          background: #e8f5e9;
          color: #2e7d32;
        }

        .allergen-tag.emergency {
          background: #ffebee;
          color: #b71c1c;
        }

        .allergen-tag .link-type {
          font-size: 0.625rem;
          opacity: 0.75;
        }

        .allergen-tag .link-type::before {
          content: '·';
          margin-right: 0.125rem;
        }

        .collection-reason {
          font-size: 0.75rem;
          color: #666;
          line-height: 1.4;
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

const formatDateTime = (dateStr) => {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleDateString('ko-KR') + ' ' + d.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
};

const getSourceName = (source) => {
  const sources = {
    pubmed: 'PubMed',
    semantic_scholar: 'Semantic Scholar',
    manual: '직접 입력',
  };
  return sources[source] || source;
};

const getLinkTypeName = (type) => {
  const types = {
    symptom: '증상',
    dietary: '식이',
    cross_reactivity: '교차반응',
    substitute: '대체식품',
    emergency: '응급',
    management: '관리',
    general: '일반',
  };
  return types[type] || type;
};

export default PapersPage;
