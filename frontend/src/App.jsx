/**
 * AllergyInsight Main App
 *
 * URL 기반 라우팅으로 Professional과 Consumer 앱을 분기합니다.
 * - /pro/* : 의료진 전용 (Professional)
 * - /app/* : 일반 사용자 (Consumer)
 */
import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './shared/contexts/AuthContext';

// Apps
import ProApp from './apps/professional/ProApp';
import ConsumerApp from './apps/consumer/ConsumerApp';
import AdminApp from './apps/admin/AdminApp';
import AnalyticsApp from './apps/analytics/AnalyticsApp';

// Public Pages
import LoginPage from './pages/LoginPage';
import AdminLoginPage from './apps/admin/pages/AdminLoginPage';
import AuthCallback from './pages/AuthCallback';

// Public Subscription Pages
import SubscribePage from './pages/subscribe/SubscribePage';
import VerifyPage from './pages/subscribe/VerifyPage';
import ManagePage from './pages/subscribe/ManagePage';
import UnsubscribePage from './pages/subscribe/UnsubscribePage';

// Public Report Page
import AllergyReportPage from './pages/report/AllergyReportPage';

// Public AI Portal Pages
import AIConsultPage from './pages/ai-consult/AIConsultPage';
import AIInsightPage from './pages/ai-insight/AIInsightPage';

// Public MAST Page (Phase 1)
import MastPage from './pages/mast/MastPage';

// Public Symptom Match Page (Phase 2)
import SymptomMatchPage from './pages/symptoms/SymptomMatchPage';

// Public Drug Info Page (Phase 3)
import DrugInfoPage from './pages/drugs/DrugInfoPage';

// Gateway Landing
import GatewayLanding from './pages/gateway-landing/GatewayLanding';

/**
 * Protected Route Component
 * - professionalOnly: 의료진만 접근 가능
 * - superAdminOnly: super_admin만 접근 가능
 */
const ProtectedRoute = ({ children, professionalOnly = false, superAdminOnly = false }) => {
  const { isAuthenticated, isProfessional, isSuperAdmin, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
        background: '#f8f9fa',
      }}>
        <div style={{ textAlign: 'center' }}>
          <div className="spinner" style={{
            width: '40px',
            height: '40px',
            border: '4px solid #e9ecef',
            borderTop: '4px solid #667eea',
            borderRadius: '50%',
            animation: 'spin 1s linear infinite',
            margin: '0 auto 1rem',
          }} />
          <p style={{ color: '#666' }}>로딩 중...</p>
        </div>
        <style>{`
          @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
          }
        `}</style>
      </div>
    );
  }

  if (!isAuthenticated) {
    // 관리자 페이지 접근 시 관리자 로그인으로 리다이렉트
    const loginPath = location.pathname.startsWith('/admin') ? '/admin/login' : '/login';
    return <Navigate to={loginPath} state={{ from: location }} replace />;
  }

  if (superAdminOnly && !isSuperAdmin) {
    // super_admin 전용 페이지에 접근 시 Pro 앱으로 리다이렉트
    return <Navigate to="/pro" replace />;
  }

  if (professionalOnly && !isProfessional) {
    // 의료진 전용 페이지에 일반 사용자가 접근 시 Consumer 앱으로 리다이렉트
    return <Navigate to="/app" replace />;
  }

  return children;
};

/**
 * Public Route Component
 * - 이미 로그인된 경우 적절한 앱으로 리다이렉트
 */
const PublicRoute = ({ children }) => {
  const { isAuthenticated, getDefaultApp, loading } = useAuth();
  const location = useLocation();

  if (loading) {
    return (
      <div style={{
        display: 'flex',
        justifyContent: 'center',
        alignItems: 'center',
        minHeight: '100vh',
      }}>
        <p>로딩 중...</p>
      </div>
    );
  }

  if (isAuthenticated) {
    // 로그인 후 원래 가려던 페이지가 있으면 해당 페이지로
    const from = location.state?.from?.pathname;
    if (from && from !== '/login') {
      return <Navigate to={from} replace />;
    }
    // 없으면 역할 기반 기본 앱으로
    const defaultApp = getDefaultApp();
    const appRoutes = { admin: '/admin', professional: '/pro', consumer: '/app' };
    return <Navigate to={appRoutes[defaultApp] || '/app'} replace />;
  }

  return children;
};

/**
 * Main Router
 */
const AppRouter = () => {
  return (
    <Routes>
      {/* Public Routes */}
      <Route path="/login" element={
        <PublicRoute>
          <LoginPage />
        </PublicRoute>
      } />
      <Route path="/auth/callback" element={<AuthCallback />} />
      <Route path="/admin/login" element={<AdminLoginPage />} />

      {/* Public Analytics Routes (no auth required) */}
      <Route path="/analytics/*" element={<AnalyticsApp />} />

      {/* Public Subscription Routes (no auth required) */}
      <Route path="/subscribe" element={<SubscribePage />} />
      <Route path="/subscribe/verify" element={<VerifyPage />} />
      <Route path="/subscribe/manage" element={<ManagePage />} />
      <Route path="/subscribe/unsubscribe" element={<UnsubscribePage />} />

      {/* Public Report Route (no auth required) */}
      <Route path="/report" element={<AllergyReportPage />} />

      {/* Public AI Portal Routes (no auth required) */}
      <Route path="/ai/consult" element={<AIConsultPage />} />
      <Route path="/ai/insight" element={<AIInsightPage />} />

      {/* Public MAST Route (Phase 1, no auth required) */}
      <Route path="/mast" element={<MastPage />} />

      {/* Public Symptom Match Route (Phase 2, no auth required) */}
      <Route path="/symptoms" element={<SymptomMatchPage />} />

      {/* Public Drug Info Route (Phase 3, no auth required) */}
      <Route path="/drugs" element={<DrugInfoPage />} />

      {/* Admin App (/admin/*) - 자체 관리자 로그인 폼 포함 */}
      <Route path="/admin/*" element={<AdminApp />} />

      {/* Professional App (/pro/*) */}
      <Route path="/pro/*" element={
        <ProtectedRoute professionalOnly>
          <ProApp />
        </ProtectedRoute>
      } />

      {/* Consumer App (/app/*) */}
      <Route path="/app/*" element={
        <ProtectedRoute>
          <ConsumerApp />
        </ProtectedRoute>
      } />

      {/* Default Route - Gateway or role-based redirect */}
      <Route path="/" element={<GatewayLanding />} />

      {/* Legacy Routes Redirect */}
      <Route path="/hospital/*" element={<Navigate to="/pro" replace />} />
      <Route path="/my-diagnosis" element={<Navigate to="/app/my-diagnosis" replace />} />
      <Route path="/diagnosis" element={<Navigate to="/app/my-diagnosis" replace />} />

      {/* Catch all */}
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
};

/**
 * App Component
 */
function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <AppRouter />
      </AuthProvider>
    </BrowserRouter>
  );
}

export default App;
