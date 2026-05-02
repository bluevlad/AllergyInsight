/**
 * Medical Disclaimer Banner
 *
 * 모든 알러지 정보 화면에 의무적으로 표시되는 의료 면책 안내.
 * 변형: 'banner' (페이지 상단), 'inline' (결과 카드 내), 'compact' (푸터)
 */
import React from 'react';

const MESSAGES = {
  banner:
    '본 정보는 논문 · 전문기관 출처 기반의 교육 · 정보 매칭 목적이며, ' +
    '의료 진단 · 처방을 대체하지 않습니다. 정확한 진단과 처방은 반드시 의료진과 상담하세요.',
  inline:
    '본 정보는 교육 목적이며 의료 진단을 대체하지 않습니다.',
  compact:
    '⚠️ 의료 진단 대체 불가',
};

const STYLES = {
  banner: {
    padding: '0.75rem 1rem',
    background: '#fff8e1',
    border: '1px solid #ffc107',
    borderRadius: '8px',
    color: '#5d4037',
    fontSize: '0.85rem',
    lineHeight: 1.5,
  },
  inline: {
    padding: '0.5rem 0.75rem',
    background: '#f5f5f5',
    borderLeft: '3px solid #ffc107',
    color: '#666',
    fontSize: '0.8rem',
    margin: '0.5rem 0',
  },
  compact: {
    color: '#999',
    fontSize: '0.75rem',
  },
};

const MedicalDisclaimer = ({ variant = 'banner', message }) => {
  const text = message ?? MESSAGES[variant] ?? MESSAGES.banner;
  const style = STYLES[variant] ?? STYLES.banner;

  return (
    <div style={style} role="note">
      {variant === 'banner' && '⚠️ '}{text}
    </div>
  );
};

export default MedicalDisclaimer;
