import React, { useState, useEffect } from 'react';
import { searchApi, allergenApi } from '../services/api';

function SearchPage() {
  const [allergens, setAllergens] = useState({ food: [], inhalant: [] });
  const [selectedAllergen, setSelectedAllergen] = useState('peanut');
  const [includeCrossReactivity, setIncludeCrossReactivity] = useState(true);
  const [maxResults, setMaxResults] = useState(20);
  const [loading, setLoading] = useState(false);
  const [results, setResults] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadAllergens();
  }, []);

  const loadAllergens = async () => {
    try {
      const data = await allergenApi.getAll();
      setAllergens(data);
    } catch (err) {
      console.error('Failed to load allergens:', err);
    }
  };

  const handleSearch = async () => {
    try {
      setLoading(true);
      setError(null);

      const data = await searchApi.search(selectedAllergen, {
        includeCrossReactivity,
        maxResults,
      });

      setResults(data);
    } catch (err) {
      setError('검색 중 오류가 발생했습니다.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div>
      <h2 style={{ marginBottom: '1.5rem' }}>🔍 논문 검색</h2>

      {/* 검색 폼 */}
      <div className="card">
        <div className="card-header">
          <h3 className="card-title">검색 조건</h3>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '1rem' }}>
          {/* 알러지 항원 선택 */}
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
              알러지 항원
            </label>
            <select
              className="select"
              value={selectedAllergen}
              onChange={(e) => setSelectedAllergen(e.target.value)}
              style={{ width: '100%' }}
            >
              <optgroup label="식품 알러지">
                {allergens.food.map((a) => (
                  <option key={a.name} value={a.name}>
                    {a.name_kr} ({a.name})
                  </option>
                ))}
              </optgroup>
              <optgroup label="흡입성 알러지">
                {allergens.inhalant.map((a) => (
                  <option key={a.name} value={a.name}>
                    {a.name_kr} ({a.name})
                  </option>
                ))}
              </optgroup>
            </select>
          </div>

          {/* 최대 결과 수 */}
          <div>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontWeight: '500' }}>
              최대 결과 수
            </label>
            <select
              className="select"
              value={maxResults}
              onChange={(e) => setMaxResults(Number(e.target.value))}
              style={{ width: '100%' }}
            >
              <option value={10}>10개</option>
              <option value={20}>20개</option>
              <option value={50}>50개</option>
              <option value={100}>100개</option>
            </select>
          </div>

          {/* 교차 반응 포함 */}
          <div style={{ display: 'flex', alignItems: 'center', paddingTop: '1.5rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', cursor: 'pointer' }}>
              <input
                type="checkbox"
                checked={includeCrossReactivity}
                onChange={(e) => setIncludeCrossReactivity(e.target.checked)}
                style={{ marginRight: '0.5rem', width: '18px', height: '18px' }}
              />
              교차 반응 논문 포함
            </label>
          </div>
        </div>

        <div style={{ marginTop: '1.5rem' }}>
          <button
            className="btn btn-primary"
            onClick={handleSearch}
            disabled={loading}
          >
            {loading ? '검색 중...' : '🔍 검색'}
          </button>
        </div>
      </div>

      {/* 에러 메시지 */}
      {error && (
        <div className="card" style={{ background: '#ffebee', borderLeft: '4px solid #c62828' }}>
          <p style={{ color: '#c62828' }}>{error}</p>
        </div>
      )}

      {/* 검색 결과 */}
      {results && (
        <div className="card">
          <div className="card-header">
            <h3 className="card-title">검색 결과</h3>
            <span style={{ color: '#666' }}>
              {results.search_time_ms}ms | {results.total_found}개 논문
            </span>
          </div>

          {/* 통계 */}
          <div style={{ display: 'flex', gap: '1rem', marginBottom: '1rem', flexWrap: 'wrap' }}>
            <span className="badge badge-info">PubMed: {results.pubmed_count}개</span>
            <span className="badge badge-success">Semantic Scholar: {results.semantic_scholar_count}개</span>
            <span className="badge badge-warning">PDF 가능: {results.downloadable_count}개</span>
          </div>

          {/* 논문 목록 */}
          <div className="table-container">
            <table className="table">
              <thead>
                <tr>
                  <th style={{ width: '50%' }}>논문 제목</th>
                  <th>저자</th>
                  <th>연도</th>
                  <th>출처</th>
                  <th>링크</th>
                </tr>
              </thead>
              <tbody>
                {results.papers.map((paper, idx) => (
                  <tr key={idx}>
                    <td>
                      <div style={{ fontWeight: '500' }}>{paper.title}</div>
                      {paper.journal && (
                        <div style={{ fontSize: '0.75rem', color: '#666', marginTop: '0.25rem' }}>
                          {paper.journal}
                        </div>
                      )}
                    </td>
                    <td style={{ fontSize: '0.875rem' }}>
                      {paper.authors.slice(0, 2).join(', ')}
                      {paper.authors.length > 2 && '...'}
                    </td>
                    <td>{paper.year || '-'}</td>
                    <td>
                      <span className={`badge ${paper.source === 'pubmed' ? 'badge-info' : 'badge-success'}`}>
                        {paper.source === 'pubmed' ? 'PubMed' : 'S2'}
                      </span>
                    </td>
                    <td>
                      {paper.doi && (
                        <a
                          href={`https://doi.org/${paper.doi}`}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="citation-link"
                        >
                          DOI
                        </a>
                      )}
                      {paper.pdf_url && (
                        <a
                          href={paper.pdf_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          className="citation-link"
                          style={{ marginLeft: '0.5rem' }}
                        >
                          PDF
                        </a>
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* 검색 전 안내 */}
      {!results && !loading && (
        <div className="card" style={{ textAlign: 'center', padding: '3rem' }}>
          <div style={{ fontSize: '3rem', marginBottom: '1rem' }}>📚</div>
          <h3 style={{ marginBottom: '0.5rem' }}>논문 검색</h3>
          <p style={{ color: '#666' }}>
            알러지 항원을 선택하고 검색 버튼을 클릭하세요.
            <br />
            PubMed와 Semantic Scholar에서 관련 논문을 검색합니다.
          </p>
        </div>
      )}
    </div>
  );
}

export default SearchPage;
