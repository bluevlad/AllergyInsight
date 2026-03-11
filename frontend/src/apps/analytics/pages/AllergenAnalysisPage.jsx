/**
 * 알러젠 분석 페이지 (공개, read-only)
 * 관리자 화면과 동일한 알러젠 마스터 데이터 카드 표시
 * + 양성률 TOP10, 트렌드, 등급분포, 동반양성 알러젠
 */
import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, BarChart, Bar, PieChart, Pie, Cell,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
} from 'recharts';
import { analyticsApi } from '../services/analyticsApi';

const COLORS = ['#1abc9c', '#3498db', '#2ecc71', '#e74c3c', '#f39c12', '#9b59b6', '#e67e22', '#667eea'];

const getTypeName = (type) => {
  const typeNames = {
    seafood: '해산물', meat: '육류', egg: '달걀', dairy: '유제품',
    grain: '곡물', legume: '콩류', nut: '견과류', fruit: '과일',
    vegetable: '채소', spice: '향신료', pollen: '꽃가루', mite: '진드기',
    animal: '동물', mold: '곰팡이', insect: '곤충', other: '기타',
  };
  return typeNames[type] || type;
};

const AllergenAnalysisPage = () => {
  // 알러젠 마스터 데이터 상태
  const [allergens, setAllergens] = useState([]);
  const [allergenLoading, setAllergenLoading] = useState(true);
  const [categoryFilter, setCategoryFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [search, setSearch] = useState('');
  const [selectedAllergenDetail, setSelectedAllergenDetail] = useState(null);

  // 분석 데이터 상태
  const [overview, setOverview] = useState(null);
  const [selectedAllergen, setSelectedAllergen] = useState('');
  const [trendData, setTrendData] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadAllergens();
    loadOverview();
  }, []);

  useEffect(() => {
    loadAllergens();
  }, [categoryFilter, typeFilter]);

  useEffect(() => {
    if (selectedAllergen) loadTrend(selectedAllergen);
  }, [selectedAllergen]);

  // 알러젠 마스터 데이터 로드
  const loadAllergens = async () => {
    try {
      setAllergenLoading(true);
      const params = {};
      if (categoryFilter) params.category = categoryFilter;
      if (typeFilter) params.type = typeFilter;
      const response = await analyticsApi.getAllergenList(params);
      setAllergens(response.items || []);
    } catch (err) {
      console.error('Allergens load failed:', err);
    } finally {
      setAllergenLoading(false);
    }
  };

  // 분석 데이터 로드
  const loadOverview = async () => {
    try {
      setLoading(true);
      setError(null);
      const result = await analyticsApi.getOverview();
      setOverview(result);
      if (result.allergens?.length > 0 && !selectedAllergen) {
        setSelectedAllergen(result.allergens[0].allergen_code);
      }
    } catch (err) {
      setError('알러젠 분석 데이터를 불러오지 못했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const loadTrend = async (code) => {
    try {
      const result = await analyticsApi.getAllergenTrend(code, 12);
      setTrendData(result);
    } catch (err) {
      console.error('Trend load failed:', err);
    }
  };

  const handleViewDetail = async (code) => {
    try {
      const detail = await analyticsApi.getAllergenDetail(code);
      setSelectedAllergenDetail(detail);
    } catch (err) {
      console.error('Allergen detail load failed:', err);
    }
  };

  // 검색 필터
  const filteredAllergens = allergens.filter((a) => {
    if (!search) return true;
    const searchLower = search.toLowerCase();
    return (
      a.code.toLowerCase().includes(searchLower) ||
      a.name_kr.includes(search) ||
      a.name_en.toLowerCase().includes(searchLower)
    );
  });

  // 카테고리별 그룹화 (food → inhalant 순서)
  const groupedAllergens = filteredAllergens.reduce((acc, allergen) => {
    const cat = allergen.category;
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(allergen);
    return acc;
  }, {});

  const categoryOrder = ['food', 'inhalant'];
  const sortedGroups = Object.entries(groupedAllergens).sort(([a], [b]) => {
    return (categoryOrder.indexOf(a) === -1 ? 99 : categoryOrder.indexOf(a)) -
           (categoryOrder.indexOf(b) === -1 ? 99 : categoryOrder.indexOf(b));
  });

  // 분석 차트 데이터
  const analyticsAllergens = overview?.allergens || [];
  const top10 = analyticsAllergens.slice(0, 10);
  const barData = top10.map(a => ({
    name: a.allergen_code,
    양성률: +(a.positive_rate * 100).toFixed(1),
  }));

  const trendChartData = (trendData?.trend || []).map(t => ({
    period: t.period?.slice(0, 7),
    양성률: +(t.positive_rate * 100).toFixed(1),
    평균등급: +t.avg_grade?.toFixed(2),
  }));

  const gradeDistData = trendData?.trend?.length > 0
    ? Object.entries(trendData.trend[trendData.trend.length - 1].grade_distribution || {}).map(([grade, count]) => ({
        name: `${grade}등급`,
        value: count,
      }))
    : [];

  const selectedDetail = analyticsAllergens.find(a => a.allergen_code === selectedAllergen);
  const cooccurrence = selectedDetail?.cooccurrence_top5 || [];

  return (
    <div className="aa-page">
      <h2 className="aa-page-title">알러젠 분석</h2>
      <p className="aa-subtitle">SGTi-Allergy Screen PLUS 120종 알러젠 데이터</p>

      {/* ===== 알러젠 마스터 데이터 섹션 ===== */}
      <div className="aa-toolbar">
        <input
          type="text"
          placeholder="코드, 한글명, 영문명 검색..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="aa-search-input"
        />
        <select value={categoryFilter} onChange={(e) => setCategoryFilter(e.target.value)} className="aa-filter-select">
          <option value="">전체 카테고리</option>
          <option value="food">식품</option>
          <option value="inhalant">흡입</option>
        </select>
        <select value={typeFilter} onChange={(e) => setTypeFilter(e.target.value)} className="aa-filter-select">
          <option value="">전체 타입</option>
          <option value="seafood">해산물</option>
          <option value="meat">육류</option>
          <option value="egg">달걀</option>
          <option value="dairy">유제품</option>
          <option value="grain">곡물</option>
          <option value="legume">콩류</option>
          <option value="nut">견과류</option>
          <option value="fruit">과일</option>
          <option value="vegetable">채소</option>
          <option value="spice">향신료</option>
          <option value="pollen">꽃가루</option>
          <option value="mite">진드기</option>
          <option value="animal">동물</option>
          <option value="mold">곰팡이</option>
          <option value="insect">곤충</option>
        </select>
      </div>

      <div className="aa-stats-bar">
        <span>전체: <strong>{filteredAllergens.length}종</strong></span>
        <span>식품: <strong>{filteredAllergens.filter((a) => a.category === 'food').length}종</strong></span>
        <span>흡입: <strong>{filteredAllergens.filter((a) => a.category === 'inhalant').length}종</strong></span>
      </div>

      {allergenLoading ? (
        <div className="aa-loading">로딩 중...</div>
      ) : (
        <div className="aa-allergens-grid">
          {sortedGroups.map(([category, items]) => (
            <div key={category} className="aa-category-section">
              <h3 className={`aa-category-header ${category}`}>
                {category === 'food' ? '식품 (Food)' : '흡입 (Inhalant)'}
                <span className="aa-cat-count">{items.length}종</span>
              </h3>
              <div className="aa-allergen-cards">
                {items.map((allergen) => (
                  <div
                    key={allergen.code}
                    className={`aa-allergen-card ${allergen.has_prescription ? 'has-prescription' : ''}`}
                    onClick={() => handleViewDetail(allergen.code)}
                  >
                    <div className="aa-allergen-code">{allergen.code}</div>
                    <div className="aa-allergen-name">{allergen.name_kr}</div>
                    <div className="aa-allergen-name-en">{allergen.name_en}</div>
                    <div className="aa-allergen-type">{getTypeName(allergen.type)}</div>
                    {allergen.has_prescription && (
                      <span className="aa-prescription-badge">처방</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 알러젠 상세 모달 */}
      {selectedAllergenDetail && (
        <div className="aa-modal-overlay" onClick={() => setSelectedAllergenDetail(null)}>
          <div className="aa-modal" onClick={(e) => e.stopPropagation()}>
            <div className="aa-modal-header">
              <h3>{selectedAllergenDetail.name_kr}</h3>
              <button onClick={() => setSelectedAllergenDetail(null)}>X</button>
            </div>
            <div className="aa-modal-body">
              <div className="aa-detail-row">
                <span className="aa-label">코드:</span>
                <span className="aa-value">{selectedAllergenDetail.code}</span>
              </div>
              <div className="aa-detail-row">
                <span className="aa-label">영문명:</span>
                <span className="aa-value">{selectedAllergenDetail.name_en}</span>
              </div>
              <div className="aa-detail-row">
                <span className="aa-label">카테고리:</span>
                <span className="aa-value">
                  {selectedAllergenDetail.category === 'food' ? '식품' : '흡입'}
                </span>
              </div>
              <div className="aa-detail-row">
                <span className="aa-label">타입:</span>
                <span className="aa-value">{getTypeName(selectedAllergenDetail.type)}</span>
              </div>
              {selectedAllergenDetail.description && (
                <div className="aa-detail-row">
                  <span className="aa-label">설명:</span>
                  <span className="aa-value">{selectedAllergenDetail.description}</span>
                </div>
              )}
              {selectedAllergenDetail.note && (
                <div className="aa-detail-row">
                  <span className="aa-label">비고:</span>
                  <span className="aa-value">{selectedAllergenDetail.note}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      {/* ===== 분석 데이터 섹션 ===== */}
      {overview && (
        <>
          <hr className="aa-section-divider" />
          <h3 className="aa-section-title">분석 통계</h3>

          {/* 상단 정보 바 */}
          <div className="aa-info-bar">
            <div className="aa-info-items">
              <span className="aa-info-item">기준: <strong>{overview.latest_period?.slice(0, 7) || '-'}</strong></span>
              <span className="aa-info-item">알러젠: <strong>{overview.total_allergens ?? '-'}종</strong></span>
              <span className="aa-info-item">검사: <strong>{overview.total_tests?.toLocaleString() ?? '-'}건</strong></span>
            </div>
            <button onClick={loadOverview} className="aa-refresh-btn">새로고침</button>
          </div>

          {/* 양성률 TOP 10 */}
          {barData.length > 0 && (
            <div className="aa-card" style={{ marginBottom: '1.5rem' }}>
              <h4 className="aa-card-title">알러젠 양성률 TOP 10</h4>
              <ResponsiveContainer width="100%" height={300}>
                <BarChart data={barData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                  <XAxis dataKey="name" tick={{ fontSize: 12 }} />
                  <YAxis unit="%" tick={{ fontSize: 12 }} />
                  <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #eee', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} formatter={(value) => [`${value}%`, '양성률']} />
                  <Bar dataKey="양성률" fill="#1abc9c" radius={[6, 6, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          )}

          {/* 알러젠 선택 */}
          {analyticsAllergens.length > 0 && (
            <div style={{ marginBottom: '1rem', display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
              <label style={{ fontSize: '0.85rem', color: '#666' }}>알러젠 선택:</label>
              <select value={selectedAllergen} onChange={e => setSelectedAllergen(e.target.value)} className="aa-filter-select">
                {analyticsAllergens.map(a => (
                  <option key={a.allergen_code} value={a.allergen_code}>{a.allergen_code}</option>
                ))}
              </select>
            </div>
          )}

          <div className="aa-grid-2col" style={{ marginBottom: '1.5rem' }}>
            {trendChartData.length > 0 && (
              <div className="aa-card">
                <h4 className="aa-card-title">{selectedAllergen} 양성률 / 평균등급 추이</h4>
                <ResponsiveContainer width="100%" height={300}>
                  <LineChart data={trendChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="period" tick={{ fontSize: 11 }} />
                    <YAxis yAxisId="left" unit="%" tick={{ fontSize: 11 }} />
                    <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} />
                    <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #eee', boxShadow: '0 4px 12px rgba(0,0,0,0.1)' }} />
                    <Legend />
                    <Line yAxisId="left" type="monotone" dataKey="양성률" stroke="#1abc9c" strokeWidth={2.5} dot={{ r: 4, fill: '#1abc9c' }} activeDot={{ r: 6 }} />
                    <Line yAxisId="right" type="monotone" dataKey="평균등급" stroke="#3498db" strokeWidth={2.5} dot={{ r: 4, fill: '#3498db' }} activeDot={{ r: 6 }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            {gradeDistData.length > 0 && (
              <div className="aa-card">
                <h4 className="aa-card-title">등급 분포 (최근 월)</h4>
                <ResponsiveContainer width="100%" height={300}>
                  <PieChart>
                    <Pie data={gradeDistData} dataKey="value" nameKey="name" cx="50%" cy="50%" outerRadius={100} innerRadius={50}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`} labelLine={{ stroke: '#ccc' }}>
                      {gradeDistData.map((_, i) => <Cell key={i} fill={COLORS[i % COLORS.length]} />)}
                    </Pie>
                    <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #eee' }} />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}
          </div>

          {cooccurrence.length > 0 && (
            <div className="aa-card">
              <h4 className="aa-card-title">동반 양성 알러젠 (TOP 5)</h4>
              <table className="aa-table">
                <thead><tr><th>순위</th><th>알러젠</th><th>동반 건수</th><th>동반률</th></tr></thead>
                <tbody>
                  {cooccurrence.map((c, i) => (
                    <tr key={i}>
                      <td><span className={`aa-rank ${i < 3 ? `aa-rank-${i + 1}` : ''}`}>{i + 1}</span></td>
                      <td style={{ fontWeight: 500 }}>{c.allergen}</td>
                      <td>{c.count?.toLocaleString()}</td>
                      <td style={{ fontWeight: 600, color: '#1abc9c' }}>{(c.rate * 100).toFixed(1)}%</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </>
      )}

      {loading && <p className="aa-loading">분석 데이터 로딩 중...</p>}
      {error && <div className="aa-error">{error} <button onClick={loadOverview} className="aa-retry-btn">재시도</button></div>}

      <style>{`
        .aa-page { padding: 1rem; }
        .aa-page-title { margin-bottom: 0.5rem; font-size: 1.25rem; font-weight: 700; color: #2c3e50; }
        .aa-subtitle { color: #666; margin-bottom: 1.5rem; font-size: 0.9rem; }
        .aa-loading { padding: 2rem; text-align: center; color: #888; }
        .aa-error { color: #e74c3c; padding: 1rem; }
        .aa-retry-btn { margin-left: 0.5rem; padding: 0.25rem 0.75rem; border: 1px solid #e74c3c; border-radius: 4px; background: white; color: #e74c3c; cursor: pointer; }

        /* 필터 툴바 */
        .aa-toolbar { display: flex; gap: 1rem; margin-bottom: 1rem; flex-wrap: wrap; }
        .aa-search-input { flex: 1; min-width: 200px; padding: 0.5rem 1rem; border: 1px solid #ddd; border-radius: 6px; font-size: 0.875rem; }
        .aa-filter-select { padding: 0.5rem 1rem; border: 1px solid #ddd; border-radius: 6px; background: white; font-size: 0.875rem; }

        /* 통계 바 */
        .aa-stats-bar { display: flex; gap: 2rem; padding: 1rem; background: #f8f9fa; border-radius: 8px; margin-bottom: 1.5rem; font-size: 0.875rem; color: #666; }
        .aa-stats-bar strong { color: #333; }

        /* 카테고리 섹션 */
        .aa-allergens-grid { margin-bottom: 2rem; }
        .aa-category-section { margin-bottom: 2rem; }
        .aa-category-header { display: flex; align-items: center; gap: 1rem; padding: 0.75rem 1rem; border-radius: 8px; margin-bottom: 1rem; color: white; font-size: 1rem; }
        .aa-category-header.food { background: linear-gradient(135deg, #f39c12 0%, #d68910 100%); }
        .aa-category-header.inhalant { background: linear-gradient(135deg, #3498db 0%, #2980b9 100%); }
        .aa-cat-count { font-size: 0.875rem; font-weight: normal; opacity: 0.9; }

        /* 알러젠 카드 */
        .aa-allergen-cards { display: grid; grid-template-columns: repeat(auto-fill, minmax(180px, 1fr)); gap: 1rem; }
        .aa-allergen-card { background: white; border-radius: 8px; padding: 1rem; box-shadow: 0 2px 8px rgba(0,0,0,0.1); cursor: pointer; transition: transform 0.2s, box-shadow 0.2s; position: relative; }
        .aa-allergen-card:hover { transform: translateY(-2px); box-shadow: 0 4px 12px rgba(0,0,0,0.15); }
        .aa-allergen-card.has-prescription { border-left: 3px solid #27ae60; }
        .aa-allergen-code { font-size: 0.75rem; color: #999; margin-bottom: 0.25rem; }
        .aa-allergen-name { font-weight: 600; color: #333; margin-bottom: 0.25rem; }
        .aa-allergen-name-en { font-size: 0.875rem; color: #666; margin-bottom: 0.5rem; }
        .aa-allergen-type { font-size: 0.75rem; color: #999; background: #f8f9fa; padding: 0.25rem 0.5rem; border-radius: 4px; display: inline-block; }
        .aa-prescription-badge { position: absolute; top: 0.5rem; right: 0.5rem; background: #27ae60; color: white; font-size: 0.625rem; padding: 0.125rem 0.375rem; border-radius: 8px; }

        /* 모달 */
        .aa-modal-overlay { position: fixed; top: 0; left: 0; right: 0; bottom: 0; background: rgba(0,0,0,0.5); display: flex; align-items: center; justify-content: center; z-index: 1000; }
        .aa-modal { background: white; border-radius: 12px; width: 90%; max-width: 500px; max-height: 80vh; overflow-y: auto; }
        .aa-modal-header { display: flex; justify-content: space-between; align-items: center; padding: 1rem 1.5rem; border-bottom: 1px solid #eee; }
        .aa-modal-header h3 { margin: 0; }
        .aa-modal-header button { background: none; border: none; font-size: 1.25rem; cursor: pointer; color: #666; }
        .aa-modal-body { padding: 1.5rem; }
        .aa-detail-row { display: flex; margin-bottom: 0.75rem; }
        .aa-label { width: 80px; color: #666; flex-shrink: 0; font-size: 0.875rem; }
        .aa-value { color: #333; font-size: 0.875rem; }

        /* 구분선 */
        .aa-section-divider { border: none; border-top: 1px solid #eee; margin: 2rem 0 1.5rem; }
        .aa-section-title { font-size: 1.1rem; font-weight: 700; color: #2c3e50; margin-bottom: 1.25rem; }

        /* 분석 섹션 */
        .aa-info-bar { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 1rem; margin-bottom: 1.5rem; padding: 0.75rem 1rem; background: white; border-radius: 10px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); }
        .aa-info-items { display: flex; gap: 1.5rem; flex-wrap: wrap; }
        .aa-info-item { font-size: 0.85rem; color: #666; }
        .aa-info-item strong { color: #333; }
        .aa-refresh-btn { padding: 0.5rem 1rem; background: linear-gradient(135deg, #1abc9c, #16a085); color: white; border: none; border-radius: 6px; cursor: pointer; font-size: 0.85rem; font-weight: 500; transition: opacity 0.2s; }
        .aa-refresh-btn:hover { opacity: 0.85; }
        .aa-grid-2col { display: grid; grid-template-columns: repeat(auto-fit, minmax(360px, 1fr)); gap: 1.5rem; }
        .aa-card { background: white; border-radius: 12px; padding: 1.25rem; box-shadow: 0 2px 12px rgba(0,0,0,0.06); }
        .aa-card-title { margin: 0 0 1rem 0; font-size: 0.95rem; font-weight: 600; color: #333; }
        .aa-table { width: 100%; border-collapse: collapse; }
        .aa-table thead tr { background: #f8f9fa; }
        .aa-table th { padding: 0.625rem 0.75rem; text-align: left; font-size: 0.75rem; font-weight: 600; color: #888; text-transform: uppercase; letter-spacing: 0.5px; }
        .aa-table td { padding: 0.625rem 0.75rem; font-size: 0.85rem; border-bottom: 1px solid #f0f0f0; }
        .aa-table tbody tr:hover { background: #f0faf8; }
        .aa-table tbody tr:last-child td { border-bottom: none; }
        .aa-rank { display: inline-flex; align-items: center; justify-content: center; width: 24px; height: 24px; border-radius: 50%; font-size: 0.7rem; font-weight: 700; background: #eee; color: #666; }
        .aa-rank-1 { background: #ffd700; color: #7a6100; }
        .aa-rank-2 { background: #c0c0c0; color: #555; }
        .aa-rank-3 { background: #cd7f32; color: white; }
        @media (max-width: 640px) { .aa-grid-2col { grid-template-columns: 1fr; } .aa-allergen-cards { grid-template-columns: repeat(auto-fill, minmax(150px, 1fr)); } }
      `}</style>
    </div>
  );
};

export default AllergenAnalysisPage;
