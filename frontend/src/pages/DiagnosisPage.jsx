import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { allergenApi, diagnosisApi, prescriptionApi, sgtiApi } from '../services/api';

// 등급별 색상
const gradeColors = {
  0: '#4CAF50',  // 녹색 - 음성
  1: '#8BC34A',  // 연두색 - 약양성
  2: '#FFEB3B',  // 노란색 - 양성
  3: '#FFC107',  // 주황색 - 양성
  4: '#FF9800',  // 진주황 - 강양성
  5: '#F44336',  // 빨간색 - 강양성
  6: '#B71C1C',  // 진빨강 - 최강양성
};

// 등급별 배경색 (연하게)
const gradeBgColors = {
  0: '#E8F5E9',
  1: '#F1F8E9',
  2: '#FFFDE7',
  3: '#FFF8E1',
  4: '#FFF3E0',
  5: '#FFEBEE',
  6: '#FFCDD2',
};

function DiagnosisPage() {
  const navigate = useNavigate();
  const [allergens, setAllergens] = useState({ food: [], inhalant: [] });
  const [gradeInfo, setGradeInfo] = useState(null);
  const [diagnosisResults, setDiagnosisResults] = useState({});
  const [diagnosisDate, setDiagnosisDate] = useState(new Date().toISOString().split('T')[0]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  // 알러젠 목록 및 등급 정보 로드
  useEffect(() => {
    const loadData = async () => {
      try {
        const [allergensData, gradesData] = await Promise.all([
          allergenApi.getAll(),
          sgtiApi.getGrades(),
        ]);
        setAllergens(allergensData);
        setGradeInfo(gradesData);

        // 초기 진단 결과 설정 (모두 0등급)
        const initialResults = {};
        [...allergensData.food, ...allergensData.inhalant].forEach(a => {
          initialResults[a.code] = 0;
        });
        setDiagnosisResults(initialResults);
      } catch (err) {
        console.error('Failed to load data:', err);
        setError('데이터를 불러오는데 실패했습니다.');
      }
    };
    loadData();
  }, []);

  // 등급 변경 핸들러
  const handleGradeChange = (allergenCode, grade) => {
    setDiagnosisResults(prev => ({
      ...prev,
      [allergenCode]: parseInt(grade),
    }));
  };

  // 모두 초기화
  const handleReset = () => {
    const resetResults = {};
    Object.keys(diagnosisResults).forEach(key => {
      resetResults[key] = 0;
    });
    setDiagnosisResults(resetResults);
  };

  // 처방 권고 생성
  const handleGeneratePrescription = async () => {
    setLoading(true);
    setError(null);

    try {
      // 진단 결과 배열 변환
      const results = Object.entries(diagnosisResults).map(([allergen, grade]) => ({
        allergen,
        grade,
      }));

      // 처방 생성
      const prescription = await prescriptionApi.generate(
        results,
        diagnosisDate ? new Date(diagnosisDate).toISOString() : null
      );

      // 처방 결과 페이지로 이동
      navigate('/prescription', { state: { prescription } });
    } catch (err) {
      console.error('Failed to generate prescription:', err);
      setError('처방 권고 생성에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  // 양성 항원 수 계산
  const positiveCount = Object.values(diagnosisResults).filter(g => g > 0).length;
  const highRiskCount = Object.values(diagnosisResults).filter(g => g >= 5).length;

  // 등급 선택 컴포넌트
  const GradeSelector = ({ allergen }) => {
    const currentGrade = diagnosisResults[allergen.code] || 0;
    const gradeDesc = gradeInfo?.grades?.[currentGrade];

    return (
      <div
        className="allergen-card"
        style={{
          backgroundColor: gradeBgColors[currentGrade],
          border: `2px solid ${gradeColors[currentGrade]}`,
          borderRadius: '8px',
          padding: '12px',
          marginBottom: '8px',
        }}
      >
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
          <div>
            <strong style={{ fontSize: '1rem' }}>{allergen.name_kr}</strong>
            <span style={{ color: '#666', marginLeft: '8px', fontSize: '0.875rem' }}>
              ({allergen.name_en || allergen.code})
            </span>
          </div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <select
              value={currentGrade}
              onChange={(e) => handleGradeChange(allergen.code, e.target.value)}
              style={{
                padding: '6px 12px',
                borderRadius: '4px',
                border: '1px solid #ccc',
                fontSize: '1rem',
                backgroundColor: 'white',
              }}
            >
              {[0, 1, 2, 3, 4, 5, 6].map(g => (
                <option key={g} value={g}>
                  {g}등급 {g === 0 ? '(음성)' : g >= 5 ? '(강양성)' : '(양성)'}
                </option>
              ))}
            </select>
            <div
              style={{
                width: '24px',
                height: '24px',
                borderRadius: '50%',
                backgroundColor: gradeColors[currentGrade],
              }}
            />
          </div>
        </div>
        {currentGrade > 0 && gradeDesc && (
          <div style={{ marginTop: '8px', fontSize: '0.875rem', color: '#555' }}>
            {gradeDesc.level} - {gradeDesc.action}
          </div>
        )}
      </div>
    );
  };

  return (
    <div className="diagnosis-page" style={{ maxWidth: '900px', margin: '0 auto' }}>
      <h2>SGTi-Allergy Screen PLUS 진단 결과 입력</h2>
      <p style={{ color: '#666', marginBottom: '24px' }}>
        검사 결과를 항목별로 입력하면 맞춤형 처방 권고를 받을 수 있습니다.
      </p>

      {error && (
        <div style={{
          backgroundColor: '#FFEBEE',
          color: '#C62828',
          padding: '12px',
          borderRadius: '4px',
          marginBottom: '16px',
        }}>
          {error}
        </div>
      )}

      {/* 검사 날짜 입력 */}
      <div style={{
        backgroundColor: '#f5f5f5',
        padding: '16px',
        borderRadius: '8px',
        marginBottom: '24px',
      }}>
        <label style={{ display: 'block', marginBottom: '8px', fontWeight: 'bold' }}>
          검사 날짜
        </label>
        <input
          type="date"
          value={diagnosisDate}
          onChange={(e) => setDiagnosisDate(e.target.value)}
          style={{
            padding: '8px 12px',
            borderRadius: '4px',
            border: '1px solid #ccc',
            fontSize: '1rem',
          }}
        />
      </div>

      {/* 요약 카드 */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(3, 1fr)',
        gap: '16px',
        marginBottom: '24px',
      }}>
        <div style={{
          backgroundColor: '#E3F2FD',
          padding: '16px',
          borderRadius: '8px',
          textAlign: 'center',
        }}>
          <div style={{ fontSize: '2rem', fontWeight: 'bold', color: '#1976D2' }}>
            {Object.keys(diagnosisResults).length}
          </div>
          <div style={{ color: '#666' }}>검사 항목</div>
        </div>
        <div style={{
          backgroundColor: positiveCount > 0 ? '#FFF3E0' : '#E8F5E9',
          padding: '16px',
          borderRadius: '8px',
          textAlign: 'center',
        }}>
          <div style={{
            fontSize: '2rem',
            fontWeight: 'bold',
            color: positiveCount > 0 ? '#F57C00' : '#388E3C',
          }}>
            {positiveCount}
          </div>
          <div style={{ color: '#666' }}>양성 항목</div>
        </div>
        <div style={{
          backgroundColor: highRiskCount > 0 ? '#FFEBEE' : '#E8F5E9',
          padding: '16px',
          borderRadius: '8px',
          textAlign: 'center',
        }}>
          <div style={{
            fontSize: '2rem',
            fontWeight: 'bold',
            color: highRiskCount > 0 ? '#C62828' : '#388E3C',
          }}>
            {highRiskCount}
          </div>
          <div style={{ color: '#666' }}>고위험 항목</div>
        </div>
      </div>

      {/* 식품 알러지 */}
      <div style={{ marginBottom: '32px' }}>
        <h3 style={{
          borderBottom: '2px solid #1976D2',
          paddingBottom: '8px',
          marginBottom: '16px',
        }}>
          식품 알러지 (Food Allergens)
        </h3>
        {allergens.food.map(allergen => (
          <GradeSelector key={allergen.code} allergen={allergen} />
        ))}
      </div>

      {/* 흡입성 알러지 */}
      <div style={{ marginBottom: '32px' }}>
        <h3 style={{
          borderBottom: '2px solid #7B1FA2',
          paddingBottom: '8px',
          marginBottom: '16px',
        }}>
          흡입성 알러지 (Inhalant Allergens)
        </h3>
        {allergens.inhalant.map(allergen => (
          <GradeSelector key={allergen.code} allergen={allergen} />
        ))}
      </div>

      {/* 버튼 영역 */}
      <div style={{
        display: 'flex',
        gap: '16px',
        justifyContent: 'center',
        marginTop: '32px',
        marginBottom: '32px',
      }}>
        <button
          onClick={handleReset}
          style={{
            padding: '12px 24px',
            borderRadius: '4px',
            border: '1px solid #ccc',
            backgroundColor: 'white',
            cursor: 'pointer',
            fontSize: '1rem',
          }}
        >
          초기화
        </button>
        <button
          onClick={handleGeneratePrescription}
          disabled={loading}
          style={{
            padding: '12px 32px',
            borderRadius: '4px',
            border: 'none',
            backgroundColor: '#1976D2',
            color: 'white',
            cursor: loading ? 'not-allowed' : 'pointer',
            fontSize: '1rem',
            fontWeight: 'bold',
            opacity: loading ? 0.7 : 1,
          }}
        >
          {loading ? '처방 생성 중...' : '처방 권고 생성'}
        </button>
      </div>

      {/* 등급 안내 */}
      <div style={{
        backgroundColor: '#f9f9f9',
        padding: '16px',
        borderRadius: '8px',
        marginTop: '24px',
      }}>
        <h4 style={{ marginBottom: '12px' }}>등급 안내</h4>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))', gap: '8px' }}>
          {gradeInfo?.grades && Object.entries(gradeInfo.grades).map(([grade, info]) => (
            <div
              key={grade}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '8px',
                padding: '8px',
                backgroundColor: gradeBgColors[grade],
                borderRadius: '4px',
              }}
            >
              <div
                style={{
                  width: '20px',
                  height: '20px',
                  borderRadius: '50%',
                  backgroundColor: gradeColors[grade],
                  flexShrink: 0,
                }}
              />
              <div style={{ fontSize: '0.875rem' }}>
                <strong>{grade}등급</strong> - {info.level}
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

export default DiagnosisPage;
