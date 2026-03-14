/**
 * AI Insight Page - 알러지 인사이트
 *
 * 공개 페이지 (인증 불필요)
 * 알러젠별 논문, 뉴스, 트렌드 정보를 통합 제공합니다.
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../../shared/services/apiClient';

const TABS = [
  { key: 'overview', label: '개요' },
  { key: 'allergen', label: '알러젠 탐색' },
  { key: 'news', label: '최신 뉴스' },
];

function AIInsightPage() {
  const navigate = useNavigate();
  const [activeTab, setActiveTab] = useState('overview');
  const [overview, setOverview] = useState(null);
  const [selectedAllergen, setSelectedAllergen] = useState(null);
  const [allergenDetail, setAllergenDetail] = useState(null);
  const [news, setNews] = useState([]);
  const [loading, setLoading] = useState(false);

  // 개요 로드
  useEffect(() => {
    apiClient.get('/ai/insight/overview')
      .then(data => setOverview(data))
      .catch(() => {});
  }, []);

  // 알러젠 상세 로드
  useEffect(() => {
    if (!selectedAllergen) return;
    setLoading(true);
    apiClient.get(`/ai/insight/allergen/${selectedAllergen}`)
      .then(data => setAllergenDetail(data))
      .catch(() => {})
      .finally(() => setLoading(false));
  }, [selectedAllergen]);

  // 뉴스 로드
  useEffect(() => {
    if (activeTab === 'news') {
      apiClient.get('/ai/insight/news?days=7&limit=30')
        .then(data => setNews(data.items || []))
        .catch(() => {});
    }
  }, [activeTab]);

  const handleAllergenClick = (code) => {
    setSelectedAllergen(code);
    setActiveTab('allergen');
  };

  return (
    <div style={{ minHeight: '100vh', background: '#f5f6fa' }}>
      {/* 헤더 */}
      <div style={{
        background: 'linear-gradient(135deg, #27ae60 0%, #2ecc71 50%, #1abc9c 100%)',
        padding: '1.25rem 1rem',
        textAlign: 'center',
        color: 'white',
      }}>
        <h1
          style={{ margin: 0, fontSize: '1.5rem', cursor: 'pointer' }}
          onClick={() => navigate('/')}
        >
          AllergyInsight
        </h1>
        <p style={{ margin: '0.25rem 0 0', opacity: 0.85, fontSize: '0.9rem' }}>
          알러지 인사이트
        </p>
      </div>

      {/* 탭 네비게이션 */}
      <div style={{
        background: 'white',
        borderBottom: '1px solid #e0e0e0',
        display: 'flex',
        justifyContent: 'center',
        gap: '0',
      }}>
        {TABS.map(tab => (
          <button
            key={tab.key}
            className={`tab-btn ${activeTab === tab.key ? 'active' : ''}`}
            onClick={() => setActiveTab(tab.key)}
          >
            {tab.label}
          </button>
        ))}
      </div>

      <div style={{ maxWidth: '900px', margin: '0 auto', padding: '1.5rem 1rem' }}>
        {/* 개요 탭 */}
        {activeTab === 'overview' && overview && (
          <OverviewTab overview={overview} onAllergenClick={handleAllergenClick} />
        )}

        {/* 알러젠 탐색 탭 */}
        {activeTab === 'allergen' && (
          <AllergenTab
            overview={overview}
            selected={selectedAllergen}
            detail={allergenDetail}
            loading={loading}
            onSelect={setSelectedAllergen}
          />
        )}

        {/* 뉴스 탭 */}
        {activeTab === 'news' && (
          <NewsTab news={news} />
        )}
      </div>

      {/* 푸터 */}
      <footer style={{ textAlign: 'center', padding: '2rem 1rem', color: '#999', fontSize: '0.85rem' }}>
        <a href="/ai/consult" style={{ color: '#2980b9', textDecoration: 'none', marginRight: '1.5rem' }}>
          알러지 AI 상담
        </a>
        <a href="/" style={{ color: '#667eea', textDecoration: 'none' }}>
          AllergyInsight 홈으로
        </a>
      </footer>

      <style>{`
        .card {
          background: white;
          border-radius: 12px;
          padding: 1.5rem;
          box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        .tab-btn {
          padding: 0.85rem 1.5rem;
          border: none;
          background: transparent;
          cursor: pointer;
          font-size: 0.9rem;
          font-weight: 500;
          color: #777;
          border-bottom: 3px solid transparent;
          transition: all 0.15s;
        }
        .tab-btn:hover {
          color: #27ae60;
        }
        .tab-btn.active {
          color: #27ae60;
          border-bottom-color: #27ae60;
          font-weight: 600;
        }
        .stat-card {
          background: white;
          border-radius: 12px;
          padding: 1.25rem;
          text-align: center;
          box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        .stat-number {
          font-size: 2rem;
          font-weight: 700;
          color: #27ae60;
        }
        .stat-label {
          font-size: 0.85rem;
          color: #777;
          margin-top: 0.25rem;
        }
        .allergen-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(140px, 1fr));
          gap: 0.75rem;
        }
        .allergen-card {
          background: white;
          border: 1.5px solid #e0e0e0;
          border-radius: 10px;
          padding: 1rem;
          cursor: pointer;
          transition: all 0.15s;
          text-align: center;
        }
        .allergen-card:hover {
          border-color: #27ae60;
          box-shadow: 0 4px 12px rgba(39,174,96,0.15);
          transform: translateY(-2px);
        }
        .allergen-card.selected {
          border-color: #27ae60;
          background: #e8f5e9;
        }
        .allergen-card-name {
          font-weight: 600;
          font-size: 0.95rem;
          color: #333;
        }
        .allergen-card-count {
          font-size: 0.8rem;
          color: #27ae60;
          margin-top: 0.35rem;
        }
        .paper-item {
          padding: 0.75rem;
          border-bottom: 1px solid #f0f0f0;
        }
        .paper-item:last-child {
          border-bottom: none;
        }
        .news-item {
          padding: 1rem;
          border-bottom: 1px solid #f0f0f0;
          transition: background 0.15s;
        }
        .news-item:hover {
          background: #f8f9fa;
        }
        .news-item:last-child {
          border-bottom: none;
        }
        .year-bar-container {
          display: flex;
          align-items: flex-end;
          gap: 4px;
          height: 80px;
          padding-top: 0.5rem;
        }
        .year-bar {
          flex: 1;
          background: #27ae60;
          border-radius: 3px 3px 0 0;
          min-width: 12px;
          transition: height 0.3s;
          position: relative;
        }
        .year-bar:hover {
          opacity: 0.8;
        }
        .detail-section {
          margin-bottom: 1.5rem;
        }
        .detail-section h4 {
          margin: 0 0 0.75rem;
          color: #2c3e50;
        }
        .avoid-tag {
          display: inline-block;
          padding: 0.3rem 0.7rem;
          background: #ffebee;
          color: #c62828;
          border-radius: 16px;
          font-size: 0.8rem;
          margin: 0.25rem;
        }
        .sub-tag {
          display: inline-block;
          padding: 0.3rem 0.7rem;
          background: #e8f5e9;
          color: #2e7d32;
          border-radius: 16px;
          font-size: 0.8rem;
          margin: 0.25rem;
        }
        @media (max-width: 600px) {
          .card { padding: 1rem; }
          .allergen-grid {
            grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
          }
        }
      `}</style>
    </div>
  );
}

/**
 * 개요 탭
 */
function OverviewTab({ overview, onAllergenClick }) {
  const maxPaperCount = Math.max(...(overview.allergen_stats || []).map(a => a.paper_count), 1);
  const maxYearCount = Math.max(...(overview.by_year || []).map(y => y.count), 1);

  return (
    <>
      {/* 통계 카드 */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(150px, 1fr))', gap: '1rem', marginBottom: '1.5rem' }}>
        <div className="stat-card">
          <div className="stat-number">{overview.total_papers?.toLocaleString()}</div>
          <div className="stat-label">수집 논문 수</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{overview.allergen_stats?.filter(a => a.paper_count > 0).length}</div>
          <div className="stat-label">연구된 알러젠</div>
        </div>
        <div className="stat-card">
          <div className="stat-number">{overview.by_year?.length}</div>
          <div className="stat-label">연구 기간 (년)</div>
        </div>
      </div>

      {/* 알러젠별 논문 현황 */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ marginTop: 0, marginBottom: '1rem' }}>알러젠별 논문 현황</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {overview.allergen_stats?.filter(a => a.paper_count > 0).map(a => (
            <div
              key={a.code}
              style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', cursor: 'pointer' }}
              onClick={() => onAllergenClick(a.code)}
            >
              <span style={{ minWidth: '80px', fontSize: '0.9rem', fontWeight: 500 }}>
                {a.name_kr}
              </span>
              <div style={{ flex: 1, background: '#f0f0f0', borderRadius: '4px', height: '20px', overflow: 'hidden' }}>
                <div style={{
                  width: `${(a.paper_count / maxPaperCount) * 100}%`,
                  height: '100%',
                  background: a.category === 'food'
                    ? 'linear-gradient(90deg, #27ae60, #2ecc71)'
                    : 'linear-gradient(90deg, #2980b9, #3498db)',
                  borderRadius: '4px',
                  transition: 'width 0.5s',
                }} />
              </div>
              <span style={{ minWidth: '40px', textAlign: 'right', fontSize: '0.85rem', color: '#666' }}>
                {a.paper_count}
              </span>
            </div>
          ))}
        </div>
        {overview.allergen_stats?.every(a => a.paper_count === 0) && (
          <p style={{ color: '#999', textAlign: 'center' }}>아직 수집된 논문이 없습니다.</p>
        )}
      </div>

      {/* 연도별 논문 분포 */}
      {overview.by_year?.length > 0 && (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ marginTop: 0, marginBottom: '0.5rem' }}>연도별 논문 분포</h3>
          <div className="year-bar-container">
            {overview.by_year.slice(-15).map(y => (
              <div
                key={y.year}
                className="year-bar"
                style={{ height: `${(y.count / maxYearCount) * 100}%` }}
                title={`${y.year}: ${y.count}편`}
              />
            ))}
          </div>
          <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.7rem', color: '#999', marginTop: '0.25rem' }}>
            <span>{overview.by_year.slice(-15)[0]?.year}</span>
            <span>{overview.by_year[overview.by_year.length - 1]?.year}</span>
          </div>
        </div>
      )}

      {/* 최근 논문 */}
      {overview.recent_papers?.length > 0 && (
        <div className="card">
          <h3 style={{ marginTop: 0, marginBottom: '0.5rem' }}>최근 수집 논문</h3>
          {overview.recent_papers.map((p, i) => (
            <div key={i} className="paper-item">
              <div style={{ fontWeight: 500, fontSize: '0.9rem' }}>{p.title}</div>
              <div style={{ fontSize: '0.8rem', color: '#777', marginTop: '0.25rem' }}>
                {p.journal && <span>{p.journal} · </span>}
                {p.year && <span>{p.year} · </span>}
                {p.source && <span style={{ textTransform: 'uppercase' }}>{p.source}</span>}
              </div>
            </div>
          ))}
        </div>
      )}
    </>
  );
}

/**
 * 알러젠 탐색 탭
 */
function AllergenTab({ overview, selected, detail, loading, onSelect }) {
  const foodAllergens = overview?.allergen_stats?.filter(a => a.category === 'food') || [];
  const inhalantAllergens = overview?.allergen_stats?.filter(a => a.category === 'inhalant') || [];

  return (
    <>
      {/* 알러젠 그리드 */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h4 style={{ marginTop: 0, marginBottom: '0.5rem', color: '#27ae60' }}>식품 알러젠</h4>
        <div className="allergen-grid" style={{ marginBottom: '1rem' }}>
          {foodAllergens.map(a => (
            <div
              key={a.code}
              className={`allergen-card ${selected === a.code ? 'selected' : ''}`}
              onClick={() => onSelect(a.code)}
            >
              <div className="allergen-card-name">{a.name_kr}</div>
              <div className="allergen-card-count">{a.paper_count}편</div>
            </div>
          ))}
        </div>

        <h4 style={{ marginTop: 0, marginBottom: '0.5rem', color: '#2980b9' }}>흡입 알러젠</h4>
        <div className="allergen-grid">
          {inhalantAllergens.map(a => (
            <div
              key={a.code}
              className={`allergen-card ${selected === a.code ? 'selected' : ''}`}
              onClick={() => onSelect(a.code)}
            >
              <div className="allergen-card-name">{a.name_kr}</div>
              <div className="allergen-card-count">{a.paper_count}편</div>
            </div>
          ))}
        </div>
      </div>

      {/* 로딩 */}
      {loading && (
        <div className="card" style={{ textAlign: 'center', padding: '2rem' }}>
          <div style={{
            width: '36px', height: '36px',
            border: '4px solid #e9ecef', borderTop: '4px solid #27ae60',
            borderRadius: '50%', animation: 'spin 1s linear infinite',
            margin: '0 auto',
          }} />
          <p style={{ color: '#666', marginTop: '1rem' }}>알러젠 정보를 불러오는 중...</p>
          <style>{`@keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }`}</style>
        </div>
      )}

      {/* 알러젠 상세 */}
      {!loading && detail && detail.allergen && (
        <AllergenDetail detail={detail} />
      )}

      {/* 선택 안내 */}
      {!selected && !loading && (
        <div className="card" style={{ textAlign: 'center', color: '#999', padding: '2rem' }}>
          위 알러젠 카드를 선택하면 상세 정보를 확인할 수 있습니다.
        </div>
      )}
    </>
  );
}

/**
 * 알러젠 상세 정보
 */
function AllergenDetail({ detail }) {
  const { allergen, papers, paper_count } = detail;

  return (
    <div className="card">
      {/* 헤더 */}
      <div style={{
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        marginBottom: '1rem',
        paddingBottom: '0.75rem',
        borderBottom: '2px solid #27ae60',
      }}>
        <div>
          <h3 style={{ margin: 0 }}>{allergen.name_kr} ({allergen.name_en})</h3>
          <span style={{
            display: 'inline-block',
            marginTop: '0.35rem',
            padding: '0.2rem 0.6rem',
            borderRadius: '12px',
            fontSize: '0.75rem',
            background: allergen.category === 'food' ? '#e8f5e9' : '#e3f2fd',
            color: allergen.category === 'food' ? '#2e7d32' : '#1565c0',
          }}>
            {allergen.category === 'food' ? '식품' : '흡입'}
          </span>
        </div>
        <a
          href={`/ai/consult`}
          style={{
            padding: '0.5rem 1rem',
            background: '#2980b9',
            color: 'white',
            borderRadius: '8px',
            textDecoration: 'none',
            fontSize: '0.85rem',
          }}
        >
          AI 상담하기
        </a>
      </div>

      {/* 설명 */}
      {allergen.description && (
        <div className="detail-section">
          <p style={{ color: '#555', margin: 0, lineHeight: 1.6 }}>{allergen.description}</p>
        </div>
      )}

      {/* 회피 식품 */}
      {allergen.avoid_foods?.length > 0 && (
        <div className="detail-section">
          <h4>회피 식품</h4>
          <div style={{ display: 'flex', flexWrap: 'wrap' }}>
            {allergen.avoid_foods.map((f, i) => (
              <span key={i} className="avoid-tag">{f}</span>
            ))}
          </div>
        </div>
      )}

      {/* 대체 식품 */}
      {allergen.substitutes?.length > 0 && (
        <div className="detail-section">
          <h4>대체 식품</h4>
          {allergen.substitutes.map((s, i) => (
            <div key={i} style={{ marginBottom: '0.5rem' }}>
              <span style={{ fontWeight: 500, fontSize: '0.9rem' }}>{s.original}</span>
              <span style={{ color: '#999', margin: '0 0.35rem' }}>→</span>
              {s.alternatives?.map((alt, j) => (
                <span key={j} className="sub-tag">{alt}</span>
              ))}
            </div>
          ))}
        </div>
      )}

      {/* 관련 논문 */}
      <div className="detail-section">
        <h4>관련 논문 ({paper_count}건)</h4>
        {papers.length > 0 ? (
          papers.map((p, i) => (
            <div key={i} className="paper-item" style={{ borderLeft: '3px solid #27ae60', paddingLeft: '0.75rem', marginBottom: '0.5rem' }}>
              <div style={{ fontWeight: 500, fontSize: '0.9rem' }}>{p.title}</div>
              <div style={{ fontSize: '0.8rem', color: '#777', marginTop: '0.25rem' }}>
                {p.authors && <span>{typeof p.authors === 'string' ? p.authors : p.authors?.slice(0, 3).join(', ')} · </span>}
                {p.year && <span>{p.year} · </span>}
                {p.journal && <span>{p.journal}</span>}
              </div>
              {p.abstract && (
                <div style={{ fontSize: '0.8rem', color: '#555', marginTop: '0.35rem' }}>
                  {p.abstract}
                </div>
              )}
            </div>
          ))
        ) : (
          <p style={{ color: '#999', fontSize: '0.9rem' }}>아직 이 알러젠에 대한 논문이 수집되지 않았습니다.</p>
        )}
      </div>
    </div>
  );
}

/**
 * 뉴스 탭
 */
function NewsTab({ news }) {
  if (news.length === 0) {
    return (
      <div className="card" style={{ textAlign: 'center', color: '#999', padding: '2rem' }}>
        최근 7일 동안 수집된 뉴스가 없습니다.
      </div>
    );
  }

  return (
    <div className="card">
      <h3 style={{ marginTop: 0, marginBottom: '0.5rem' }}>최신 알러지 뉴스</h3>
      <p style={{ color: '#999', fontSize: '0.85rem', marginTop: 0, marginBottom: '1rem' }}>
        최근 7일간 수집된 뉴스 {news.length}건
      </p>
      {news.map((item, i) => (
        <div key={i} className="news-item">
          <a
            href={item.url}
            target="_blank"
            rel="noopener noreferrer"
            style={{ textDecoration: 'none', color: 'inherit' }}
          >
            <div style={{ fontWeight: 500, fontSize: '0.95rem', color: '#333' }}>{item.title}</div>
            {item.summary && (
              <div style={{ fontSize: '0.85rem', color: '#666', marginTop: '0.35rem', lineHeight: 1.5 }}>
                {item.summary}
              </div>
            )}
            <div style={{ fontSize: '0.75rem', color: '#aaa', marginTop: '0.35rem', display: 'flex', gap: '0.75rem' }}>
              {item.source && <span>{item.source}</span>}
              {item.published_at && <span>{new Date(item.published_at).toLocaleDateString('ko-KR')}</span>}
              {item.category && (
                <span style={{
                  padding: '0.1rem 0.4rem',
                  background: '#f0f0f0',
                  borderRadius: '4px',
                }}>
                  {item.category}
                </span>
              )}
              {item.importance_score != null && (
                <span>중요도 {item.importance_score}</span>
              )}
            </div>
          </a>
        </div>
      ))}
    </div>
  );
}

export default AIInsightPage;
