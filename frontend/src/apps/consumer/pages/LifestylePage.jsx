/**
 * Consumer Lifestyle Page - 생활 관리
 */
import React, { useState, useEffect } from 'react';
import { consumerApi } from '../services/consumerApi';

function LifestylePage() {
  const [lifestyle, setLifestyle] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const data = await consumerApi.guide.getLifestyle();
      setLifestyle(data);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="loading">
        <div className="spinner"></div>
      </div>
    );
  }

  const getCategoryIcon = (category) => {
    const icons = {
      '실내 환경': '🏠',
      '청소': '🧹',
      '외출': '🚶',
      '수면': '😴',
      '계절': '🍂',
    };
    return icons[category] || '💡';
  };

  return (
    <div style={{ maxWidth: '900px', margin: '0 auto' }}>
      <h2>생활 관리 가이드</h2>
      <p style={{ color: '#666', marginBottom: '1.5rem' }}>
        알러지 증상을 줄이기 위한 일상 생활 관리 팁입니다.
      </p>

      {/* 알러젠별 관리 팁 */}
      {lifestyle?.allergen_specific?.length > 0 && (
        <div style={{ marginBottom: '2rem' }}>
          <h3>알러젠별 관리 방법</h3>
          <div style={{ display: 'grid', gap: '1rem' }}>
            {lifestyle.allergen_specific.map((item, idx) => (
              <div key={idx} className="card">
                <h4>{item.allergen}</h4>
                <ul style={{ paddingLeft: '1.5rem', marginTop: '0.5rem' }}>
                  {item.tips.map((tip, i) => (
                    <li key={i} style={{ marginBottom: '0.5rem' }}>{tip}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 공통 생활 팁 */}
      {lifestyle?.common_tips?.length > 0 && (
        <div>
          <h3>일반 관리 팁</h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))', gap: '1rem' }}>
            {lifestyle.common_tips.map((section, idx) => (
              <div key={idx} className="tip-card">
                <div className="tip-header">
                  <span className="tip-icon">{getCategoryIcon(section.category)}</span>
                  <div>
                    <p className="tip-category">{section.category}</p>
                    <h4 className="tip-title">{section.title}</h4>
                  </div>
                </div>
                <ul className="tip-list">
                  {section.tips.map((tip, i) => (
                    <li key={i}>{tip}</li>
                  ))}
                </ul>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* 추가 팁 카드들 */}
      <div style={{ marginTop: '2rem' }}>
        <h3>추가 관리 팁</h3>
        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '1rem' }}>
          <div className="card" style={{ background: '#e3f2fd' }}>
            <h4>😴 수면 환경</h4>
            <ul style={{ paddingLeft: '1.5rem', marginTop: '0.5rem' }}>
              <li>알러지 방지 베개/이불 커버 사용</li>
              <li>침구류 주 1회 이상 고온 세탁</li>
              <li>침실에 공기청정기 배치</li>
              <li>침대 아래 물건 최소화</li>
            </ul>
          </div>

          <div className="card" style={{ background: '#f3e5f5' }}>
            <h4>🍽️ 식사 시</h4>
            <ul style={{ paddingLeft: '1.5rem', marginTop: '0.5rem' }}>
              <li>식품 라벨 꼼꼼히 확인</li>
              <li>외식 시 알러지 정보 문의</li>
              <li>교차 오염 주의</li>
              <li>비상약 항상 휴대</li>
            </ul>
          </div>

          <div className="card" style={{ background: '#fff3e0' }}>
            <h4>🏃 운동</h4>
            <ul style={{ paddingLeft: '1.5rem', marginTop: '0.5rem' }}>
              <li>꽃가루 시즌에는 실내 운동 권장</li>
              <li>운동 전 준비운동 충분히</li>
              <li>운동 유발 알러지 주의</li>
              <li>운동 후 샤워</li>
            </ul>
          </div>

          <div className="card" style={{ background: '#e8f5e9' }}>
            <h4>🧳 여행 시</h4>
            <ul style={{ paddingLeft: '1.5rem', marginTop: '0.5rem' }}>
              <li>응급 행동 계획서 휴대</li>
              <li>에피펜 여분 준비</li>
              <li>현지어로 알러지 설명 카드 준비</li>
              <li>근처 병원 위치 파악</li>
            </ul>
          </div>
        </div>
      </div>

      {/* 계절별 팁 */}
      <div style={{ marginTop: '2rem' }}>
        <h3>🗓️ 계절별 관리</h3>
        <div className="card">
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem' }}>
            <div style={{ textAlign: 'center', padding: '1rem', background: '#ffebee', borderRadius: '8px' }}>
              <p style={{ fontSize: '2rem' }}>🌸</p>
              <p style={{ fontWeight: '600' }}>봄</p>
              <p style={{ fontSize: '0.875rem', color: '#666' }}>꽃가루 주의</p>
            </div>
            <div style={{ textAlign: 'center', padding: '1rem', background: '#e8f5e9', borderRadius: '8px' }}>
              <p style={{ fontSize: '2rem' }}>☀️</p>
              <p style={{ fontWeight: '600' }}>여름</p>
              <p style={{ fontSize: '0.875rem', color: '#666' }}>곰팡이/진드기</p>
            </div>
            <div style={{ textAlign: 'center', padding: '1rem', background: '#fff8e1', borderRadius: '8px' }}>
              <p style={{ fontSize: '2rem' }}>🍂</p>
              <p style={{ fontWeight: '600' }}>가을</p>
              <p style={{ fontSize: '0.875rem', color: '#666' }}>쑥/돼지풀</p>
            </div>
            <div style={{ textAlign: 'center', padding: '1rem', background: '#e3f2fd', borderRadius: '8px' }}>
              <p style={{ fontSize: '2rem' }}>❄️</p>
              <p style={{ fontWeight: '600' }}>겨울</p>
              <p style={{ fontSize: '0.875rem', color: '#666' }}>실내 진드기</p>
            </div>
          </div>
        </div>
      </div>

      <style>{`
        .tip-card {
          background: white;
          border: 1px solid #eee;
          border-radius: 12px;
          padding: 1.5rem;
          transition: box-shadow 0.2s;
        }
        .tip-card:hover {
          box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }
        .tip-header {
          display: flex;
          align-items: center;
          gap: 1rem;
          margin-bottom: 1rem;
        }
        .tip-icon {
          font-size: 2.5rem;
        }
        .tip-category {
          font-size: 0.75rem;
          color: #666;
          text-transform: uppercase;
        }
        .tip-title {
          margin: 0;
        }
        .tip-list {
          padding-left: 1.5rem;
          margin: 0;
        }
        .tip-list li {
          margin-bottom: 0.5rem;
          color: #555;
        }
      `}</style>
    </div>
  );
}

export default LifestylePage;
