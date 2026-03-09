/**
 * Keyword Trend Page - 키워드 트렌드 분석
 */
import React, { useState, useEffect } from 'react';
import {
  LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { analyticsApi } from '../services/analyticsApi';

const CATEGORY_LABELS = {
  company: '기업', technology: '기술', regulation: '규제', product: '제품', allergen: '알러젠',
};
const CATEGORY_COLORS = {
  company: '#9b59b6', technology: '#3498db', regulation: '#e74c3c', product: '#2ecc71', allergen: '#f39c12',
};
const CATEGORY_ICONS = {
  company: '🏢', technology: '💡', regulation: '📜', product: '📦', allergen: '🧬',
};

const KeywordTrendPage = () => {
  const [overview, setOverview] = useState(null);
  const [keywords, setKeywords] = useState([]);
  const [selectedKeyword, setSelectedKeyword] = useState(null);
  const [keywordTrend, setKeywordTrend] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => { loadKeywords(); }, []);

  useEffect(() => {
    if (selectedKeyword) loadTrend(selectedKeyword);
  }, [selectedKeyword]);

  const loadKeywords = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await analyticsApi.getKeywordsOverview();
      if (Array.isArray(data)) {
        setKeywords(data);
        setOverview(null);
      } else {
        setOverview(data);
        setKeywords([]);
      }
    } catch {
      setError('키워드 데이터를 불러올 수 없습니다.');
    } finally {
      setLoading(false);
    }
  };

  const loadTrend = async (keyword) => {
    try {
      const data = await analyticsApi.getKeywordTrend({ keyword, limit: 12 });
      setKeywordTrend(data);
    } catch {
      setKeywordTrend(null);
    }
  };

  if (loading) {
    return <div className="pub-loading"><div className="pub-spinner" /><p>로딩 중...</p></div>;
  }

  const risingKeywords = overview?.rising_keywords || [];
  const categories = overview?.categories || {};
  const hasStructured = Object.keys(categories).length > 0 || risingKeywords.length > 0;

  const trendChartData = (keywordTrend?.trend || []).map(t => ({
    period: (t.period || '').slice(0, 7),
    언급수: t.mention_count,
  }));

  const contextSamples = keywordTrend?.trend?.length > 0
    ? keywordTrend.trend[keywordTrend.trend.length - 1]?.context_samples || []
    : [];

  return (
    <div className="pub-page">
      <h2 className="pub-page-title">키워드 트렌드 분석</h2>

      {error && (
        <div className="pub-error-banner">{error} <button onClick={loadKeywords} className="pub-retry-sm">재시도</button></div>
      )}

      {/* Rising Keywords */}
      {risingKeywords.length > 0 && (
        <div className="pub-card">
          <div className="pub-card-header-flex">
            <h3 className="pub-card-title">상승 키워드</h3>
            <span className="pub-badge-count">{risingKeywords.length}건</span>
          </div>
          <div className="pub-keyword-tags">
            {risingKeywords.map((kw, i) => (
              <span
                key={i}
                onClick={() => setSelectedKeyword(kw.keyword)}
                className="pub-rising-tag"
                style={{
                  background: CATEGORY_COLORS[kw.category] || '#1abc9c',
                  outline: selectedKeyword === kw.keyword ? '2px solid #333' : 'none',
                }}
              >
                {kw.keyword}
                <span className="pub-rising-rate">
                  {kw.change_rate != null ? `+${kw.change_rate.toFixed(0)}%` : 'NEW'}
                </span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* Category Cards */}
      {hasStructured && (
        <div className="pub-cat-grid">
          {Object.entries(categories).map(([cat, kws]) => (
            <div key={cat} className="pub-card pub-cat-card">
              <div className="pub-card-header-flex">
                <h3 className="pub-card-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span>{CATEGORY_ICONS[cat] || '📌'}</span>
                  <span style={{ color: CATEGORY_COLORS[cat] || '#333' }}>{CATEGORY_LABELS[cat] || cat}</span>
                </h3>
                <span className="pub-badge-count">{(kws || []).length}</span>
              </div>
              {(kws || []).length === 0 ? (
                <p className="pub-empty" style={{ padding: '0.5rem 0' }}>키워드가 없습니다.</p>
              ) : (
                <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                  {kws.map((kw, i) => (
                    <div
                      key={i}
                      onClick={() => setSelectedKeyword(kw.keyword)}
                      className="pub-kw-row"
                      style={{
                        background: selectedKeyword === kw.keyword ? `${CATEGORY_COLORS[cat]}12` : 'transparent',
                        borderLeft: selectedKeyword === kw.keyword ? `3px solid ${CATEGORY_COLORS[cat]}` : '3px solid transparent',
                      }}
                    >
                      <span className="pub-kw-name">{kw.keyword}</span>
                      <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span className="pub-kw-count">{kw.mention_count}회</span>
                        <TrendBadge direction={kw.trend_direction} rate={kw.change_rate} />
                      </span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      {/* Flat keyword list (fallback) */}
      {!hasStructured && keywords.length > 0 && (
        <div className="pub-card">
          <h3 className="pub-card-title">키워드 목록</h3>
          <table className="pub-table">
            <thead><tr><th>키워드</th><th>카테고리</th><th>언급 수</th><th>트렌드</th></tr></thead>
            <tbody>
              {keywords.map((kw, i) => (
                <tr key={i} onClick={() => setSelectedKeyword(kw.keyword)} style={{ cursor: 'pointer' }}>
                  <td className="pub-allergen-name">{kw.keyword}</td>
                  <td>{kw.category ? <span className="pub-cat-badge">{CATEGORY_LABELS[kw.category] || kw.category}</span> : '-'}</td>
                  <td>{kw.mention_count ?? 0}</td>
                  <td><TrendBadge direction={kw.trend_direction} rate={kw.change_rate} /></td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Selected Keyword Trend */}
      {selectedKeyword && (
        <div className="pub-card">
          <h3 className="pub-card-title">"{selectedKeyword}" 언급 추이</h3>
          {trendChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trendChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="period" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #eee', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
                <Legend />
                <Line type="monotone" dataKey="언급수" stroke="#1abc9c" strokeWidth={2.5} dot={{ r: 4, fill: '#1abc9c' }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="pub-empty">추이 데이터가 없습니다.</p>
          )}

          {contextSamples.length > 0 && (
            <div className="pub-context-box">
              <h5 className="pub-context-title">관련 기사 샘플</h5>
              <ul className="pub-context-list">
                {contextSamples.map((s, i) => <li key={i}>{s}</li>)}
              </ul>
            </div>
          )}
        </div>
      )}

      {!hasStructured && keywords.length === 0 && !error && (
        <div className="pub-card"><p className="pub-empty">키워드 데이터가 없습니다.</p></div>
      )}

      <style>{`
        .pub-page { padding: 1rem; }
        .pub-page-title { margin-bottom: 1.25rem; font-size: 1.25rem; font-weight: 700; color: #2c3e50; }
        .pub-loading { display: flex; flex-direction: column; align-items: center; justify-content: center; min-height: 300px; gap: 1rem; color: #888; }
        .pub-spinner { width: 40px; height: 40px; border: 4px solid #e9ecef; border-top: 4px solid #1abc9c; border-radius: 50%; animation: pub-spin 1s linear infinite; }
        @keyframes pub-spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .pub-error-banner { display: flex; align-items: center; gap: 1rem; padding: 0.75rem 1rem; background: #fdecea; color: #c0392b; border-radius: 8px; margin-bottom: 1rem; font-size: 0.9rem; }
        .pub-retry-sm { padding: 0.3rem 0.7rem; background: #e74c3c; color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 0.8rem; margin-left: auto; }

        .pub-card { background: white; border-radius: 12px; padding: 1.25rem; box-shadow: 0 2px 12px rgba(0,0,0,0.06); margin-bottom: 1.5rem; }
        .pub-card-title { margin: 0; font-size: 0.95rem; font-weight: 600; color: #333; }
        .pub-card-header-flex { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
        .pub-badge-count { background: #e8f8f5; color: #1abc9c; padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.7rem; font-weight: 600; }

        .pub-keyword-tags { display: flex; flex-wrap: wrap; gap: 0.5rem; }
        .pub-rising-tag { display: inline-flex; align-items: center; gap: 0.375rem; padding: 0.4rem 0.75rem; color: white; border-radius: 20px; font-size: 0.8rem; font-weight: 500; cursor: pointer; transition: transform 0.15s; }
        .pub-rising-tag:hover { transform: scale(1.05); }
        .pub-rising-rate { font-size: 0.65rem; background: rgba(255,255,255,0.25); padding: 0.1rem 0.35rem; border-radius: 8px; }

        .pub-cat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1rem; margin-bottom: 1.5rem; }
        .pub-cat-card { transition: box-shadow 0.2s; margin-bottom: 0; }
        .pub-cat-card:hover { box-shadow: 0 4px 20px rgba(0,0,0,0.1); }

        .pub-kw-row { display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0.625rem; border-radius: 6px; cursor: pointer; transition: background 0.15s; }
        .pub-kw-row:hover { background: #f8f9fa; }
        .pub-kw-name { font-size: 0.85rem; font-weight: 500; }
        .pub-kw-count { font-size: 0.75rem; color: #888; }

        .pub-table { width: 100%; border-collapse: collapse; }
        .pub-table thead tr { background: #f8f9fa; }
        .pub-table th { padding: 0.625rem 0.75rem; text-align: left; font-size: 0.75rem; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }
        .pub-table td { padding: 0.625rem 0.75rem; font-size: 0.85rem; border-bottom: 1px solid #f0f0f0; }
        .pub-table tbody tr:hover { background: #f0faf8; }
        .pub-table tbody tr:last-child td { border-bottom: none; }
        .pub-allergen-name { font-weight: 500; }
        .pub-cat-badge { display: inline-block; padding: 0.15rem 0.5rem; background: #e8f8f5; color: #16a085; border-radius: 10px; font-size: 0.75rem; font-weight: 500; }
        .pub-empty { color: #aaa; font-size: 0.85rem; text-align: center; padding: 1.5rem 0; margin: 0; }

        .pub-context-box { margin-top: 1rem; padding: 0.75rem; background: #f8f9fa; border-radius: 8px; }
        .pub-context-title { margin: 0 0 0.5rem; font-size: 0.8rem; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }
        .pub-context-list { margin: 0; padding-left: 1.25rem; }
        .pub-context-list li { font-size: 0.8rem; color: #555; margin-bottom: 0.3rem; line-height: 1.5; }

        @media (max-width: 640px) { .pub-cat-grid { grid-template-columns: 1fr; } }
      `}</style>
    </div>
  );
};

const TrendBadge = ({ direction, rate }) => {
  const config = {
    rising: { color: '#27ae60', bg: '#e8f5e9', symbol: '▲' },
    up: { color: '#27ae60', bg: '#e8f5e9', symbol: '▲' },
    declining: { color: '#e74c3c', bg: '#ffebee', symbol: '▼' },
    down: { color: '#e74c3c', bg: '#ffebee', symbol: '▼' },
    stable: { color: '#888', bg: '#f5f5f5', symbol: '−' },
    new: { color: '#3498db', bg: '#e3f2fd', symbol: 'NEW' },
  };
  const c = config[direction] || config.stable;
  return (
    <span style={{ fontSize: '0.65rem', color: c.color, fontWeight: 700, background: c.bg, padding: '0.15rem 0.4rem', borderRadius: '6px' }}>
      {c.symbol} {rate != null && direction !== 'new' ? `${Math.abs(typeof rate === 'number' && Math.abs(rate) < 1 ? rate * 100 : rate).toFixed(0)}%` : ''}
    </span>
  );
};

export default KeywordTrendPage;
