/**
 * Insight Detail Page - 알러젠 인사이트 리포트 상세 보기
 */
import React, { useState, useEffect } from 'react';
import { useParams, useNavigate } from 'react-router-dom';
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

const InsightDetailPage = () => {
  const { reportId } = useParams();
  const navigate = useNavigate();
  const [report, setReport] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);

  useEffect(() => {
    setLoading(true);
    analyticsApi.getInsightDetail(reportId)
      .then(setReport)
      .catch((err) => setError(err.response?.status === 404 ? '리포트를 찾을 수 없습니다.' : '데이터를 불러올 수 없습니다.'))
      .finally(() => setLoading(false));
  }, [reportId]);

  const getScoreColor = (score) => {
    if (score >= 70) return '#27ae60';
    if (score >= 40) return '#f39c12';
    return '#e74c3c';
  };

  const renderMarkdown = (text) => {
    if (!text) return '';
    return text
      .replace(/^### (.+)$/gm, '<h4 style="margin:1.2rem 0 0.5rem;color:#2c3e50">$1</h4>')
      .replace(/^## (.+)$/gm, '<h3 style="margin:1.5rem 0 0.75rem;color:#1abc9c;border-bottom:2px solid #e8f8f5;padding-bottom:0.4rem">$1</h3>')
      .replace(/^# (.+)$/gm, '<h2 style="margin:1.5rem 0 0.75rem;color:#2c3e50">$1</h2>')
      .replace(/\*\*(.+?)\*\*/g, '<strong>$1</strong>')
      .replace(/\*(.+?)\*/g, '<em>$1</em>')
      .replace(/^- (.+)$/gm, '<li style="margin:0.25rem 0;color:#555">$1</li>')
      .replace(/(<li[^>]*>.*<\/li>\n?)+/g, '<ul style="padding-left:1.5rem;margin:0.5rem 0">$&</ul>')
      .replace(/\n\n/g, '<br/><br/>')
      .replace(/\n/g, '<br/>');
  };

  if (loading) {
    return <div style={styles.loading}>불러오는 중...</div>;
  }

  if (error) {
    return (
      <div style={styles.errorContainer}>
        <p>{error}</p>
        <button onClick={() => navigate('/analytics/insights')} style={styles.backBtn}>
          목록으로 돌아가기
        </button>
      </div>
    );
  }

  if (!report) return null;

  const allergenLabel = ALLERGEN_LABELS[report.allergen_code] || report.allergen_code;

  return (
    <div style={styles.container}>
      <button onClick={() => navigate('/analytics/insights')} style={styles.backBtn}>
        &larr; 인사이트 목록
      </button>

      <article style={styles.article}>
        {/* Header */}
        <div style={styles.articleHeader}>
          <div style={styles.meta}>
            <span style={styles.allergenTag}>{allergenLabel}</span>
            <span style={styles.period}>{report.period_date} ({report.period_type})</span>
          </div>
          <h1 style={styles.articleTitle}>{report.title}</h1>
          <div style={styles.stats}>
            <span style={styles.statItem}>
              분석 소스 <strong>{report.source_count}</strong>건
            </span>
            {report.source_paper_ids && (
              <span style={styles.statItem}>
                논문 <strong>{report.source_paper_ids.length}</strong>편
              </span>
            )}
            {report.source_news_ids && (
              <span style={styles.statItem}>
                뉴스 <strong>{report.source_news_ids.length}</strong>건
              </span>
            )}
          </div>
        </div>

        {/* Treatment Score */}
        {report.treatment_score != null && (
          <div style={styles.scoreSection}>
            <div style={styles.scoreHeader}>
              <span style={styles.scoreTitle}>치료 발전도</span>
              <span style={{ ...styles.scoreBig, color: getScoreColor(report.treatment_score) }}>
                {report.treatment_score}
                <span style={styles.scoreMax}>/100</span>
              </span>
            </div>
            <div style={styles.scoreBarBig}>
              <div
                style={{
                  height: '100%',
                  width: `${report.treatment_score}%`,
                  background: `linear-gradient(90deg, ${getScoreColor(report.treatment_score)}88, ${getScoreColor(report.treatment_score)})`,
                  borderRadius: '5px',
                  transition: 'width 0.5s',
                }}
              />
            </div>
          </div>
        )}

        {/* Key Findings */}
        {report.key_findings && report.key_findings.length > 0 && (
          <div style={styles.findingsSection}>
            <h3 style={styles.sectionTitle}>핵심 발견</h3>
            <div style={styles.findingsGrid}>
              {report.key_findings.map((finding, i) => (
                <div key={i} style={styles.findingCard}>
                  <span style={styles.findingNum}>{i + 1}</span>
                  <span style={styles.findingText}>{finding}</span>
                </div>
              ))}
            </div>
          </div>
        )}

        {/* Content */}
        <div style={styles.contentSection}>
          <div
            style={styles.contentBody}
            dangerouslySetInnerHTML={{ __html: renderMarkdown(report.content) }}
          />
        </div>

        {/* Footer */}
        <div style={styles.footer}>
          <span style={styles.footerText}>
            생성일: {report.created_at ? new Date(report.created_at).toLocaleDateString('ko-KR') : '-'}
          </span>
          <span style={styles.footerText}>
            AI 기반 자동 분석 리포트
          </span>
        </div>
      </article>
    </div>
  );
};

const styles = {
  container: { maxWidth: '800px', margin: '0 auto', padding: '2rem 1rem' },
  loading: { textAlign: 'center', padding: '3rem', color: '#999' },
  errorContainer: { textAlign: 'center', padding: '3rem', color: '#e74c3c' },
  backBtn: {
    display: 'inline-flex', alignItems: 'center', gap: '0.25rem',
    padding: '0.5rem 1rem', background: 'none', border: '1px solid #ddd',
    borderRadius: '8px', cursor: 'pointer', color: '#555', fontSize: '0.9rem',
    marginBottom: '1rem', transition: 'all 0.2s',
  },
  article: {
    background: 'white', borderRadius: '16px', overflow: 'hidden',
    boxShadow: '0 2px 12px rgba(0,0,0,0.08)',
  },
  articleHeader: {
    padding: '2rem 2rem 1.5rem',
    borderBottom: '1px solid #f0f0f0',
    background: 'linear-gradient(180deg, #f8fffe 0%, white 100%)',
  },
  meta: { display: 'flex', alignItems: 'center', gap: '0.75rem', marginBottom: '0.75rem' },
  allergenTag: {
    background: '#1abc9c', color: 'white', padding: '0.3rem 0.8rem',
    borderRadius: '15px', fontSize: '0.85rem', fontWeight: 600,
  },
  period: { color: '#999', fontSize: '0.85rem' },
  articleTitle: { margin: 0, fontSize: '1.4rem', color: '#2c3e50', lineHeight: 1.4 },
  stats: { display: 'flex', gap: '1rem', marginTop: '1rem' },
  statItem: { fontSize: '0.85rem', color: '#888' },
  scoreSection: {
    padding: '1.5rem 2rem', background: '#fafbfc',
    borderBottom: '1px solid #f0f0f0',
  },
  scoreHeader: {
    display: 'flex', justifyContent: 'space-between', alignItems: 'center',
    marginBottom: '0.75rem',
  },
  scoreTitle: { fontSize: '0.9rem', color: '#555', fontWeight: 600 },
  scoreBig: { fontSize: '1.5rem', fontWeight: 700 },
  scoreMax: { fontSize: '0.85rem', color: '#999', fontWeight: 400 },
  scoreBarBig: {
    height: '10px', background: '#eee', borderRadius: '5px', overflow: 'hidden',
  },
  findingsSection: { padding: '1.5rem 2rem', borderBottom: '1px solid #f0f0f0' },
  sectionTitle: { margin: '0 0 1rem', fontSize: '1rem', color: '#2c3e50' },
  findingsGrid: { display: 'flex', flexDirection: 'column', gap: '0.5rem' },
  findingCard: {
    display: 'flex', alignItems: 'flex-start', gap: '0.75rem',
    padding: '0.75rem 1rem', background: '#f8f9fa', borderRadius: '8px',
  },
  findingNum: {
    display: 'flex', alignItems: 'center', justifyContent: 'center',
    width: '24px', height: '24px', background: '#1abc9c', color: 'white',
    borderRadius: '50%', fontSize: '0.75rem', fontWeight: 700, flexShrink: 0,
  },
  findingText: { fontSize: '0.9rem', color: '#444', lineHeight: 1.5 },
  contentSection: { padding: '2rem' },
  contentBody: { fontSize: '0.95rem', lineHeight: 1.8, color: '#333' },
  footer: {
    display: 'flex', justifyContent: 'space-between', padding: '1rem 2rem',
    borderTop: '1px solid #f0f0f0', background: '#fafbfc',
  },
  footerText: { fontSize: '0.8rem', color: '#999' },
};

export default InsightDetailPage;
