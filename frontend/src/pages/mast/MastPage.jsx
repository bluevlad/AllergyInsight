/**
 * MAST Page (Phase 1)
 *
 * 비회원 공개 — 병원 MAST 등급 입력 → 알러젠별 정보 매칭
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../../shared/services/apiClient';
import MedicalDisclaimer from '../../shared/components/MedicalDisclaimer';
import MastInputForm from './MastInputForm';
import MastResultView from './MastResultView';

const MastPage = () => {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async ({ allergen_code, grade }) => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.post('/public/mast/match', { allergen_code, grade });
      setResult(data);
      setStep(2);
      window.scrollTo(0, 0);
    } catch (err) {
      setError(err.response?.data?.detail || '정보 매칭에 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    setStep(1);
    setResult(null);
    setError(null);
    window.scrollTo(0, 0);
  };

  return (
    <div style={{ minHeight: '100vh', background: '#f5f6fa' }}>
      <div
        style={{
          background: 'linear-gradient(135deg, #1976d2 0%, #1565c0 100%)',
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
          MAST 검사 등급별 알러지 정보
        </p>
      </div>

      <div style={{ maxWidth: '900px', margin: '0 auto', padding: '1.5rem 1rem' }}>
        <div style={{ marginBottom: '1rem' }}>
          <MedicalDisclaimer variant="banner" />
        </div>

        {step === 1 && (
          <>
            <h2 style={{ marginBottom: '0.5rem' }}>병원 검사 결과 입력</h2>
            <p style={{ color: '#666', margin: '0 0 1.25rem' }}>
              병원 또는 진단소에서 받은 MAST 알러지 검사 등급을 입력하면, 해당 알러젠에 대한
              식이 관리 · 증상 위험 · 응급 정보를 논문 · 전문기관 출처 기반으로 보여드립니다.
            </p>

            {error && (
              <div
                role="alert"
                style={{
                  padding: '0.75rem 1rem',
                  background: '#ffebee',
                  color: '#c62828',
                  borderRadius: '8px',
                  marginBottom: '1rem',
                }}
              >
                {error}
              </div>
            )}

            <MastInputForm onSubmit={handleSubmit} loading={loading} />
          </>
        )}

        {step === 2 && result && (
          <MastResultView result={result} onBack={handleBack} />
        )}
      </div>

      <footer
        style={{
          textAlign: 'center',
          padding: '2rem 1rem',
          color: '#999',
          fontSize: '0.85rem',
        }}
      >
        <a href="/" style={{ color: '#1976d2', textDecoration: 'none' }}>
          AllergyInsight 홈으로
        </a>
      </footer>
    </div>
  );
};

export default MastPage;
