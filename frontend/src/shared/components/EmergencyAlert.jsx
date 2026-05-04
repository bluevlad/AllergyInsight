/**
 * Emergency Alert
 *
 * 안전 가드(safety_gate) 응답을 받아 응급/주의 알림을 노출한다.
 * 사용자가 닫을 수 없는 stickier 배너로 표시되어, 챗봇 답변보다 먼저 인지된다.
 *
 * Props:
 *   safety: { level: 'emergency'|'concern'|'none', message: string, matched_keywords?: string[] }
 *
 * level === 'none' 또는 safety가 falsy 면 렌더링하지 않는다.
 */
import React from 'react';

const STYLES = {
  emergency: {
    background: '#ffebee',
    border: '2px solid #c62828',
    color: '#5d1717',
    title: '🚨 응급 상황 의심',
    titleColor: '#c62828',
  },
  concern: {
    background: '#fff8e1',
    border: '2px solid #f57c00',
    color: '#5d4037',
    title: '⚠️ 응급 가능성 안내',
    titleColor: '#e65100',
  },
};

const EmergencyAlert = ({ safety }) => {
  if (!safety || !safety.level || safety.level === 'none') return null;

  const palette = STYLES[safety.level] ?? STYLES.concern;
  const lines = (safety.message ?? '').split('\n').filter(Boolean);

  return (
    <div
      role="alert"
      style={{
        padding: '1rem 1.25rem',
        background: palette.background,
        border: palette.border,
        borderRadius: '8px',
        marginBottom: '1rem',
      }}
    >
      <h3
        style={{
          margin: '0 0 0.6rem',
          color: palette.titleColor,
          fontSize: '1.05rem',
        }}
      >
        {palette.title}
      </h3>
      {lines.map((line, i) => (
        <p
          key={i}
          style={{
            margin: i === 0 ? 0 : '0.4rem 0 0',
            color: palette.color,
            lineHeight: 1.65,
            whiteSpace: 'pre-wrap',
          }}
        >
          {renderInlineBold(line)}
        </p>
      ))}
      <p
        style={{
          margin: '0.75rem 0 0',
          color: palette.color,
          fontSize: '0.85rem',
          opacity: 0.8,
        }}
      >
        본 서비스는 응급 의료 서비스가 아닙니다. 응급 시 119 / 의료진이 우선입니다.
      </p>
    </div>
  );
};

// 시스템 메시지의 **bold** 처리 (간이 마크다운)
const renderInlineBold = (text) => {
  const parts = text.split(/\*\*(.+?)\*\*/g);
  return parts.map((p, i) =>
    i % 2 === 1 ? <strong key={i}>{p}</strong> : <React.Fragment key={i}>{p}</React.Fragment>
  );
};

export default EmergencyAlert;
