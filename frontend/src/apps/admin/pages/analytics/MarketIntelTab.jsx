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

  if (loading) return <p>로딩 중...</p>;
  if (error) return <div style={{ color: '#e74c3c', padding: '1rem' }}>{error} <button onClick={loadOverview}>재시도</button></div>;
  if (!overview) return <p style={{ color: '#888', padding: '1rem' }}>키워드 데이터가 없습니다. 키워드 추출을 먼저 실행해주세요.</p>;

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
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        <span style={{ fontSize: '0.85rem', color: '#888' }}>기준 기간: {overview.latest_period?.slice(0, 7) || '-'}</span>
        <span style={{ fontSize: '0.85rem', color: '#888' }}>총 키워드: {overview.total_keywords ?? '-'}</span>
        <button onClick={loadOverview} style={{ padding: '0.5rem 1rem', background: '#9b59b6', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>
          새로고침
        </button>
      </div>

      {/* 상승 키워드 */}
      {risingKeywords.length > 0 && (
        <div style={{ background: 'white', borderRadius: '8px', padding: '1rem', marginBottom: '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}>
          <h4 style={{ margin: '0 0 0.75rem 0' }}>상승 키워드</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            {risingKeywords.map((kw, i) => (
              <span
                key={i}
                onClick={() => setSelectedKeyword(kw.keyword)}
                style={{
                  padding: '0.4rem 0.75rem',
                  background: CATEGORY_COLORS[kw.category] || '#667eea',
                  color: 'white',
                  borderRadius: '16px',
                  fontSize: '0.85rem',
                  cursor: 'pointer',
                  transition: 'opacity 0.2s',
                }}
              >
                {kw.keyword} {kw.change_rate != null ? `+${kw.change_rate.toFixed(0)}%` : '🆕'}
              </span>
            ))}
          </div>
        </div>
      )}

      {/* 카테고리별 카드 그리드 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        {Object.entries(categories).map(([cat, keywords]) => (
          <div key={cat} style={{ background: 'white', borderRadius: '8px', padding: '1rem', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}>
            <h4 style={{ margin: '0 0 0.75rem 0', color: CATEGORY_COLORS[cat] || '#333' }}>
              {CATEGORY_LABELS[cat] || cat}
            </h4>
            {(keywords || []).length === 0 ? (
              <p style={{ color: '#888', fontSize: '0.85rem' }}>키워드가 없습니다.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.4rem' }}>
                {keywords.map((kw, i) => (
                  <div
                    key={i}
                    onClick={() => setSelectedKeyword(kw.keyword)}
                    style={{
                      display: 'flex', justifyContent: 'space-between', alignItems: 'center',
                      padding: '0.4rem 0.5rem', borderRadius: '4px', cursor: 'pointer',
                      background: selectedKeyword === kw.keyword ? '#f0e6f6' : 'transparent',
                      transition: 'background 0.2s',
                    }}
                  >
                    <span style={{ fontSize: '0.9rem' }}>{kw.keyword}</span>
                    <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <span style={{ fontSize: '0.8rem', color: '#888' }}>{kw.mention_count}회</span>
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
        <div style={{ background: 'white', borderRadius: '8px', padding: '1rem', marginBottom: '1.5rem', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}>
          <h4 style={{ margin: '0 0 1rem 0' }}>"{selectedKeyword}" 언급 추이</h4>
          {trendChartData.length > 0 ? (
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={trendChartData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="period" />
                <YAxis />
                <Tooltip />
                <Legend />
                <Line type="monotone" dataKey="언급수" stroke="#9b59b6" strokeWidth={2} dot={{ r: 3 }} />
              </LineChart>
            </ResponsiveContainer>
          ) : (
            <p style={{ color: '#888', textAlign: 'center' }}>추이 데이터가 없습니다.</p>
          )}

          {contextSamples.length > 0 && (
            <div style={{ marginTop: '1rem' }}>
              <h5 style={{ margin: '0 0 0.5rem 0', color: '#888' }}>관련 기사 샘플</h5>
              <ul style={{ margin: 0, paddingLeft: '1.5rem' }}>
                {contextSamples.map((s, i) => (
                  <li key={i} style={{ fontSize: '0.85rem', color: '#555', marginBottom: '0.3rem' }}>{s}</li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}

      {Object.keys(categories).length === 0 && risingKeywords.length === 0 && (
        <p style={{ color: '#888', textAlign: 'center', padding: '2rem' }}>키워드 데이터가 없습니다. 키워드 추출을 먼저 실행해주세요.</p>
      )}
    </div>
  );
};

const TrendBadge = ({ direction, rate }) => {
  const config = {
    rising: { color: '#27ae60', symbol: '▲' },
    declining: { color: '#e74c3c', symbol: '▼' },
    stable: { color: '#888', symbol: '−' },
    new: { color: '#3498db', symbol: '🆕' },
  };
  const c = config[direction] || config.stable;
  return (
    <span style={{ fontSize: '0.75rem', color: c.color, fontWeight: 600 }}>
      {c.symbol} {rate != null && direction !== 'new' ? `${Math.abs(rate).toFixed(0)}%` : ''}
    </span>
  );
};

export default MarketIntelTab;
