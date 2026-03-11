/**
 * Analytics App - 공개 분석 대시보드
 *
 * /analytics/* 경로에서 라우팅됩니다.
 * 인증 불필요 - 누구나 접근 가능합니다.
 *
 * 3개 메뉴: 알러젠 분석, 논문 수집정보, 알러젠뉴스 정보
 */
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import AnalyticsNav from './components/AnalyticsNav';
import AllergenAnalysisPage from './pages/AllergenAnalysisPage';
import PaperCollectionPage from './pages/PaperCollectionPage';
import AllergenNewsPage from './pages/AllergenNewsPage';

const AnalyticsApp = () => {
  return (
    <div className="analytics-app">
      <header className="header analytics-header">
        <h1>AllergyInsight Analytics</h1>
        <p className="header-subtitle">
          알러지 트렌드 분석 | Public Dashboard
        </p>
        <AnalyticsNav />
      </header>

      <main className="main-content">
        <Routes>
          <Route path="/" element={<AllergenAnalysisPage />} />
          <Route path="/allergen-analysis" element={<AllergenAnalysisPage />} />
          <Route path="/paper-collection" element={<PaperCollectionPage />} />
          <Route path="/allergen-news" element={<AllergenNewsPage />} />
          <Route path="*" element={<Navigate to="/analytics" replace />} />
        </Routes>
      </main>

      <footer style={{ textAlign: 'center', padding: '1rem', color: '#666', fontSize: '0.875rem' }}>
        AllergyInsight Analytics | Open Data Dashboard
      </footer>

      <style>{`
        .analytics-app {
          min-height: 100vh;
          background: #f5f6fa;
        }

        .analytics-header {
          background: linear-gradient(135deg, #1abc9c 0%, #16a085 100%);
        }

        .analytics-header h1 {
          color: white;
        }

        .analytics-header .header-subtitle {
          color: rgba(255, 255, 255, 0.9);
        }
      `}</style>
    </div>
  );
};

export default AnalyticsApp;
