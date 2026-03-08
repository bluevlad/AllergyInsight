/**
 * 주간 브리핑 탭 - 뉴스레터 미리보기 + 키워드 + 임상 하이라이트
 */
import React, { useState, useEffect } from 'react';
import { adminApi } from '../../services/adminApi';

const BriefingTab = () => {
  const [days, setDays] = useState(7);
  const [previewHtml, setPreviewHtml] = useState('');
  const [keywords, setKeywords] = useState(null);
  const [clinical, setClinical] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    loadAll();
  }, [days]);

  const loadAll = async () => {
    try {
      setLoading(true);
      setError(null);
      const [html, kw, cl] = await Promise.all([
        adminApi.newsletter.preview({ days }).catch(() => ''),
        adminApi.analytics.keywordsOverview().catch(() => null),
        adminApi.analytics.overview().catch(() => null),
      ]);
      setPreviewHtml(html);
      setKeywords(kw);
      setClinical(cl);
    } catch (err) {
      setError('브리핑 데이터를 불러오지 못했습니다.');
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <p>로딩 중...</p>;
  if (error) return <div style={{ color: '#e74c3c', padding: '1rem' }}>{error} <button onClick={loadAll}>재시도</button></div>;

  const risingKeywords = keywords?.rising_keywords || [];
  const allergens = clinical?.allergens || [];
  const top5 = allergens.slice(0, 5);

  return (
    <div>
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        <label>기간: </label>
        <select value={days} onChange={e => setDays(Number(e.target.value))} style={{ padding: '0.5rem', borderRadius: '6px', border: '1px solid #ddd' }}>
          <option value={1}>1일</option>
          <option value={3}>3일</option>
          <option value={7}>7일</option>
        </select>
        <button onClick={loadAll} style={{ padding: '0.5rem 1rem', background: '#9b59b6', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>
          새로고침
        </button>
      </div>

      {/* KPI 요약 카드 */}
      <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
        <KpiCard label="알러젠 수" value={clinical?.total_allergens ?? '-'} />
        <KpiCard label="검사 수" value={clinical?.total_tests?.toLocaleString() ?? '-'} color="#3498db" />
        <KpiCard label="키워드 수" value={keywords?.total_keywords ?? '-'} color="#2ecc71" />
        <KpiCard label="상승 키워드" value={risingKeywords.length} color="#e74c3c" />
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(300px, 1fr))', gap: '1.5rem', marginBottom: '1.5rem' }}>
        {/* 키워드 핫 토픽 */}
        <div style={{ background: 'white', borderRadius: '8px', padding: '1rem', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}>
          <h4 style={{ margin: '0 0 0.75rem 0' }}>키워드 핫 토픽</h4>
          {risingKeywords.length > 0 ? (
            <div style={{ display: 'flex', flexWrap: 'wrap', gap: '0.5rem' }}>
              {risingKeywords.map((kw, i) => (
                <span key={i} style={{
                  padding: '0.4rem 0.75rem',
                  background: '#9b59b6',
                  color: 'white',
                  borderRadius: '16px',
                  fontSize: '0.85rem',
                }}>
                  {kw.keyword} {kw.change_rate != null ? `+${kw.change_rate.toFixed(0)}%` : '🆕'}
                </span>
              ))}
            </div>
          ) : (
            <p style={{ color: '#888', fontSize: '0.85rem' }}>상승 키워드가 없습니다.</p>
          )}
        </div>

        {/* 임상 하이라이트 */}
        <div style={{ background: 'white', borderRadius: '8px', padding: '1rem', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}>
          <h4 style={{ margin: '0 0 0.75rem 0' }}>임상 하이라이트 (양성률 TOP 5)</h4>
          {top5.length > 0 ? (
            <table style={{ width: '100%', borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ background: '#f8f9fa', textAlign: 'left' }}>
                  <th style={{ padding: '0.5rem' }}>알러젠</th>
                  <th style={{ padding: '0.5rem' }}>양성률</th>
                  <th style={{ padding: '0.5rem' }}>검사 수</th>
                </tr>
              </thead>
              <tbody>
                {top5.map((a, i) => (
                  <tr key={i} style={{ borderBottom: '1px solid #eee' }}>
                    <td style={{ padding: '0.5rem' }}>{a.allergen_code}</td>
                    <td style={{ padding: '0.5rem', fontWeight: 600, color: '#9b59b6' }}>{(a.positive_rate * 100).toFixed(1)}%</td>
                    <td style={{ padding: '0.5rem', color: '#888' }}>{a.total_tests?.toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          ) : (
            <p style={{ color: '#888', fontSize: '0.85rem' }}>임상 데이터가 없습니다.</p>
          )}
        </div>
      </div>

      {/* 뉴스레터 미리보기 */}
      <div style={{ background: 'white', borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)', overflow: 'hidden' }}>
        <h4 style={{ margin: 0, padding: '1rem 1rem 0.5rem 1rem' }}>뉴스레터 미리보기 ({days}일)</h4>
        {previewHtml ? (
          <div dangerouslySetInnerHTML={{ __html: previewHtml }} />
        ) : (
          <p style={{ color: '#888', padding: '1rem', textAlign: 'center' }}>뉴스레터 미리보기를 불러올 수 없습니다.</p>
        )}
      </div>
    </div>
  );
};

const KpiCard = ({ label, value, color }) => (
  <div style={{ background: 'white', padding: '0.75rem 1.25rem', borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}>
    <span style={{ fontSize: '0.85rem', color: '#888' }}>{label} </span>
    <span style={{ fontSize: '1.1rem', fontWeight: 700, color: color || '#333' }}>{value}</span>
  </div>
);

export default BriefingTab;
