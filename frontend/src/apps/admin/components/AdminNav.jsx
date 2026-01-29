/**
 * Admin Navigation Component
 */
import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../../shared/contexts/AuthContext';

const AdminNav = () => {
  const { user, logout } = useAuth();

  const navItems = [
    { to: '/admin/dashboard', label: '대시보드', icon: '📊' },
    { to: '/admin/users', label: '사용자 관리', icon: '👥' },
    { to: '/admin/allergens', label: '알러젠 관리', icon: '🧬' },
    { to: '/admin/papers', label: '논문 관리', icon: '📄' },
    { to: '/admin/organizations', label: '조직 관리', icon: '🏥' },
  ];

  return (
    <nav className="nav admin-nav">
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
          {user?.name} (Super Admin)
        </span>
        <NavLink to="/pro" className="nav-link switch-link">
          Pro
        </NavLink>
        <button onClick={logout} className="logout-btn">
          로그아웃
        </button>
      </div>

      <style>{`
        .admin-nav {
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
          background: #9b59b6;
          color: white;
        }

        .switch-link {
          background: #3498db;
          color: white !important;
        }

        .switch-link:hover {
          background: #2980b9;
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
          .admin-nav {
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

export default AdminNav;
