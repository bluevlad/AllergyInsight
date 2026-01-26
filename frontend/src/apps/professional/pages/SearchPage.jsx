/**
 * Professional Search Page - 논문 검색
 */
import React, { useState } from 'react';
import { proApi } from '../services/proApi';

function SearchPage() {
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({
    allergen_code: '',
    link_type: '',
    paper_type: '',
    year_from: '',
    year_to: '',
    verified_only: true,
  });
  const [results, setResults] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [totalCount, setTotalCount] = useState(0);
  const pageSize = 20;

  const allergenOptions = [
    { code: '', label: '전체' },
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

  const linkTypeOptions = [
    { code: '', label: '전체' },
    { code: 'symptom', label: '증상' },
    { code: 'dietary', label: '식이' },
    { code: 'cross_reactivity', label: '교차반응' },
    { code: 'emergency', label: '응급' },
    { code: 'management', label: '관리' },
  ];

  const paperTypeOptions = [
    { code: '', label: '전체' },
    { code: 'research', label: '연구' },
    { code: 'review', label: '리뷰' },
    { code: 'guideline', label: '가이드라인' },
    { code: 'meta_analysis', label: '메타분석' },
  ];

  const handleSearch = async (e) => {
    e?.preventDefault();
    if (!searchQuery.trim()) {
      alert('검색어를 입력해주세요.');
      return;
    }

    try {
      setLoading(true);
      setError(null);
      const response = await proApi.research.search({
        query: searchQuery,
        allergen_code: filters.allergen_code || null,
        link_type: filters.link_type || null,
        paper_type: filters.paper_type || null,
        year_from: filters.year_from ? parseInt(filters.year_from) : null,
        year_to: filters.year_to ? parseInt(filters.year_to) : null,
        verified_only: filters.verified_only,
        page,
        size: pageSize,
      });
      setResults(response.items || []);
      setTotalCount(response.total || 0);
    } catch (err) {
      setError('검색에 실패했습니다.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handlePageChange = (newPage) => {
    setPage(newPage);
    handleSearch();
  };

  return (
    <div>
      <h2>논문 검색</h2>

      {/* 검색 폼 */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <form onSubmit={handleSearch}>
          <div className="form-group">
            <input
              type="text"
              placeholder="검색어를 입력하세요 (제목, 저자, 초록 내용)"
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              className="form-control"
              style={{ fontSize: '1.1rem' }}
            />
          </div>

          {/* 필터 */}
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(5, 1fr)', gap: '0.5rem', marginBottom: '1rem' }}>
            <select
              value={filters.allergen_code}
              onChange={(e) => setFilters({ ...filters, allergen_code: e.target.value })}
              className="form-control"
            >
              {allergenOptions.map(opt => (
                <option key={opt.code} value={opt.code}>{opt.label}</option>
              ))}
            </select>
            <select
              value={filters.link_type}
              onChange={(e) => setFilters({ ...filters, link_type: e.target.value })}
              className="form-control"
            >
              {linkTypeOptions.map(opt => (
                <option key={opt.code} value={opt.code}>{opt.label}</option>
              ))}
            </select>
            <select
              value={filters.paper_type}
              onChange={(e) => setFilters({ ...filters, paper_type: e.target.value })}
              className="form-control"
            >
              {paperTypeOptions.map(opt => (
                <option key={opt.code} value={opt.code}>{opt.label}</option>
              ))}
            </select>
            <input
              type="number"
              placeholder="시작 연도"
              value={filters.year_from}
              onChange={(e) => setFilters({ ...filters, year_from: e.target.value })}
              className="form-control"
              min="1990"
              max="2030"
            />
            <input
              type="number"
              placeholder="종료 연도"
              value={filters.year_to}
              onChange={(e) => setFilters({ ...filters, year_to: e.target.value })}
              className="form-control"
              min="1990"
              max="2030"
            />
          </div>

          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <input
                type="checkbox"
                checked={filters.verified_only}
                onChange={(e) => setFilters({ ...filters, verified_only: e.target.checked })}
              />
              검증된 논문만 표시
            </label>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? '검색 중...' : '검색'}
            </button>
          </div>
        </form>
      </div>

      {/* 에러 */}
      {error && (
        <div className="card" style={{ marginBottom: '1rem' }}>
          <p style={{ color: '#c62828' }}>{error}</p>
        </div>
      )}

      {/* 검색 결과 */}
      {results.length > 0 && (
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
            <h3>검색 결과 ({totalCount}건)</h3>
          </div>

          <div className="papers-list">
            {results.map((paper) => (
              <div key={paper.id} className="paper-item">
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                  <div style={{ flex: 1 }}>
                    <h4 style={{ marginBottom: '0.5rem' }}>
                      {paper.title}
                      {paper.is_verified && (
                        <span className="badge badge-success" style={{ marginLeft: '0.5rem' }}>검증됨</span>
                      )}
                    </h4>
                    {paper.title_kr && (
                      <p style={{ color: '#666', fontSize: '0.9rem', marginBottom: '0.5rem' }}>
                        {paper.title_kr}
                      </p>
                    )}
                    <p style={{ fontSize: '0.875rem', color: '#888' }}>
                      {paper.authors} | {paper.journal} ({paper.year})
                    </p>
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem' }}>
                    {paper.paper_type && (
                      <span className="badge badge-info">{paper.paper_type}</span>
                    )}
                    {paper.url && (
                      <a href={paper.url} target="_blank" rel="noopener noreferrer" className="btn btn-sm btn-secondary">
                        원문
                      </a>
                    )}
                  </div>
                </div>
              </div>
            ))}
          </div>

          {/* 페이지네이션 */}
          {totalCount > pageSize && (
            <div style={{ display: 'flex', justifyContent: 'center', gap: '0.5rem', marginTop: '1rem' }}>
              <button
                className="btn btn-secondary"
                disabled={page === 1}
                onClick={() => handlePageChange(page - 1)}
              >
                이전
              </button>
              <span style={{ padding: '0.5rem 1rem' }}>
                {page} / {Math.ceil(totalCount / pageSize)}
              </span>
              <button
                className="btn btn-secondary"
                disabled={page >= Math.ceil(totalCount / pageSize)}
                onClick={() => handlePageChange(page + 1)}
              >
                다음
              </button>
            </div>
          )}
        </div>
      )}

      {results.length === 0 && searchQuery && !loading && (
        <div className="card" style={{ textAlign: 'center' }}>
          <p>검색 결과가 없습니다.</p>
        </div>
      )}

      <style>{`
        .papers-list {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }
        .paper-item {
          padding: 1rem;
          border: 1px solid #eee;
          border-radius: 8px;
        }
        .paper-item:hover {
          background: #f8f9fa;
        }
        .btn-sm {
          padding: 0.25rem 0.5rem;
          font-size: 0.875rem;
        }
      `}</style>
    </div>
  );
}

export default SearchPage;
