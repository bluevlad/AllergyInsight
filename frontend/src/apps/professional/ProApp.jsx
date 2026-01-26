/**
 * Professional App - 의료진 전용 앱
 *
 * /pro/* 경로에서 라우팅됩니다.
 */
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import ProNav from './components/ProNav';
import { useAuth } from '../../shared/contexts/AuthContext';
import { LoadingSpinner } from '../../shared/components';

// Professional Pages
import Dashboard from './pages/Dashboard';
import DiagnosisPage from './pages/DiagnosisPage';
import PatientsPage from './pages/PatientsPage';
import PatientRegisterPage from './pages/PatientRegisterPage';
import SearchPage from './pages/SearchPage';
import QAPage from './pages/QAPage';
import PapersPage from './pages/PapersPage';
import ClinicalReportPage from './pages/ClinicalReportPage';

const ProApp = () => {
  const { user, loading, isProfessional } = useAuth();

  if (loading) {
    return <LoadingSpinner message="로딩 중..." />;
  }

  if (!isProfessional) {
    return <Navigate to="/app" replace />;
  }

  const getSubtitle = () => {
    if (user?.role === 'doctor') return '의사 전용';
    if (user?.role === 'nurse') return '간호사 전용';
    if (user?.role === 'lab_tech') return '검사 담당자 전용';
    if (user?.role === 'hospital_admin') return '병원 관리자';
    return '의료진 전용';
  };

  return (
    <div className="pro-app">
      <header className="header">
        <h1>AllergyInsight Pro</h1>
        <p className="header-subtitle">
          SGTi-Allergy Screen PLUS 진단 결과 분석 및 처방 권고 시스템 | {getSubtitle()}
        </p>
        <ProNav />
      </header>

      <main className="main-content">
        <Routes>
          {/* Dashboard */}
          <Route path="/" element={<Dashboard />} />
          <Route path="/dashboard" element={<Dashboard />} />

          {/* Diagnosis */}
          <Route path="/diagnosis" element={<DiagnosisPage />} />
          <Route path="/diagnosis/:id" element={<DiagnosisPage />} />

          {/* Patients */}
          <Route path="/patients" element={<PatientsPage />} />
          <Route path="/patients/new" element={<PatientRegisterPage />} />
          <Route path="/patients/:id" element={<PatientsPage />} />

          {/* Research */}
          <Route path="/search" element={<SearchPage />} />
          <Route path="/qa" element={<QAPage />} />
          <Route path="/papers" element={<PapersPage />} />
          <Route path="/papers/:id" element={<PapersPage />} />

          {/* Clinical Report */}
          <Route path="/clinical-report" element={<ClinicalReportPage />} />
          <Route path="/clinical-report/:patientId" element={<ClinicalReportPage />} />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/pro" replace />} />
        </Routes>
      </main>

      <footer style={{ textAlign: 'center', padding: '1rem', color: '#666', fontSize: '0.875rem' }}>
        AllergyInsight Pro v1.2.0 | 의료진 전용 서비스
      </footer>
    </div>
  );
};

export default ProApp;
