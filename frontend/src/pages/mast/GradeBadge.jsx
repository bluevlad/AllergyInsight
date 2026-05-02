/**
 * Grade Badge - MAST Class 0~4 한·영 병기 배지
 *
 * 사용 예: <GradeBadge value={3} level="강양성" levelEn="Class 3" color="orangered" />
 */
import React from 'react';

const COLOR_MAP = {
  green: { bg: '#e8f5e9', fg: '#2e7d32' },
  yellow: { bg: '#fff8e1', fg: '#f57f17' },
  orange: { bg: '#fff3e0', fg: '#e65100' },
  orangered: { bg: '#ffebee', fg: '#c62828' },
  darkred: { bg: '#b71c1c', fg: '#ffffff' },
};

const GradeBadge = ({ value, level, levelEn, color = 'green', size = 'md' }) => {
  const palette = COLOR_MAP[color] ?? COLOR_MAP.green;
  const padding = size === 'lg' ? '0.5rem 1rem' : size === 'sm' ? '0.2rem 0.5rem' : '0.35rem 0.75rem';
  const fontSize = size === 'lg' ? '1.1rem' : size === 'sm' ? '0.75rem' : '0.9rem';

  return (
    <span
      style={{
        display: 'inline-flex',
        alignItems: 'center',
        gap: '0.4rem',
        padding,
        background: palette.bg,
        color: palette.fg,
        borderRadius: '999px',
        fontSize,
        fontWeight: 600,
        lineHeight: 1,
        whiteSpace: 'nowrap',
      }}
    >
      <span>{level}</span>
      <span style={{ opacity: 0.7, fontSize: '0.85em', fontWeight: 500 }}>
        {levelEn ?? `Class ${value}`}
      </span>
    </span>
  );
};

export default GradeBadge;
