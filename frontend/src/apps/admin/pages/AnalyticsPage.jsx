/**
 * Admin Analytics 대시보드 페이지
 * 4개 탭: 주간 브리핑, 임상 트렌드, 시장 인텔리전스, 활동 통계
 */
import React, { useState } from 'react';
import BriefingTab from './analytics/BriefingTab';
import ClinicalTrendTab from './analytics/ClinicalTrendTab';
import MarketIntelTab from './analytics/MarketIntelTab';
import ActivityTab from './analytics/ActivityTab';

const tabs = [
  { key: 'briefing', label: '주간 브리핑', icon: '📋' },
  { key: 'clinical', label: '임상 트렌드', icon: '🧬' },
  { key: 'market', label: '시장 인텔리전스', icon: '🔍' },
  { key: 'activity', label: '활동 통계', icon: '📈' },
];

const tabComponents = {
  briefing: BriefingTab,
  clinical: ClinicalTrendTab,
  market: MarketIntelTab,
  activity: ActivityTab,
};

const AnalyticsPage = () => {
  const [activeTab, setActiveTab] = useState('briefing');
  const ActiveComponent = tabComponents[activeTab];

  return (
    <div style={{ padding: '1rem' }}>
      <h2>분석 대시보드</h2>

      <div style={{ display: 'flex', gap: 0, borderBottom: '2px solid #eee', marginBottom: '1rem' }}>
        {tabs.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            style={{
              padding: '0.75rem 1.5rem',
              background: 'none',
              border: 'none',
              borderBottom: activeTab === tab.key ? '2px solid #9b59b6' : '2px solid transparent',
              color: activeTab === tab.key ? '#9b59b6' : '#888',
              fontWeight: activeTab === tab.key ? 600 : 400,
              cursor: 'pointer',
              marginBottom: '-2px',
              display: 'flex',
              alignItems: 'center',
              gap: '0.25rem',
            }}
          >
            <span>{tab.icon}</span>
            <span className="analytics-tab-label">{tab.label}</span>
          </button>
        ))}
      </div>

      <ActiveComponent />

      <style>{`
        @media (max-width: 768px) {
          .analytics-tab-label {
            display: none;
          }
        }
      `}</style>
    </div>
  );
};

export default AnalyticsPage;
