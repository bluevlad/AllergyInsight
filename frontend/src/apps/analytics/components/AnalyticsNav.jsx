/**
 * Analytics Navigation Component
 *
 * 공개 Analytics 앱의 네비게이션 바입니다.
 * 인증 불필요 - 로그인 링크만 제공합니다.
 */
import React from 'react';
import { NavLink } from 'react-router-dom';

const AnalyticsNav = () => {
  const navItems = [
    { to: '/analytics/dashboard', label: 'Dashboard' },
    { to: '/analytics/allergen-trends', label: '알러젠 트렌드' },
    { to: '/analytics/keyword-trends', label: '키워드 트렌드' },
  ];

  return (
    <nav style={styles.nav}>
      <div style={styles.navLinks}>
        {navItems.map((item) => (
          <NavLink
            key={item.to}
            to={item.to}
            style={({ isActive }) => ({
              ...styles.navLink,
              ...(isActive ? styles.navLinkActive : {}),
            })}
          >
            {item.label}
          </NavLink>
        ))}
      </div>

      <div style={styles.navRight}>
        <NavLink to="/login" style={styles.loginLink}>
          로그인
        </NavLink>
      </div>
    </nav>
  );
};

const styles = {
  nav: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
    flexWrap: 'wrap',
    gap: '1rem',
  },
  navLinks: {
    display: 'flex',
    gap: '0.5rem',
    flexWrap: 'wrap',
  },
  navLink: {
    display: 'flex',
    alignItems: 'center',
    gap: '0.25rem',
    padding: '0.5rem 1rem',
    borderRadius: '6px',
    textDecoration: 'none',
    color: 'rgba(255, 255, 255, 0.85)',
    transition: 'all 0.2s',
    fontSize: '0.9rem',
  },
  navLinkActive: {
    background: 'rgba(255, 255, 255, 0.25)',
    color: 'white',
    fontWeight: 600,
  },
  navRight: {
    display: 'flex',
    alignItems: 'center',
    gap: '1rem',
  },
  loginLink: {
    padding: '0.5rem 1rem',
    background: 'rgba(255, 255, 255, 0.2)',
    color: 'white',
    border: '1px solid rgba(255, 255, 255, 0.4)',
    borderRadius: '6px',
    textDecoration: 'none',
    fontSize: '0.875rem',
    transition: 'all 0.2s',
  },
};

export default AnalyticsNav;
