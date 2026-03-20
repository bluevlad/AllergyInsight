/**
 * Comprehensive Allergen Trend Dashboard (Phase 5)
 *
 * 논문 언급률 + 치료법 + 뉴스 + 진단 양성률 + 역학 데이터를
 * 단일 페이지에 통합하여 시각화합니다.
 */
import React, { useState, useEffect } from 'react';
import {
  LineChart, Line, BarChart, Bar, AreaChart, Area,
  XAxis, YAxis, CartesianGrid, Tooltip, Legend,
  ResponsiveContainer, Cell, PieChart, Pie,
} from 'recharts';
import { analyticsApi } from '../services/analyticsApi';

const COLORS = ['#1abc9c', '#3498db', '#9b59b6', '#e74c3c', '#f39c12', '#2ecc71', '#e67e22', '#1f77b4'];
const TYPE_COLORS = {
  drug: '#3498db', immunotherapy: '#9b59b6', biologic: '#e74c3c',
  avoidance: '#f39c12', dietary: '#2ecc71',
};
const DIRECTION_BADGE = {
  rising: { label: 'Rising', color: '#e74c3c', bg: '#fdeaea' },
  stable: { label: 'Stable', color: '#f39c12', bg: '#fef5e7' },
  declining: { label: 'Declining', color: '#3498db', bg: '#eaf2fd' },
  new: { label: 'New', color: '#2ecc71', bg: '#eafaf1' },
};

const KpiCard = ({ icon, label, value, sub, color = '#333' }) => (
  <div className="ct-kpi-card">
    <div className="ct-kpi-icon" style={{ background: `${color}15`, color }}>{icon}</div>
    <div>
      <div className="ct-kpi-label">{label}</div>
      <div className="ct-kpi-value" style={{ color }}>{value}</div>
      {sub && <div className="ct-kpi-sub">{sub}</div>}
    </div>
  </div>
);

const DirectionBadge = ({ direction }) => {
  const d = DIRECTION_BADGE[direction] || { label: direction, color: '#999', bg: '#f5f5f5' };
  return (
    <span className="ct-badge" style={{ color: d.color, background: d.bg }}>
      {d.label}
    </span>
  );
};

const ComprehensiveTrendPage = () => {
  const [overview, setOverview] = useState(null);
  const [ranking, setRanking] = useState(null);
  const [allergenList, setAllergenList] = useState([]);
  const [selectedAllergen, setSelectedAllergen] = useState('');
  const [comprehensive, setComprehensive] = useState(null);
  const [loading, setLoading] = useState(true);
  const [detailLoading, setDetailLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => { loadOverview(); }, []);

  useEffect(() => {
    if (selectedAllergen) loadDetail(selectedAllergen);
  }, [selectedAllergen]);

  const loadOverview = async () => {
    try {
      setLoading(true);
      const [ov, rk, al] = await Promise.allSettled([
        analyticsApi.getPaperTrendOverview(),
        analyticsApi.getPaperTrendRanking({ direction: 'rising', limit: 10 }),
        analyticsApi.getAllergenList({ active_only: true }),
      ]);
      if (ov.status === 'fulfilled') setOverview(ov.value);
      if (rk.status === 'fulfilled') setRanking(rk.value);
      if (al.status === 'fulfilled') {
        const list = al.value?.allergens || al.value || [];
        setAllergenList(Array.isArray(list) ? list : []);
        // 자동 선택: overview의 top_allergens 첫번째
        if (!selectedAllergen && ov.status === 'fulfilled' && ov.value?.top_allergens?.length) {
          setSelectedAllergen(ov.value.top_allergens[0].allergen_code);
        }
      }
    } catch (e) {
      setError('데이터를 불러오는 데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const loadDetail = async (code) => {
    try {
      setDetailLoading(true);
      const data = await analyticsApi.getComprehensiveTrend(code);
      setComprehensive(data);
    } catch {
      setComprehensive(null);
    } finally {
      setDetailLoading(false);
    }
  };

  if (loading) return <div className="ct-loading">Loading...</div>;
  if (error && !overview) return (
    <div className="ct-error">
      <p>{error}</p>
      <button onClick={loadOverview} className="ct-retry-btn">다시 시도</button>
    </div>
  );

  // 차트 데이터 변환
  const paperChartData = comprehensive?.paper_trend?.trends?.map(t => ({
    period: t.period,
    '언급률': +((t.mention_rate || 0) * 100).toFixed(2),
    '논문수': t.paper_count,
  })) || [];

  const newsChartData = comprehensive?.news_trend?.trends?.map(t => ({
    period: t.period,
    '뉴스수': t.total,
  })) || [];

  const diagnosisChartData = comprehensive?.diagnosis_trend?.trends?.map(t => ({
    period: (t.period || '').slice(0, 7),
    '양성률': +((t.positive_rate || 0) * 100).toFixed(1),
    '평균등급': +(t.avg_grade || 0).toFixed(2),
  })) || [];

  const treatmentPieData = comprehensive?.treatments?.items?.map(t => ({
    name: t.name_kr || t.name,
    value: t.paper_count,
    type: t.type,
  })) || [];

  // 역학 데이터
  const epiData = comprehensive?.epidemiology?.by_type || {};

  return (
    <div className="ct-page">
      {/* KPI Cards */}
      {overview && (
        <div className="ct-kpi-grid">
          <KpiCard icon="📊" label="최신 분석 연도" value={overview.latest_year || '-'} color="#1abc9c" />
          <KpiCard icon="🧬" label="분석 알러젠" value={`${overview.total_allergens || 0}종`} color="#3498db" />
          <KpiCard icon="📄" label="총 논문 수" value={`${(overview.total_papers || 0).toLocaleString()}편`} color="#9b59b6" />
          <KpiCard
            icon="📈" label="트렌드 요약" color="#e74c3c"
            value={`${overview.summary?.rising || 0} Rising`}
            sub={`${overview.summary?.declining || 0} Declining / ${overview.summary?.stable || 0} Stable`}
          />
        </div>
      )}

      {/* 알러젠 선택 */}
      <div className="ct-card">
        <div className="ct-card-header">
          <h3>알러젠 종합 트렌드</h3>
          <select
            className="ct-select"
            value={selectedAllergen}
            onChange={(e) => setSelectedAllergen(e.target.value)}
          >
            <option value="">-- 알러젠 선택 --</option>
            {overview?.top_allergens?.map(a => (
              <option key={a.allergen_code} value={a.allergen_code}>
                {a.allergen_code} ({a.paper_count}편)
              </option>
            ))}
            {allergenList.filter(a => !overview?.top_allergens?.some(t => t.allergen_code === a.code))
              .map(a => (
                <option key={a.code} value={a.code}>{a.code} - {a.name_kr}</option>
              ))}
          </select>
        </div>

        {detailLoading && <div className="ct-loading-inline">Loading...</div>}

        {comprehensive && !detailLoading && (
          <div className="ct-detail-grid">
            {/* 논문 언급률 추이 (Line Chart) */}
            {paperChartData.length > 0 && (
              <div className="ct-chart-card">
                <h4>논문 언급률 추이</h4>
                <p className="ct-chart-desc">수집 논문 기준 — 전체 논문 대비 해당 알러젠 언급 비율</p>
                <ResponsiveContainer width="100%" height={280}>
                  <LineChart data={paperChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="period" tick={{ fontSize: 11 }} />
                    <YAxis yAxisId="left" unit="%" tick={{ fontSize: 11 }} />
                    <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} />
                    <Tooltip contentStyle={{ borderRadius: '8px', border: '1px solid #eee' }} />
                    <Legend />
                    <Line yAxisId="left" type="monotone" dataKey="언급률" stroke="#1abc9c" strokeWidth={2.5}
                      dot={{ r: 3, fill: '#1abc9c' }} activeDot={{ r: 5 }} />
                    <Line yAxisId="right" type="monotone" dataKey="논문수" stroke="#3498db" strokeWidth={2}
                      dot={{ r: 3, fill: '#3498db' }} strokeDasharray="5 5" />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* 진단 양성률 추이 */}
            {diagnosisChartData.length > 0 && (
              <div className="ct-chart-card">
                <h4>진단 양성률 추이</h4>
                <ResponsiveContainer width="100%" height={280}>
                  <LineChart data={diagnosisChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="period" tick={{ fontSize: 11 }} />
                    <YAxis yAxisId="left" unit="%" tick={{ fontSize: 11 }} />
                    <YAxis yAxisId="right" orientation="right" tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Legend />
                    <Line yAxisId="left" type="monotone" dataKey="양성률" stroke="#e74c3c" strokeWidth={2.5}
                      dot={{ r: 3, fill: '#e74c3c' }} />
                    <Line yAxisId="right" type="monotone" dataKey="평균등급" stroke="#f39c12" strokeWidth={2}
                      dot={{ r: 3, fill: '#f39c12' }} />
                  </LineChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* 뉴스 언급량 추이 (Area Chart) */}
            {newsChartData.length > 0 && (
              <div className="ct-chart-card">
                <h4>뉴스 언급량 추이</h4>
                <ResponsiveContainer width="100%" height={280}>
                  <AreaChart data={newsChartData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#f0f0f0" />
                    <XAxis dataKey="period" tick={{ fontSize: 11 }} />
                    <YAxis tick={{ fontSize: 11 }} />
                    <Tooltip />
                    <Area type="monotone" dataKey="뉴스수" stroke="#9b59b6" fill="#9b59b620" strokeWidth={2} />
                  </AreaChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* 치료법 분포 (Pie Chart) */}
            {treatmentPieData.length > 0 && (
              <div className="ct-chart-card">
                <h4>관련 치료법</h4>
                <ResponsiveContainer width="100%" height={280}>
                  <PieChart>
                    <Pie data={treatmentPieData} dataKey="value" nameKey="name"
                      cx="50%" cy="50%" outerRadius={90} innerRadius={45}
                      label={({ name, percent }) => `${name} ${(percent * 100).toFixed(0)}%`}
                      labelLine={{ stroke: '#ccc' }}>
                      {treatmentPieData.map((entry, i) => (
                        <Cell key={i} fill={TYPE_COLORS[entry.type] || COLORS[i % COLORS.length]} />
                      ))}
                    </Pie>
                    <Tooltip />
                  </PieChart>
                </ResponsiveContainer>
              </div>
            )}

            {/* 역학 데이터 테이블 */}
            {Object.keys(epiData).length > 0 && (
              <div className="ct-chart-card ct-full-width">
                <h4>역학 데이터</h4>
                <p className="ct-disclaimer">{comprehensive.epidemiology?.disclaimer}</p>
                {Object.entries(epiData).map(([type, items]) => (
                  <div key={type} style={{ marginBottom: '1rem' }}>
                    <h5 className="ct-epi-type">{type}</h5>
                    <table className="ct-table">
                      <thead>
                        <tr><th>연도</th><th>수치</th><th>단위</th><th>지역</th><th>신뢰도</th></tr>
                      </thead>
                      <tbody>
                        {items.map((item, i) => (
                          <tr key={i}>
                            <td>{item.year || '-'}</td>
                            <td><strong>{item.value}</strong></td>
                            <td>{item.unit}</td>
                            <td>{item.region || '-'}</td>
                            <td>
                              <span className="ct-confidence" style={{
                                color: item.confidence_score >= 0.7 ? '#2ecc71' : item.confidence_score >= 0.4 ? '#f39c12' : '#e74c3c',
                              }}>
                                {((item.confidence_score || 0) * 100).toFixed(0)}%
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ))}
              </div>
            )}

            {/* 데이터 없는 섹션 안내 */}
            {paperChartData.length === 0 && newsChartData.length === 0 &&
             diagnosisChartData.length === 0 && treatmentPieData.length === 0 &&
             Object.keys(epiData).length === 0 && (
              <div className="ct-chart-card ct-full-width">
                <p style={{ textAlign: 'center', color: '#999', padding: '2rem' }}>
                  선택한 알러젠의 분석 데이터가 아직 없습니다.
                </p>
              </div>
            )}
          </div>
        )}
      </div>

      {/* 상승/하락 알러젠 랭킹 */}
      {overview?.top_allergens && (
        <div className="ct-card">
          <h3>알러젠 논문 언급 랭킹 ({overview.latest_year})</h3>
          <div className="ct-ranking-grid">
            {overview.top_allergens.map((a, i) => (
              <div
                key={a.allergen_code}
                className={`ct-ranking-item ${selectedAllergen === a.allergen_code ? 'selected' : ''}`}
                onClick={() => setSelectedAllergen(a.allergen_code)}
              >
                <span className="ct-rank">#{i + 1}</span>
                <span className="ct-allergen-name">{a.allergen_code}</span>
                <span className="ct-paper-count">{a.paper_count}편</span>
                <span className="ct-mention-rate">{((a.mention_rate || 0) * 100).toFixed(1)}%</span>
                <DirectionBadge direction={a.trend_direction} />
              </div>
            ))}
          </div>
        </div>
      )}

      <style>{`
        .ct-page { max-width: 1200px; margin: 0 auto; padding: 1.5rem; }

        .ct-kpi-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 1rem; margin-bottom: 1.5rem; }
        .ct-kpi-card { background: white; border-radius: 12px; padding: 1.25rem; box-shadow: 0 2px 12px rgba(0,0,0,0.06); display: flex; align-items: center; gap: 1rem; }
        .ct-kpi-icon { width: 48px; height: 48px; border-radius: 12px; display: flex; align-items: center; justify-content: center; font-size: 1.25rem; flex-shrink: 0; }
        .ct-kpi-label { font-size: 0.8rem; color: #888; margin-bottom: 2px; }
        .ct-kpi-value { font-size: 1.25rem; font-weight: 700; }
        .ct-kpi-sub { font-size: 0.75rem; color: #999; }

        .ct-card { background: white; border-radius: 12px; padding: 1.5rem; box-shadow: 0 2px 12px rgba(0,0,0,0.06); margin-bottom: 1.5rem; }
        .ct-card-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 1rem; flex-wrap: wrap; gap: 0.75rem; }
        .ct-card-header h3 { margin: 0; font-size: 1.1rem; color: #333; }
        .ct-card h3 { margin: 0 0 1rem; font-size: 1.1rem; color: #333; }

        .ct-select { padding: 0.5rem 1rem; border: 1px solid #ddd; border-radius: 8px; font-size: 0.9rem; min-width: 220px; }

        .ct-detail-grid { display: grid; grid-template-columns: repeat(2, 1fr); gap: 1.5rem; }
        .ct-chart-card { background: #fafbfc; border-radius: 10px; padding: 1.25rem; }
        .ct-chart-card h4 { margin: 0 0 0.25rem; font-size: 0.95rem; color: #444; }
        .ct-chart-desc { font-size: 0.75rem; color: #999; margin: 0 0 0.75rem; }
        .ct-full-width { grid-column: 1 / -1; }

        .ct-ranking-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(280px, 1fr)); gap: 0.5rem; }
        .ct-ranking-item { display: flex; align-items: center; gap: 0.5rem; padding: 0.75rem 1rem; border-radius: 8px; background: #fafbfc; cursor: pointer; transition: all 0.15s; }
        .ct-ranking-item:hover { background: #f0f4f8; }
        .ct-ranking-item.selected { background: #e8f5e9; border: 1px solid #1abc9c40; }
        .ct-rank { font-weight: 700; color: #aaa; width: 28px; }
        .ct-allergen-name { font-weight: 600; flex: 1; }
        .ct-paper-count { font-size: 0.85rem; color: #666; }
        .ct-mention-rate { font-size: 0.85rem; color: #1abc9c; font-weight: 600; }

        .ct-badge { padding: 2px 8px; border-radius: 10px; font-size: 0.7rem; font-weight: 600; }

        .ct-table { width: 100%; border-collapse: collapse; font-size: 0.85rem; }
        .ct-table th { text-align: left; padding: 0.5rem; border-bottom: 2px solid #eee; color: #888; font-weight: 600; }
        .ct-table td { padding: 0.5rem; border-bottom: 1px solid #f5f5f5; }
        .ct-epi-type { font-size: 0.85rem; color: #9b59b6; margin: 0 0 0.5rem; text-transform: uppercase; }
        .ct-confidence { font-weight: 600; font-size: 0.8rem; }
        .ct-disclaimer { font-size: 0.75rem; color: #e74c3c; margin: 0 0 0.75rem; font-style: italic; }

        .ct-loading { text-align: center; padding: 4rem; color: #999; }
        .ct-loading-inline { text-align: center; padding: 2rem; color: #999; }
        .ct-error { text-align: center; padding: 4rem; }
        .ct-retry-btn { padding: 0.5rem 1.5rem; background: #1abc9c; color: white; border: none; border-radius: 8px; cursor: pointer; }

        @media (max-width: 1024px) {
          .ct-kpi-grid { grid-template-columns: repeat(2, 1fr); }
          .ct-detail-grid { grid-template-columns: 1fr; }
        }
        @media (max-width: 640px) {
          .ct-kpi-grid { grid-template-columns: 1fr; }
          .ct-page { padding: 1rem; }
        }
      `}</style>
    </div>
  );
};

export default ComprehensiveTrendPage;
