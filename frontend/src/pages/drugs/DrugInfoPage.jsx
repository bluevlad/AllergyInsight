/**
 * Drug Info Page (Phase 3)
 *
 * 비회원 공개 — 알러지 치료 약물의 성분명 · 작용기전 · ATC 분류 · 출처 표시.
 * 약사법 회피 원칙: 제품명·복용량·효능효과·복약 지시 일절 노출하지 않음.
 */
import React, { useEffect, useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../../shared/services/apiClient';
import MedicalDisclaimer from '../../shared/components/MedicalDisclaimer';

const DrugInfoPage = () => {
  const navigate = useNavigate();
  const [classes, setClasses] = useState([]);
  const [classesError, setClassesError] = useState(null);

  const [query, setQuery] = useState('');
  const [allergyOnly, setAllergyOnly] = useState(true);
  const [atcPrefix, setAtcPrefix] = useState('');
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [searched, setSearched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    let cancelled = false;
    apiClient
      .get('/public/drugs/allergy-classes')
      .then((data) => {
        if (!cancelled) setClasses(data.items ?? []);
      })
      .catch(() => {
        if (!cancelled) setClassesError('약리군 카탈로그를 불러오지 못했습니다.');
      });
    return () => {
      cancelled = true;
    };
  }, []);

  const handleSearch = async (overrideAtc) => {
    try {
      setLoading(true);
      setError(null);
      setSearched(true);
      const params = new URLSearchParams();
      if (query.trim()) params.set('q', query.trim());
      params.set('allergy_only', allergyOnly ? 'true' : 'false');
      const atc = overrideAtc ?? atcPrefix;
      if (atc) params.set('atc_prefix', atc);
      params.set('limit', '30');
      const data = await apiClient.get(`/public/drugs/search?${params.toString()}`);
      setItems(data.items ?? []);
      setTotal(data.total ?? 0);
    } catch (err) {
      setError(err.response?.data?.detail || '검색에 실패했습니다.');
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  const handleClassClick = (prefix) => {
    setAtcPrefix(prefix);
    setAllergyOnly(true);
    handleSearch(prefix);
    window.scrollTo({ top: 280, behavior: 'smooth' });
  };

  const onKeyDown = (e) => {
    if (e.key === 'Enter') {
      e.preventDefault();
      handleSearch();
    }
  };

  return (
    <div style={{ minHeight: '100vh', background: '#f5f6fa' }}>
      <div
        style={{
          background: 'linear-gradient(135deg, #2980b9 0%, #3498db 50%, #2c3e50 100%)',
          padding: '1.25rem 1rem',
          textAlign: 'center',
          color: 'white',
        }}
      >
        <h1
          style={{ margin: 0, fontSize: '1.5rem', cursor: 'pointer' }}
          onClick={() => navigate('/')}
        >
          AllergyInsight
        </h1>
        <p style={{ margin: '0.25rem 0 0', opacity: 0.85, fontSize: '0.9rem' }}>
          알러지 약물 성분 정보
        </p>
      </div>

      <div style={{ maxWidth: '900px', margin: '0 auto', padding: '1.5rem 1rem' }}>
        <div style={{ marginBottom: '1rem' }}>
          <MedicalDisclaimer variant="banner" />
        </div>

        <div style={cardStyle}>
          <h2 style={{ margin: '0 0 0.5rem' }}>알러지 치료 약물 성분 정보</h2>
          <p style={{ color: '#666', margin: 0, fontSize: '0.9rem', lineHeight: 1.6 }}>
            본 페이지는 알러지 치료에 사용되는 약물의 <strong>성분명(INN) · 작용기전 · ATC 분류 · 출처</strong>만 보여드립니다.
            제품명 · 복용량 · 복약 지시는 제공하지 않으며, 약물 사용은 반드시 처방 · 복약 지도를 받으세요.
          </p>
        </div>

        {/* 약리군 카탈로그 */}
        <div style={cardStyle}>
          <h3 style={{ margin: '0 0 0.6rem' }}>알러지 치료 약리군 (ATC 분류)</h3>
          {classesError && <p style={{ color: '#c62828' }}>{classesError}</p>}
          {classes.length === 0 && !classesError && <p style={{ color: '#999' }}>불러오는 중...</p>}
          {classes.length > 0 && (
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))', gap: '0.6rem' }}>
              {classes.map((c) => (
                <button
                  key={c.atc_prefix}
                  type="button"
                  onClick={() => handleClassClick(c.atc_prefix)}
                  style={{
                    padding: '0.75rem 0.85rem',
                    border: atcPrefix === c.atc_prefix ? '2px solid #1976d2' : '1px solid #e0e0e0',
                    borderRadius: '8px',
                    background: atcPrefix === c.atc_prefix ? '#e3f2fd' : 'white',
                    cursor: 'pointer',
                    textAlign: 'left',
                  }}
                >
                  <div style={{ fontWeight: 600, fontSize: '0.95rem' }}>
                    {c.name_kr}
                  </div>
                  <div style={{ fontSize: '0.8rem', color: '#666', marginTop: '0.2rem' }}>
                    {c.name_en} · ATC {c.atc_prefix}
                  </div>
                  <div style={{ fontSize: '0.78rem', color: '#888', marginTop: '0.35rem', lineHeight: 1.45 }}>
                    {c.description}
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* 검색 */}
        <div style={cardStyle}>
          <h3 style={{ margin: '0 0 0.6rem' }}>성분 검색</h3>
          <div style={{ display: 'flex', gap: '0.5rem', flexWrap: 'wrap' }}>
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyDown={onKeyDown}
              placeholder="성분명(INN) 또는 RxNorm ID — 예: cetirizine, montelukast, 20610"
              style={{
                flex: 1,
                minWidth: '240px',
                padding: '0.6rem 0.75rem',
                border: '1px solid #e0e0e0',
                borderRadius: '8px',
                fontSize: '0.95rem',
              }}
            />
            <button
              onClick={() => handleSearch()}
              disabled={loading}
              style={{
                padding: '0.6rem 1.25rem',
                border: 'none',
                borderRadius: '8px',
                background: loading ? '#bdbdbd' : '#1976d2',
                color: 'white',
                fontWeight: 600,
                cursor: loading ? 'not-allowed' : 'pointer',
              }}
            >
              {loading ? '검색 중...' : '검색'}
            </button>
          </div>
          <div style={{ marginTop: '0.6rem', display: 'flex', gap: '1rem', alignItems: 'center', flexWrap: 'wrap', fontSize: '0.85rem' }}>
            <label style={{ display: 'flex', alignItems: 'center', gap: '0.35rem' }}>
              <input
                type="checkbox"
                checked={allergyOnly}
                onChange={(e) => setAllergyOnly(e.target.checked)}
              />
              알러지 약리군만 검색
            </label>
            {atcPrefix && (
              <span style={{ color: '#1976d2' }}>
                ATC 필터: <strong>{atcPrefix}</strong>
                <button
                  type="button"
                  onClick={() => setAtcPrefix('')}
                  style={{ marginLeft: '0.4rem', background: 'none', border: 'none', color: '#999', cursor: 'pointer', textDecoration: 'underline' }}
                >
                  해제
                </button>
              </span>
            )}
          </div>
        </div>

        {/* 결과 */}
        {error && (
          <div role="alert" style={{ ...cardStyle, background: '#ffebee', color: '#c62828' }}>
            {error}
          </div>
        )}

        {searched && !loading && (
          <div style={cardStyle}>
            <h3 style={{ margin: '0 0 0.6rem' }}>
              검색 결과 {total > 0 && <span style={{ color: '#666', fontWeight: 'normal' }}>({total}건)</span>}
            </h3>
            {items.length === 0 ? (
              <p style={{ color: '#999', margin: 0 }}>일치하는 성분을 찾지 못했습니다.</p>
            ) : (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
                {items.map((it) => <IngredientCard key={it.id} item={it} />)}
              </div>
            )}
            <div
              style={{
                marginTop: '0.85rem',
                padding: '0.6rem 0.85rem',
                background: '#f5f5f5',
                borderLeft: '3px solid #ffc107',
                color: '#5d4037',
                fontSize: '0.78rem',
                lineHeight: 1.5,
              }}
            >
              {items[0]?.disclaimer || '본 정보는 약물 성분 교육 목적이며, 특정 제품 · 복용량은 제공하지 않습니다.'}
            </div>
          </div>
        )}
      </div>

      <footer style={{ textAlign: 'center', padding: '2rem 1rem', color: '#999', fontSize: '0.85rem' }}>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          <a href="/help/medical-disclaimer.html" target="_blank" rel="noopener" style={linkStyle}>
            의료 정보 면책 안내
          </a>
          <span style={{ color: '#ddd' }}>·</span>
          <a href="/mast" style={linkStyle}>MAST 등급 매칭</a>
          <span style={{ color: '#ddd' }}>·</span>
          <a href="/symptoms" style={linkStyle}>증상 매칭</a>
          <span style={{ color: '#ddd' }}>·</span>
          <a href="/ai/consult" style={linkStyle}>AI 상담</a>
          <span style={{ color: '#ddd' }}>·</span>
          <a href="/" style={linkStyle}>홈</a>
        </div>
      </footer>
    </div>
  );
};

const IngredientCard = ({ item }) => {
  const [expanded, setExpanded] = useState(false);
  return (
    <div
      style={{
        padding: '0.85rem 1rem',
        border: '1px solid #e0e0e0',
        borderRadius: '8px',
        background: 'white',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', flexWrap: 'wrap', gap: '0.5rem' }}>
        <div>
          <strong style={{ fontSize: '1.05rem' }}>{item.inn}</strong>
          {item.atc_code && (
            <span style={{ marginLeft: '0.5rem', color: '#666', fontSize: '0.85rem' }}>
              ATC {item.atc_code}
            </span>
          )}
          {item.rxcui && (
            <span style={{ marginLeft: '0.5rem', color: '#aaa', fontSize: '0.8rem' }}>
              RxNorm {item.rxcui}
            </span>
          )}
        </div>
        {item.is_allergy_related ? (
          <span style={{ padding: '0.2rem 0.55rem', background: '#e3f2fd', color: '#1565c0', borderRadius: '999px', fontSize: '0.75rem', fontWeight: 600 }}>
            알러지 약리군
          </span>
        ) : (
          <span style={{ padding: '0.2rem 0.55rem', background: '#f5f5f5', color: '#666', borderRadius: '999px', fontSize: '0.75rem' }}>
            기타 분류
          </span>
        )}
      </div>

      {item.atc_category && (
        <div style={{ marginTop: '0.4rem', fontSize: '0.85rem', color: '#444' }}>
          분류: <strong>{item.atc_category.name_kr}</strong>{' '}
          <span style={{ color: '#888' }}>({item.atc_category.name_en})</span>
        </div>
      )}

      {item.moa && (
        <div style={{ marginTop: '0.4rem', fontSize: '0.88rem', color: '#444', lineHeight: 1.55 }}>
          <strong>작용기전:</strong> {item.moa}
        </div>
      )}

      {(item.citations?.length > 0 || item.atc_category?.description) && (
        <button
          type="button"
          onClick={() => setExpanded(!expanded)}
          style={{ marginTop: '0.5rem', background: 'none', border: 'none', color: '#1976d2', cursor: 'pointer', fontSize: '0.85rem', padding: 0 }}
        >
          {expanded ? '간단히 보기 ▲' : '자세히 / 출처 보기 ▼'}
        </button>
      )}

      {expanded && (
        <div style={{ marginTop: '0.6rem', padding: '0.6rem 0.85rem', background: '#fafafa', borderRadius: '6px' }}>
          {item.atc_category?.description && (
            <p style={{ margin: '0 0 0.5rem', fontSize: '0.85rem', color: '#555', lineHeight: 1.6 }}>
              {item.atc_category.description}
            </p>
          )}
          {item.anticholinergic_score !== null && item.anticholinergic_score !== undefined && (
            <p style={{ margin: '0 0 0.5rem', fontSize: '0.82rem', color: '#666' }}>
              항콜린 부담 점수 (ACB): {item.anticholinergic_score}
            </p>
          )}
          {item.citations?.length > 0 && (
            <div>
              <div style={{ fontSize: '0.82rem', fontWeight: 600, marginBottom: '0.35rem' }}>출처</div>
              <ul style={{ margin: 0, paddingLeft: '1.1rem', fontSize: '0.82rem', color: '#444' }}>
                {item.citations.map((c, i) => (
                  <li key={i} style={{ marginBottom: '0.25rem' }}>
                    <a href={c.url} target="_blank" rel="noopener noreferrer" style={{ color: '#1976d2' }}>
                      {c.source_name}
                    </a>{' '}
                    <span style={{ color: '#999' }}>· {c.license}</span>
                  </li>
                ))}
              </ul>
            </div>
          )}
        </div>
      )}
    </div>
  );
};

const cardStyle = {
  padding: '1rem 1.25rem',
  background: 'white',
  border: '1px solid #e0e0e0',
  borderRadius: '8px',
  marginBottom: '1rem',
};

const linkStyle = {
  color: '#1976d2',
  textDecoration: 'none',
};

export default DrugInfoPage;
