/**
 * Consumer App - 일반 사용자 앱
 *
 * /app/* 경로에서 라우팅됩니다.
 */
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import ConsumerNav from './components/ConsumerNav';
import { useAuth } from '../../shared/contexts/AuthContext';
import { LoadingSpinner } from '../../shared/components';

// Consumer Pages
import MyDiagnosisPage from './pages/MyDiagnosisPage';
import DiagnosisDetailPage from './pages/DiagnosisDetailPage';
import FoodGuidePage from './pages/FoodGuidePage';
import EmergencyPage from './pages/EmergencyPage';
import LifestylePage from './pages/LifestylePage';
import KitRegisterPage from './pages/KitRegisterPage';

const ConsumerApp = () => {
  const { user, loading, isAuthenticated } = useAuth();

  if (loading) {
    return <LoadingSpinner message="로딩 중..." />;
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  return (
    <div className="consumer-app">
      <header className="header consumer-header">
        <h1>AllergyInsight</h1>
        <p className="header-subtitle">
          나의 알러지 관리 파트너
        </p>
        <ConsumerNav />
      </header>

      <main className="main-content">
        <Routes>
          {/* My Diagnosis */}
          <Route path="/" element={<MyDiagnosisPage />} />
          <Route path="/my-diagnosis" element={<MyDiagnosisPage />} />
          <Route path="/my-diagnosis/:id" element={<DiagnosisDetailPage />} />

          {/* Guides */}
          <Route path="/food-guide" element={<FoodGuidePage />} />
          <Route path="/lifestyle" element={<LifestylePage />} />

          {/* Emergency */}
          <Route path="/emergency" element={<EmergencyPage />} />

          {/* Kit Registration */}
          <Route path="/kit-register" element={<KitRegisterPage />} />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/app" replace />} />
        </Routes>
      </main>

      <footer style={{ textAlign: 'center', padding: '1rem', color: '#666', fontSize: '0.875rem' }}>
        AllergyInsight v1.2.0 | 안전한 일상을 위한 알러지 관리
      </footer>

      <style>{`
        .consumer-header {
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
        }
        .consumer-header h1 {
          color: white;
        }
        .consumer-header .header-subtitle {
          color: rgba(255, 255, 255, 0.9);
        }
      `}</style>
    </div>
  );
};

export default ConsumerApp;
