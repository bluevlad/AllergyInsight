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
      <h2 style={{ marginBottom: '1.25rem', fontSize: '1.25rem', fontWeight: 700, color: '#2c3e50' }}>
        분석 대시보드
      </h2>

      {/* 탭 네비게이션 */}
      <div className="analytics-tabs">
        {tabs.map(tab => (
          <button
            key={tab.key}
            onClick={() => setActiveTab(tab.key)}
            className={`analytics-tab ${activeTab === tab.key ? 'active' : ''}`}
          >
            <span className="analytics-tab-icon">{tab.icon}</span>
            <span className="analytics-tab-label">{tab.label}</span>
          </button>
        ))}
      </div>

      {/* 탭 콘텐츠 */}
      <ActiveComponent />

      <style>{`
        .analytics-tabs {
          display: flex;
          gap: 0;
          margin-bottom: 1.5rem;
          background: white;
          border-radius: 10px;
          padding: 0.25rem;
          box-shadow: 0 2px 8px rgba(0,0,0,0.05);
        }

        .analytics-tab {
          flex: 1;
          display: flex;
          align-items: center;
          justify-content: center;
          gap: 0.375rem;
          padding: 0.75rem 1rem;
          background: none;
          border: none;
          border-radius: 8px;
          color: #888;
          font-size: 0.85rem;
          font-weight: 500;
          cursor: pointer;
          transition: all 0.2s;
        }

        .analytics-tab:hover:not(.active) {
          background: #f8f9fa;
          color: #555;
        }

        .analytics-tab.active {
          background: linear-gradient(135deg, #9b59b6, #8e44ad);
          color: white;
          font-weight: 600;
          box-shadow: 0 2px 8px rgba(155, 89, 182, 0.3);
        }

        .analytics-tab-icon {
          font-size: 1rem;
        }

        @media (max-width: 768px) {
          .analytics-tab-label {
            display: none;
          }

          .analytics-tab {
            padding: 0.75rem 0.5rem;
          }

          .analytics-tab-icon {
            font-size: 1.2rem;
          }
        }
      `}</style>
    </div>
  );
};

export default AnalyticsPage;
