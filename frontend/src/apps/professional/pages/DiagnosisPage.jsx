/**
 * Professional Diagnosis Page - 진단 입력
 */
import React, { useState, useEffect } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { proApi } from '../services/proApi';

function DiagnosisPage() {
  const navigate = useNavigate();
  const [searchParams] = useSearchParams();
  const patientId = searchParams.get('patient');

  const [allergenInfo, setAllergenInfo] = useState(null);
  const [patientInfo, setPatientInfo] = useState(null);
  const [results, setResults] = useState({});
  const [doctorNote, setDoctorNote] = useState('');
  const [diagnosisDate, setDiagnosisDate] = useState(new Date().toISOString().split('T')[0]);
  const [loading, setLoading] = useState(true);
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadInitialData();
  }, [patientId]);

  const loadInitialData = async () => {
    try {
      setLoading(true);
      const [allergens, patient] = await Promise.all([
        proApi.diagnosis.getAllergenInfo(),
        patientId ? proApi.patients.get(patientId) : Promise.resolve(null),
      ]);
      setAllergenInfo(allergens);
      setPatientInfo(patient);

      // 초기 결과값 설정 (모두 0)
      const initialResults = {};
      [...(allergens.food || []), ...(allergens.inhalant || [])].forEach(a => {
        initialResults[a.code] = 0;
      });
      setResults(initialResults);
    } catch (err) {
      setError('데이터를 불러오는데 실패했습니다.');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  const handleGradeChange = (allergenCode, grade) => {
    setResults(prev => ({
      ...prev,
      [allergenCode]: parseInt(grade, 10),
    }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!patientInfo) {
      alert('환자를 선택해주세요.');
      return;
    }

    try {
      setSubmitting(true);
      await proApi.diagnosis.create({
        patient_user_id: patientInfo.patient_user_id,
        results: results,
        diagnosis_date: diagnosisDate,
        doctor_note: doctorNote || null,
      });

      alert('진단 결과가 저장되었습니다.');
      navigate(`/pro/patients/${patientId}`);
    } catch (err) {
      console.error(err);
      alert('저장에 실패했습니다: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSubmitting(false);
    }
  };

  const getGradeColor = (grade) => {
    const colors = allergenInfo?.grades || {};
    return colors[grade]?.color || '#ccc';
  };

  const getGradeLabel = (grade) => {
    const grades = allergenInfo?.grades || {};
    return grades[grade]?.label || '-';
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    );
  }

  if (error) {
    return (
      <div className="card">
        <p style={{ color: '#c62828' }}>{error}</p>
        <button className="btn btn-primary" onClick={loadInitialData}>
          다시 시도
        </button>
      </div>
    );
  }

  return (
    <div>
      <h2>진단 결과 입력</h2>

      {/* 환자 정보 */}
      {patientInfo ? (
        <div className="card" style={{ marginBottom: '1.5rem' }}>
          <h3>환자 정보</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
            <div>
              <p style={{ color: '#666', fontSize: '0.875rem' }}>환자명</p>
              <p style={{ fontWeight: '600' }}>{patientInfo.patient_name}</p>
            </div>
            <div>
              <p style={{ color: '#666', fontSize: '0.875rem' }}>환자번호</p>
              <p style={{ fontWeight: '600' }}>{patientInfo.patient_number || '-'}</p>
            </div>
            <div>
              <p style={{ color: '#666', fontSize: '0.875rem' }}>연락처</p>
              <p style={{ fontWeight: '600' }}>{patientInfo.patient_phone || '-'}</p>
            </div>
            <div>
              <p style={{ color: '#666', fontSize: '0.875rem' }}>담당의</p>
              <p style={{ fontWeight: '600' }}>{patientInfo.assigned_doctor_name || '-'}</p>
            </div>
          </div>
        </div>
      ) : (
        <div className="card" style={{ marginBottom: '1.5rem', textAlign: 'center' }}>
          <p>환자를 선택해주세요.</p>
          <button className="btn btn-primary" onClick={() => navigate('/pro/patients')}>
            환자 목록으로 이동
          </button>
        </div>
      )}

      {patientInfo && (
        <form onSubmit={handleSubmit}>
          {/* 진단 날짜 */}
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <div className="form-group">
              <label>진단 날짜</label>
              <input
                type="date"
                value={diagnosisDate}
                onChange={(e) => setDiagnosisDate(e.target.value)}
                className="form-control"
                style={{ maxWidth: '200px' }}
              />
            </div>
          </div>

          {/* 식품 알러젠 */}
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <h3>식품 알러젠</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
              {(allergenInfo?.food || []).map((allergen) => (
                <div key={allergen.code} className="allergen-item">
                  <label style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span>
                      {allergen.name_kr}
                      <span style={{ color: '#666', fontSize: '0.8rem', marginLeft: '0.5rem' }}>
                        ({allergen.name_en})
                      </span>
                    </span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <select
                        value={results[allergen.code] || 0}
                        onChange={(e) => handleGradeChange(allergen.code, e.target.value)}
                        style={{
                          padding: '0.25rem 0.5rem',
                          borderRadius: '4px',
                          border: '1px solid #ddd',
                          backgroundColor: getGradeColor(results[allergen.code] || 0),
                          color: results[allergen.code] >= 4 ? 'white' : 'inherit',
                        }}
                      >
                        {[0, 1, 2, 3, 4, 5, 6].map(g => (
                          <option key={g} value={g}>
                            {g} - {getGradeLabel(g)}
                          </option>
                        ))}
                      </select>
                    </div>
                  </label>
                </div>
              ))}
            </div>
          </div>

          {/* 흡입 알러젠 */}
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <h3>흡입 알러젠</h3>
            <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '1rem' }}>
              {(allergenInfo?.inhalant || []).map((allergen) => (
                <div key={allergen.code} className="allergen-item">
                  <label style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                    <span>
                      {allergen.name_kr}
                      <span style={{ color: '#666', fontSize: '0.8rem', marginLeft: '0.5rem' }}>
                        ({allergen.name_en})
                      </span>
                    </span>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <select
                        value={results[allergen.code] || 0}
                        onChange={(e) => handleGradeChange(allergen.code, e.target.value)}
                        style={{
                          padding: '0.25rem 0.5rem',
                          borderRadius: '4px',
                          border: '1px solid #ddd',
                          backgroundColor: getGradeColor(results[allergen.code] || 0),
                          color: results[allergen.code] >= 4 ? 'white' : 'inherit',
                        }}
                      >
                        {[0, 1, 2, 3, 4, 5, 6].map(g => (
                          <option key={g} value={g}>
                            {g} - {getGradeLabel(g)}
                          </option>
                        ))}
                      </select>
                    </div>
                  </label>
                </div>
              ))}
            </div>
          </div>

          {/* 의사 소견 */}
          <div className="card" style={{ marginBottom: '1.5rem' }}>
            <div className="form-group">
              <label>의사 소견 (선택)</label>
              <textarea
                value={doctorNote}
                onChange={(e) => setDoctorNote(e.target.value)}
                className="form-control"
                rows={4}
                placeholder="진단에 대한 소견이나 환자 지도 사항을 입력하세요..."
              />
            </div>
          </div>

          {/* 제출 버튼 */}
          <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={() => navigate(-1)}
            >
              취소
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting}
            >
              {submitting ? '저장 중...' : '진단 결과 저장'}
            </button>
          </div>
        </form>
      )}

      <style>{`
        .allergen-item {
          padding: 0.75rem;
          background: #f8f9fa;
          border-radius: 6px;
        }
        .allergen-item:hover {
          background: #e9ecef;
        }
      `}</style>
    </div>
  );
}

export default DiagnosisPage;
