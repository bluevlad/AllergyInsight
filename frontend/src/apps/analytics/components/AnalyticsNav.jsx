/**
 * Analytics Navigation Component
 */
import React from 'react';
import { NavLink } from 'react-router-dom';

const AnalyticsNav = () => {
  const navItems = [
    { to: '/analytics/allergen-analysis', label: '알러젠 분석', icon: '🧬' },
    { to: '/analytics/paper-collection', label: '논문 수집정보', icon: '📄' },
    { to: '/analytics/allergen-news', label: '알러젠뉴스 정보', icon: '📰' },
  ];

  return (
    <nav className="an-nav">
      <div className="an-nav-links">
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            className={({ isActive }) => `an-nav-link ${isActive ? 'active' : ''}`}
          >
            <span className="an-nav-icon">{item.icon}</span>
            <span className="an-nav-label">{item.label}</span>
          </NavLink>
        ))}
      </div>

      <div className="an-nav-right">
        <NavLink to="/login" className="an-login-link">
          로그인
        </NavLink>
      </div>

      <style>{`
        .an-nav {
          display: flex;
          justify-content: space-between;
          align-items: center;
          flex-wrap: wrap;
          gap: 1rem;
        }
        .an-nav-links {
          display: flex;
          gap: 0.25rem;
          flex-wrap: wrap;
        }
        .an-nav-link {
          display: flex;
          align-items: center;
          gap: 0.375rem;
          padding: 0.5rem 1rem;
          border-radius: 8px;
          text-decoration: none;
          color: rgba(255, 255, 255, 0.8);
          font-size: 0.875rem;
          transition: all 0.2s;
        }
        .an-nav-link:hover {
          background: rgba(255, 255, 255, 0.15);
          color: white;
        }
        .an-nav-link.active {
          background: rgba(255, 255, 255, 0.25);
          color: white;
          font-weight: 600;
        }
        .an-nav-icon { font-size: 1rem; }
        .an-nav-right {
          display: flex;
          align-items: center;
        }
        .an-login-link {
          padding: 0.5rem 1rem;
          background: rgba(255, 255, 255, 0.2);
          color: white;
          border: 1px solid rgba(255, 255, 255, 0.35);
          border-radius: 8px;
          text-decoration: none;
          font-size: 0.85rem;
          transition: all 0.2s;
        }
        .an-login-link:hover {
          background: rgba(255, 255, 255, 0.3);
        }
        @media (max-width: 768px) {
          .an-nav-label { display: none; }
          .an-nav-icon { font-size: 1.2rem; }
        }
      `}</style>
    </nav>
  );
};

export default AnalyticsNav;
