/**
 * Competitor News Management Page
 *
 * 경쟁사 뉴스 모니터링 대시보드
 */
import React, { useState, useEffect } from 'react';
import { adminApi } from '../services/adminApi';

const CompetitorNewsPage = () => {
  const [news, setNews] = useState([]);
  const [companies, setCompanies] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [collecting, setCollecting] = useState(false);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [companyFilter, setCompanyFilter] = useState('');
  const [sourceFilter, setSourceFilter] = useState('');
  const [importantOnly, setImportantOnly] = useState(false);
  const [unreadOnly, setUnreadOnly] = useState(false);
  const [activeTab, setActiveTab] = useState('list'); // 'list', 'search'
  const [searchKeyword, setSearchKeyword] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);
  const pageSize = 20;

  useEffect(() => {
    loadCompanies();
    loadStats();
  }, []);

  useEffect(() => {
    if (activeTab === 'list') {
      loadNews();
    }
  }, [page, companyFilter, sourceFilter, importantOnly, unreadOnly, activeTab]);

  const loadNews = async () => {
    try {
      setLoading(true);
      const params = { page, page_size: pageSize };
      if (search) params.search = search;
      if (companyFilter) params.company = companyFilter;
      if (sourceFilter) params.source = sourceFilter;
      if (importantOnly) params.is_important = true;
      if (unreadOnly) params.is_read = false;

      const response = await adminApi.news.list(params);
      setNews(response.items || []);
      setTotal(response.total || 0);
    } catch (err) {
      console.error('News load failed:', err);
      setError('뉴스 목록 로딩 실패');
    } finally {
      setLoading(false);
    }
  };

  const loadCompanies = async () => {
    try {
      const response = await adminApi.news.companies();
      setCompanies(response.items || []);
    } catch (err) {
      console.error('Companies load failed:', err);
    }
  };

  const loadStats = async () => {
    try {
      const response = await adminApi.news.stats();
      setStats(response);
    } catch (err) {
      console.error('Stats load failed:', err);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    loadNews();
  };

  const handleCollect = async (companyCode = null) => {
    if (!window.confirm(
      companyCode
        ? `${companyCode} 업체의 뉴스를 수집하시겠습니까?`
        : '전체 업체 뉴스를 수집하시겠습니까?'
    )) return;

    try {
      setCollecting(true);
      const result = await adminApi.news.collect({
        company_code: companyCode,
        max_results: 10,
      });
      alert(`수집 완료: 신규 ${result.total_new}건, 중복 ${result.total_duplicate}건`);
      loadNews();
      loadStats();
    } catch (err) {
      console.error('Collect failed:', err);
      alert('수집 실패: ' + (err.message || '알 수 없는 오류'));
    } finally {
      setCollecting(false);
    }
  };

  const handleLiveSearch = async (e) => {
    e.preventDefault();
    if (!searchKeyword.trim()) return;

    try {
      setSearching(true);
      const response = await adminApi.news.search({
        keyword: searchKeyword,
        max_results: 30,
      });
      setSearchResults(response.articles || []);
    } catch (err) {
      console.error('Live search failed:', err);
      alert('검색 실패');
    } finally {
      setSearching(false);
    }
  };

  const handleCompanySearch = async (companyCode) => {
    try {
      setSearching(true);
      setActiveTab('search');
      const response = await adminApi.news.search({
        company: companyCode,
        max_results: 30,
      });
      setSearchResults(response.articles || []);
    } catch (err) {
      console.error('Company search failed:', err);
    } finally {
      setSearching(false);
    }
  };

  const toggleRead = async (id) => {
    try {
      const result = await adminApi.news.toggleRead(id);
      setNews(prev => prev.map(n =>
        n.id === id ? { ...n, is_read: result.is_read } : n
      ));
    } catch (err) {
      console.error('Toggle read failed:', err);
    }
  };

  const toggleImportant = async (id) => {
    try {
      const result = await adminApi.news.toggleImportant(id);
      setNews(prev => prev.map(n =>
        n.id === id ? { ...n, is_important: result.is_important } : n
      ));
    } catch (err) {
      console.error('Toggle important failed:', err);
    }
  };

  const totalPages = Math.ceil(total / pageSize);

  const getCategoryLabel = (cat) => {
    const labels = { self: '자사', overseas: '해외', domestic: '국내', industry: '업계' };
    return labels[cat] || cat;
  };

  const getCategoryColor = (cat) => {
    const colors = { self: '#9b59b6', overseas: '#3498db', domestic: '#27ae60', industry: '#e67e22' };
    return colors[cat] || '#666';
  };

  return (
    <div className="news-page">
      <div className="page-header">
        <h2>경쟁사 뉴스</h2>
        <button
          className="btn-collect"
          onClick={() => handleCollect()}
          disabled={collecting}
        >
          {collecting ? '수집 중...' : '전체 수집'}
        </button>
      </div>

      {/* 통계 요약 */}
      {stats && (
        <div className="stats-bar">
          <div className="stat-item">
            <span className="stat-label">전체</span>
            <span className="stat-value">{stats.total_news}건</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">미읽음</span>
            <span className="stat-value unread">{stats.unread_count}건</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">중요</span>
            <span className="stat-value important">{stats.important_count}건</span>
          </div>
          <div className="stat-item">
            <span className="stat-label">최근 7일</span>
            <span className="stat-value">{stats.recent_7days}건</span>
          </div>
        </div>
      )}

      {/* 탭 */}
      <div className="tabs">
        <button
          className={`tab ${activeTab === 'list' ? 'active' : ''}`}
          onClick={() => setActiveTab('list')}
        >
          수집된 뉴스
        </button>
        <button
          className={`tab ${activeTab === 'search' ? 'active' : ''}`}
          onClick={() => setActiveTab('search')}
        >
          실시간 검색
        </button>
        <button
          className={`tab ${activeTab === 'companies' ? 'active' : ''}`}
          onClick={() => setActiveTab('companies')}
        >
          모니터링 업체
        </button>
      </div>

      {/* 수집된 뉴스 탭 */}
      {activeTab === 'list' && (
        <div className="tab-content">
          {/* 필터 */}
          <div className="toolbar">
            <form onSubmit={handleSearch} className="search-form">
              <input
                type="text"
                placeholder="뉴스 제목, 내용 검색..."
                value={search}
                onChange={(e) => setSearch(e.target.value)}
              />
              <button type="submit">검색</button>
            </form>
            <select
              value={companyFilter}
              onChange={(e) => { setCompanyFilter(e.target.value); setPage(1); }}
            >
              <option value="">전체 업체</option>
              {companies.map((c) => (
                <option key={c.code} value={c.code}>{c.name_kr}</option>
              ))}
            </select>
            <select
              value={sourceFilter}
              onChange={(e) => { setSourceFilter(e.target.value); setPage(1); }}
            >
              <option value="">전체 소스</option>
              <option value="naver">네이버</option>
              <option value="google">구글</option>
            </select>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={unreadOnly}
                onChange={(e) => { setUnreadOnly(e.target.checked); setPage(1); }}
              />
              미읽음만
            </label>
            <label className="checkbox-label">
              <input
                type="checkbox"
                checked={importantOnly}
                onChange={(e) => { setImportantOnly(e.target.checked); setPage(1); }}
              />
              중요만
            </label>
          </div>

          {/* 뉴스 목록 */}
          {loading ? (
            <div className="loading">로딩 중...</div>
          ) : error ? (
            <div className="error">{error}</div>
          ) : news.length === 0 ? (
            <div className="empty">
              수집된 뉴스가 없습니다. '전체 수집' 버튼을 눌러 뉴스를 수집하세요.
            </div>
          ) : (
            <>
              <div className="news-list">
                {news.map((item) => (
                  <NewsCard
                    key={item.id}
                    item={item}
                    onToggleRead={toggleRead}
                    onToggleImportant={toggleImportant}
                  />
                ))}
              </div>
              <div className="pagination">
                <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1}>
                  이전
                </button>
                <span>{page} / {totalPages} (총 {total}건)</span>
                <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page >= totalPages}>
                  다음
                </button>
              </div>
            </>
          )}
        </div>
      )}

      {/* 실시간 검색 탭 */}
      {activeTab === 'search' && (
        <div className="tab-content">
          <form onSubmit={handleLiveSearch} className="search-form live-search">
            <input
              type="text"
              placeholder="검색 키워드 입력..."
              value={searchKeyword}
              onChange={(e) => setSearchKeyword(e.target.value)}
            />
            <button type="submit" disabled={searching}>
              {searching ? '검색 중...' : '실시간 검색'}
            </button>
          </form>
          <div className="company-quick-search">
            {companies.slice(0, 6).map((c) => (
              <button
                key={c.code}
                className="btn-quick"
                onClick={() => handleCompanySearch(c.code)}
                disabled={searching}
              >
                {c.name_kr}
              </button>
            ))}
          </div>
          {searchResults.length > 0 && (
            <div className="news-list">
              {searchResults.map((item, idx) => (
                <div key={idx} className="news-card">
                  <div className="news-header">
                    <a href={item.url} target="_blank" rel="noopener noreferrer" className="news-title">
                      {item.title}
                    </a>
                    <span className={`badge source-${item.source}`}>
                      {item.source === 'naver' ? '네이버' : '구글'}
                    </span>
                  </div>
                  {item.description && (
                    <p className="news-desc">{item.description}</p>
                  )}
                  <div className="news-meta">
                    {item.published_at && (
                      <span>{new Date(item.published_at).toLocaleDateString('ko-KR')}</span>
                    )}
                    {item.search_keyword && (
                      <span className="keyword">#{item.search_keyword}</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      )}

      {/* 모니터링 업체 탭 */}
      {activeTab === 'companies' && (
        <div className="tab-content">
          <div className="companies-grid">
            {companies.map((company) => (
              <div key={company.code} className="company-card">
                <div className="company-header">
                  <span
                    className="category-badge"
                    style={{ background: getCategoryColor(company.category) }}
                  >
                    {getCategoryLabel(company.category)}
                  </span>
                  <h3>{company.name_kr}</h3>
                  <span className="company-en">{company.name_en}</span>
                </div>
                <div className="company-keywords">
                  {company.keywords.map((kw, i) => (
                    <span key={i} className="keyword-tag">{kw}</span>
                  ))}
                </div>
                <div className="company-footer">
                  <span className="news-count">수집 {company.news_count}건</span>
                  <div className="company-actions">
                    <button
                      className="btn-sm"
                      onClick={() => { setCompanyFilter(company.code); setActiveTab('list'); }}
                    >
                      뉴스 보기
                    </button>
                    <button
                      className="btn-sm btn-collect-sm"
                      onClick={() => handleCollect(company.code)}
                      disabled={collecting}
                    >
                      수집
                    </button>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      )}

      <style>{`
        .news-page {
          padding: 1rem;
        }

        .page-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          margin-bottom: 1.5rem;
        }

        .page-header h2 {
          margin: 0;
        }

        .btn-collect {
          padding: 0.6rem 1.2rem;
          background: #9b59b6;
          color: white;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-weight: 600;
        }

        .btn-collect:hover {
          background: #8e44ad;
        }

        .btn-collect:disabled {
          opacity: 0.6;
          cursor: not-allowed;
        }

        /* Stats Bar */
        .stats-bar {
          display: flex;
          gap: 1rem;
          margin-bottom: 1.5rem;
          flex-wrap: wrap;
        }

        .stat-item {
          background: white;
          padding: 0.75rem 1.25rem;
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.08);
          display: flex;
          gap: 0.5rem;
          align-items: baseline;
        }

        .stat-label {
          font-size: 0.85rem;
          color: #888;
        }

        .stat-value {
          font-size: 1.1rem;
          font-weight: 700;
          color: #333;
        }

        .stat-value.unread { color: #e67e22; }
        .stat-value.important { color: #e74c3c; }

        /* Tabs */
        .tabs {
          display: flex;
          gap: 0;
          margin-bottom: 1rem;
          border-bottom: 2px solid #eee;
        }

        .tab {
          padding: 0.75rem 1.5rem;
          background: none;
          border: none;
          cursor: pointer;
          font-size: 0.95rem;
          color: #888;
          border-bottom: 2px solid transparent;
          margin-bottom: -2px;
          transition: all 0.2s;
        }

        .tab:hover {
          color: #555;
        }

        .tab.active {
          color: #9b59b6;
          border-bottom-color: #9b59b6;
          font-weight: 600;
        }

        .tab-content {
          padding: 1rem 0;
        }

        /* Toolbar */
        .toolbar {
          display: flex;
          gap: 0.75rem;
          margin-bottom: 1.5rem;
          flex-wrap: wrap;
          align-items: center;
        }

        .search-form {
          display: flex;
          gap: 0.5rem;
          flex: 1;
          min-width: 250px;
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
          white-space: nowrap;
        }

        .toolbar select {
          padding: 0.5rem 0.75rem;
          border: 1px solid #ddd;
          border-radius: 6px;
          background: white;
        }

        .checkbox-label {
          display: flex;
          align-items: center;
          gap: 0.4rem;
          cursor: pointer;
          font-size: 0.9rem;
          white-space: nowrap;
        }

        /* News List */
        .news-list {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }

        .news-card {
          background: white;
          border-radius: 8px;
          padding: 1rem 1.25rem;
          box-shadow: 0 2px 8px rgba(0,0,0,0.08);
          border-left: 3px solid transparent;
        }

        .news-card.unread {
          border-left-color: #e67e22;
        }

        .news-card.important {
          border-left-color: #e74c3c;
          background: #fff8f8;
        }

        .news-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 0.75rem;
          margin-bottom: 0.5rem;
        }

        .news-title {
          font-size: 0.95rem;
          font-weight: 600;
          color: #333;
          text-decoration: none;
          flex: 1;
          line-height: 1.4;
        }

        .news-title:hover {
          color: #9b59b6;
        }

        .news-desc {
          font-size: 0.85rem;
          color: #666;
          margin: 0 0 0.5rem 0;
          line-height: 1.5;
          display: -webkit-box;
          -webkit-line-clamp: 2;
          -webkit-box-orient: vertical;
          overflow: hidden;
        }

        .news-meta {
          display: flex;
          gap: 0.75rem;
          font-size: 0.8rem;
          color: #999;
          align-items: center;
          flex-wrap: wrap;
        }

        .news-actions {
          display: flex;
          gap: 0.5rem;
          margin-left: auto;
        }

        .btn-icon {
          background: none;
          border: 1px solid #ddd;
          border-radius: 4px;
          padding: 0.25rem 0.5rem;
          cursor: pointer;
          font-size: 0.85rem;
        }

        .btn-icon:hover {
          background: #f5f5f5;
        }

        .btn-icon.active {
          background: #fff3e0;
          border-color: #e67e22;
        }

        /* Badges */
        .badge {
          padding: 0.2rem 0.5rem;
          border-radius: 4px;
          font-size: 0.75rem;
          font-weight: 500;
          white-space: nowrap;
        }

        .source-naver {
          background: #e8f5e9;
          color: #2e7d32;
        }

        .source-google {
          background: #e3f2fd;
          color: #1565c0;
        }

        .badge-company {
          background: #f3e5f5;
          color: #7b1fa2;
        }

        .keyword {
          color: #9b59b6;
          font-size: 0.8rem;
        }

        /* Live Search */
        .live-search {
          margin-bottom: 1rem;
        }

        .company-quick-search {
          display: flex;
          gap: 0.5rem;
          flex-wrap: wrap;
          margin-bottom: 1.5rem;
        }

        .btn-quick {
          padding: 0.4rem 0.8rem;
          background: #f0f0f0;
          border: 1px solid #ddd;
          border-radius: 20px;
          cursor: pointer;
          font-size: 0.85rem;
          transition: all 0.2s;
        }

        .btn-quick:hover {
          background: #9b59b6;
          color: white;
          border-color: #9b59b6;
        }

        .btn-quick:disabled {
          opacity: 0.5;
        }

        /* Companies Grid */
        .companies-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(280px, 1fr));
          gap: 1rem;
        }

        .company-card {
          background: white;
          border-radius: 8px;
          padding: 1.25rem;
          box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }

        .company-header {
          margin-bottom: 0.75rem;
        }

        .category-badge {
          display: inline-block;
          padding: 0.15rem 0.5rem;
          border-radius: 4px;
          color: white;
          font-size: 0.7rem;
          font-weight: 600;
          margin-bottom: 0.5rem;
        }

        .company-header h3 {
          margin: 0;
          font-size: 1.05rem;
        }

        .company-en {
          font-size: 0.8rem;
          color: #999;
        }

        .company-keywords {
          display: flex;
          flex-wrap: wrap;
          gap: 0.3rem;
          margin-bottom: 0.75rem;
        }

        .keyword-tag {
          padding: 0.15rem 0.5rem;
          background: #f5f5f5;
          border-radius: 4px;
          font-size: 0.75rem;
          color: #666;
        }

        .company-footer {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding-top: 0.75rem;
          border-top: 1px solid #eee;
        }

        .news-count {
          font-size: 0.85rem;
          color: #888;
        }

        .company-actions {
          display: flex;
          gap: 0.5rem;
        }

        .btn-sm {
          padding: 0.3rem 0.6rem;
          background: #f0f0f0;
          border: 1px solid #ddd;
          border-radius: 4px;
          cursor: pointer;
          font-size: 0.8rem;
        }

        .btn-sm:hover {
          background: #e0e0e0;
        }

        .btn-collect-sm {
          background: #9b59b6;
          color: white;
          border-color: #9b59b6;
        }

        .btn-collect-sm:hover {
          background: #8e44ad;
        }

        .btn-collect-sm:disabled {
          opacity: 0.6;
        }

        /* Pagination */
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

        .loading, .error, .empty {
          text-align: center;
          padding: 3rem 1rem;
          color: #888;
          font-size: 0.95rem;
        }

        @media (max-width: 768px) {
          .toolbar {
            flex-direction: column;
          }
          .search-form {
            min-width: 100%;
          }
          .stats-bar {
            gap: 0.5rem;
          }
          .stat-item {
            flex: 1;
            min-width: 120px;
          }
        }
      `}</style>
    </div>
  );
};

/**
 * 개별 뉴스 카드 컴포넌트
 */
const NewsCard = ({ item, onToggleRead, onToggleImportant }) => {
  const cardClass = [
    'news-card',
    !item.is_read && 'unread',
    item.is_important && 'important',
  ].filter(Boolean).join(' ');

  return (
    <div className={cardClass}>
      <div className="news-header">
        <a href={item.url} target="_blank" rel="noopener noreferrer" className="news-title">
          {item.title}
        </a>
        <div style={{ display: 'flex', gap: '0.3rem' }}>
          <span className={`badge source-${item.source}`}>
            {item.source === 'naver' ? '네이버' : '구글'}
          </span>
          {item.company_name && (
            <span className="badge badge-company">{item.company_name}</span>
          )}
        </div>
      </div>
      {item.description && (
        <p className="news-desc">{item.description}</p>
      )}
      <div className="news-meta">
        {item.published_at && (
          <span>{new Date(item.published_at).toLocaleDateString('ko-KR')}</span>
        )}
        {item.search_keyword && (
          <span className="keyword">#{item.search_keyword}</span>
        )}
        <div className="news-actions">
          <button
            className={`btn-icon ${item.is_read ? '' : 'active'}`}
            onClick={() => onToggleRead(item.id)}
            title={item.is_read ? '읽음' : '미읽음'}
          >
            {item.is_read ? '읽음' : '미읽음'}
          </button>
          <button
            className={`btn-icon ${item.is_important ? 'active' : ''}`}
            onClick={() => onToggleImportant(item.id)}
            title={item.is_important ? '중요 해제' : '중요 표시'}
          >
            {item.is_important ? '★' : '☆'}
          </button>
        </div>
      </div>
    </div>
  );
};

export default CompetitorNewsPage;
