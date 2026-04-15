/**
 * Allergy Report Page - 알러지 리포트
 *
 * 공개 페이지 (인증 불필요)
 * Step 1: 알러젠 등급 입력
 * Step 2: 통합 리포트 출력
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import apiClient from '../../shared/services/apiClient';
import AllergenInputForm from './AllergenInputForm';
import AllergyReportView from './AllergyReportView';

function AllergyReportPage() {
  const navigate = useNavigate();
  const [step, setStep] = useState(1);
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const handleSubmit = async ({ allergens, name }) => {
    try {
      setLoading(true);
      setError(null);
      const data = await apiClient.post('/report/generate', { allergens, name });
      setReport(data);
      setStep(2);
      window.scrollTo(0, 0);
    } catch (err) {
      setError(err.response?.data?.detail || '리포트 생성에 실패했습니다. 다시 시도해주세요.');
    } finally {
      setLoading(false);
    }
  };

  const handleBack = () => {
    setStep(1);
    setReport(null);
    window.scrollTo(0, 0);
  };

  return (
    <div style={{ minHeight: '100vh', background: '#f5f6fa' }}>
      {/* 헤더 (인쇄 시 숨김) */}
      <div className="no-print" style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: '1.25rem 1rem',
        textAlign: 'center',
        color: 'white',
      }}>
        <h1
          style={{ margin: 0, fontSize: '1.5rem', cursor: 'pointer' }}
          onClick={() => navigate('/')}
        >
          AllergyInsight
        </h1>
        <p style={{ margin: '0.25rem 0 0', opacity: 0.85, fontSize: '0.9rem' }}>
          알러지 리포트
        </p>
      </div>

      <div style={{ maxWidth: '900px', margin: '0 auto', padding: '1.5rem 1rem' }}>
        {/* Step 1: 입력 폼 */}
        {step === 1 && (
          <>
            <div style={{ marginBottom: '1.5rem' }}>
              <h2 style={{ marginBottom: '0.5rem' }}>알러지 리포트 생성</h2>
              <p style={{ color: '#666', margin: 0 }}>
                알러젠별 등급을 입력하면 맞춤 식품가이드, 생활관리, 응급정보를 통합한 리포트를 제공합니다.
              </p>
            </div>

            {error && (
              <div style={{
                padding: '0.75rem 1rem',
                background: '#ffebee',
                color: '#c62828',
                borderRadius: '8px',
                marginBottom: '1rem',
              }}>
                {error}
              </div>
            )}

            <AllergenInputForm onSubmit={handleSubmit} loading={loading} />

            <div style={{
              marginTop: '1.5rem',
              padding: '1rem',
              background: '#fff3cd',
              border: '1px solid #ffc107',
              borderRadius: '8px',
              fontSize: '0.85rem',
              color: '#856404',
            }}>
              ⚠️ 본 리포트는 의학적 진단을 대체하지 않으며, 참고 정보로만 활용하시기 바랍니다.
            </div>
          </>
        )}

        {/* Step 2: 리포트 출력 */}
        {step === 2 && report && (
          <AllergyReportView report={report} onBack={handleBack} />
        )}
      </div>

      {/* 푸터 (인쇄 시 숨김) */}
      <footer className="no-print" style={{
        textAlign: 'center',
        padding: '2rem 1rem',
        color: '#999',
        fontSize: '0.85rem',
      }}>
        <a
          href="/"
          style={{ color: '#667eea', textDecoration: 'none' }}
        >
          AllergyInsight 홈으로
        </a>
      </footer>

      <style>{`
        .card {
          background: white;
          border-radius: 12px;
          padding: 1.5rem;
          box-shadow: 0 2px 8px rgba(0,0,0,0.08);
        }
        @media print {
          .no-print { display: none !important; }
        }
      `}</style>
    </div>
  );
}

export default AllergyReportPage;
