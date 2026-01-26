/**
 * Consumer Food Guide Page - 식품 가이드
 */
import React, { useState, useEffect } from 'react';
import { consumerApi } from '../services/consumerApi';

function FoodGuidePage() {
  const [foodGuide, setFoodGuide] = useState(null);
  const [loading, setLoading] = useState(true);
  const [selectedAllergen, setSelectedAllergen] = useState(null);
  const [crossReactivity, setCrossReactivity] = useState(null);

  const allergenOptions = [
    { code: 'peanut', name: '땅콩' },
    { code: 'milk', name: '우유' },
    { code: 'egg', name: '계란' },
    { code: 'wheat', name: '밀' },
    { code: 'soy', name: '대두' },
    { code: 'fish', name: '생선' },
    { code: 'shellfish', name: '갑각류' },
    { code: 'tree_nuts', name: '견과류' },
    { code: 'sesame', name: '참깨' },
  ];

  useEffect(() => {
    loadFoodGuide();
  }, []);

  const loadFoodGuide = async () => {
    try {
      setLoading(true);
      const data = await consumerApi.guide.getFoods();
      setFoodGuide(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const loadCrossReactivity = async (code) => {
    try {
      const data = await consumerApi.guide.getCrossReactivity(code);
      setCrossReactivity(data);
      setSelectedAllergen(code);
    } catch (err) {
      console.error(err);
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    );
  }

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto' }}>
      <h2>식품 가이드</h2>
      <p style={{ color: '#666', marginBottom: '1.5rem' }}>
        알러젠별 회피 식품 및 대체 식품 정보입니다.
      </p>

      {/* 알러젠 선택 */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3>알러젠 선택</h3>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          {allergenOptions.map(opt => (
            <button
              key={opt.code}
              className={`allergen-btn ${selectedAllergen === opt.code ? 'active' : ''}`}
              onClick={() => loadCrossReactivity(opt.code)}
            >
              {opt.name}
            </button>
          ))}
        </div>
      </div>

      {/* 회피 식품 */}
      {foodGuide?.avoid_foods?.length > 0 && (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ color: '#e74c3c' }}>🚫 회피 식품</h3>
          {foodGuide.avoid_foods.map((item, idx) => (
            <div key={idx} style={{
              marginBottom: '1rem',
              padding: '1rem',
              background: '#fff5f5',
              borderRadius: '8px',
            }}>
              <h4 style={{ marginBottom: '0.5rem' }}>{item.allergen}</h4>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {item.foods.map((food, i) => (
                  <span key={i} className="food-tag avoid">
                    {food}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 대체 식품 */}
      {foodGuide?.substitutes?.length > 0 && (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ color: '#27ae60' }}>✅ 대체 식품</h3>
          {foodGuide.substitutes.map((item, idx) => (
            <div key={idx} style={{
              marginBottom: '1rem',
              padding: '1rem',
              background: '#f0fff4',
              borderRadius: '8px',
            }}>
              <p style={{ marginBottom: '0.5rem' }}>
                <span style={{ fontWeight: '600' }}>{item.allergen}</span>:
                <span style={{ color: '#e74c3c', textDecoration: 'line-through', marginLeft: '0.5rem' }}>
                  {item.original}
                </span>
              </p>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {item.alternatives.map((alt, i) => (
                  <span key={i} className="food-tag safe">
                    {alt}
                  </span>
                ))}
              </div>
              {item.notes && (
                <p style={{ fontSize: '0.875rem', color: '#666', marginTop: '0.5rem' }}>
                  💡 {item.notes}
                </p>
              )}
            </div>
          ))}
        </div>
      )}

      {/* 숨겨진 알러젠 */}
      {foodGuide?.hidden_sources?.length > 0 && (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <h3 style={{ color: '#f39c12' }}>⚠️ 숨겨진 알러젠 주의</h3>
          <p style={{ color: '#666', marginBottom: '1rem' }}>
            예상치 못한 곳에 알러젠이 포함되어 있을 수 있습니다.
          </p>
          {foodGuide.hidden_sources.map((item, idx) => (
            <div key={idx} style={{
              marginBottom: '1rem',
              padding: '1rem',
              background: '#fff8e1',
              borderRadius: '8px',
            }}>
              <h4 style={{ marginBottom: '0.5rem' }}>{item.allergen}</h4>
              <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                {item.sources.map((source, i) => (
                  <span key={i} className="food-tag warning">
                    {source}
                  </span>
                ))}
              </div>
            </div>
          ))}
        </div>
      )}

      {/* 교차반응 */}
      {crossReactivity && crossReactivity.cross_reactivity?.length > 0 && (
        <div className="card">
          <h3>🔄 교차반응 정보 - {crossReactivity.allergen_name}</h3>
          <p style={{ color: '#666', marginBottom: '1rem' }}>
            {crossReactivity.allergen_name} 알러지가 있으면 다음 식품에도 반응할 수 있습니다.
          </p>
          {crossReactivity.cross_reactivity.map((cross, idx) => (
            <div key={idx} style={{
              marginBottom: '1rem',
              padding: '1rem',
              background: '#f3e5f5',
              borderRadius: '8px',
            }}>
              <p style={{ fontWeight: '600', marginBottom: '0.5rem' }}>
                {cross.to_allergen}
                <span style={{ fontWeight: 'normal', color: '#666', marginLeft: '0.5rem' }}>
                  (확률: {cross.probability})
                </span>
              </p>
              {cross.related_foods?.length > 0 && (
                <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
                  {cross.related_foods.map((food, i) => (
                    <span key={i} className="food-tag cross">
                      {food}
                    </span>
                  ))}
                </div>
              )}
            </div>
          ))}
        </div>
      )}

      <style>{`
        .allergen-btn {
          padding: 0.5rem 1rem;
          border: 1px solid #ddd;
          background: white;
          border-radius: 20px;
          cursor: pointer;
          transition: all 0.2s;
        }
        .allergen-btn:hover {
          background: #f8f9fa;
        }
        .allergen-btn.active {
          background: #667eea;
          color: white;
          border-color: #667eea;
        }
        .food-tag {
          padding: 0.25rem 0.75rem;
          border-radius: 16px;
          font-size: 0.875rem;
        }
        .food-tag.avoid {
          background: #ffcdd2;
          color: #c62828;
        }
        .food-tag.safe {
          background: #c8e6c9;
          color: #2e7d32;
        }
        .food-tag.warning {
          background: #ffe082;
          color: #f57c00;
        }
        .food-tag.cross {
          background: #e1bee7;
          color: #7b1fa2;
        }
      `}</style>
    </div>
  );
}

export default FoodGuidePage;
