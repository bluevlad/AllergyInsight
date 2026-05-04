import React from 'react';
import { Link } from 'react-router-dom';

const BackToHomeBar = ({ variant = 'light' }) => {
  const isDark = variant === 'dark';

  const barStyle = {
    width: '100%',
    background: isDark ? 'rgba(15, 23, 42, 0.85)' : '#ffffff',
    borderBottom: isDark ? '1px solid rgba(148, 163, 184, 0.18)' : '1px solid #e5e7eb',
    padding: '0.5rem 1rem',
    boxSizing: 'border-box',
    backdropFilter: 'blur(6px)',
    WebkitBackdropFilter: 'blur(6px)',
  };

  const linkStyle = {
    display: 'inline-flex',
    alignItems: 'center',
    gap: '0.35rem',
    color: isDark ? '#cbd5e1' : '#475569',
    textDecoration: 'none',
    fontSize: '0.875rem',
    fontWeight: 500,
    lineHeight: 1.4,
  };

  return (
    <nav style={barStyle} aria-label="홈 복귀">
      <Link to="/" style={linkStyle} className="back-to-home-link">
        <span aria-hidden="true">←</span>
        <span>AllergyInsight 홈</span>
      </Link>
      <style>{`
        .back-to-home-link:hover {
          color: ${isDark ? '#ffffff' : '#1e293b'} !important;
          text-decoration: underline;
        }
      `}</style>
    </nav>
  );
};

export default BackToHomeBar;
