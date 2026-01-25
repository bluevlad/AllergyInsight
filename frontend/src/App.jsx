import React from 'react';
import { BrowserRouter, Routes, Route, NavLink, Navigate } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';

// Pages
import Dashboard from './pages/Dashboard';
import SearchPage from './pages/SearchPage';
import QAPage from './pages/QAPage';
import PapersPage from './pages/PapersPage';
import DiagnosisPage from './pages/DiagnosisPage';
import PrescriptionPage from './pages/PrescriptionPage';
import LoginPage from './pages/LoginPage';
import AuthCallback from './pages/AuthCallback';
import MyDiagnosisPage from './pages/MyDiagnosisPage';

// Hospital Pages (Phase 2)
import HospitalDashboard from './pages/hospital/HospitalDashboard';
import PatientListPage from './pages/hospital/PatientListPage';
import PatientRegisterPage from './pages/hospital/PatientRegisterPage';

// Protected Route Component
const ProtectedRoute = ({ children, adminOnly = false, hospitalOnly = false }) => {
  const { isAuthenticated, isAdmin, isHospitalStaff, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <p>로딩 중...</p>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" replace />;
  }

  if (adminOnly && !isAdmin) {
    return <Navigate to="/my-diagnosis" replace />;
  }

  if (hospitalOnly && !isHospitalStaff && !isAdmin) {
    return <Navigate to="/my-diagnosis" replace />;
  }

  return children;
};

// Public Route Component (redirects if logged in)
const PublicRoute = ({ children }) => {
  const { isAuthenticated, loading } = useAuth();

  if (loading) {
    return (
      <div style={{ display: 'flex', justifyContent: 'center', alignItems: 'center', minHeight: '50vh' }}>
        <p>로딩 중...</p>
      </div>
    );
  }

  if (isAuthenticated) {
    return <Navigate to="/my-diagnosis" replace />;
  }

  return children;
};

// Admin Navigation Component
const AdminNav = () => {
  const { user, isAdmin } = useAuth();

  if (!isAdmin) return null;

  return (
    <nav className="nav">
      <NavLink to="/admin" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
        대시보드
      </NavLink>
      <NavLink to="/admin/diagnosis" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
        진단 입력
      </NavLink>
      <NavLink to="/admin/search" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
        논문 검색
      </NavLink>
      <NavLink to="/admin/qa" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
        Q&A
      </NavLink>
      <NavLink to="/admin/papers" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
        논문 목록
      </NavLink>
    </nav>
  );
};

// User Navigation Component
const UserNav = () => {
  const { isAuthenticated, isAdmin, isHospitalStaff } = useAuth();

  if (!isAuthenticated || isAdmin || isHospitalStaff) return null;

  return (
    <nav className="nav">
      <NavLink to="/my-diagnosis" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
        내 검사 결과
      </NavLink>
      <NavLink to="/diagnosis" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
        진단 입력
      </NavLink>
      <NavLink to="/qa" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
        Q&A
      </NavLink>
    </nav>
  );
};

// Hospital Staff Navigation Component (Phase 2)
const HospitalNav = () => {
  const { isHospitalStaff } = useAuth();

  if (!isHospitalStaff) return null;

  return (
    <nav className="nav">
      <NavLink to="/hospital" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
        대시보드
      </NavLink>
      <NavLink to="/hospital/patients" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
        환자 관리
      </NavLink>
      <NavLink to="/admin/diagnosis" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
        진단 입력
      </NavLink>
    </nav>
  );
};

// Main App Layout
const AppLayout = () => {
  const { isAuthenticated, isAdmin, isHospitalStaff, user } = useAuth();

  const getSubtitle = () => {
    if (isAdmin) return 'SGTi-Allergy Screen PLUS 진단 결과 분석 및 처방 권고 시스템';
    if (isHospitalStaff) return '병원 환자 관리 시스템';
    return '나의 알러지 검사 결과 조회';
  };

  const getNav = () => {
    if (isAdmin) return <AdminNav />;
    if (isHospitalStaff) return <HospitalNav />;
    return <UserNav />;
  };

  return (
    <div className="app-container">
      {/* 헤더 */}
      <header className="header">
        <h1>AllergyInsight</h1>
        <p className="header-subtitle">{getSubtitle()}</p>
        {getNav()}
      </header>

      {/* 메인 컨텐츠 */}
      <main className="main-content">
        <Routes>
          {/* Public Routes */}
          <Route path="/login" element={
            <PublicRoute><LoginPage /></PublicRoute>
          } />
          <Route path="/auth/callback" element={<AuthCallback />} />

          {/* User Routes */}
          <Route path="/my-diagnosis" element={
            <ProtectedRoute><MyDiagnosisPage /></ProtectedRoute>
          } />
          <Route path="/diagnosis" element={
            <ProtectedRoute><DiagnosisPage /></ProtectedRoute>
          } />
          <Route path="/prescription" element={
            <ProtectedRoute><PrescriptionPage /></ProtectedRoute>
          } />
          <Route path="/qa" element={
            <ProtectedRoute><QAPage /></ProtectedRoute>
          } />

          {/* Hospital Staff Routes (Phase 2) */}
          <Route path="/hospital" element={
            <ProtectedRoute hospitalOnly><HospitalDashboard /></ProtectedRoute>
          } />
          <Route path="/hospital/patients" element={
            <ProtectedRoute hospitalOnly><PatientListPage /></ProtectedRoute>
          } />
          <Route path="/hospital/patients/new" element={
            <ProtectedRoute hospitalOnly><PatientRegisterPage /></ProtectedRoute>
          } />

          {/* Admin Routes */}
          <Route path="/admin" element={
            <ProtectedRoute adminOnly><Dashboard /></ProtectedRoute>
          } />
          <Route path="/admin/diagnosis" element={
            <ProtectedRoute adminOnly><DiagnosisPage /></ProtectedRoute>
          } />
          <Route path="/admin/search" element={
            <ProtectedRoute adminOnly><SearchPage /></ProtectedRoute>
          } />
          <Route path="/admin/qa" element={
            <ProtectedRoute adminOnly><QAPage /></ProtectedRoute>
          } />
          <Route path="/admin/papers" element={
            <ProtectedRoute adminOnly><PapersPage /></ProtectedRoute>
          } />

          {/* Default Route */}
          <Route path="/" element={
            isAuthenticated
              ? (isAdmin ? <Navigate to="/admin" replace /> : <Navigate to="/my-diagnosis" replace />)
              : <Navigate to="/login" replace />
          } />

          {/* Catch all */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </main>

      {/* 푸터 */}
      <footer style={{ textAlign: 'center', padding: '1rem', color: '#666', fontSize: '0.875rem' }}>
        AllergyInsight v1.1.0 | SGTi-Allergy Screen PLUS 기반 알러지 처방 권고 시스템
      </footer>
    </div>
  );
};

function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppLayout />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
