/**
 * Professional Navigation Component
 */
import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../../shared/contexts/AuthContext';

const ProNav = () => {
  const { user, logout } = useAuth();

  const navItems = [
    { to: '/pro/dashboard', label: '대시보드', icon: '📊' },
    { to: '/pro/patients', label: '환자 관리', icon: '👥' },
    { to: '/pro/diagnosis', label: '진단 입력', icon: '🩺' },
    { to: '/pro/clinical-report', label: '임상보고서', icon: '📋' },
    { to: '/pro/search', label: '논문 검색', icon: '🔍' },
    { to: '/pro/qa', label: 'Q&A', icon: '💬' },
    { to: '/pro/papers', label: '논문 목록', icon: '📄' },
  ];

  const getRoleName = (role) => {
    const roleNames = {
      doctor: '의사',
      nurse: '간호사',
      lab_tech: '검사 담당자',
      hospital_admin: '병원 관리자',
      admin: '관리자',
      super_admin: '최고 관리자',
    };
    return roleNames[role] || role;
  };

  return (
    <nav className="nav pro-nav">
      <div className="nav-links">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
          >
            <span className="nav-icon">{item.icon}</span>
            <span className="nav-label">{item.label}</span>
          </NavLink>
        ))}
      </div>

      <div className="nav-user">
        <span className="user-info">
          {user?.name} ({getRoleName(user?.role)})
        </span>
        <button onClick={logout} className="logout-btn">
          로그아웃
        </button>
      </div>

      <style>{`
        .pro-nav {
          display: flex;
          justify-content: space-between;
          align-items: center;
          flex-wrap: wrap;
          gap: 1rem;
        }

        .nav-links {
          display: flex;
          gap: 0.5rem;
          flex-wrap: wrap;
        }

        .nav-link {
          display: flex;
          align-items: center;
          gap: 0.25rem;
          padding: 0.5rem 1rem;
          border-radius: 6px;
          text-decoration: none;
          color: #666;
          transition: all 0.2s;
        }

        .nav-link:hover {
          background: rgba(255, 255, 255, 0.1);
          color: #333;
        }

        .nav-link.active {
          background: #3498db;
          color: white;
        }

        .nav-icon {
          font-size: 1rem;
        }

        .nav-user {
          display: flex;
          align-items: center;
          gap: 1rem;
        }

        .user-info {
          color: #666;
          font-size: 0.875rem;
        }

        .logout-btn {
          padding: 0.5rem 1rem;
          background: #e74c3c;
          color: white;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-size: 0.875rem;
          transition: background 0.2s;
        }

        .logout-btn:hover {
          background: #c0392b;
        }

        @media (max-width: 768px) {
          .pro-nav {
            flex-direction: column;
          }

          .nav-links {
            justify-content: center;
          }

          .nav-label {
            display: none;
          }
        }
      `}</style>
    </nav>
  );
};

export default ProNav;
