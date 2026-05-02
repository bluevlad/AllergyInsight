/**
 * MAST Input Form
 *
 * Step 1 — 알러젠 검색·선택 + MAST 등급(0~4) 입력
 */
import React, { useEffect, useMemo, useState } from 'react';
import apiClient from '../../shared/services/apiClient';
import GradeBadge from './GradeBadge';

const GRADE_OPTIONS = [
  { value: 0, level: '음성', levelEn: 'Class 0', color: 'green' },
  { value: 1, level: '약양성', levelEn: 'Class 1', color: 'yellow' },
  { value: 2, level: '중등도 양성', levelEn: 'Class 2', color: 'orange' },
  { value: 3, level: '강양성', levelEn: 'Class 3', color: 'orangered' },
  { value: 4, level: '매우 강양성', levelEn: 'Class 4', color: 'darkred' },
];

const MastInputForm = ({ onSubmit, loading }) => {
  const [allergens, setAllergens] = useState([]);
  const [allergensLoading, setAllergensLoading] = useState(true);
  const [allergensError, setAllergensError] = useState(null);

  const [search, setSearch] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('all');
  const [selectedAllergen, setSelectedAllergen] = useState(null);
  const [grade, setGrade] = useState(null);

  useEffect(() => {
    let cancelled = false;
    (async () => {
      try {
        const data = await apiClient.get('/allergens/?limit=500');
        if (!cancelled) setAllergens(data.items ?? []);
      } catch (err) {
        if (!cancelled) setAllergensError('알러젠 목록을 불러오지 못했습니다.');
      } finally {
        if (!cancelled) setAllergensLoading(false);
      }
    })();
    return () => {
      cancelled = true;
    };
  }, []);

  const categories = useMemo(() => {
    const set = new Set(allergens.map((a) => a.category));
    return Array.from(set).sort();
  }, [allergens]);

  const filtered = useMemo(() => {
    const q = search.trim().toLowerCase();
    return allergens.filter((a) => {
      if (selectedCategory !== 'all' && a.category !== selectedCategory) return false;
      if (!q) return true;
      return (
        a.name_kr.toLowerCase().includes(q) ||
        a.name_en.toLowerCase().includes(q) ||
        a.code.toLowerCase().includes(q)
      );
    });
  }, [allergens, search, selectedCategory]);

  const canSubmit = selectedAllergen && grade !== null && !loading;

  const handleSubmit = (e) => {
    e.preventDefault();
    if (!canSubmit) return;
    onSubmit({ allergen_code: selectedAllergen.code, grade });
  };

  return (
    <form onSubmit={handleSubmit}>
      {/* Step 1.1: 알러젠 선택 */}
      <section style={sectionStyle}>
        <h3 style={sectionTitleStyle}>1. 알러젠 선택</h3>

        <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
          <input
            type="text"
            placeholder="한글명 · 영문명 · 코드로 검색"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={inputStyle}
          />
          <select
            value={selectedCategory}
            onChange={(e) => setSelectedCategory(e.target.value)}
            style={{ ...inputStyle, flex: '0 0 160px' }}
          >
            <option value="all">전체 카테고리</option>
            {categories.map((c) => (
              <option key={c} value={c}>{c}</option>
            ))}
          </select>
        </div>

        {allergensLoading && <p style={{ color: '#999' }}>불러오는 중...</p>}
        {allergensError && <p style={{ color: '#c62828' }}>{allergensError}</p>}

        {!allergensLoading && !allergensError && (
          <div
            role="listbox"
            style={{
              maxHeight: '280px',
              overflowY: 'auto',
              border: '1px solid #e0e0e0',
              borderRadius: '8px',
              background: 'white',
            }}
          >
            {filtered.length === 0 && (
              <p style={{ padding: '1rem', color: '#999', margin: 0 }}>
                일치하는 알러젠이 없습니다.
              </p>
            )}
            {filtered.map((a) => {
              const active = selectedAllergen?.code === a.code;
              return (
                <button
                  type="button"
                  key={a.code}
                  onClick={() => setSelectedAllergen(a)}
                  style={{
                    display: 'block',
                    width: '100%',
                    textAlign: 'left',
                    padding: '0.6rem 0.75rem',
                    border: 'none',
                    borderBottom: '1px solid #f0f0f0',
                    background: active ? '#e3f2fd' : 'white',
                    cursor: 'pointer',
                    fontSize: '0.9rem',
                  }}
                >
                  <strong>{a.name_kr}</strong>
                  <span style={{ color: '#666', marginLeft: '0.5rem' }}>
                    {a.name_en}
                  </span>
                  <span style={{ color: '#aaa', marginLeft: '0.5rem', fontSize: '0.8rem' }}>
                    [{a.code}] · {a.category}
                  </span>
                </button>
              );
            })}
          </div>
        )}
      </section>

      {/* Step 1.2: 등급 입력 */}
      <section style={sectionStyle}>
        <h3 style={sectionTitleStyle}>2. MAST 등급 (Class 0~4)</h3>
        <div style={{ display: 'flex', flexDirection: 'column', gap: '0.5rem' }}>
          {GRADE_OPTIONS.map((opt) => {
            const active = grade === opt.value;
            return (
              <label
                key={opt.value}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.75rem',
                  padding: '0.6rem 0.75rem',
                  border: active ? '2px solid #1976d2' : '1px solid #e0e0e0',
                  borderRadius: '8px',
                  background: active ? '#e3f2fd' : 'white',
                  cursor: 'pointer',
                }}
              >
                <input
                  type="radio"
                  name="grade"
                  value={opt.value}
                  checked={active}
                  onChange={() => setGrade(opt.value)}
                />
                <GradeBadge {...opt} />
              </label>
            );
          })}
        </div>
      </section>

      {selectedAllergen && grade !== null && (
        <div
          style={{
            padding: '0.75rem 1rem',
            background: '#f5f5f5',
            borderRadius: '8px',
            marginBottom: '1rem',
            fontSize: '0.9rem',
            color: '#333',
          }}
        >
          <strong>{selectedAllergen.name_kr}</strong>
          <span style={{ marginLeft: '0.5rem' }}>—</span>
          <span style={{ marginLeft: '0.5rem' }}>
            <GradeBadge {...GRADE_OPTIONS[grade]} size="sm" />
          </span>
        </div>
      )}

      <button
        type="submit"
        disabled={!canSubmit}
        style={{
          width: '100%',
          padding: '0.85rem',
          border: 'none',
          borderRadius: '8px',
          background: canSubmit ? '#1976d2' : '#bdbdbd',
          color: 'white',
          fontSize: '1rem',
          fontWeight: 600,
          cursor: canSubmit ? 'pointer' : 'not-allowed',
        }}
      >
        {loading ? '조회 중...' : '정보 매칭하기'}
      </button>
    </form>
  );
};

const sectionStyle = {
  marginBottom: '1.25rem',
  padding: '1rem',
  background: '#fafafa',
  borderRadius: '8px',
};
const sectionTitleStyle = {
  margin: '0 0 0.75rem',
  fontSize: '1rem',
  color: '#333',
};
const inputStyle = {
  flex: 1,
  padding: '0.6rem 0.75rem',
  border: '1px solid #e0e0e0',
  borderRadius: '8px',
  fontSize: '0.9rem',
  background: 'white',
};

export default MastInputForm;
