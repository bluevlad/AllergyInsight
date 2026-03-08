/**
 * Allergen Trend Page
 *
 * 알러젠별 트렌드를 조회하고 표시합니다.
 */
import React, { useState, useEffect } from 'react';
import { analyticsApi } from '../services/analyticsApi';

const AllergenTrendPage = () => {
  const [allergens, setAllergens] = useState([]);
  const [selectedAllergen, setSelectedAllergen] = useState('');
  const [trendData, setTrendData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [trendLoading, setTrendLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadOverview();
  }, []);

  const loadOverview = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await analyticsApi.getOverview();
      setAllergens(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Overview load failed:', err);
      setError('알러젠 목록을 불러올 수 없습니다.');
    } finally {
      setLoading(false);
    }
  };

  const loadTrend = async (allergenCode) => {
    if (!allergenCode) {
      setTrendData([]);
      return;
    }
    try {
      setTrendLoading(true);
      setError(null);
      const data = await analyticsApi.getAllergenTrend(allergenCode, 12);
      setTrendData(Array.isArray(data) ? data : []);
    } catch (err) {
      console.error('Trend load failed:', err);
      setError('트렌드 데이터를 불러올 수 없습니다.');
      setTrendData([]);
    } finally {
      setTrendLoading(false);
    }
  };

  const handleAllergenChange = (e) => {
    const code = e.target.value;
    setSelectedAllergen(code);
    loadTrend(code);
  };

  if (loading) {
    return (
      <div className="at-loading">
        <div className="at-spinner" />
        <p>알러젠 목록 로딩 중...</p>
        <style>{`
          .at-loading {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 300px;
            gap: 1rem;
          }
          .at-spinner {
            width: 40px;
            height: 40px;
            border: 4px solid #e9ecef;
            border-top: 4px solid #1abc9c;
            border-radius: 50%;
            animation: at-spin 1s linear infinite;
          }
          @keyframes at-spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  return (
    <div className="allergen-trend-page">
      <h2>알러젠 트렌드 분석</h2>

      {error && (
        <div className="at-error-banner">
          <span>{error}</span>
          <button onClick={loadOverview}>다시 시도</button>
        </div>
      )}

      {/* Allergen Selector */}
      <div className="at-selector-section">
        <label htmlFor="allergen-select" className="at-label">알러젠 선택</label>
        <select
          id="allergen-select"
          value={selectedAllergen}
          onChange={handleAllergenChange}
          className="at-select"
        >
          <option value="">-- 알러젠을 선택하세요 --</option>
          {allergens.map((a, idx) => (
            <option key={a.allergen_code || idx} value={a.allergen_code}>
              {a.allergen_code} - {a.allergen_name || ''}
            </option>
          ))}
        </select>
      </div>

      {/* Trend Table */}
      {trendLoading && (
        <div className="at-loading-inline">
          <div className="at-spinner-small" />
          <span>트렌드 데이터 로딩 중...</span>
        </div>
      )}

      {!trendLoading && selectedAllergen && trendData.length > 0 && (
        <div className="at-trend-section">
          <h3>{selectedAllergen} 트렌드</h3>
          <div className="at-table-wrapper">
            <table className="at-table">
              <thead>
                <tr>
                  <th>기간</th>
                  <th>총 검사 수</th>
                  <th>양성률</th>
                  <th>평균 등급</th>
                </tr>
              </thead>
              <tbody>
                {trendData.map((row, idx) => (
                  <tr key={row.period || idx}>
                    <td>{row.period || '-'}</td>
                    <td>{row.total_tests ?? '-'}</td>
                    <td>
                      <span className="at-rate">
                        {row.positive_rate != null
                          ? `${(row.positive_rate * 100).toFixed(1)}%`
                          : '-'}
                      </span>
                    </td>
                    <td>{row.avg_grade != null ? row.avg_grade.toFixed(2) : '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {!trendLoading && selectedAllergen && trendData.length === 0 && !error && (
        <div className="at-empty">
          <p>선택한 알러젠에 대한 트렌드 데이터가 없습니다.</p>
        </div>
      )}

      {!selectedAllergen && !trendLoading && (
        <div className="at-empty">
          <p>알러젠을 선택하면 기간별 트렌드를 확인할 수 있습니다.</p>
        </div>
      )}

      <style>{`
        .allergen-trend-page {
          padding: 1rem;
        }

        .allergen-trend-page h2 {
          margin-bottom: 1.5rem;
          color: #333;
        }

        .at-error-banner {
          display: flex;
          align-items: center;
          gap: 1rem;
          padding: 0.75rem 1rem;
          background: #fdecea;
          color: #c0392b;
          border-radius: 8px;
          margin-bottom: 1rem;
        }

        .at-error-banner button {
          margin-left: auto;
          padding: 0.4rem 0.8rem;
          background: #e74c3c;
          color: white;
          border: none;
          border-radius: 4px;
          cursor: pointer;
          font-size: 0.8rem;
        }

        .at-selector-section {
          background: white;
          border-radius: 12px;
          padding: 1.5rem;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          margin-bottom: 1.5rem;
        }

        .at-label {
          display: block;
          margin-bottom: 0.5rem;
          font-weight: 600;
          color: #333;
          font-size: 0.9rem;
        }

        .at-select {
          width: 100%;
          max-width: 400px;
          padding: 0.6rem 1rem;
          border: 2px solid #e0e0e0;
          border-radius: 8px;
          font-size: 0.9rem;
          background: white;
          cursor: pointer;
          transition: border-color 0.2s;
        }

        .at-select:focus {
          outline: none;
          border-color: #1abc9c;
        }

        .at-loading-inline {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 1.5rem;
          background: white;
          border-radius: 12px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          color: #666;
        }

        .at-spinner-small {
          width: 24px;
          height: 24px;
          border: 3px solid #e9ecef;
          border-top: 3px solid #1abc9c;
          border-radius: 50%;
          animation: at-spin 1s linear infinite;
        }

        .at-trend-section {
          background: white;
          border-radius: 12px;
          padding: 1.5rem;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          margin-bottom: 1.5rem;
        }

        .at-trend-section h3 {
          margin: 0 0 1rem 0;
          color: #333;
          font-size: 1rem;
          border-bottom: 2px solid #1abc9c;
          padding-bottom: 0.5rem;
        }

        .at-table-wrapper {
          overflow-x: auto;
        }

        .at-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 0.9rem;
        }

        .at-table th,
        .at-table td {
          padding: 0.75rem 1rem;
          text-align: left;
          border-bottom: 1px solid #eee;
        }

        .at-table th {
          background: #f8f9fa;
          color: #555;
          font-weight: 600;
        }

        .at-table tbody tr:hover {
          background: #f0faf8;
        }

        .at-rate {
          display: inline-block;
          padding: 0.2rem 0.6rem;
          background: #e8f8f5;
          color: #16a085;
          border-radius: 12px;
          font-weight: 600;
          font-size: 0.85rem;
        }

        .at-empty {
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

export default AllergenTrendPage;
