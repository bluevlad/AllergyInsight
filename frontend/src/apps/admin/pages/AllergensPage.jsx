/**
 * Allergens Management Page
 */
import React, { useState, useEffect } from 'react';
import { adminApi } from '../services/adminApi';

const AllergensPage = () => {
  const [allergens, setAllergens] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [categoryFilter, setCategoryFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const [search, setSearch] = useState('');
  const [selectedAllergen, setSelectedAllergen] = useState(null);

  useEffect(() => {
    loadAllergens();
  }, [categoryFilter, typeFilter]);

  const loadAllergens = async () => {
    try {
      setLoading(true);
      const params = {};
      if (categoryFilter) params.category = categoryFilter;
      if (typeFilter) params.type = typeFilter;

      const response = await adminApi.allergens.list(params);
      setAllergens(response.items || response || []);
    } catch (err) {
      console.error('Allergens load failed:', err);
      setError('알러젠 목록 로딩 실패');
    } finally {
      setLoading(false);
    }
  };

  const filteredAllergens = allergens.filter((a) => {
    if (!search) return true;
    const searchLower = search.toLowerCase();
    return (
      a.code.toLowerCase().includes(searchLower) ||
      a.name_kr.includes(search) ||
      a.name_en.toLowerCase().includes(searchLower)
    );
  });

  const handleViewDetail = async (code) => {
    try {
      const detail = await adminApi.allergens.get(code);
      setSelectedAllergen(detail);
    } catch (err) {
      alert('알러젠 상세 정보 로딩 실패');
    }
  };

  // 카테고리별 그룹화
  const groupedAllergens = filteredAllergens.reduce((acc, allergen) => {
    const cat = allergen.category;
    if (!acc[cat]) acc[cat] = [];
    acc[cat].push(allergen);
    return acc;
  }, {});

  return (
    <div className="allergens-page">
      <h2>알러젠 관리</h2>
      <p className="subtitle">SGTi-Allergy Screen PLUS 120종 알러젠 데이터</p>

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
          value={categoryFilter}
          onChange={(e) => setCategoryFilter(e.target.value)}
        >
          <option value="">전체 카테고리</option>
          <option value="food">식품</option>
          <option value="inhalant">흡입</option>
        </select>
        <select
          value={typeFilter}
          onChange={(e) => setTypeFilter(e.target.value)}
        >
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

      {/* 통계 */}
      <div className="stats-bar">
        <span>전체: {filteredAllergens.length}종</span>
        <span>식품: {filteredAllergens.filter((a) => a.category === 'food').length}종</span>
        <span>흡입: {filteredAllergens.filter((a) => a.category === 'inhalant').length}종</span>
      </div>

      {/* 알러젠 목록 */}
      {loading ? (
        <div className="loading">로딩 중...</div>
      ) : error ? (
        <div className="error">{error}</div>
      ) : (
        <div className="allergens-grid">
          {Object.entries(groupedAllergens).map(([category, items]) => (
            <div key={category} className="category-section">
              <h3 className={`category-header ${category}`}>
                {category === 'food' ? '식품 (Food)' : '흡입 (Inhalant)'}
                <span className="count">{items.length}종</span>
              </h3>
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
                    <div className="allergen-type">{getTypeName(allergen.type)}</div>
                    {allergen.has_prescription && (
                      <span className="prescription-badge">처방</span>
                    )}
                  </div>
                ))}
              </div>
            </div>
          ))}
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
                  {selectedAllergen.category === 'food' ? '식품' : '흡입'}
                </span>
              </div>
              <div className="detail-row">
                <span className="label">타입:</span>
                <span className="value">{getTypeName(selectedAllergen.type)}</span>
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
          color: #666;
        }

        .stats-bar span {
          font-weight: 500;
        }

        .category-section {
          margin-bottom: 2rem;
        }

        .category-header {
          display: flex;
          align-items: center;
          gap: 1rem;
          padding: 0.75rem 1rem;
          border-radius: 8px;
          margin-bottom: 1rem;
          color: white;
        }

        .category-header.food {
          background: linear-gradient(135deg, #f39c12 0%, #d68910 100%);
        }

        .category-header.inhalant {
          background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
        }

        .category-header .count {
          font-size: 0.875rem;
          font-weight: normal;
          opacity: 0.9;
        }

        .allergen-cards {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(180px, 1fr));
          gap: 1rem;
        }

        .allergen-card {
          background: white;
          border-radius: 8px;
          padding: 1rem;
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
          font-size: 0.875rem;
          color: #666;
          margin-bottom: 0.5rem;
        }

        .allergen-type {
          font-size: 0.75rem;
          color: #999;
          background: #f8f9fa;
          padding: 0.25rem 0.5rem;
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

const getTypeName = (type) => {
  const typeNames = {
    seafood: '해산물',
    meat: '육류',
    egg: '달걀',
    dairy: '유제품',
    grain: '곡물',
    legume: '콩류',
    nut: '견과류',
    fruit: '과일',
    vegetable: '채소',
    spice: '향신료',
    pollen: '꽃가루',
    mite: '진드기',
    animal: '동물',
    mold: '곰팡이',
    insect: '곤충',
    other: '기타',
  };
  return typeNames[type] || type;
};

export default AllergensPage;
