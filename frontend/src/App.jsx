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
 * Role Based Redirect / Gateway Landing
 * - 로그인 상태: 역할에 따라 적절한 앱으로 리다이렉트
 * - 비로그인 상태: 4-서비스 게이트웨이 표시
 */
const GatewayLanding = () => {
  const { isAuthenticated, getDefaultApp, loading } = useAuth();

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
    const defaultApp = getDefaultApp();
    const appRoutes = { admin: '/admin', professional: '/pro', consumer: '/app' };
    return <Navigate to={appRoutes[defaultApp] || '/app'} replace />;
  }

  // 비로그인 사용자용 게이트웨이
  return (
    <div style={{ minHeight: '100vh', background: '#f5f6fa' }}>
      <div style={{
        background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
        padding: '3rem 1rem',
        textAlign: 'center',
        color: 'white',
      }}>
        <h1 style={{ margin: 0, fontSize: '2rem' }}>AllergyInsight</h1>
        <p style={{ margin: '0.5rem 0 0', opacity: 0.9, fontSize: '1rem' }}>
          알러지 연구 논문 검색/분석 플랫폼
        </p>
      </div>

      <div style={{
        maxWidth: '900px',
        margin: '2rem auto',
        padding: '0 1rem',
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '1.5rem',
      }}>
        <GatewayCard
          title="알러지 리포트"
          description="알러젠 정보를 입력하고 맞춤 관리 리포트를 받으세요"
          href="/report"
          color="#e74c3c"
          icon="M9 12h6m-6 4h6m2 5H7a2 2 0 01-2-2V5a2 2 0 012-2h5.586a1 1 0 01.707.293l5.414 5.414a1 1 0 01.293.707V19a2 2 0 01-2 2z"
        />
        <GatewayCard
          title="뉴스레터"
          description="알러지 관련 최신 뉴스와 연구 동향을 구독하세요"
          href="/subscribe"
          color="#e67e22"
          icon="M3 8l7.89 5.26a2 2 0 002.22 0L21 8M5 19h14a2 2 0 002-2V7a2 2 0 00-2-2H5a2 2 0 00-2 2v10a2 2 0 002 2z"
        />
        <GatewayCard
          title="사용자"
          description="검사 결과 조회 및 맞춤 건강 가이드"
          href="/login"
          color="#3498db"
          icon="M16 7a4 4 0 11-8 0 4 4 0 018 0zM12 14a7 7 0 00-7 7h14a7 7 0 00-7-7z"
        />
        <GatewayCard
          title="관리자"
          description="플랫폼 관리 및 운영 시스템"
          href="/admin/login"
          color="#9b59b6"
          icon="M12 15v2m-6 4h12a2 2 0 002-2v-6a2 2 0 00-2-2H6a2 2 0 00-2 2v6a2 2 0 002 2zm10-10V7a4 4 0 00-8 0v4h8z"
        />
        <GatewayCard
          title="분석/통계"
          description="알러젠 트렌드 및 키워드 분석 대시보드"
          href="/analytics"
          color="#1abc9c"
          icon="M9 19v-6a2 2 0 00-2-2H5a2 2 0 00-2 2v6a2 2 0 002 2h2a2 2 0 002-2zm0 0V9a2 2 0 012-2h2a2 2 0 012 2v10m-6 0a2 2 0 002 2h2a2 2 0 002-2m0 0V5a2 2 0 012-2h2a2 2 0 012 2v14a2 2 0 01-2 2h-2a2 2 0 01-2-2z"
        />
      </div>

      <footer style={{ textAlign: 'center', padding: '2rem 1rem', color: '#999', fontSize: '0.85rem' }}>
        AllergyInsight Platform v2.0.0
      </footer>
    </div>
  );
};

const GatewayCard = ({ title, description, href, color, icon }) => (
  <a
    href={href}
    style={{
      display: 'block',
      background: 'white',
      borderRadius: '12px',
      boxShadow: '0 2px 8px rgba(0,0,0,0.1)',
      padding: '1.5rem',
      textDecoration: 'none',
      color: 'inherit',
      transition: 'transform 0.2s, box-shadow 0.2s',
      borderTop: `4px solid ${color}`,
    }}
    onMouseEnter={e => {
      e.currentTarget.style.transform = 'translateY(-4px)';
      e.currentTarget.style.boxShadow = '0 8px 24px rgba(0,0,0,0.15)';
    }}
    onMouseLeave={e => {
      e.currentTarget.style.transform = 'translateY(0)';
      e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.1)';
    }}
  >
    <div style={{
      width: '48px',
      height: '48px',
      borderRadius: '12px',
      background: color,
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      marginBottom: '1rem',
    }}>
      <svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
        <path d={icon} />
      </svg>
    </div>
    <h3 style={{ margin: '0 0 0.5rem', fontSize: '1.1rem', color: '#333' }}>{title}</h3>
    <p style={{ margin: 0, fontSize: '0.85rem', color: '#777', lineHeight: 1.5 }}>{description}</p>
  </a>
);

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
