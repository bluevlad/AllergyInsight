/**
 * 알러젠뉴스 정보 페이지 (공개, read-only)
 * 전일 수집 뉴스 목록 + 키워드 트렌드, 카테고리별 분석, 언급 추이
 */
import React, { useState, useEffect } from 'react';
import {
  LineChart, Line,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { analyticsApi } from '../services/analyticsApi';

const CATEGORY_LABELS = {
  company: '기업',
  technology: '기술',
  regulation: '규제',
  product: '제품',
  allergen: '알러젠',
  general: '일반',
  regulatory: '규제',
  financial: '재무',
  partnership: '제휴',
};

const CATEGORY_COLORS = {
  company: '#9b59b6',
  technology: '#3498db',
  regulation: '#e74c3c',
  product: '#2ecc71',
  allergen: '#f39c12',
  general: '#95a5a6',
  regulatory: '#e74c3c',
  financial: '#27ae60',
  partnership: '#8e44ad',
};

const CATEGORY_ICONS = {
  company: '🏢',
  technology: '💡',
  regulation: '📜',
  product: '📦',
  allergen: '🧬',
};

const NEWS_CATEGORY_TABS = [
  { key: '', label: '전체' },
  { key: 'product', label: '제품' },
  { key: 'regulatory', label: '규제' },
  { key: 'technology', label: '기술' },
  { key: 'financial', label: '재무' },
  { key: 'partnership', label: '제휴' },
  { key: 'general', label: '일반' },
];

const getImportanceLabel = (score) => {
  if (score == null) return null;
  if (score >= 0.7) return { text: '높음', color: '#e74c3c', bg: '#ffebee' };
  if (score >= 0.4) return { text: '보통', color: '#f39c12', bg: '#fff8e1' };
  return { text: '낮음', color: '#95a5a6', bg: '#f5f5f5' };
};

const formatDate = (dateStr) => {
  if (!dateStr) return '-';
  const d = new Date(dateStr);
  const month = String(d.getMonth() + 1).padStart(2, '0');
  const day = String(d.getDate()).padStart(2, '0');
  const hours = String(d.getHours()).padStart(2, '0');
  const mins = String(d.getMinutes()).padStart(2, '0');
  return `${month}.${day} ${hours}:${mins}`;
};

const AllergenNewsPage = () => {
  // 뉴스 상태
  const [newsData, setNewsData] = useState(null);
  const [newsLoading, setNewsLoading] = useState(false);
  const [newsCategoryFilter, setNewsCategoryFilter] = useState('');
  const [newsDays, setNewsDays] = useState(1);

  // 키워드 트렌드 상태
  const [overview, setOverview] = useState(null);
  const [selectedKeyword, setSelectedKeyword] = useState(null);
  const [keywordTrend, setKeywordTrend] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadRecentNews();
    loadOverview();
  }, []);

  useEffect(() => {
    loadRecentNews();
  }, [newsCategoryFilter, newsDays]);

  useEffect(() => {
    if (selectedKeyword) loadKeywordTrend(selectedKeyword);
  }, [selectedKeyword]);

  // 최근 뉴스 로드
  const loadRecentNews = async () => {
    try {
      setNewsLoading(true);
      const params = { days: newsDays, limit: 30 };
      if (newsCategoryFilter) params.category = newsCategoryFilter;
      const result = await analyticsApi.getRecentNews(params);
      setNewsData(result);
    } catch (err) {
      console.error('Recent news load failed:', err);
    } finally {
      setNewsLoading(false);
    }
  };

  // 키워드 트렌드 로드
  const loadOverview = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await analyticsApi.getKeywordsOverview();
      setOverview(result);
    } catch (err) {
      setError('키워드 트렌드 데이터를 불러오지 못했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const loadKeywordTrend = async (keyword) => {
    try {
      const result = await analyticsApi.getKeywordTrend({ keyword, limit: 12 });
      setKeywordTrend(result);
    } catch (err) {
      console.error('Keyword trend load failed:', err);
    }
  };

  const newsItems = newsData?.items || [];
  const newsByCategory = newsData?.by_category || {};
  const newsTotal = newsData?.total || 0;

  const risingKeywords = overview?.rising_keywords || [];
  const categories = overview?.categories || {};

  const trendChartData = (keywordTrend?.trend || []).map(t => ({
    period: t.period?.slice(0, 7),
    언급수: t.mention_count,
  }));

  const contextSamples = keywordTrend?.trend?.length > 0
    ? keywordTrend.trend[keywordTrend.trend.length - 1]?.context_samples || []
    : [];

  return (
    <div className="an-page">
      <h2 className="an-page-title">알러젠뉴스 정보</h2>

      {/* ===== 최근 수집 뉴스 섹션 ===== */}
      <div className="an-section">
        <div className="an-section-header">
          <h3 className="an-section-title">오늘의 알러젠뉴스</h3>
          <div className="an-days-select">
            <select value={newsDays} onChange={(e) => setNewsDays(Number(e.target.value))} className="an-select">
              <option value={1}>최근 1일</option>
              <option value={2}>최근 2일</option>
              <option value={3}>최근 3일</option>
              <option value={7}>최근 7일</option>
            </select>
            <button onClick={loadRecentNews} className="an-refresh-btn">새로고침</button>
          </div>
        </div>

        {/* 뉴스 통계 바 */}
        <div className="an-news-stats">
          <span className="an-news-stat-total">전체 <strong>{newsTotal}건</strong></span>
          {Object.entries(newsByCategory).map(([cat, cnt]) => (
            <span key={cat} className="an-news-stat-item">
              {CATEGORY_LABELS[cat] || cat} <strong>{cnt}</strong>
            </span>
          ))}
        </div>

        {/* 카테고리 탭 필터 */}
        <div className="an-news-tabs">
          {NEWS_CATEGORY_TABS.map((tab) => (
            <button
              key={tab.key}
              className={`an-news-tab ${newsCategoryFilter === tab.key ? 'active' : ''}`}
              onClick={() => setNewsCategoryFilter(tab.key)}
            >
              {tab.label}
              {tab.key && newsByCategory[tab.key] ? ` (${newsByCategory[tab.key]})` : ''}
            </button>
          ))}
        </div>

        {/* 뉴스 리스트 */}
        {newsLoading ? (
          <div className="an-loading">로딩 중...</div>
        ) : newsItems.length === 0 ? (
          <p className="an-empty">수집된 뉴스가 없습니다.</p>
        ) : (
          <div className="an-news-list">
            {newsItems.map((news) => {
              const importance = getImportanceLabel(news.importance_score);
              return (
                <div key={news.id} className="an-news-card">
                  <div className="an-news-card-header">
                    <div className="an-news-badges">
                      <span
                        className="an-news-source"
                        style={{
                          background: news.source === 'naver' ? '#03C75A' : '#4285F4',
                        }}
                      >
                        {news.source === 'naver' ? 'N' : 'G'}
                      </span>
                      {news.category && (
                        <span
                          className="an-news-category"
                          style={{
                            color: CATEGORY_COLORS[news.category] || '#666',
                            background: `${CATEGORY_COLORS[news.category] || '#666'}15`,
                          }}
                        >
                          {CATEGORY_LABELS[news.category] || news.category}
                        </span>
                      )}
                      {importance && (
                        <span
                          className="an-news-importance"
                          style={{ color: importance.color, background: importance.bg }}
                        >
                          {importance.text}
                        </span>
                      )}
                    </div>
                    <span className="an-news-date">{formatDate(news.published_at)}</span>
                  </div>
                  <a href={news.url} target="_blank" rel="noopener noreferrer" className="an-news-title">
                    {news.title}
                  </a>
                  {news.summary && (
                    <p className="an-news-summary">{news.summary}</p>
                  )}
                  <div className="an-news-meta">
                    {news.company_name && (
                      <span className="an-news-company">{news.company_name}</span>
                    )}
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* ===== 키워드 트렌드 섹션 ===== */}
      {(loading || error || overview) && (
        <>
          <hr className="an-divider" />
          <h3 className="an-section-title">키워드 트렌드</h3>

          {loading && <p className="an-loading">로딩 중...</p>}
          {error && <div className="an-error">{error} <button onClick={loadOverview} className="an-retry-btn">재시도</button></div>}

          {overview && (
            <>
              {/* 상단 정보 바 */}
              <div className="an-info-bar">
                <div className="an-info-items">
                  <span className="an-info-item">기준: <strong>{overview.latest_period?.slice(0, 7) || '-'}</strong></span>
                  <span className="an-info-item">키워드: <strong>{overview.total_keywords ?? '-'}개</strong></span>
                </div>
                <button onClick={loadOverview} className="an-refresh-btn">새로고침</button>
              </div>

              {/* 상승 키워드 */}
              {risingKeywords.length > 0 && (
                <div className="an-card" style={{ marginBottom: '1.5rem' }}>
                  <div className="an-card-header">
                    <h4 className="an-card-title">상승 키워드</h4>
                    <span className="an-card-badge">{risingKeywords.length}건</span>
                  </div>
                  <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                    {risingKeywords.map((kw, i) => (
                      <span
                        key={i}
                        onClick={() => setSelectedKeyword(kw.keyword)}
                        className="an-rising-tag"
                        style={{
                          background: selectedKeyword === kw.keyword
                            ? CATEGORY_COLORS[kw.category] || '#667eea'
                            : `${CATEGORY_COLORS[kw.category] || '#667eea'}dd`,
                          outline: selectedKeyword === kw.keyword ? '2px solid #333' : 'none',
                        }}
                      >
                        {kw.keyword}
                        <span className="an-rising-rate">
                          {kw.change_rate != null ? `+${kw.change_rate.toFixed(0)}%` : 'NEW'}
                        </span>
                      </span>
                    ))}
                  </div>
                </div>
              )}

              {/* 카테고리별 키워드 */}
              <div className="an-cat-grid">
                {Object.entries(categories).map(([cat, keywords]) => (
                  <div key={cat} className="an-card an-cat-card">
                    <div className="an-card-header">
                      <h4 className="an-card-title" style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                        <span>{CATEGORY_ICONS[cat] || '📌'}</span>
                        <span style={{ color: CATEGORY_COLORS[cat] || '#333' }}>{CATEGORY_LABELS[cat] || cat}</span>
                      </h4>
                      <span className="an-card-badge">{(keywords || []).length}</span>
                    </div>
                    {(keywords || []).length === 0 ? (
                      <p className="an-empty" style={{ padding: '0.5rem 0' }}>키워드가 없습니다.</p>
                    ) : (
                      <div style={{ display: 'flex', flexDirection: 'column', gap: '0.25rem' }}>
                        {keywords.map((kw, i) => (
                          <div
                            key={i}
                            onClick={() => setSelectedKeyword(kw.keyword)}
                            className="an-keyword-row"
                            style={{
                              background: selectedKeyword === kw.keyword ? `${CATEGORY_COLORS[cat]}12` : 'transparent',
                              borderLeft: selectedKeyword === kw.keyword ? `3px solid ${CATEGORY_COLORS[cat]}` : '3px solid transparent',
                            }}
                          >
                            <span className="an-keyword-name">{kw.keyword}</span>
                            <span style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                              <span className="an-keyword-count">{kw.mention_count}회</span>
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
                <div className="an-card" style={{ marginTop: '1.5rem' }}>
                  <h4 className="an-card-title">"{selectedKeyword}" 언급 추이</h4>
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
                    <p className="an-empty">추이 데이터가 없습니다.</p>
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
                <p className="an-empty">키워드 트렌드 데이터가 없습니다.</p>
              )}
            </>
          )}
        </>
      )}

      <style>{`
        .an-page { padding: 1rem; }
        .an-page-title { margin-bottom: 1.25rem; font-size: 1.25rem; font-weight: 700; color: #2c3e50; }
        .an-loading { padding: 2rem; text-align: center; color: #888; }
        .an-error { color: #e74c3c; padding: 1rem; }
        .an-retry-btn { margin-left: 0.5rem; padding: 0.25rem 0.75rem; border: 1px solid #e74c3c; border-radius: 4px; background: white; color: #e74c3c; cursor: pointer; }
        .an-empty { color: #aaa; font-size: 0.85rem; text-align: center; padding: 2rem 0; margin: 0; }
        .an-divider { border: none; border-top: 1px solid #eee; margin: 2rem 0 1.5rem; }
        .an-select { padding: 0.4rem 0.75rem; border: 1px solid #ddd; border-radius: 6px; background: white; font-size: 0.85rem; }

        /* 섹션 */
        .an-section { margin-bottom: 1.5rem; }
        .an-section-header { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 0.75rem; margin-bottom: 1rem; }
        .an-section-title { font-size: 1.05rem; font-weight: 700; color: #2c3e50; margin: 0 0 1rem 0; }
        .an-days-select { display: flex; gap: 0.5rem; align-items: center; }

        /* 뉴스 통계 */
        .an-news-stats { display: flex; gap: 1.5rem; flex-wrap: wrap; padding: 0.75rem 1rem; background: #f8f9fa; border-radius: 8px; margin-bottom: 1rem; font-size: 0.8rem; color: #666; }
        .an-news-stats strong { color: #333; }
        .an-news-stat-total { font-weight: 600; }

        /* 카테고리 탭 */
        .an-news-tabs { display: flex; gap: 0.375rem; flex-wrap: wrap; margin-bottom: 1rem; }
        .an-news-tab { padding: 0.375rem 0.75rem; border: 1px solid #ddd; border-radius: 20px; background: white; font-size: 0.8rem; cursor: pointer; transition: all 0.15s; color: #666; }
        .an-news-tab:hover { border-color: #1abc9c; color: #1abc9c; }
        .an-news-tab.active { background: #1abc9c; color: white; border-color: #1abc9c; }

        /* 뉴스 카드 리스트 */
        .an-news-list { display: flex; flex-direction: column; gap: 0.75rem; }
        .an-news-card { background: white; border-radius: 10px; padding: 1rem 1.25rem; box-shadow: 0 2px 8px rgba(0,0,0,0.06); transition: box-shadow 0.2s; }
        .an-news-card:hover { box-shadow: 0 4px 16px rgba(0,0,0,0.1); }
        .an-news-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 0.5rem; }
        .an-news-badges { display: flex; gap: 0.375rem; align-items: center; }
        .an-news-source { display: inline-flex; align-items: center; justify-content: center; width: 20px; height: 20px; border-radius: 4px; color: white; font-size: 0.65rem; font-weight: 700; }
        .an-news-category { font-size: 0.7rem; font-weight: 600; padding: 0.15rem 0.5rem; border-radius: 10px; }
        .an-news-importance { font-size: 0.65rem; font-weight: 700; padding: 0.15rem 0.4rem; border-radius: 6px; }
        .an-news-date { font-size: 0.75rem; color: #999; }
        .an-news-title { display: block; font-size: 0.9rem; font-weight: 600; color: #333; text-decoration: none; line-height: 1.5; margin-bottom: 0.375rem; }
        .an-news-title:hover { color: #1abc9c; }
        .an-news-summary { font-size: 0.8rem; color: #666; line-height: 1.5; margin: 0 0 0.375rem 0; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; }
        .an-news-meta { display: flex; gap: 0.5rem; align-items: center; }
        .an-news-company { font-size: 0.75rem; color: #888; background: #f0f0f0; padding: 0.15rem 0.5rem; border-radius: 4px; }

        /* 키워드 트렌드 섹션 */
        .an-info-bar { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; margin-bottom: 1.5rem; padding: 0.75rem 1rem; background: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
        .an-info-items { display: flex; gap: 1.5rem; flex-wrap: wrap; }
        .an-info-item { font-size: 0.85rem; color: #666; }
        .an-info-item strong { color: #333; }
        .an-refresh-btn { padding: 0.5rem 1rem; background: linear-gradient(135deg, #1abc9c, #16a085); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.85rem; font-weight: 500; transition: opacity 0.2s; }
        .an-refresh-btn:hover { opacity: 0.85; }
        .an-card { background: white; border-radius: 12px; padding: 1.25rem; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
        .an-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; }
        .an-card-title { margin: 0; font-size: 0.95rem; font-weight: 600; color: #333; }
        .an-card-badge { background: #e0f2f1; color: #1abc9c; padding: 0.2rem 0.6rem; border-radius: 12px; font-size: 0.7rem; font-weight: 600; }
        .an-rising-tag { display: inline-flex; align-items: center; gap: 0.375rem; padding: 0.4rem 0.75rem; color: white; border-radius: 20px; font-size: 0.8rem; font-weight: 500; cursor: pointer; transition: transform 0.15s, outline 0.15s; }
        .an-rising-tag:hover { transform: scale(1.05); }
        .an-rising-rate { font-size: 0.65rem; background: rgba(255,255,255,0.25); padding: 0.1rem 0.35rem; border-radius: 8px; }
        .an-cat-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 1rem; }
        .an-cat-card { transition: box-shadow 0.2s; }
        .an-cat-card:hover { box-shadow: 0 4px 20px rgba(0,0,0,0.1); }
        .an-keyword-row { display: flex; justify-content: space-between; align-items: center; padding: 0.5rem 0.625rem; border-radius: 6px; cursor: pointer; transition: background 0.15s, border-left 0.15s; }
        .an-keyword-row:hover { background: #f8f9fa; }
        .an-keyword-name { font-size: 0.85rem; font-weight: 500; }
        .an-keyword-count { font-size: 0.75rem; color: #888; }
        @media (max-width: 640px) { .an-cat-grid { grid-template-columns: 1fr; } }
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

export default AllergenNewsPage;
