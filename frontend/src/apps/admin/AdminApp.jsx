/**
 * Admin App - 플랫폼 관리자 전용 앱
 *
 * /admin/* 경로에서 라우팅됩니다.
 * super_admin 역할만 접근 가능합니다.
 */
import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import AdminNav from './components/AdminNav';
import { useAuth } from '../../shared/contexts/AuthContext';
import { LoadingSpinner } from '../../shared/components';

// Admin Pages
import AdminDashboard from './pages/AdminDashboard';
import UsersPage from './pages/UsersPage';
import AllergensPage from './pages/AllergensPage';
import PapersPage from './pages/PapersPage';
import OrganizationsPage from './pages/OrganizationsPage';
import CompetitorNewsPage from './pages/CompetitorNewsPage';

const AdminApp = () => {
  const { user, loading, isSuperAdmin } = useAuth();

  if (loading) {
    return <LoadingSpinner message="로딩 중..." />;
  }

  if (!isSuperAdmin) {
    return <Navigate to="/pro" replace />;
  }

  return (
    <div className="admin-app">
      <header className="header admin-header">
        <h1>AllergyInsight Admin</h1>
        <p className="header-subtitle">
          플랫폼 관리 시스템 | Super Admin
        </p>
        <AdminNav />
      </header>

      <main className="main-content">
        <Routes>
          {/* Dashboard */}
          <Route path="/" element={<AdminDashboard />} />
          <Route path="/dashboard" element={<AdminDashboard />} />

          {/* Users */}
          <Route path="/users" element={<UsersPage />} />
          <Route path="/users/:id" element={<UsersPage />} />

          {/* Allergens */}
          <Route path="/allergens" element={<AllergensPage />} />
          <Route path="/allergens/:code" element={<AllergensPage />} />

          {/* Papers */}
          <Route path="/papers" element={<PapersPage />} />
          <Route path="/papers/:id" element={<PapersPage />} />

          {/* Organizations */}
          <Route path="/organizations" element={<OrganizationsPage />} />
          <Route path="/organizations/:id" element={<OrganizationsPage />} />

          {/* Competitor News */}
          <Route path="/news" element={<CompetitorNewsPage />} />

          {/* Fallback */}
          <Route path="*" element={<Navigate to="/admin" replace />} />
        </Routes>
      </main>

      <footer style={{ textAlign: 'center', padding: '1rem', color: '#666', fontSize: '0.875rem' }}>
        AllergyInsight Admin v1.0.0 | Platform Administration
      </footer>

      <style>{`
        .admin-app {
          min-height: 100vh;
          background: #f5f6fa;
        }

        .admin-header {
          background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%);
        }

        .admin-header h1 {
          color: white;
        }

        .admin-header .header-subtitle {
          color: rgba(255, 255, 255, 0.9);
        }
      `}</style>
    </div>
  );
};

export default AdminApp;
