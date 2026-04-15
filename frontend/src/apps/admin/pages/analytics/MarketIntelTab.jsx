/**
 * 시장 인텔리전스 탭 - 키워드 트렌드 분석
 */
import React, { useState, useEffect } from 'react';
import {
  LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { adminApi } from '../../services/adminApi';

const CATEGORY_LABELS = {
  company: '기업',
  technology: '기술',
  regulation: '규제',
  product: '제품',
  allergen: '알러젠',
};

const CATEGORY_COLORS = {
  company: '#9b59b6',
  technology: '#3498db',
  regulation: '#e74c3c',
  product: '#2ecc71',
  allergen: '#f39c12',
};

const CATEGORY_ICONS = {
  company: '🏢',
  technology: '💡',
  regulation: '📜',
  product: '📦',
  allergen: '🧬',
};

const MarketIntelTab = () => {
  const [overview, setOverview] = useState(null);
  const [selectedKeyword, setSelectedKeyword] = useState(null);
  const [keywordTrend, setKeywordTrend] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadOverview();
  }, []);

  useEffect(() => {
    if (selectedKeyword) loadKeywordTrend(selectedKeyword);
  }, [selectedKeyword]);

  const loadOverview = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await adminApi.analytics.keywordsOverview();
      setOverview(result);
    } catch (err) {
      setError('키워드 트렌드 데이터를 불러오지 못했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const loadKeywordTrend = async (keyword) => {
    try {
      const result = await adminApi.analytics.keywordsTrend({ keyword, limit: 12 });
      setKeywordTrend(result);
    } catch (err) {
      console.error('Keyword trend load failed:', err);
    }
  };

  if (loading) return <p style={{ padding: '2rem', textAlign: 'center', color: '#888' }}>로딩 중...</p>;
  if (error) return <div style={{ color: '#e74c3c', padding: '1rem' }}>{error} <button onClick={loadOverview} style={{ marginLeft: '0.5rem', padding: '0.25rem 0.75rem', border: '1px solid #e74c3c', borderRadius: '4px', background: 'white', color: '#e74c3c', cursor: 'pointer' }}>재시도</button></div>;
  if (!overview) return <p className="ai-empty-text">키워드 데이터가 없습니다. 키워드 추출을 먼저 실행해주세요.</p>;

  const risingKeywords = overview.rising_keywords || [];
  const categories = overview.categories || {};

  const trendChartData = (keywordTrend?.trend || []).map(t => ({
    period: t.period?.slice(0, 7),
    언급수: t.mention_count,
  }));

  const contextSamples = keywordTrend?.trend?.length > 0
    ? keywordTrend.trend[keywordTrend.trend.length - 1]?.context_samples || []
    : [];

  return (
    <div>
      {/* 상단 정보 바 */}
      <div className="ai-info-bar">
        <div className="ai-info-items">
          <span className="ai-info-item">기준: <strong>{overview.latest_period?.slice(0, 7) || '-'}</strong></span>
          <span className="ai-info-item">키워드: <strong>{overview.total_keywords ?? '-'}개</strong></span>
        </div>
        <button onClick={loadOverview} className="ai-refresh-btn">새로고침</button>
      </div>

      {/* 상승 키워드 */}
      {risingKeywords.length > 0 && (
        <div className="ai-card" style={{ marginBottom: '1.5rem' }}>
          <div className="ai-card-header">
            <h4 className="ai-card-title">상승 키워드</h4>
            <span className="ai-card-badge">{risingKeywords.length}건</span>
          </div>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {risingKeywords.map((kw, i) => (
              <span
                key={i}
                onClick={() => setSelectedKeyword(kw.keyword)}
                className="mi-rising-tag"
                style={{
                  background: selectedKeyword === kw.keyword
                    ? CATEGORY_COLORS[kw.category] || '#667eea'
                    : `${CATEGORY_COLORS[kw.category] || '#667eea'}dd`,
                  outline: selectedKeyword === kw.keyword ? '2px solid #333' : 'none',
                }}
              >
                {kw.keyword}
                <span className="mi-rising-rate">
                  {kw.change_rate != null ? `+${kw.change_rate.toFixed(0)}%` : 'NEW'}
                </span>
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 카테고리별 키워드 */}
      <div className="mi-cat-grid">
        {Object.entries(categories).map(([cat, keywords]) => (
          <div key={cat} className="ai-card mi-cat-card">
            <div className="ai-card-header">
              <h4 className="ai-card-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                <span>{CATEGORY_ICONS[cat] || '📌'}</span>
                <span style={{ color: CATEGORY_COLORS[cat] || '#333' }}>{CATEGORY_LABELS[cat] || cat}</span>
              </h4>
              <span className="ai-card-badge">{(keywords || []).length}</span>
            </div>
            {(keywords || []).length === 0 ? (
              <p className="ai-empty-text" style={{ padding: '0.5rem 0' }}>키워드가 없습니다.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                {keywords.map((kw, i) => (
                  <div
                    key={i}
                    onClick={() => setSelectedKeyword(kw.keyword)}
                    className="mi-keyword-row"
                    style={{
                      background: selectedKeyword === kw.keyword ? `${CATEGORY_COLORS[cat]}12` : 'transparent',
                      borderLeft: selectedKeyword === kw.keyword ? `3px solid ${CATEGORY_COLORS[cat]}` : '3px solid transparent',
                    }}
                  >
                    <span className="mi-keyword-name">{kw.keyword}</span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span className="mi-keyword-count">{kw.mention_count}회</span>
                      <TrendBadge direction={kw.trend_direction} rate={kw.change_rate} />
                    </span>
                  </div>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>

      {/* 선택 키워드 추이 */}
      {selectedKeyword && (
        <div className="ai-card" style={{ marginTop: '1.5rem' }}>
          <h4 className="ai-card-title">"{selectedKeyword}" 언급 추이</h4>
          {trendChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trendChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="period" tick={{ fontSize: 11 }} />
                <YAxis tick={{ fontSize: 11 }} />
                <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #eee', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
                <Legend />
                <Line type="monotone" dataKey="언급수" stroke="#9b59b6" strokeWidth={2.5} dot={{ r: 4, fill: '#9b59b6' }} activeDot={{ r: 6 }} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p className="ai-empty-text">추이 데이터가 없습니다.</p>
          )}

          {contextSamples.length > 0 && (
            <div style={{ marginTop: '1rem', padding: '0.75rem', background: '#f8f9fa', borderRadius: '8px' }}>
              <h5 style={{ margin: '0 0 0.5rem 0', fontSize: '0.8rem', color: '#888', textTransform: 'uppercase', letterSpacing: '0.5px' }}>관련 기사 샘플</h5>
              <ul style={{ margin: 0, paddingLeft: '1.25rem' }}>
                {contextSamples.map((s, i) => (
                  <li key={i} style={{ fontSize: '0.8rem', color: '#555', marginBottom: '0.3rem', lineHeight: 1.5 }}>{s}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {Object.keys(categories).length === 0 && risingKeywords.length === 0 && (
        <p className="ai-empty-text">키워드 데이터가 없습니다. 키워드 추출을 먼저 실행해주세요.</p>
      )}

      <style>{`
        .ai-info-bar { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; margin-bottom: 1.5rem; padding: 0.75rem 1rem; background: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
        .ai-info-items { display: flex; gap: 1.5rem; flex-wrap: wrap; }
        .ai-info-item { font-size: 0.85rem; color: #666; }
        .ai-info-item strong { color: #333; }
        .ai-refresh-btn { padding: 0.5rem 1rem; background: linear-gradient(135deg, #9b59b6, #8e44ad); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.85rem; font-weight: 500; transition: opacity 0.2s; }
        .ai-refresh-btn:hover { opacity: 0.85; }
        .ai-card { background: white; border-radius: 12px; padding: 1.25rem; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
        .ai-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
        .ai-card-title { margin: 0; font-size: 0.95rem; font-weight: 600; color: #333; }
        .ai-card-badge { background: #f0e6f6; color: #9b59b6; padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.7rem; font-weight: 600; }
        .ai-empty-text { color: #aaa; font-size: 0.85rem; text-align: center; padding: 2rem 0; margin: 0; }

        .mi-rising-tag {
          display: inline-flex; align-items: center; gap: 0.375rem;
          padding: 0.4rem 0.75rem; color: white; border-radius: 20px;
          font-size: 0.8rem; font-weight: 500; cursor: pointer;
          transition: transform 0.15s, outline 0.15s;
        }
        .mi-rising-tag:hover { transform: scale(1.05); }
        .mi-rising-rate { font-size: 0.65rem; background: rgba(255,255,255,0.25); padding: 0.1rem 0.35rem; border-radius: 8px; }

        .mi-cat-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(260px, 1fr));
          gap: 1rem;
        }
        .mi-cat-card { transition: box-shadow 0.2s; }
        .mi-cat-card:hover { box-shadow: 0 4px 20px rgba(0,0,0,0.1); }

        .mi-keyword-row {
          display: flex; justify-content: space-between; align-items: center;
          padding: 0.5rem 0.625rem; border-radius: 6px; cursor: pointer;
          transition: background 0.15s, border-left 0.15s;
        }
        .mi-keyword-row:hover { background: #f8f9fa; }
        .mi-keyword-name { font-size: 0.85rem; font-weight: 500; }
        .mi-keyword-count { font-size: 0.75rem; color: #888; }

        @media (max-width: 640px) { .mi-cat-grid { grid-template-columns: 1fr; } }
      `}</style>
    </div>
  );
};

const TrendBadge = ({ direction, rate }) => {
  const config = {
    rising: { color: '#27ae60', bg: '#e8f5e9', symbol: '▲' },
    declining: { color: '#e74c3c', bg: '#ffebee', symbol: '▼' },
    stable: { color: '#888', bg: '#f5f5f5', symbol: '−' },
    new: { color: '#3498db', bg: '#e3f2fd', symbol: 'NEW' },
  };
  const c = config[direction] || config.stable;
  return (
    <span style={{
      fontSize: '0.65rem', color: c.color, fontWeight: 700,
      background: c.bg, padding: '0.15rem 0.4rem', borderRadius: '6px',
    }}>
      {c.symbol} {rate != null && direction !== 'new' ? `${Math.abs(rate).toFixed(0)}%` : ''}
    </span>
  );
};

export default MarketIntelTab;
