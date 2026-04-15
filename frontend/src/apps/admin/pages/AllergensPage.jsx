/**
 * Allergens Management Page
 *
 * 분류 체계:
 *   - type (유형): food, inhalant, contact, venom — 알러젠 반응 경로
 *   - category (카테고리): mite, dust, animal, ... seed_nut — 17개 세부 분류
 *
 * 화면 구성:
 *   1) 대분류 섹션: 흡입성 알러젠 / 식품 알러젠 (type 기반)
 *   2) 카테고리별 그룹: 각 섹션 내에서 category 기준으로 그룹화
 *   3) 통계: type 기준으로 식품/흡입 카운트
 */
import React, { useState, useEffect } from 'react';
import { adminApi } from '../services/adminApi';

// 카테고리 표시명 및 정렬 순서
const CATEGORY_CONFIG = {
  // 흡입성 그룹
  mite:          { name: '진드기', nameEn: 'Mite', group: 'inhalant', order: 1 },
  dust:          { name: '집먼지', nameEn: 'Dust', group: 'inhalant', order: 2 },
  animal:        { name: '동물/비듬/상피', nameEn: 'Animal', group: 'inhalant', order: 3 },
  insect:        { name: '벌독/곤충', nameEn: 'Insect', group: 'inhalant', order: 4 },
  latex:         { name: '라텍스', nameEn: 'Latex', group: 'inhalant', order: 5 },
  microorganism: { name: '미생물', nameEn: 'Microorganism', group: 'inhalant', order: 6 },
  tree:          { name: '나무', nameEn: 'Tree', group: 'inhalant', order: 7 },
  grass:         { name: '목초/잔디', nameEn: 'Grass', group: 'inhalant', order: 8 },
  weed:          { name: '잡초', nameEn: 'Weed', group: 'inhalant', order: 9 },
  // 식품 그룹
  egg_dairy:       { name: '알/유제품', nameEn: 'Egg/Dairy', group: 'food', order: 10 },
  crustacean:      { name: '갑각류', nameEn: 'Crustacean', group: 'food', order: 11 },
  fish_shellfish:  { name: '어패류', nameEn: 'Fish/Shellfish', group: 'food', order: 12 },
  vegetable:       { name: '채소', nameEn: 'Vegetable', group: 'food', order: 13 },
  meat:            { name: '육류', nameEn: 'Meat', group: 'food', order: 14 },
  fruit:           { name: '과일', nameEn: 'Fruit', group: 'food', order: 15 },
  seed_nut:        { name: '씨/견과류', nameEn: 'Seed/Nut', group: 'food', order: 16 },
  // 기타
  other:           { name: '기타', nameEn: 'Other', group: 'other', order: 17 },
};

// type 표시명
const TYPE_NAMES = {
  food: '식품',
  inhalant: '흡입',
  contact: '접촉',
  venom: '독소',
};

const AllergensPage = () => {
  const [allergens, setAllergens] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [groupFilter, setGroupFilter] = useState(''); // 대분류: '', 'inhalant', 'food'
  const [categoryFilter, setCategoryFilter] = useState(''); // 세부 카테고리
  const [search, setSearch] = useState('');
  const [selectedAllergen, setSelectedAllergen] = useState(null);

  useEffect(() => {
    loadAllergens();
  }, []);

  const loadAllergens = async () => {
    try {
      setLoading(true);
      const response = await adminApi.allergens.list({});
      setAllergens(response.items || response || []);
    } catch (err) {
      console.error('Allergens load failed:', err);
      setError('알러젠 목록 로딩 실패');
    } finally {
      setLoading(false);
    }
  };

  // 검색 + 필터 적용
  const filteredAllergens = allergens.filter((a) => {
    // 대분류 필터 (type 기반 그룹)
    if (groupFilter) {
      const catConfig = CATEGORY_CONFIG[a.category];
      const group = catConfig ? catConfig.group : '';
      if (groupFilter === 'inhalant' && group !== 'inhalant') return false;
      if (groupFilter === 'food' && group !== 'food') return false;
    }
    // 세부 카테고리 필터
    if (categoryFilter && a.category !== categoryFilter) return false;
    // 검색
    if (search) {
      const s = search.toLowerCase();
      return (
        a.code.toLowerCase().includes(s) ||
        a.name_kr.includes(search) ||
        a.name_en.toLowerCase().includes(s)
      );
    }
    return true;
  });

  // type 기준 통계
  const foodCount = allergens.filter((a) => a.type === 'food').length;
  const inhalantCount = allergens.filter(
    (a) => a.type === 'inhalant' || a.type === 'contact' || a.type === 'venom'
  ).length;

  // 카테고리별 그룹화 + 정렬
  const groupedAllergens = filteredAllergens.reduce((acc, allergen) => {
    const cat = allergen.category;
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(allergen);
    return acc;
  }, {});

  const sortedCategories = Object.keys(groupedAllergens).sort((a, b) => {
    const orderA = CATEGORY_CONFIG[a]?.order ?? 99;
    const orderB = CATEGORY_CONFIG[b]?.order ?? 99;
    return orderA - orderB;
  });

  // 섹션별 분리 (흡입성 / 식품 / 기타)
  const inhalantCategories = sortedCategories.filter(
    (c) => CATEGORY_CONFIG[c]?.group === 'inhalant'
  );
  const foodCategories = sortedCategories.filter(
    (c) => CATEGORY_CONFIG[c]?.group === 'food'
  );
  const otherCategories = sortedCategories.filter(
    (c) => CATEGORY_CONFIG[c]?.group === 'other'
  );

  const handleViewDetail = async (code) => {
    try {
      const detail = await adminApi.allergens.get(code);
      setSelectedAllergen(detail);
    } catch (err) {
      alert('알러젠 상세 정보 로딩 실패');
    }
  };

  // 카테고리 필터용 드롭다운 옵션 (현재 groupFilter에 맞는 것만)
  const getCategoryOptions = () => {
    if (groupFilter === 'inhalant') {
      return Object.entries(CATEGORY_CONFIG).filter(([, v]) => v.group === 'inhalant');
    }
    if (groupFilter === 'food') {
      return Object.entries(CATEGORY_CONFIG).filter(([, v]) => v.group === 'food');
    }
    return Object.entries(CATEGORY_CONFIG);
  };

  const renderCategorySection = (category) => {
    const items = groupedAllergens[category];
    const config = CATEGORY_CONFIG[category] || { name: category, nameEn: '', group: 'other' };
    const isFood = config.group === 'food';
    const colorClass = isFood ? 'food' : 'inhalant';

    return (
      <div key={category} className="category-section">
        <h4 className={`category-header ${colorClass}`}>
          {config.name} ({config.nameEn})
          <span className="count">{items.length}종</span>
        </h4>
        <div className="allergen-cards">
          {items.map((allergen) => (
            <div
              key={allergen.code}
              className={`allergen-card ${allergen.has_prescription ? 'has-prescription' : ''}`}
              onClick={() => handleViewDetail(allergen.code)}
            >
              <div className="allergen-code">{allergen.code}</div>
              <div className="allergen-name">{allergen.name_kr}</div>
              <div className="allergen-name-en">{allergen.name_en}</div>
              <div className="allergen-type">
                {TYPE_NAMES[allergen.type] || allergen.type}
              </div>
              {allergen.has_prescription && (
                <span className="prescription-badge">처방</span>
              )}
            </div>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div className="allergens-page">
      <h2>알러젠 관리</h2>
      <p className="subtitle">SGTi-Allergy Screen PLUS 119종 알러젠 데이터</p>

      {/* 필터 */}
      <div className="toolbar">
        <input
          type="text"
          placeholder="코드, 한글명, 영문명 검색..."
          value={search}
          onChange={(e) => setSearch(e.target.value)}
          className="search-input"
        />
        <select
          value={groupFilter}
          onChange={(e) => {
            setGroupFilter(e.target.value);
            setCategoryFilter('');
          }}
        >
          <option value="">전체</option>
          <option value="inhalant">흡입성</option>
          <option value="food">식품</option>
        </select>
        <select
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
        >
          <option value="">전체 카테고리</option>
          {getCategoryOptions()
            .sort(([, a], [, b]) => a.order - b.order)
            .map(([key, config]) => (
              <option key={key} value={key}>
                {config.name} ({config.nameEn})
              </option>
            ))}
        </select>
      </div>

      {/* 통계 */}
      <div className="stats-bar">
        <span>전체: {filteredAllergens.length}종</span>
        <span className="stat-food">식품: {foodCount}종</span>
        <span className="stat-inhalant">흡입: {inhalantCount}종</span>
      </div>

      {/* 알러젠 목록 */}
      {loading ? (
        <div className="loading">로딩 중...</div>
      ) : error ? (
        <div className="error">{error}</div>
      ) : (
        <div className="allergens-grid">
          {/* 흡입성 알러젠 섹션 */}
          {inhalantCategories.length > 0 && (
            <div className="section-group">
              <h3 className="section-title inhalant-title">
                흡입성 알러젠
                <span className="section-count">
                  {inhalantCategories.reduce(
                    (sum, c) => sum + groupedAllergens[c].length,
                    0
                  )}
                  종
                </span>
              </h3>
              {inhalantCategories.map(renderCategorySection)}
            </div>
          )}

          {/* 식품 알러젠 섹션 */}
          {foodCategories.length > 0 && (
            <div className="section-group">
              <h3 className="section-title food-title">
                식품 알러젠
                <span className="section-count">
                  {foodCategories.reduce(
                    (sum, c) => sum + groupedAllergens[c].length,
                    0
                  )}
                  종
                </span>
              </h3>
              {foodCategories.map(renderCategorySection)}
            </div>
          )}

          {/* 기타 섹션 */}
          {otherCategories.length > 0 && (
            <div className="section-group">
              <h3 className="section-title other-title">
                기타
                <span className="section-count">
                  {otherCategories.reduce(
                    (sum, c) => sum + groupedAllergens[c].length,
                    0
                  )}
                  종
                </span>
              </h3>
              {otherCategories.map(renderCategorySection)}
            </div>
          )}
        </div>
      )}

      {/* 상세 모달 */}
      {selectedAllergen && (
        <div className="modal-overlay" onClick={() => setSelectedAllergen(null)}>
          <div className="modal" onClick={(e) => e.stopPropagation()}>
            <div className="modal-header">
              <h3>{selectedAllergen.name_kr}</h3>
              <button onClick={() => setSelectedAllergen(null)}>X</button>
            </div>
            <div className="modal-body">
              <div className="detail-row">
                <span className="label">코드:</span>
                <span className="value">{selectedAllergen.code}</span>
              </div>
              <div className="detail-row">
                <span className="label">영문명:</span>
                <span className="value">{selectedAllergen.name_en}</span>
              </div>
              <div className="detail-row">
                <span className="label">카테고리:</span>
                <span className="value">
                  {CATEGORY_CONFIG[selectedAllergen.category]?.name || selectedAllergen.category}
                </span>
              </div>
              <div className="detail-row">
                <span className="label">유형:</span>
                <span className="value">
                  {TYPE_NAMES[selectedAllergen.type] || selectedAllergen.type}
                </span>
              </div>
              {selectedAllergen.description && (
                <div className="detail-row">
                  <span className="label">설명:</span>
                  <span className="value">{selectedAllergen.description}</span>
                </div>
              )}
              {selectedAllergen.note && (
                <div className="detail-row">
                  <span className="label">비고:</span>
                  <span className="value">{selectedAllergen.note}</span>
                </div>
              )}
            </div>
          </div>
        </div>
      )}

      <style>{`
        .allergens-page {
          padding: 1rem;
        }

        .allergens-page h2 {
          margin-bottom: 0.5rem;
        }

        .subtitle {
          color: #666;
          margin-bottom: 1.5rem;
        }

        .toolbar {
          display: flex;
          gap: 1rem;
          margin-bottom: 1rem;
          flex-wrap: wrap;
        }

        .search-input {
          flex: 1;
          min-width: 200px;
          padding: 0.5rem 1rem;
          border: 1px solid #ddd;
          border-radius: 6px;
        }

        .toolbar select {
          padding: 0.5rem 1rem;
          border: 1px solid #ddd;
          border-radius: 6px;
          background: white;
        }

        .stats-bar {
          display: flex;
          gap: 2rem;
          padding: 1rem;
          background: #f8f9fa;
          border-radius: 8px;
          margin-bottom: 1.5rem;
          font-size: 0.875rem;
        }

        .stats-bar span {
          font-weight: 600;
          color: #333;
        }

        .stat-food {
          color: #b7791f !important;
        }

        .stat-inhalant {
          color: #1a5276 !important;
        }

        /* 대분류 섹션 */
        .section-group {
          margin-bottom: 2.5rem;
        }

        .section-title {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.75rem 1.25rem;
          border-radius: 8px;
          margin-bottom: 1.5rem;
          font-size: 1.125rem;
          font-weight: 700;
        }

        .inhalant-title {
          background: #dbeafe;
          color: #1e40af;
          border-left: 5px solid #3b82f6;
        }

        .food-title {
          background: #fef3c7;
          color: #92400e;
          border-left: 5px solid #f59e0b;
        }

        .other-title {
          background: #f3f4f6;
          color: #374151;
          border-left: 5px solid #9ca3af;
        }

        .section-count {
          font-size: 0.875rem;
          font-weight: normal;
          opacity: 0.8;
        }

        /* 카테고리 섹션 */
        .category-section {
          margin-bottom: 1.5rem;
          margin-left: 1rem;
        }

        .category-header {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 0.5rem 1rem;
          border-radius: 6px;
          margin-bottom: 0.75rem;
          font-size: 0.9375rem;
          font-weight: 600;
        }

        .category-header.food {
          background: #fef3e2;
          color: #b7791f;
          border-left: 3px solid #f39c12;
        }

        .category-header.inhalant {
          background: #e8f4fd;
          color: #1a5276;
          border-left: 3px solid #3498db;
        }

        .category-header .count {
          font-size: 0.8125rem;
          font-weight: normal;
          opacity: 0.9;
        }

        .allergen-cards {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
          gap: 0.75rem;
          margin-left: 0.5rem;
        }

        .allergen-card {
          background: white;
          border-radius: 8px;
          padding: 0.875rem;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          cursor: pointer;
          transition: transform 0.2s, box-shadow 0.2s;
          position: relative;
        }

        .allergen-card:hover {
          transform: translateY(-2px);
          box-shadow: 0 4px 12px rgba(0, 0, 0, 0.15);
        }

        .allergen-card.has-prescription {
          border-left: 3px solid #27ae60;
        }

        .allergen-code {
          font-size: 0.75rem;
          color: #999;
          margin-bottom: 0.25rem;
        }

        .allergen-name {
          font-weight: 600;
          color: #333;
          margin-bottom: 0.25rem;
        }

        .allergen-name-en {
          font-size: 0.8125rem;
          color: #666;
          margin-bottom: 0.5rem;
        }

        .allergen-type {
          font-size: 0.75rem;
          color: #999;
          background: #f8f9fa;
          padding: 0.2rem 0.5rem;
          border-radius: 4px;
          display: inline-block;
        }

        .prescription-badge {
          position: absolute;
          top: 0.5rem;
          right: 0.5rem;
          background: #27ae60;
          color: white;
          font-size: 0.625rem;
          padding: 0.125rem 0.375rem;
          border-radius: 8px;
        }

        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0, 0, 0, 0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .modal {
          background: white;
          border-radius: 12px;
          width: 90%;
          max-width: 500px;
          max-height: 80vh;
          overflow-y: auto;
        }

        .modal-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          padding: 1rem 1.5rem;
          border-bottom: 1px solid #eee;
        }

        .modal-header h3 {
          margin: 0;
        }

        .modal-header button {
          background: none;
          border: none;
          font-size: 1.25rem;
          cursor: pointer;
          color: #666;
        }

        .modal-body {
          padding: 1.5rem;
        }

        .detail-row {
          display: flex;
          margin-bottom: 0.75rem;
        }

        .detail-row .label {
          width: 80px;
          color: #666;
          flex-shrink: 0;
        }

        .detail-row .value {
          color: #333;
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

export default AllergensPage;
