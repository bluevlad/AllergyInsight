/**
 * Admin App - 플랫폼 관리자 전용 앱
 *
 * /admin/* 경로에서 라우팅됩니다.
 * super_admin 역할만 접근 가능합니다.
 * 미인증 시 관리자 전용 로그인 폼을 표시합니다.
 */
import React, { useState } from 'react';
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
import AnalyticsPage from './pages/AnalyticsPage';

const AdminLoginForm = () => {
  const { loginAdmin } = useAuth();
  const [name, setName] = useState('');
  const [accessPin, setAccessPin] = useState('');
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);
    setError('');

    try {
      await loginAdmin({ name, accessPin });
    } catch (err) {
      const message = err.response?.data?.detail || '로그인에 실패했습니다.';
      setError(message);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      display: 'flex',
      justifyContent: 'center',
      alignItems: 'center',
      minHeight: '100vh',
      background: 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
      padding: '1rem',
    }}>
      <div style={{
        background: 'white',
        borderRadius: '16px',
        boxShadow: '0 20px 60px rgba(0, 0, 0, 0.3)',
        padding: '2.5rem',
        width: '100%',
        maxWidth: '400px',
      }}>
        <div style={{ textAlign: 'center', marginBottom: '2rem' }}>
          <div style={{
            width: '64px',
            height: '64px',
            background: 'linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%)',
            borderRadius: '16px',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            margin: '0 auto 1rem',
            fontSize: '1.75rem',
          }}>
            🔐
          </div>
          <h1 style={{ margin: 0, color: '#2c3e50', fontSize: '1.5rem' }}>AllergyInsight 관리자</h1>
          <p style={{ color: '#888', margin: '0.5rem 0 0', fontSize: '0.9rem' }}>관리자 전용 로그인</p>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: '#555', fontWeight: 500 }}>이름</label>
            <input
              type="text"
              value={name}
              onChange={e => { setName(e.target.value); setError(''); }}
              placeholder="관리자 이름"
              required
              style={{
                width: '100%',
                padding: '0.75rem 1rem',
                border: '2px solid #eee',
                borderRadius: '10px',
                fontSize: '1rem',
                boxSizing: 'border-box',
                transition: 'border-color 0.2s',
                outline: 'none',
              }}
              onFocus={e => e.target.style.borderColor = '#9b59b6'}
              onBlur={e => e.target.style.borderColor = '#eee'}
            />
          </div>

          <div style={{ marginBottom: '1.25rem' }}>
            <label style={{ display: 'block', marginBottom: '0.5rem', fontSize: '0.9rem', color: '#555', fontWeight: 500 }}>접속 PIN</label>
            <input
              type="password"
              value={accessPin}
              onChange={e => { setAccessPin(e.target.value); setError(''); }}
              placeholder="6자리 접속 PIN"
              maxLength={6}
              required
              style={{
                width: '100%',
                padding: '0.75rem 1rem',
                border: '2px solid #eee',
                borderRadius: '10px',
                fontSize: '1rem',
                boxSizing: 'border-box',
                letterSpacing: '0.3rem',
                transition: 'border-color 0.2s',
                outline: 'none',
              }}
              onFocus={e => e.target.style.borderColor = '#9b59b6'}
              onBlur={e => e.target.style.borderColor = '#eee'}
            />
          </div>

          {error && (
            <div style={{
              color: '#e74c3c',
              background: '#fdf0ef',
              padding: '0.75rem 1rem',
              borderRadius: '8px',
              marginBottom: '1rem',
              fontSize: '0.9rem',
            }}>
              {error}
            </div>
          )}

          <button
            type="submit"
            disabled={loading}
            style={{
              width: '100%',
              padding: '0.85rem',
              background: loading ? '#b39ddb' : 'linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%)',
              color: 'white',
              border: 'none',
              borderRadius: '10px',
              fontSize: '1rem',
              fontWeight: 600,
              cursor: loading ? 'not-allowed' : 'pointer',
              transition: 'opacity 0.2s',
            }}
          >
            {loading ? '로그인 중...' : '관리자 로그인'}
          </button>
        </form>

        <p style={{ textAlign: 'center', marginTop: '1.5rem', fontSize: '0.8rem', color: '#aaa' }}>
          AllergyInsight Platform Administration
        </p>
      </div>
    </div>
  );
};

const AdminApp = () => {
  const { user, loading, isSuperAdmin } = useAuth();

  if (loading) {
    return <LoadingSpinner message="로딩 중..." />;
  }

  if (!isSuperAdmin) {
    return <AdminLoginForm />;
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

          {/* Analytics */}
          <Route path="/analytics" element={<AnalyticsPage />} />

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
