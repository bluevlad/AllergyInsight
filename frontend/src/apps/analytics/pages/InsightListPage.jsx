/**
 * Insight List Page - 알러젠별 연구 인사이트 리포트 목록
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { analyticsApi } from '../services/analyticsApi';

const ALLERGEN_LABELS = {
  peanut: '땅콩', milk: '우유', egg: '계란', wheat: '밀', soy: '대두',
  fish: '생선', shrimp: '새우', crab: '게', peach: '복숭아', walnut: '호두',
  dust_mite: '집먼지진드기', dog: '개', cat: '고양이', mold: '곰팡이',
  cedar: '삼나무', birch: '자작나무', ragweed: '돼지풀', grass: '잔디',
  pine_nut: '잣', sesame: '참깨', buckwheat: '메밀', tomato: '토마토',
  pork: '돼지고기', chicken: '닭고기', beef: '소고기', squid: '오징어',
  mussel: '홍합', abalone: '전복', cockroach: '바퀴벌레', mugwort: '쑥',
};

const InsightListPage = () => {
  const navigate = useNavigate();
  const [allergens, setAllergens] = useState([]);
  const [reports, setReports] = useState([]);
  const [selectedAllergen, setSelectedAllergen] = useState('');
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    analyticsApi.getInsightAllergens()
      .then(setAllergens)
      .catch(() => setAllergens([]))
      .finally(() => setLoading(false));
  }, []);

  useEffect(() => {
    setLoading(true);
    const params = selectedAllergen ? { allergen: selectedAllergen, limit: 20 } : { limit: 20 };
    analyticsApi.getInsightReports(params)
      .then(setReports)
      .catch(() => setReports([]))
      .finally(() => setLoading(false));
  }, [selectedAllergen]);

  const getScoreColor = (score) => {
    if (score >= 70) return '#27ae60';
    if (score >= 40) return '#f39c12';
    return '#e74c3c';
  };

  return (
    <div style={styles.container}>
      <div style={styles.header}>
        <h2 style={styles.title}>연구 인사이트</h2>
        <p style={styles.subtitle}>
          수집된 논문/뉴스를 AI가 분석하여 알러젠별 연구 동향과 치료 발전 현황을 제공합니다
        </p>
      </div>

      {/* 알러젠 필터 */}
      <div style={styles.filterSection}>
        <button
          onClick={() => setSelectedAllergen('')}
          style={{
            ...styles.filterBtn,
            ...(selectedAllergen === '' ? styles.filterBtnActive : {}),
          }}
        >
          전체
        </button>
        {allergens.map((a) => (
          <button
            key={a.allergen_code}
            onClick={() => setSelectedAllergen(a.allergen_code)}
            style={{
              ...styles.filterBtn,
              ...(selectedAllergen === a.allergen_code ? styles.filterBtnActive : {}),
            }}
          >
            {ALLERGEN_LABELS[a.allergen_code] || a.allergen_code}
            <span style={styles.badge}>{a.report_count}</span>
          </button>
        ))}
      </div>

      {/* 리포트 목록 */}
      {loading ? (
        <div style={styles.loading}>불러오는 중...</div>
      ) : reports.length === 0 ? (
        <div style={styles.empty}>
          <p style={styles.emptyText}>아직 생성된 인사이트 리포트가 없습니다.</p>
          <p style={styles.emptySubtext}>
            논문/뉴스가 충분히 수집되면 매월 자동으로 생성됩니다.
          </p>
        </div>
      ) : (
        <div style={styles.grid}>
          {reports.map((report) => (
            <div
              key={report.id}
              style={styles.card}
              onClick={() => navigate(`/analytics/insights/${report.id}`)}
              onMouseEnter={(e) => {
                e.currentTarget.style.transform = 'translateY(-4px)';
                e.currentTarget.style.boxShadow = '0 8px 24px rgba(0,0,0,0.12)';
              }}
              onMouseLeave={(e) => {
                e.currentTarget.style.transform = 'translateY(0)';
                e.currentTarget.style.boxShadow = '0 2px 8px rgba(0,0,0,0.08)';
              }}
            >
              <div style={styles.cardTop}>
                <span style={styles.allergenTag}>
                  {ALLERGEN_LABELS[report.allergen_code] || report.allergen_code}
                </span>
                <span style={styles.period}>{report.period_date}</span>
              </div>
              <h3 style={styles.cardTitle}>{report.title}</h3>
              {report.key_findings && report.key_findings.length > 0 && (
                <ul style={styles.findings}>
                  {report.key_findings.slice(0, 3).map((f, i) => (
                    <li key={i} style={styles.findingItem}>{f}</li>
                  ))}
                </ul>
              )}
              <div style={styles.cardBottom}>
                <div style={styles.scoreWrap}>
                  <span style={styles.scoreLabel}>치료 발전도</span>
                  <div style={styles.scoreBar}>
                    <div
                      style={{
                        ...styles.scoreFill,
                        width: `${report.treatment_score || 0}%`,
                        background: getScoreColor(report.treatment_score),
                      }}
                    />
                  </div>
                  <span style={{ ...styles.scoreValue, color: getScoreColor(report.treatment_score) }}>
                    {report.treatment_score || 0}
                  </span>
                </div>
                <span style={styles.sourceCount}>{report.source_count}건 분석</span>
              </div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const styles = {
  container: { maxWidth: '1000px', margin: '0 auto', padding: '2rem 1rem' },
  header: { marginBottom: '1.5rem' },
  title: { margin: 0, fontSize: '1.5rem', color: '#2c3e50' },
  subtitle: { margin: '0.5rem 0 0', color: '#7f8c8d', fontSize: '0.9rem' },
  filterSection: {
    display: 'flex', flexWrap: 'wrap', gap: '0.5rem', marginBottom: '1.5rem',
    padding: '1rem', background: 'white', borderRadius: '10px',
    boxShadow: '0 1px 4px rgba(0,0,0,0.06)',
  },
  filterBtn: {
    display: 'flex', alignItems: 'center', gap: '0.35rem',
    padding: '0.4rem 0.8rem', border: '1px solid #ddd', borderRadius: '20px',
    background: 'white', cursor: 'pointer', fontSize: '0.85rem', color: '#555',
    transition: 'all 0.2s',
  },
  filterBtnActive: {
    background: '#1abc9c', color: 'white', borderColor: '#1abc9c',
  },
  badge: {
    fontSize: '0.7rem', background: 'rgba(0,0,0,0.1)', borderRadius: '10px',
    padding: '0.1rem 0.4rem',
  },
  loading: { textAlign: 'center', padding: '3rem', color: '#999' },
  empty: {
    textAlign: 'center', padding: '4rem 2rem', background: 'white',
    borderRadius: '12px', boxShadow: '0 2px 8px rgba(0,0,0,0.06)',
  },
  emptyText: { fontSize: '1.1rem', color: '#555', margin: 0 },
  emptySubtext: { fontSize: '0.9rem', color: '#999', marginTop: '0.5rem' },
  grid: { display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(300px, 1fr))', gap: '1rem' },
  card: {
    background: 'white', borderRadius: '12px', padding: '1.25rem',
    boxShadow: '0 2px 8px rgba(0,0,0,0.08)', cursor: 'pointer',
    transition: 'transform 0.2s, box-shadow 0.2s',
    display: 'flex', flexDirection: 'column', gap: '0.75rem',
  },
  cardTop: { display: 'flex', justifyContent: 'space-between', alignItems: 'center' },
  allergenTag: {
    background: '#e8f8f5', color: '#1abc9c', padding: '0.2rem 0.6rem',
    borderRadius: '12px', fontSize: '0.8rem', fontWeight: 600,
  },
  period: { color: '#999', fontSize: '0.8rem' },
  cardTitle: { margin: 0, fontSize: '1rem', color: '#2c3e50', lineHeight: 1.4 },
  findings: { margin: 0, padding: '0 0 0 1.2rem', fontSize: '0.85rem', color: '#666' },
  findingItem: { marginBottom: '0.25rem' },
  cardBottom: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    marginTop: 'auto', paddingTop: '0.5rem', borderTop: '1px solid #f0f0f0',
  },
  scoreWrap: { display: 'flex', alignItems: 'center', gap: '0.5rem', flex: 1 },
  scoreLabel: { fontSize: '0.75rem', color: '#999', whiteSpace: 'nowrap' },
  scoreBar: {
    flex: 1, height: '6px', background: '#eee', borderRadius: '3px',
    overflow: 'hidden', maxWidth: '80px',
  },
  scoreFill: { height: '100%', borderRadius: '3px', transition: 'width 0.3s' },
  scoreValue: { fontSize: '0.8rem', fontWeight: 700, minWidth: '24px' },
  sourceCount: { fontSize: '0.75rem', color: '#999' },
};

export default InsightListPage;
