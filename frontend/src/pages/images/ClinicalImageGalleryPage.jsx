/**
 * Clinical Image Gallery Page (Phase 4 P4-PR1)
 *
 * 비회원 공개 — 논문/전문기관 출처의 알러지 임상 이미지를 알러젠/증상 필터로
 * 단방향 표시. 사용자 사진 업로드/매칭/비교는 제공하지 않는다.
 *
 * Phase 4 P4-PR1 단계에서는 시드 데이터가 비어 있을 수 있으며, 그때는
 * "큐레이션 준비 중" placeholder 가 표시된다.
 */
import React, { useEffect, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../../shared/services/apiClient';
import MedicalDisclaimer from '../../shared/components/MedicalDisclaimer';
import BackToHomeBar from '../../shared/components/BackToHomeBar';

const SEVERITY_OPTIONS = [
  { value: '', label: '전체' },
  { value: 'mild', label: '경미' },
  { value: 'moderate', label: '중등도' },
  { value: 'severe', label: '심각' },
];

const ClinicalImageGalleryPage = () => {
  const navigate = useNavigate();

  // 활성 알러젠 36종 (Phase 1 화이트리스트)
  const [allergens, setAllergens] = useState([]);
  const [filterAllergen, setFilterAllergen] = useState('');
  const [filterSymptom, setFilterSymptom] = useState('');
  const [filterSeverity, setFilterSeverity] = useState('');

  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [message, setMessage] = useState(null);
  const [disclaimer, setDisclaimer] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    apiClient
      .get('/public/mast/allergens')
      .then((data) => setAllergens(data.items ?? []))
      .catch(() => {});
  }, []);

  // 페이지 진입 시 한 번 자동 조회 (전체)
  useEffect(() => {
    fetchImages();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const fetchImages = async (overrides = {}) => {
    try {
      setLoading(true);
      setError(null);
      const params = new URLSearchParams();
      const allergen = overrides.allergen ?? filterAllergen;
      const symptom = overrides.symptom ?? filterSymptom;
      const severity = overrides.severity ?? filterSeverity;
      if (allergen) params.set('allergen', allergen);
      if (symptom.trim()) params.set('symptom', symptom.trim());
      if (severity) params.set('severity', severity);
      params.set('limit', '24');
      const data = await apiClient.get(`/public/clinical-images?${params.toString()}`);
      setItems(data.items ?? []);
      setTotal(data.total ?? 0);
      setMessage(data.message ?? null);
      setDisclaimer(data.disclaimer ?? '');
    } catch (err) {
      setError(err.response?.data?.detail || '이미지를 불러오지 못했습니다.');
      setItems([]);
      setTotal(0);
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = (e) => {
    e?.preventDefault();
    fetchImages();
  };

  const resetFilters = () => {
    setFilterAllergen('');
    setFilterSymptom('');
    setFilterSeverity('');
    fetchImages({ allergen: '', symptom: '', severity: '' });
  };

  return (
    <div style={{ minHeight: '100vh', background: '#f5f6fa' }}>
      <BackToHomeBar />
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
          알러지 임상 이미지 갤러리
        </p>
      </div>

      <div style={{ maxWidth: '1100px', margin: '0 auto', padding: '1.5rem 1rem' }}>
        <div style={{ marginBottom: '1rem' }}>
          <MedicalDisclaimer variant="banner" />
        </div>

        <div style={cardStyle}>
          <h2 style={{ margin: '0 0 0.5rem' }}>논문 출처 임상 이미지</h2>
          <p style={{ color: '#666', margin: 0, fontSize: '0.9rem', lineHeight: 1.6 }}>
            본 갤러리는 PubMed Central · 전문학회 등에서 라이선스(CC-BY/CC0/Public Domain)가 검증된
            알러지 임상 이미지를 단방향으로 보여드립니다. <strong>사용자가 업로드한 사진의 분석 · 비교 · 진단은 제공하지 않습니다</strong>.
            모든 이미지는 출처와 라이선스가 함께 표시됩니다.
          </p>
        </div>

        <form onSubmit={handleSubmit} style={cardStyle}>
          <h3 style={{ margin: '0 0 0.6rem' }}>필터</h3>
          <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
            <select
              value={filterAllergen}
              onChange={(e) => setFilterAllergen(e.target.value)}
              style={inputStyle}
            >
              <option value="">알러젠 선택 (전체)</option>
              {allergens.map((a) => (
                <option key={a.code} value={a.code}>
                  {a.name_kr} ({a.name_en})
                </option>
              ))}
            </select>
            <input
              type="text"
              placeholder="증상 키워드 (예: urticaria, 두드러기)"
              value={filterSymptom}
              onChange={(e) => setFilterSymptom(e.target.value)}
              style={{ ...inputStyle, flex: 1, minWidth: '180px' }}
            />
            <select
              value={filterSeverity}
              onChange={(e) => setFilterSeverity(e.target.value)}
              style={{ ...inputStyle, flex: '0 0 130px' }}
            >
              {SEVERITY_OPTIONS.map((s) => (
                <option key={s.value} value={s.value}>심각도: {s.label}</option>
              ))}
            </select>
          </div>
          <div style={{ marginTop: '0.75rem', display: 'flex', gap: '0.5rem' }}>
            <button type="submit" disabled={loading} style={primaryBtnStyle(!loading)}>
              {loading ? '불러오는 중...' : '검색'}
            </button>
            <button type="button" onClick={resetFilters} style={secondaryBtnStyle}>
              필터 초기화
            </button>
          </div>
        </form>

        {error && (
          <div role="alert" style={{ ...cardStyle, background: '#ffebee', color: '#c62828' }}>
            {error}
          </div>
        )}

        {!loading && items.length === 0 && (
          <div style={cardStyle}>
            <h3 style={{ margin: '0 0 0.5rem' }}>📷 이미지 큐레이션 준비 중</h3>
            <p style={{ color: '#666', margin: 0, lineHeight: 1.6 }}>
              {message ||
                '현재 노출 가능한 임상 이미지가 없습니다. 본 갤러리는 단계적으로 큐레이션 중이며, ' +
                'PubMed Central Open Access · 전문학회 자료에서 라이선스(CC-BY/CC0/Public Domain)가 명확히 검증된 이미지만 추가됩니다.'}
            </p>
          </div>
        )}

        {!loading && items.length > 0 && (
          <div style={cardStyle}>
            <h3 style={{ margin: '0 0 0.6rem' }}>
              결과 <span style={{ color: '#666', fontWeight: 'normal' }}>({total}건)</span>
            </h3>
            <div
              style={{
                display: 'grid',
                gridTemplateColumns: 'repeat(auto-fill, minmax(220px, 1fr))',
                gap: '0.85rem',
              }}
            >
              {items.map((it) => <ImageCard key={it.id} item={it} />)}
            </div>
          </div>
        )}

        {disclaimer && (
          <div style={{ ...cardStyle, background: '#f5f5f5', borderLeft: '3px solid #ffc107', color: '#5d4037', fontSize: '0.85rem' }}>
            {disclaimer}
          </div>
        )}
      </div>

      <footer style={{ textAlign: 'center', padding: '2rem 1rem', color: '#999', fontSize: '0.85rem' }}>
        <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', flexWrap: 'wrap' }}>
          <a href="/help/medical-disclaimer.html" target="_blank" rel="noopener" style={linkStyle}>
            의료 정보 면책 안내
          </a>
          <span style={{ color: '#ddd' }}>·</span>
          <a href="/mast" style={linkStyle}>MAST 등급</a>
          <span style={{ color: '#ddd' }}>·</span>
          <a href="/symptoms" style={linkStyle}>증상 매칭</a>
          <span style={{ color: '#ddd' }}>·</span>
          <a href="/drugs" style={linkStyle}>약물 성분</a>
          <span style={{ color: '#ddd' }}>·</span>
          <a href="/" style={linkStyle}>홈</a>
        </div>
      </footer>
    </div>
  );
};

const ImageCard = ({ item }) => {
  const src = item.thumbnail_url || item.image_url;
  return (
    <div style={{ background: 'white', border: '1px solid #e0e0e0', borderRadius: '8px', overflow: 'hidden' }}>
      <div style={{ aspectRatio: '4 / 3', background: '#f5f5f5', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
        {src ? (
          <img
            src={src}
            alt={item.caption_en || item.caption_kr || 'clinical image'}
            style={{ maxWidth: '100%', maxHeight: '100%', objectFit: 'cover' }}
            loading="lazy"
          />
        ) : (
          <span style={{ color: '#999', fontSize: '0.85rem' }}>이미지 없음</span>
        )}
      </div>
      <div style={{ padding: '0.6rem 0.75rem', fontSize: '0.85rem' }}>
        {item.caption_kr && <div style={{ color: '#333', marginBottom: '0.2rem' }}>{item.caption_kr}</div>}
        {item.caption_en && (
          <div style={{ color: '#666', fontStyle: 'italic', fontSize: '0.78rem', marginBottom: '0.4rem' }}>
            {item.caption_en}
          </div>
        )}
        {item.allergen_code && (
          <div style={{ fontSize: '0.78rem', color: '#1565c0' }}>알러젠: {item.allergen_code}</div>
        )}
        {item.severity_level && (
          <div style={{ fontSize: '0.78rem', color: '#666' }}>심각도: {item.severity_level}</div>
        )}
        <div style={{ marginTop: '0.45rem', fontSize: '0.75rem', color: '#888', borderTop: '1px solid #f0f0f0', paddingTop: '0.4rem' }}>
          {item.source?.title && <div>{item.source.title}{item.source.year ? ` (${item.source.year})` : ''}</div>}
          {item.license?.name && (
            <div>
              {item.license.url ? (
                <a href={item.license.url} target="_blank" rel="noopener noreferrer" style={{ color: '#1976d2' }}>
                  {item.license.name}
                </a>
              ) : item.license.name}
              {item.license.attribution && ` · ${item.license.attribution}`}
            </div>
          )}
        </div>
      </div>
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

const inputStyle = {
  padding: '0.55rem 0.75rem',
  border: '1px solid #e0e0e0',
  borderRadius: '8px',
  fontSize: '0.9rem',
  background: 'white',
};

const primaryBtnStyle = (enabled) => ({
  padding: '0.55rem 1.25rem',
  border: 'none',
  borderRadius: '8px',
  background: enabled ? '#1976d2' : '#bdbdbd',
  color: 'white',
  fontSize: '0.9rem',
  fontWeight: 600,
  cursor: enabled ? 'pointer' : 'not-allowed',
});

const secondaryBtnStyle = {
  padding: '0.55rem 1rem',
  border: '1px solid #e0e0e0',
  borderRadius: '8px',
  background: 'white',
  color: '#666',
  fontSize: '0.9rem',
  cursor: 'pointer',
};

const linkStyle = {
  color: '#1976d2',
  textDecoration: 'none',
};

export default ClinicalImageGalleryPage;
