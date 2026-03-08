/**
 * Keyword Trend Page
 *
 * 카테고리별 키워드 트렌드를 표시합니다.
 */
import React, { useState, useEffect } from 'react';
import { analyticsApi } from '../services/analyticsApi';

const KeywordTrendPage = () => {
  const [keywords, setKeywords] = useState([]);
  const [categories, setCategories] = useState([]);
  const [selectedCategory, setSelectedCategory] = useState('');
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadKeywords();
  }, []);

  const loadKeywords = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await analyticsApi.getKeywordsOverview();
      const items = Array.isArray(data) ? data : [];
      setKeywords(items);

      // Extract unique categories
      const cats = [...new Set(items.map((k) => k.category).filter(Boolean))];
      setCategories(cats);
    } catch (err) {
      console.error('Keywords load failed:', err);
      setError('키워드 데이터를 불러올 수 없습니다.');
    } finally {
      setLoading(false);
    }
  };

  const filteredKeywords = selectedCategory
    ? keywords.filter((k) => k.category === selectedCategory)
    : keywords;

  const getTrendLabel = (direction) => {
    if (direction === 'up') return '[ + ] 상승';
    if (direction === 'down') return '[ - ] 하락';
    return '[ = ] 유지';
  };

  const getTrendColor = (direction) => {
    if (direction === 'up') return '#27ae60';
    if (direction === 'down') return '#e74c3c';
    return '#95a5a6';
  };

  if (loading) {
    return (
      <div className="kt-loading">
        <div className="kt-spinner" />
        <p>키워드 데이터 로딩 중...</p>
        <style>{`
          .kt-loading {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 300px;
            gap: 1rem;
          }
          .kt-spinner {
            width: 40px;
            height: 40px;
            border: 4px solid #e9ecef;
            border-top: 4px solid #1abc9c;
            border-radius: 50%;
            animation: kt-spin 1s linear infinite;
          }
          @keyframes kt-spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  return (
    <div className="keyword-trend-page">
      <h2>키워드 트렌드 분석</h2>

      {error && (
        <div className="kt-error-banner">
          <span>{error}</span>
          <button onClick={loadKeywords}>다시 시도</button>
        </div>
      )}

      {/* Category Filter */}
      <div className="kt-filter-section">
        <label htmlFor="category-select" className="kt-label">카테고리 필터</label>
        <select
          id="category-select"
          value={selectedCategory}
          onChange={(e) => setSelectedCategory(e.target.value)}
          className="kt-select"
        >
          <option value="">전체 카테고리</option>
          {categories.map((cat) => (
            <option key={cat} value={cat}>{cat}</option>
          ))}
        </select>
        <span className="kt-count">
          {filteredKeywords.length}건
        </span>
      </div>

      {/* Keywords Table */}
      {filteredKeywords.length > 0 ? (
        <div className="kt-table-section">
          <div className="kt-table-wrapper">
            <table className="kt-table">
              <thead>
                <tr>
                  <th>키워드</th>
                  <th>카테고리</th>
                  <th>언급 횟수</th>
                  <th>트렌드</th>
                  <th>변화율</th>
                </tr>
              </thead>
              <tbody>
                {filteredKeywords.map((kw, idx) => (
                  <tr key={kw.keyword || idx}>
                    <td className="kt-keyword-cell">{kw.keyword}</td>
                    <td>
                      {kw.category ? (
                        <span className="kt-category-badge">{kw.category}</span>
                      ) : (
                        '-'
                      )}
                    </td>
                    <td>
                      <span className="kt-mention-count">{kw.mention_count ?? 0}</span>
                    </td>
                    <td>
                      <span style={{ color: getTrendColor(kw.trend_direction), fontWeight: 600, fontSize: '0.85rem' }}>
                        {getTrendLabel(kw.trend_direction)}
                      </span>
                    </td>
                    <td>
                      {kw.change_rate != null ? (
                        <span style={{ color: getTrendColor(kw.trend_direction), fontWeight: 500 }}>
                          {kw.change_rate > 0 ? '+' : ''}{(kw.change_rate * 100).toFixed(1)}%
                        </span>
                      ) : (
                        '-'
                      )}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      ) : (
        !error && (
          <div className="kt-empty">
            <p>키워드 데이터가 없습니다.</p>
          </div>
        )
      )}

      <style>{`
        .keyword-trend-page {
          padding: 1rem;
        }

        .keyword-trend-page h2 {
          margin-bottom: 1.5rem;
          color: #333;
        }

        .kt-error-banner {
          display: flex;
          align-items: center;
          gap: 1rem;
          padding: 0.75rem 1rem;
          background: #fdecea;
          color: #c0392b;
          border-radius: 8px;
          margin-bottom: 1rem;
        }

        .kt-error-banner button {
          margin-left: auto;
          padding: 0.4rem 0.8rem;
          background: #e74c3c;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 0.8rem;
        }

        .kt-filter-section {
          background: white;
          border-radius: 12px;
          padding: 1.5rem;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          margin-bottom: 1.5rem;
          display: flex;
          align-items: center;
          gap: 1rem;
          flex-wrap: wrap;
        }

        .kt-label {
          font-weight: 600;
          color: #333;
          font-size: 0.9rem;
        }

        .kt-select {
          padding: 0.6rem 1rem;
          border: 2px solid #e0e0e0;
          border-radius: 8px;
          font-size: 0.9rem;
          background: white;
          cursor: pointer;
          min-width: 200px;
          transition: border-color 0.2s;
        }

        .kt-select:focus {
          outline: none;
          border-color: #1abc9c;
        }

        .kt-count {
          color: #888;
          font-size: 0.85rem;
        }

        .kt-table-section {
          background: white;
          border-radius: 12px;
          padding: 1.5rem;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          margin-bottom: 1.5rem;
        }

        .kt-table-wrapper {
          overflow-x: auto;
        }

        .kt-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 0.9rem;
        }

        .kt-table th,
        .kt-table td {
          padding: 0.75rem 1rem;
          text-align: left;
          border-bottom: 1px solid #eee;
        }

        .kt-table th {
          background: #f8f9fa;
          color: #555;
          font-weight: 600;
        }

        .kt-table tbody tr:hover {
          background: #f0faf8;
        }

        .kt-keyword-cell {
          font-weight: 500;
          color: #333;
        }

        .kt-category-badge {
          display: inline-block;
          padding: 0.2rem 0.6rem;
          background: #e8f8f5;
          color: #16a085;
          border-radius: 12px;
          font-size: 0.8rem;
          font-weight: 500;
        }

        .kt-mention-count {
          display: inline-block;
          padding: 0.15rem 0.5rem;
          background: #f0f0f0;
          border-radius: 8px;
          font-weight: 600;
          font-size: 0.85rem;
          color: #333;
        }

        .kt-empty {
          background: white;
          border-radius: 12px;
          padding: 2rem;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          text-align: center;
          color: #888;
        }
      `}</style>
    </div>
  );
};

export default KeywordTrendPage;
