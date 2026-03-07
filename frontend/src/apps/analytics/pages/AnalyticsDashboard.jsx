/**
 * Analytics Dashboard Page
 *
 * 공개 대시보드 - 플랫폼 요약 통계, 알러젠 양성률, 키워드 트렌드를 표시합니다.
 */
import React, { useState, useEffect } from 'react';
import { analyticsApi } from '../services/analyticsApi';

const AnalyticsDashboard = () => {
  const [summary, setSummary] = useState(null);
  const [overview, setOverview] = useState(null);
  const [keywords, setKeywords] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      setError(null);

      const [summaryData, overviewData, keywordsData] = await Promise.allSettled([
        analyticsApi.getSummary(),
        analyticsApi.getOverview(),
        analyticsApi.getKeywordsOverview(),
      ]);

      if (summaryData.status === 'fulfilled') setSummary(summaryData.value);
      if (overviewData.status === 'fulfilled') setOverview(overviewData.value);
      if (keywordsData.status === 'fulfilled') setKeywords(keywordsData.value);

      const allFailed = [summaryData, overviewData, keywordsData].every(
        (r) => r.status === 'rejected'
      );
      if (allFailed) {
        setError('데이터를 불러올 수 없습니다.');
      }
    } catch (err) {
      console.error('Dashboard load failed:', err);
      setError('대시보드 로딩 실패');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="analytics-loading">
        <div className="analytics-spinner" />
        <p>대시보드 로딩 중...</p>
        <style>{`
          .analytics-loading {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 300px;
            gap: 1rem;
          }
          .analytics-spinner {
            width: 40px;
            height: 40px;
            border: 4px solid #e9ecef;
            border-top: 4px solid #1abc9c;
            border-radius: 50%;
            animation: analytics-spin 1s linear infinite;
          }
          @keyframes analytics-spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  if (error && !summary && !overview && !keywords) {
    return (
      <div className="analytics-error">
        <p>{error}</p>
        <button onClick={loadDashboard}>다시 시도</button>
        <style>{`
          .analytics-error {
            display: flex;
            flex-direction: column;
            align-items: center;
            justify-content: center;
            min-height: 300px;
            gap: 1rem;
          }
          .analytics-error button {
            padding: 0.5rem 1rem;
            background: #1abc9c;
            color: white;
            border: none;
            border-radius: 6px;
            cursor: pointer;
          }
          .analytics-error button:hover {
            background: #16a085;
          }
        `}</style>
      </div>
    );
  }

  return (
    <div className="analytics-dashboard">
      <h2>Analytics Overview</h2>

      {/* Platform Summary Cards */}
      {summary && (
        <section className="analytics-section">
          <h3>플랫폼 요약</h3>
          <div className="summary-grid">
            <div className="summary-card">
              <div className="summary-card-header">사용자</div>
              <div className="summary-card-body">
                <span className="summary-number">{summary.total_users ?? '-'}</span>
              </div>
            </div>
            <div className="summary-card">
              <div className="summary-card-header">진단 건수</div>
              <div className="summary-card-body">
                <span className="summary-number">{summary.total_diagnoses ?? '-'}</span>
              </div>
            </div>
            <div className="summary-card">
              <div className="summary-card-header">연구 논문</div>
              <div className="summary-card-body">
                <span className="summary-number">{summary.total_papers ?? '-'}</span>
              </div>
            </div>
          </div>
        </section>
      )}

      {/* Allergen Overview */}
      {overview && Array.isArray(overview) && overview.length > 0 && (
        <section className="analytics-section">
          <h3>알러젠 양성률 개요</h3>
          <div className="overview-table-wrapper">
            <table className="analytics-table">
              <thead>
                <tr>
                  <th>알러젠 코드</th>
                  <th>알러젠명</th>
                  <th>양성률</th>
                  <th>총 검사 수</th>
                </tr>
              </thead>
              <tbody>
                {overview.slice(0, 10).map((item, idx) => (
                  <tr key={item.allergen_code || idx}>
                    <td>{item.allergen_code}</td>
                    <td>{item.allergen_name || '-'}</td>
                    <td>
                      <span className="rate-badge">
                        {item.positive_rate != null
                          ? `${(item.positive_rate * 100).toFixed(1)}%`
                          : '-'}
                      </span>
                    </td>
                    <td>{item.total_tests ?? '-'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </section>
      )}

      {/* Keywords Overview */}
      {keywords && Array.isArray(keywords) && keywords.length > 0 && (
        <section className="analytics-section">
          <h3>주요 키워드</h3>
          <div className="keywords-grid">
            {keywords.slice(0, 12).map((kw, idx) => (
              <div key={kw.keyword || idx} className="keyword-card">
                <span className="keyword-name">{kw.keyword}</span>
                <span className="keyword-count">{kw.mention_count ?? 0}</span>
                {kw.trend_direction && (
                  <span className={`keyword-trend trend-${kw.trend_direction}`}>
                    {kw.trend_direction === 'up' ? '[ + ]' : kw.trend_direction === 'down' ? '[ - ]' : '[ = ]'}
                  </span>
                )}
              </div>
            ))}
          </div>
        </section>
      )}

      <style>{`
        .analytics-dashboard {
          padding: 1rem;
        }

        .analytics-dashboard h2 {
          margin-bottom: 1.5rem;
          color: #333;
        }

        .analytics-section {
          background: white;
          border-radius: 12px;
          padding: 1.5rem;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          margin-bottom: 1.5rem;
        }

        .analytics-section h3 {
          margin: 0 0 1rem 0;
          color: #333;
          font-size: 1.1rem;
          border-bottom: 2px solid #1abc9c;
          padding-bottom: 0.5rem;
        }

        /* Summary Cards */
        .summary-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
          gap: 1rem;
        }

        .summary-card {
          border-radius: 10px;
          overflow: hidden;
          box-shadow: 0 1px 4px rgba(0, 0, 0, 0.08);
        }

        .summary-card-header {
          padding: 0.75rem 1rem;
          background: linear-gradient(135deg, #1abc9c 0%, #16a085 100%);
          color: white;
          font-size: 0.9rem;
          font-weight: 500;
        }

        .summary-card-body {
          padding: 1rem;
          text-align: center;
        }

        .summary-number {
          font-size: 2rem;
          font-weight: 700;
          color: #333;
        }

        /* Overview Table */
        .overview-table-wrapper {
          overflow-x: auto;
        }

        .analytics-table {
          width: 100%;
          border-collapse: collapse;
          font-size: 0.9rem;
        }

        .analytics-table th,
        .analytics-table td {
          padding: 0.75rem 1rem;
          text-align: left;
          border-bottom: 1px solid #eee;
        }

        .analytics-table th {
          background: #f8f9fa;
          color: #555;
          font-weight: 600;
        }

        .analytics-table tbody tr:hover {
          background: #f0faf8;
        }

        .rate-badge {
          display: inline-block;
          padding: 0.2rem 0.6rem;
          background: #e8f8f5;
          color: #16a085;
          border-radius: 12px;
          font-weight: 600;
          font-size: 0.85rem;
        }

        /* Keywords */
        .keywords-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
          gap: 0.75rem;
        }

        .keyword-card {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.75rem 1rem;
          background: #f8f9fa;
          border-radius: 8px;
          border-left: 3px solid #1abc9c;
        }

        .keyword-name {
          flex: 1;
          font-size: 0.875rem;
          color: #333;
          font-weight: 500;
        }

        .keyword-count {
          background: #1abc9c;
          color: white;
          padding: 0.125rem 0.5rem;
          border-radius: 10px;
          font-size: 0.75rem;
          font-weight: 600;
        }

        .keyword-trend {
          font-size: 0.75rem;
          font-weight: 600;
        }

        .trend-up {
          color: #27ae60;
        }

        .trend-down {
          color: #e74c3c;
        }

        .trend-stable {
          color: #95a5a6;
        }
      `}</style>
    </div>
  );
};

export default AnalyticsDashboard;
