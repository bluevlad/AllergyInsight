/**
 * Allergen Input Form - 알러젠 등급 입력 폼
 *
 * 16종 알러젠에 대해 등급(0-6)을 입력받습니다.
 */
import React, { useState } from 'react';

const FOOD_ALLERGENS = [
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

const INHALANT_ALLERGENS = [
  { code: 'dust_mite', name: '집먼지진드기' },
  { code: 'pollen', name: '꽃가루' },
  { code: 'mold', name: '곰팡이' },
  { code: 'pet_dander', name: '반려동물' },
  { code: 'cockroach', name: '바퀴벌레' },
  { code: 'latex', name: '라텍스' },
  { code: 'bee_venom', name: '벌독' },
];

const GRADE_INFO = [
  { value: 0, label: '음성', color: '#95a5a6', bg: '#f8f9fa' },
  { value: 1, label: '1등급', color: '#27ae60', bg: '#e8f5e9' },
  { value: 2, label: '2등급', color: '#f39c12', bg: '#fff8e1' },
  { value: 3, label: '3등급', color: '#e67e22', bg: '#fff3e0' },
  { value: 4, label: '4등급', color: '#e74c3c', bg: '#ffebee' },
  { value: 5, label: '5등급', color: '#c0392b', bg: '#fce4ec' },
  { value: 6, label: '6등급', color: '#8e0000', bg: '#f8d7da' },
];

function AllergenInputForm({ onSubmit, loading }) {
  const [grades, setGrades] = useState({});
  const [name, setName] = useState('');

  const setGrade = (code, grade) => {
    setGrades(prev => ({ ...prev, [code]: grade }));
  };

  const hasPositive = Object.values(grades).some(g => g > 0);

  const handleSubmit = () => {
    const allergens = [];
    [...FOOD_ALLERGENS, ...INHALANT_ALLERGENS].forEach(item => {
      const grade = grades[item.code] || 0;
      allergens.push({ code: item.code, grade });
    });
    onSubmit({ allergens: allergens.filter(a => a.grade > 0), name: name || null });
  };

  const renderAllergenRow = (item) => {
    const currentGrade = grades[item.code] || 0;
    return (
      <div key={item.code} className="allergen-row">
        <span className="allergen-name">{item.name}</span>
        <div className="grade-buttons">
          {GRADE_INFO.map(g => (
            <button
              key={g.value}
              className={`grade-btn ${currentGrade === g.value ? 'selected' : ''}`}
              style={{
                background: currentGrade === g.value ? g.color : g.bg,
                color: currentGrade === g.value ? 'white' : g.color,
                borderColor: g.color,
              }}
              onClick={() => setGrade(item.code, g.value)}
              type="button"
            >
              {g.value}
            </button>
          ))}
        </div>
      </div>
    );
  };

  return (
    <div>
      {/* 이름 입력 (선택) */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <label style={{ fontWeight: '600', display: 'block', marginBottom: '0.5rem' }}>
          이름 (선택)
        </label>
        <input
          type="text"
          value={name}
          onChange={e => setName(e.target.value)}
          placeholder="리포트에 표시할 이름"
          maxLength={50}
          style={{
            width: '100%',
            padding: '0.75rem',
            border: '1px solid #ddd',
            borderRadius: '8px',
            fontSize: '1rem',
            boxSizing: 'border-box',
          }}
        />
      </div>

      {/* 등급 안내 */}
      <div className="card" style={{ marginBottom: '1.5rem', background: '#f8f9fa' }}>
        <h4 style={{ marginTop: 0 }}>등급 안내</h4>
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
          {GRADE_INFO.map(g => (
            <span key={g.value} style={{
              padding: '0.25rem 0.75rem',
              borderRadius: '16px',
              fontSize: '0.8rem',
              background: g.bg,
              color: g.color,
              border: `1px solid ${g.color}`,
            }}>
              {g.value}: {g.label}
            </span>
          ))}
        </div>
        <p style={{ margin: '0.75rem 0 0', fontSize: '0.85rem', color: '#666' }}>
          0 = 음성(미검사), 1-2 = 약양성, 3-4 = 중등도, 5-6 = 강양성
        </p>
      </div>

      {/* 식품 알러젠 */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ marginTop: 0 }}>식품 알러젠 (9종)</h3>
        <div className="allergen-list">
          {FOOD_ALLERGENS.map(renderAllergenRow)}
        </div>
      </div>

      {/* 흡입 알러젠 */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <h3 style={{ marginTop: 0 }}>흡입 알러젠 (7종)</h3>
        <div className="allergen-list">
          {INHALANT_ALLERGENS.map(renderAllergenRow)}
        </div>
      </div>

      {/* 제출 버튼 */}
      <button
        className="submit-btn"
        onClick={handleSubmit}
        disabled={!hasPositive || loading}
      >
        {loading ? '리포트 생성 중...' : '리포트 생성'}
      </button>

      <style>{`
        .allergen-list {
          display: flex;
          flex-direction: column;
          gap: 0.75rem;
        }
        .allergen-row {
          display: flex;
          align-items: center;
          justify-content: space-between;
          padding: 0.5rem 0;
          border-bottom: 1px solid #f0f0f0;
        }
        .allergen-row:last-child {
          border-bottom: none;
        }
        .allergen-name {
          font-weight: 500;
          min-width: 100px;
          font-size: 0.95rem;
        }
        .grade-buttons {
          display: flex;
          gap: 0.35rem;
        }
        .grade-btn {
          width: 36px;
          height: 36px;
          border: 1.5px solid;
          border-radius: 8px;
          cursor: pointer;
          font-weight: 600;
          font-size: 0.85rem;
          transition: all 0.15s;
          display: flex;
          align-items: center;
          justify-content: center;
        }
        .grade-btn:hover {
          transform: scale(1.1);
        }
        .grade-btn.selected {
          box-shadow: 0 2px 6px rgba(0,0,0,0.2);
        }
        .submit-btn {
          width: 100%;
          padding: 1rem;
          background: linear-gradient(135deg, #667eea, #764ba2);
          color: white;
          border: none;
          border-radius: 12px;
          font-size: 1.1rem;
          font-weight: 600;
          cursor: pointer;
          transition: opacity 0.2s;
        }
        .submit-btn:hover:not(:disabled) {
          opacity: 0.9;
        }
        .submit-btn:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }
        @media (max-width: 600px) {
          .allergen-row {
            flex-direction: column;
            align-items: flex-start;
            gap: 0.5rem;
          }
          .grade-btn {
            width: 32px;
            height: 32px;
            font-size: 0.8rem;
          }
        }
      `}</style>
    </div>
  );
}

export default AllergenInputForm;
