/**
 * Papers Management Page
 * 탭: 논문 목록 | 논문 수집정보 (read-only)
 */
import React, { useState, useEffect } from 'react';
import {
  BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, ResponsiveContainer,
} from 'recharts';
import { adminApi } from '../services/adminApi';

const COLORS = ['#e74c3c', '#3498db', '#2ecc71', '#f39c12', '#9b59b6', '#1abc9c', '#e67e22', '#667eea'];

const PapersPage = () => {
  const [activeTab, setActiveTab] = useState('list');

  return (
    <div className="papers-page">
      <h2>논문 관리</h2>

      {/* 탭 */}
      <div className="page-tabs">
        <button
          className={`page-tab ${activeTab === 'list' ? 'active' : ''}`}
          onClick={() => setActiveTab('list')}
        >
          논문 목록
        </button>
        <button
          className={`page-tab ${activeTab === 'collection' ? 'active' : ''}`}
          onClick={() => setActiveTab('collection')}
        >
          논문 수집정보
        </button>
      </div>

      {activeTab === 'list' && <PaperListTab />}
      {activeTab === 'collection' && <PaperCollectionTab />}

      <style>{`
        .papers-page {
          padding: 1rem;
        }

        .papers-page h2 {
          margin-bottom: 1.5rem;
        }

        .page-tabs {
          display: flex;
          gap: 0;
          margin-bottom: 1.5rem;
          border-bottom: 2px solid #eee;
        }

        .page-tab {
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

        .page-tab:hover {
          color: #555;
        }

        .page-tab.active {
          color: #e74c3c;
          border-bottom-color: #e74c3c;
          font-weight: 600;
        }

        .toolbar {
          display: flex;
          gap: 1rem;
          margin-bottom: 1.5rem;
          flex-wrap: wrap;
          align-items: center;
        }

        .search-form {
          display: flex;
          gap: 0.5rem;
          flex: 1;
          min-width: 300px;
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
        }

        .toolbar select {
          padding: 0.5rem 1rem;
          border: 1px solid #ddd;
          border-radius: 6px;
          background: white;
        }

        .checkbox-label {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          cursor: pointer;
        }

        .papers-list {
          display: flex;
          flex-direction: column;
          gap: 1rem;
        }

        .paper-card {
          background: white;
          border-radius: 8px;
          padding: 1.25rem;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        .paper-header {
          display: flex;
          justify-content: space-between;
          align-items: flex-start;
          gap: 1rem;
          margin-bottom: 0.75rem;
        }

        .paper-title {
          margin: 0;
          font-size: 1rem;
          font-weight: 600;
          color: #333;
          flex: 1;
        }

        .paper-badges {
          display: flex;
          gap: 0.5rem;
          flex-shrink: 0;
        }

        .badge {
          padding: 0.25rem 0.5rem;
          border-radius: 4px;
          font-size: 0.75rem;
          font-weight: 500;
        }

        .badge.guideline {
          background: #e8f5e9;
          color: #2e7d32;
        }

        .badge.evidence {
          background: #e3f2fd;
          color: #1565c0;
        }

        .badge.source {
          background: #f3e5f5;
          color: #7b1fa2;
        }

        .paper-meta {
          display: flex;
          flex-wrap: wrap;
          gap: 1rem;
          font-size: 0.875rem;
          color: #666;
          margin-bottom: 0.75rem;
        }

        .paper-meta span::before {
          margin-right: 0.25rem;
        }

        .authors::before {
          content: '👤';
        }

        .journal::before {
          content: '📖';
        }

        .year::before {
          content: '📅';
        }

        .collected {
          color: #999;
          font-size: 0.8rem;
        }

        .collected::before {
          content: '🕐';
        }

        .paper-links {
          display: flex;
          gap: 0.5rem;
          margin-bottom: 0.75rem;
        }

        .link-btn {
          display: inline-block;
          padding: 0.25rem 0.625rem;
          border-radius: 4px;
          font-size: 0.75rem;
          font-weight: 500;
          text-decoration: none;
          transition: opacity 0.2s;
        }

        .link-btn:hover {
          opacity: 0.8;
        }

        .link-btn.pubmed {
          background: #1a5276;
          color: white;
        }

        .link-btn.doi {
          background: #f39c12;
          color: white;
        }

        .link-btn.url {
          background: #7f8c8d;
          color: white;
        }

        .paper-collection-info {
          background: #f8f9fa;
          border-radius: 6px;
          padding: 0.625rem 0.875rem;
          margin-bottom: 0.75rem;
          border-left: 3px solid #667eea;
        }

        .allergen-tags {
          display: flex;
          flex-wrap: wrap;
          gap: 0.375rem;
          margin-bottom: 0.375rem;
        }

        .allergen-tag {
          display: inline-flex;
          align-items: center;
          gap: 0.25rem;
          padding: 0.2rem 0.5rem;
          border-radius: 12px;
          font-size: 0.7rem;
          font-weight: 500;
          background: #e8eaf6;
          color: #283593;
        }

        .allergen-tag.cross_reactivity {
          background: #fce4ec;
          color: #c62828;
        }

        .allergen-tag.symptom {
          background: #fff3e0;
          color: #e65100;
        }

        .allergen-tag.dietary {
          background: #e8f5e9;
          color: #2e7d32;
        }

        .allergen-tag.emergency {
          background: #ffebee;
          color: #b71c1c;
        }

        .allergen-tag .link-type {
          font-size: 0.625rem;
          opacity: 0.75;
        }

        .allergen-tag .link-type::before {
          content: '·';
          margin-right: 0.125rem;
        }

        .collection-reason {
          font-size: 0.75rem;
          color: #666;
          line-height: 1.4;
        }

        .paper-actions {
          display: flex;
          justify-content: flex-end;
          gap: 0.5rem;
        }

        .btn-delete {
          padding: 0.375rem 0.75rem;
          background: #e74c3c;
          color: white;
          border: none;
          border-radius: 4px;
          font-size: 0.75rem;
          cursor: pointer;
        }

        .btn-delete:hover {
          background: #c0392b;
        }

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

        .loading, .error {
          text-align: center;
          padding: 2rem;
          color: #666;
        }
      `}</style>
    </div>
  );
};

/**
 * 논문 목록 탭 (기존 기능)
 */
const PaperListTab = () => {
  const [papers, setPapers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [sourceFilter, setSourceFilter] = useState('');
  const [guidelineOnly, setGuidelineOnly] = useState(false);
  const pageSize = 20;

  useEffect(() => {
    loadPapers();
  }, [page, sourceFilter, guidelineOnly]);

  const loadPapers = async () => {
    try {
      setLoading(true);
      const params = { page, page_size: pageSize };
      if (search) params.search = search;
      if (sourceFilter) params.source = sourceFilter;
      if (guidelineOnly) params.is_guideline = true;

      const response = await adminApi.papers.list(params);
      setPapers(response.items || []);
      setTotal(response.total || 0);
    } catch (err) {
      console.error('Papers load failed:', err);
      setError('논문 목록 로딩 실패');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    loadPapers();
  };

  const handleDelete = async (id) => {
    if (!window.confirm('정말 삭제하시겠습니까?')) return;

    try {
      await adminApi.papers.delete(id);
      loadPapers();
    } catch (err) {
      alert('삭제 실패');
    }
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div>
      {/* 검색 및 필터 */}
      <div className="toolbar">
        <form onSubmit={handleSearch} className="search-form">
          <input
            type="text"
            placeholder="제목, 저자, 저널 검색..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button type="submit">검색</button>
        </form>
        <select
          value={sourceFilter}
          onChange={(e) => { setSourceFilter(e.target.value); setPage(1); }}
        >
          <option value="">전체 출처</option>
          <option value="pubmed">PubMed</option>
          <option value="semantic_scholar">Semantic Scholar</option>
          <option value="manual">직접 입력</option>
        </select>
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={guidelineOnly}
            onChange={(e) => { setGuidelineOnly(e.target.checked); setPage(1); }}
          />
          가이드라인만
        </label>
      </div>

      {/* 논문 목록 */}
      {loading ? (
        <div className="loading">로딩 중...</div>
      ) : error ? (
        <div className="error">{error}</div>
      ) : (
        <>
          <div className="papers-list">
            {papers.map((paper) => (
              <div key={paper.id} className="paper-card">
                <div className="paper-header">
                  <h3 className="paper-title">{paper.title}</h3>
                  <div className="paper-badges">
                    {paper.is_guideline && (
                      <span className="badge guideline">가이드라인</span>
                    )}
                    {paper.evidence_level && (
                      <span className="badge evidence">{paper.evidence_level}</span>
                    )}
                    {paper.source && (
                      <span className="badge source">{getSourceName(paper.source)}</span>
                    )}
                  </div>
                </div>
                <div className="paper-meta">
                  {paper.authors && (
                    <span className="authors">{paper.authors}</span>
                  )}
                  {paper.journal && (
                    <span className="journal">{paper.journal}</span>
                  )}
                  {paper.year && (
                    <span className="year">{paper.year}</span>
                  )}
                  {paper.created_at && (
                    <span className="collected">수집: {formatDateTime(paper.created_at)}</span>
                  )}
                </div>

                {/* 원본 링크 */}
                {(paper.pmid || paper.doi || paper.url) && (
                  <div className="paper-links">
                    {paper.pmid && (
                      <a href={`https://pubmed.ncbi.nlm.nih.gov/${paper.pmid}`} target="_blank" rel="noopener noreferrer" className="link-btn pubmed">
                        PubMed
                      </a>
                    )}
                    {paper.doi && (
                      <a href={`https://doi.org/${paper.doi}`} target="_blank" rel="noopener noreferrer" className="link-btn doi">
                        DOI
                      </a>
                    )}
                    {paper.url && !paper.pmid && !paper.doi && (
                      <a href={paper.url} target="_blank" rel="noopener noreferrer" className="link-btn url">
                        원본 보기
                      </a>
                    )}
                  </div>
                )}

                {/* 수집 근거 */}
                {(paper.collection_reason || (paper.allergen_links && paper.allergen_links.length > 0)) && (
                  <div className="paper-collection-info">
                    {paper.allergen_links && paper.allergen_links.length > 0 && (
                      <div className="allergen-tags">
                        {paper.allergen_links.map((link, idx) => (
                          <span key={idx} className={`allergen-tag ${link.link_type}`}>
                            {link.allergen_name || link.allergen_code}
                            <span className="link-type">{getLinkTypeName(link.link_type)}</span>
                          </span>
                        ))}
                      </div>
                    )}
                    {paper.collection_reason && (
                      <div className="collection-reason">{paper.collection_reason}</div>
                    )}
                  </div>
                )}

                <div className="paper-actions">
                  <button
                    onClick={() => handleDelete(paper.id)}
                    className="btn-delete"
                  >
                    삭제
                  </button>
                </div>
              </div>
            ))}
          </div>

          {/* 페이지네이션 */}
          <div className="pagination">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
            >
              이전
            </button>
            <span>
              {page} / {totalPages} (총 {total}건)
            </span>
            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page >= totalPages}
            >
              다음
            </button>
          </div>
        </>
      )}
    </div>
  );
};

/**
 * 논문 수집정보 탭 (read-only)
 * 출처별 수집 현황, 알러젠 연결 통계, 최근 수집 이력
 */
const PaperCollectionTab = () => {
  const [papers, setPapers] = useState([]);
  const [total, setTotal] = useState(0);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadAllData();
  }, []);

  const loadAllData = async () => {
    try {
      setLoading(true);
      setError(null);
      const response = await adminApi.papers.list({ page: 1, page_size: 1000 });
      setPapers(response.items || []);
      setTotal(response.total || 0);
    } catch (err) {
      console.error('Papers load failed:', err);
      setError('논문 수집정보 로딩 실패');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <p style={{ padding: '2rem', textAlign: 'center', color: '#888' }}>로딩 중...</p>;
  if (error) return <div style={{ color: '#e74c3c', padding: '1rem' }}>{error} <button onClick={loadAllData} style={{ marginLeft: '0.5rem', padding: '0.25rem 0.75rem', border: '1px solid #e74c3c', borderRadius: '4px', background: 'white', color: '#e74c3c', cursor: 'pointer' }}>재시도</button></div>;

  // 출처별 통계
  const sourceStats = papers.reduce((acc, p) => {
    const src = p.source || 'unknown';
    acc[src] = (acc[src] || 0) + 1;
    return acc;
  }, {});
  const sourceChartData = Object.entries(sourceStats).map(([name, value]) => ({
    name: getSourceName(name),
    value,
  }));

  // 가이드라인/일반 비율
  const guidelineCount = papers.filter(p => p.is_guideline).length;
  const typeChartData = [
    { name: '일반 논문', value: total - guidelineCount },
    { name: '가이드라인', value: guidelineCount },
  ].filter(d => d.value > 0);

  // 알러젠 연결 통계
  const allergenLinkStats = {};
  papers.forEach(p => {
    (p.allergen_links || []).forEach(link => {
      const name = link.allergen_name || link.allergen_code;
      if (!allergenLinkStats[name]) allergenLinkStats[name] = { total: 0, types: {} };
      allergenLinkStats[name].total++;
      const lt = link.link_type || 'general';
      allergenLinkStats[name].types[lt] = (allergenLinkStats[name].types[lt] || 0) + 1;
    });
  });
  const topAllergenLinks = Object.entries(allergenLinkStats)
    .sort((a, b) => b[1].total - a[1].total)
    .slice(0, 15);

  // 연도별 분포
  const yearStats = papers.reduce((acc, p) => {
    const yr = p.year || '미상';
    acc[yr] = (acc[yr] || 0) + 1;
    return acc;
  }, {});
  const yearChartData = Object.entries(yearStats)
    .filter(([yr]) => yr !== '미상')
    .sort((a, b) => a[0] - b[0])
    .slice(-10)
    .map(([year, count]) => ({ year, count }));

  // 최근 수집 논문
  const recentPapers = [...papers]
    .sort((a, b) => new Date(b.created_at || 0) - new Date(a.created_at || 0))
    .slice(0, 10);

  return (
    <div>
      {/* 상단 정보 바 */}
      <div className="pc-info-bar">
        <div className="pc-info-items">
          <span className="pc-info-item">전체 논문: <strong>{total}건</strong></span>
          <span className="pc-info-item">가이드라인: <strong>{guidelineCount}건</strong></span>
          <span className="pc-info-item">출처: <strong>{Object.keys(sourceStats).length}종</strong></span>
          <span className="pc-info-item">알러젠 연결: <strong>{Object.keys(allergenLinkStats).length}종</strong></span>
        </div>
        <button onClick={loadAllData} className="pc-refresh-btn">새로고침</button>
      </div>

      {/* 출처별 / 유형별 차트 */}
      <div className="pc-grid-2col" style={{ marginBottom: '1.5rem' }}>
        {sourceChartData.length > 0 && (
          <div className="pc-card">
            <h4 className="pc-card-title">출처별 수집 현황</h4>
            <ResponsiveContainer width="100%" height={280}>
              <PieChart>
                <Pie data={sourceChartData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} innerRadius={50}
                  label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                  labelLine={{ stroke: '#ccc' }}
                >
                  {sourceChartData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                </Pie>
                <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #eee' }} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {yearChartData.length > 0 && (
          <div className="pc-card">
            <h4 className="pc-card-title">연도별 논문 분포 (최근 10년)</h4>
            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={yearChartData}>
                <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                <XAxis dataKey="year" tick={{ fontSize: 12 }} />
                <YAxis tick={{ fontSize: 12 }} />
                <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #eee', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
                <Bar dataKey="count" name="논문 수" fill="#e74c3c" radius={[6, 6, 0, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>

      {/* 알러젠 연결 TOP 15 */}
      {topAllergenLinks.length > 0 && (
        <div className="pc-card" style={{ marginBottom: '1.5rem' }}>
          <h4 className="pc-card-title">알러젠별 논문 연결 현황 (TOP 15)</h4>
          <table className="pc-table">
            <thead>
              <tr>
                <th>순위</th>
                <th>알러젠</th>
                <th>연결 논문 수</th>
                <th>연결 유형</th>
              </tr>
            </thead>
            <tbody>
              {topAllergenLinks.map(([name, stat], i) => (
                <tr key={name}>
                  <td>
                    <span className={`pc-rank ${i < 3 ? `pc-rank-${i + 1}` : ''}`}>{i + 1}</span>
                  </td>
                  <td style={{ fontWeight: 500 }}>{name}</td>
                  <td style={{ fontWeight: 600, color: '#e74c3c' }}>{stat.total}</td>
                  <td>
                    <div style={{ display: 'flex', gap: '0.25rem', flexWrap: 'wrap' }}>
                      {Object.entries(stat.types).map(([type, cnt]) => (
                        <span key={type} style={{
                          padding: '0.15rem 0.4rem',
                          background: '#f8f9fa',
                          borderRadius: '4px',
                          fontSize: '0.7rem',
                          color: '#666',
                        }}>
                          {getLinkTypeName(type)} {cnt}
                        </span>
                      ))}
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* 최근 수집 논문 */}
      <div className="pc-card">
        <h4 className="pc-card-title">최근 수집 논문 (10건)</h4>
        {recentPapers.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
            {recentPapers.map((paper, i) => (
              <div key={paper.id || i} className="pc-recent-item">
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontSize: '0.85rem', fontWeight: 500, color: '#333', marginBottom: '0.25rem', lineHeight: 1.4 }}>
                    {paper.title}
                  </div>
                  <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap', fontSize: '0.75rem', color: '#888' }}>
                    {paper.source && <span className="badge source" style={{ fontSize: '0.7rem' }}>{getSourceName(paper.source)}</span>}
                    {paper.year && <span>{paper.year}</span>}
                    {paper.created_at && <span>수집: {formatDateTime(paper.created_at)}</span>}
                  </div>
                </div>
              </div>
            ))}
          </div>
        ) : (
          <p style={{ color: '#aaa', fontSize: '0.85rem', textAlign: 'center', padding: '1.5rem 0' }}>수집된 논문이 없습니다.</p>
        )}
      </div>

      <style>{`
        .pc-info-bar {
          display: flex;
          justify-content: space-between;
          align-items: center;
          flex-wrap: wrap;
          gap: 1rem;
          margin-bottom: 1.5rem;
          padding: 0.75rem 1rem;
          background: white;
          border-radius: 10px;
          box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }
        .pc-info-items { display: flex; gap: 1.5rem; flex-wrap: wrap; }
        .pc-info-item { font-size: 0.85rem; color: #666; }
        .pc-info-item strong { color: #333; }
        .pc-refresh-btn {
          padding: 0.5rem 1rem;
          background: linear-gradient(135deg, #e74c3c, #c0392b);
          color: white; border: none; border-radius: 6px;
          cursor: pointer; font-size: 0.85rem; font-weight: 500;
          transition: opacity 0.2s;
        }
        .pc-refresh-btn:hover { opacity: 0.85; }
        .pc-grid-2col {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(360px, 1fr));
          gap: 1.5rem;
        }
        .pc-card {
          background: white; border-radius: 12px; padding: 1.25rem;
          box-shadow: 0 2px 12px rgba(0,0,0,0.06);
        }
        .pc-card-title { margin: 0 0 1rem 0; font-size: 0.95rem; font-weight: 600; color: #333; }
        .pc-table { width: 100%; border-collapse: collapse; }
        .pc-table thead tr { background: #f8f9fa; }
        .pc-table th { padding: 0.625rem 0.75rem; text-align: left; font-size: 0.75rem; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }
        .pc-table td { padding: 0.625rem 0.75rem; font-size: 0.85rem; border-bottom: 1px solid #f0f0f0; }
        .pc-table tbody tr:hover { background: #fef5f5; }
        .pc-table tbody tr:last-child td { border-bottom: none; }
        .pc-rank { display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; border-radius: 50%; font-size: 0.7rem; font-weight: 700; background: #eee; color: #666; }
        .pc-rank-1 { background: #ffd700; color: #7a6100; }
        .pc-rank-2 { background: #c0c0c0; color: #555; }
        .pc-rank-3 { background: #cd7f32; color: white; }
        .pc-recent-item {
          display: flex;
          align-items: flex-start;
          padding: 0.75rem;
          background: #f8f9fa;
          border-radius: 8px;
          border-left: 3px solid #e74c3c;
        }
        @media (max-width: 640px) { .pc-grid-2col { grid-template-columns: 1fr; } }
      `}</style>
    </div>
  );
};

const formatDateTime = (dateStr) => {
  if (!dateStr) return '';
  const d = new Date(dateStr);
  return d.toLocaleDateString('ko-KR') + ' ' + d.toLocaleTimeString('ko-KR', { hour: '2-digit', minute: '2-digit' });
};

const getSourceName = (source) => {
  const sources = {
    pubmed: 'PubMed',
    semantic_scholar: 'Semantic Scholar',
    manual: '직접 입력',
    unknown: '미분류',
  };
  return sources[source] || source;
};

const getLinkTypeName = (type) => {
  const types = {
    symptom: '증상',
    dietary: '식이',
    cross_reactivity: '교차반응',
    substitute: '대체식품',
    emergency: '응급',
    management: '관리',
    general: '일반',
  };
  return types[type] || type;
};

export default PapersPage;
