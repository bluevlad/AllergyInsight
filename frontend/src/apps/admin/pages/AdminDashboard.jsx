/**
 * Admin Dashboard Page
 *
 * 플랫폼 전체 통계 및 관리 현황을 보여줍니다.
 */
import React, { useState, useEffect } from 'react';
import { Link } from 'react-router-dom';
import { adminApi } from '../services/adminApi';

const AdminDashboard = () => {
  const [stats, setStats] = useState(null);
  const [recentActivities, setRecentActivities] = useState([]);
  const [pendingItems, setPendingItems] = useState({});
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadDashboard();
  }, []);

  const loadDashboard = async () => {
    try {
      setLoading(true);
      const response = await adminApi.dashboard.get();
      setStats(response.stats);
      setRecentActivities(response.recent_activities || []);
      setPendingItems(response.pending_items || {});
    } catch (err) {
      console.error('Dashboard load failed:', err);
      setError('대시보드 로딩 실패');
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner" />
        <p>대시보드 로딩 중...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="error-container">
        <p>{error}</p>
        <button onClick={loadDashboard}>다시 시도</button>
      </div>
    );
  }

  return (
    <div className="admin-dashboard">
      <h2>플랫폼 관리 대시보드</h2>

      {/* 펜딩 알림 */}
      {pendingItems.pending_organizations > 0 && (
        <div className="alert alert-warning">
          <span className="alert-icon">!</span>
          <span>승인 대기 중인 조직이 {pendingItems.pending_organizations}건 있습니다.</span>
          <Link to="/admin/organizations?status=pending" className="alert-link">
            확인하기
          </Link>
        </div>
      )}

      {/* 통계 카드 */}
      <div className="stats-grid">
        {/* 사용자 통계 */}
        <div className="stat-card users">
          <div className="stat-header">
            <span className="stat-icon">👥</span>
            <h3>사용자</h3>
          </div>
          <div className="stat-body">
            <div className="stat-main">
              <span className="stat-number">{stats?.users?.total || 0}</span>
              <span className="stat-label">전체</span>
            </div>
            <div className="stat-details">
              <div className="stat-row">
                <span>활성</span>
                <span className="stat-value">{stats?.users?.active || 0}</span>
              </div>
              <div className="stat-row">
                <span>최근 7일 가입</span>
                <span className="stat-value highlight">{stats?.users?.recent_signups || 0}</span>
              </div>
            </div>
          </div>
          <div className="stat-footer">
            <Link to="/admin/users">관리하기</Link>
          </div>
        </div>

        {/* 진단 통계 */}
        <div className="stat-card diagnoses">
          <div className="stat-header">
            <span className="stat-icon">🩺</span>
            <h3>진단</h3>
          </div>
          <div className="stat-body">
            <div className="stat-main">
              <span className="stat-number">{stats?.diagnoses?.total_diagnoses || 0}</span>
              <span className="stat-label">전체 진단</span>
            </div>
            <div className="stat-details">
              <div className="stat-row">
                <span>등록 키트</span>
                <span className="stat-value">{stats?.diagnoses?.registered_kits || 0}</span>
              </div>
              <div className="stat-row">
                <span>최근 7일</span>
                <span className="stat-value highlight">{stats?.diagnoses?.recent_diagnoses || 0}</span>
              </div>
            </div>
          </div>
        </div>

        {/* 논문 통계 */}
        <div className="stat-card papers">
          <div className="stat-header">
            <span className="stat-icon">📄</span>
            <h3>논문</h3>
          </div>
          <div className="stat-body">
            <div className="stat-main">
              <span className="stat-number">{stats?.papers?.total || 0}</span>
              <span className="stat-label">전체 논문</span>
            </div>
            <div className="stat-details">
              <div className="stat-row">
                <span>가이드라인</span>
                <span className="stat-value">{stats?.papers?.guidelines || 0}</span>
              </div>
              <div className="stat-row">
                <span>임상 진술문</span>
                <span className="stat-value">{stats?.papers?.clinical_statements || 0}</span>
              </div>
            </div>
          </div>
          <div className="stat-footer">
            <Link to="/admin/papers">관리하기</Link>
          </div>
        </div>

        {/* 조직 통계 */}
        <div className="stat-card organizations">
          <div className="stat-header">
            <span className="stat-icon">🏥</span>
            <h3>조직</h3>
          </div>
          <div className="stat-body">
            <div className="stat-main">
              <span className="stat-number">{stats?.organizations?.total || 0}</span>
              <span className="stat-label">전체 조직</span>
            </div>
            <div className="stat-details">
              <div className="stat-row">
                <span>활성</span>
                <span className="stat-value">{stats?.organizations?.active || 0}</span>
              </div>
              <div className="stat-row">
                <span>승인 대기</span>
                <span className="stat-value warning">{stats?.organizations?.pending_approval || 0}</span>
              </div>
            </div>
          </div>
          <div className="stat-footer">
            <Link to="/admin/organizations">관리하기</Link>
          </div>
        </div>

        {/* 알러젠 통계 */}
        <div className="stat-card allergens">
          <div className="stat-header">
            <span className="stat-icon">🧬</span>
            <h3>알러젠</h3>
          </div>
          <div className="stat-body">
            <div className="stat-main">
              <span className="stat-number">{stats?.allergens?.total || 0}</span>
              <span className="stat-label">전체 항원</span>
            </div>
            <div className="stat-details">
              <div className="stat-row">
                <span>식품</span>
                <span className="stat-value">{stats?.allergens?.by_category?.food || 0}</span>
              </div>
              <div className="stat-row">
                <span>흡입</span>
                <span className="stat-value">{stats?.allergens?.by_category?.inhalant || 0}</span>
              </div>
            </div>
          </div>
          <div className="stat-footer">
            <Link to="/admin/allergens">관리하기</Link>
          </div>
        </div>
      </div>

      {/* 역할별 사용자 분포 */}
      {stats?.users?.by_role && Object.keys(stats.users.by_role).length > 0 && (
        <div className="section">
          <h3>역할별 사용자 분포</h3>
          <div className="role-distribution">
            {Object.entries(stats.users.by_role).map(([role, count]) => (
              <div key={role} className="role-item">
                <span className="role-name">{getRoleName(role)}</span>
                <span className="role-count">{count}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <style>{`
        .admin-dashboard {
          padding: 1rem;
        }

        .admin-dashboard h2 {
          margin-bottom: 1.5rem;
          color: #333;
        }

        .alert {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 1rem;
          border-radius: 8px;
          margin-bottom: 1.5rem;
        }

        .alert-warning {
          background: #fff3cd;
          border: 1px solid #ffc107;
          color: #856404;
        }

        .alert-icon {
          display: flex;
          align-items: center;
          justify-content: center;
          width: 24px;
          height: 24px;
          background: #ffc107;
          color: white;
          border-radius: 50%;
          font-weight: bold;
        }

        .alert-link {
          margin-left: auto;
          color: #856404;
          font-weight: 500;
        }

        .stats-grid {
          display: grid;
          grid-template-columns: repeat(auto-fit, minmax(280px, 1fr));
          gap: 1.5rem;
          margin-bottom: 2rem;
        }

        .stat-card {
          background: white;
          border-radius: 12px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          overflow: hidden;
        }

        .stat-header {
          display: flex;
          align-items: center;
          gap: 0.75rem;
          padding: 1rem;
          background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
          color: white;
        }

        .stat-card.users .stat-header {
          background: linear-gradient(135deg, #3498db 0%, #2980b9 100%);
        }

        .stat-card.diagnoses .stat-header {
          background: linear-gradient(135deg, #2ecc71 0%, #27ae60 100%);
        }

        .stat-card.papers .stat-header {
          background: linear-gradient(135deg, #e74c3c 0%, #c0392b 100%);
        }

        .stat-card.organizations .stat-header {
          background: linear-gradient(135deg, #9b59b6 0%, #8e44ad 100%);
        }

        .stat-card.allergens .stat-header {
          background: linear-gradient(135deg, #f39c12 0%, #d68910 100%);
        }

        .stat-icon {
          font-size: 1.5rem;
        }

        .stat-header h3 {
          margin: 0;
          font-size: 1rem;
          font-weight: 500;
        }

        .stat-body {
          padding: 1rem;
        }

        .stat-main {
          display: flex;
          align-items: baseline;
          gap: 0.5rem;
          margin-bottom: 1rem;
        }

        .stat-number {
          font-size: 2rem;
          font-weight: 700;
          color: #333;
        }

        .stat-label {
          color: #666;
          font-size: 0.875rem;
        }

        .stat-details {
          border-top: 1px solid #eee;
          padding-top: 0.75rem;
        }

        .stat-row {
          display: flex;
          justify-content: space-between;
          padding: 0.25rem 0;
          font-size: 0.875rem;
          color: #666;
        }

        .stat-value {
          font-weight: 500;
          color: #333;
        }

        .stat-value.highlight {
          color: #27ae60;
        }

        .stat-value.warning {
          color: #e67e22;
        }

        .stat-footer {
          padding: 0.75rem 1rem;
          background: #f8f9fa;
          border-top: 1px solid #eee;
          text-align: right;
        }

        .stat-footer a {
          color: #667eea;
          text-decoration: none;
          font-size: 0.875rem;
          font-weight: 500;
        }

        .stat-footer a:hover {
          text-decoration: underline;
        }

        .section {
          background: white;
          border-radius: 12px;
          padding: 1.5rem;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
          margin-bottom: 1.5rem;
        }

        .section h3 {
          margin: 0 0 1rem 0;
          color: #333;
          font-size: 1rem;
        }

        .role-distribution {
          display: flex;
          flex-wrap: wrap;
          gap: 1rem;
        }

        .role-item {
          display: flex;
          align-items: center;
          gap: 0.5rem;
          padding: 0.5rem 1rem;
          background: #f8f9fa;
          border-radius: 20px;
        }

        .role-name {
          color: #666;
          font-size: 0.875rem;
        }

        .role-count {
          background: #667eea;
          color: white;
          padding: 0.125rem 0.5rem;
          border-radius: 10px;
          font-size: 0.75rem;
          font-weight: 600;
        }

        .loading-container,
        .error-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          min-height: 300px;
          gap: 1rem;
        }

        .spinner {
          width: 40px;
          height: 40px;
          border: 4px solid #e9ecef;
          border-top: 4px solid #667eea;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .error-container button {
          padding: 0.5rem 1rem;
          background: #667eea;
          color: white;
          border: none;
          border-radius: 6px;
          cursor: pointer;
        }
      `}</style>
    </div>
  );
};

const getRoleName = (role) => {
  const roleNames = {
    user: '일반 사용자',
    patient: '환자',
    doctor: '의사',
    nurse: '간호사',
    lab_tech: '검사 담당자',
    hospital_admin: '병원 관리자',
    admin: '관리자',
    super_admin: '최고 관리자',
  };
  return roleNames[role] || role;
};

export default AdminDashboard;
