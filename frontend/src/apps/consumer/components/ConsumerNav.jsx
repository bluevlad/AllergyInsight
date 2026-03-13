/**
 * Consumer Navigation Component
 */
import React from 'react';
import { NavLink } from 'react-router-dom';
import { useAuth } from '../../../shared/contexts/AuthContext';

const ConsumerNav = () => {
  const { user, logout } = useAuth();

  const navItems = [
    { to: '/app/my-diagnosis', label: '내 검사결과', icon: '📋' },
    { to: '/app/food-guide', label: '식품 가이드', icon: '🍽️' },
    { to: '/app/lifestyle', label: '생활 관리', icon: '🏠' },
    { to: '/app/emergency', label: '응급 대처', icon: '🚨' },
    { to: '/app/kit-register', label: '키트 등록', icon: '📦' },
    { to: '/report', label: '알러지 리포트', icon: '📄', external: true },
  ];

  return (
    <nav className="nav consumer-nav">
      <div className="nav-links">
        {navItems.map((item) => (
          item.external ? (
            <a
              key={item.to}
              href={item.to}
              target="_blank"
              rel="noopener noreferrer"
              className="nav-link"
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </a>
          ) : (
            <NavLink
              key={item.to}
              to={item.to}
              className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}
            >
              <span className="nav-icon">{item.icon}</span>
              <span className="nav-label">{item.label}</span>
            </NavLink>
          )
        ))}
      </div>

      <div className="nav-user">
        <span className="user-info">
          {user?.name}님
        </span>
        <button onClick={logout} className="logout-btn">
          로그아웃
        </button>
      </div>

      <style>{`
        .consumer-nav {
          display: flex;
          justify-content: space-between;
          align-items: center;
          flex-wrap: wrap;
          gap: 1rem;
        }

        .nav-links {
          display: flex;
          gap: 0.25rem;
          flex-wrap: wrap;
        }

        .consumer-nav .nav-link {
          display: flex;
          align-items: center;
          gap: 0.25rem;
          padding: 0.5rem 0.75rem;
          border-radius: 20px;
          text-decoration: none;
          color: rgba(255, 255, 255, 0.8);
          transition: all 0.2s;
          font-size: 0.9rem;
        }

        .consumer-nav .nav-link:hover {
          background: rgba(255, 255, 255, 0.2);
          color: white;
        }

        .consumer-nav .nav-link.active {
          background: rgba(255, 255, 255, 0.3);
          color: white;
          font-weight: 600;
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
          color: rgba(255, 255, 255, 0.9);
          font-size: 0.875rem;
        }

        .logout-btn {
          padding: 0.5rem 1rem;
          background: rgba(255, 255, 255, 0.2);
          color: white;
          border: 1px solid rgba(255, 255, 255, 0.3);
          border-radius: 20px;
          cursor: pointer;
          font-size: 0.875rem;
          transition: all 0.2s;
        }

        .logout-btn:hover {
          background: rgba(255, 255, 255, 0.3);
        }

        @media (max-width: 768px) {
          .consumer-nav {
            flex-direction: column;
          }

          .nav-links {
            justify-content: center;
          }

          .nav-label {
            display: none;
          }

          .consumer-nav .nav-link {
            padding: 0.5rem;
          }

          .nav-icon {
            font-size: 1.25rem;
          }
        }
      `}</style>
    </nav>
  );
};

export default ConsumerNav;
