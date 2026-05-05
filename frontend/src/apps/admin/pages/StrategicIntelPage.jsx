/**
 * Strategic Intel Page (super_admin 전용)
 *
 * 내부 경영 분석 대시보드 — 외부 노출 금지.
 * 4개 탭: Hypotheses · Reports · Matrix · Stats
 */
import React, { useEffect, useMemo, useState } from 'react';
import adminApi from '../services/adminApi';

const COMPANY_LABELS = {
  sugentech: '수젠텍 (253840)',
  greencross: '녹십자엠에스 (142280)',
  bodytech: '바디텍메드 (206640)',
  madx: 'MADx (비상장)',
};

const DIRECTION_COLORS = {
  positive: { bg: '#e8f5e9', fg: '#2e7d32', label: '긍정' },
  neutral: { bg: '#f5f5f5', fg: '#616161', label: '중립' },
  negative: { bg: '#ffebee', fg: '#c62828', label: '위협' },
};

const STATUS_LABELS = {
  pending: '검증 대기',
  partial: 'T+1d 일부 확보',
  validated: 'T+5d 검증 완료',
  closed: 'T+30d 종결',
  no_data: '검증 제외 (비상장)',
};

const fmtPct = (v, precision = 2) =>
  v == null ? '—' : `${(v * 100 >= 0 ? '+' : '')}${(v * 100).toFixed(precision)}%`;

const fmtHitRateCI = (b) => {
  if (b == null || b.hit_rate == null) return '—';
  const rate = (b.hit_rate * 100).toFixed(1);
  if (b.ci_low == null || b.ci_high == null) return `${rate}%`;
  return `${rate}% [${(b.ci_low * 100).toFixed(1)}, ${(b.ci_high * 100).toFixed(1)}]`;
};

const fmtZScore = (v) => {
  if (v == null) return '—';
  const flagged = Math.abs(v) >= 2.0;
  return (
    <span style={flagged ? { color: '#c62828', fontWeight: 600 } : null}>
      {v.toFixed(2)}{flagged ? ' ⚠' : ''}
    </span>
  );
};

const fmtVerdict = (b) => {
  if (b == null) return '—';
  if (b.insufficient_n) {
    return <span style={{ color: '#888', fontSize: '0.78rem' }}>판단 보류 (n&lt;30)</span>;
  }
  if (b.is_significant === true) {
    const dir = b.hit_rate > 0.5 ? '유의 (적중)' : '유의 (미적중)';
    const color = b.hit_rate > 0.5 ? '#2e7d32' : '#c62828';
    return <span style={{ color, fontWeight: 600, fontSize: '0.78rem' }}>{dir}</span>;
  }
  return <span style={{ color: '#666', fontSize: '0.78rem' }}>유의차 없음</span>;
};

const TABS = [
  { key: 'hypotheses', label: '가설 검증' },
  { key: 'reports', label: '리포트' },
  { key: 'matrix', label: 'Fit Matrix' },
  { key: 'stats', label: '통계' },
];

const StrategicIntelPage = () => {
  const [tab, setTab] = useState('hypotheses');

  return (
    <div style={{ padding: '1.5rem' }}>
      <div style={{ marginBottom: '1rem' }}>
        <h2 style={{ margin: '0 0 0.25rem' }}>Strategic Intel</h2>
        <p style={{ color: '#777', margin: 0, fontSize: '0.9rem' }}>
          내부 경영 분석 — 알러지 IVD 진단 키트/시약 분야 4사 추적 (수젠텍 · 녹십자MS · 바디텍메드 · MADx)
        </p>
        <div
          style={{
            marginTop: '0.5rem',
            padding: '0.5rem 0.75rem',
            background: '#fff8e1',
            borderLeft: '4px solid #f9a825',
            borderRadius: '4px',
            fontSize: '0.8rem',
            color: '#5d4037',
          }}
        >
          ⚠️ 본 분석은 내부 의사결정 보조용이며, 투자 자문이나 매매 추천이 아닙니다.
          가설은 사후 주가 흐름과의 동시 발생을 1차 검증한 결과로, 인과관계를 단정하지 않습니다.
        </div>
      </div>

      <div
        style={{
          display: 'flex',
          gap: 0,
          borderBottom: '1px solid #e0e0e0',
          marginBottom: '1rem',
        }}
      >
        {TABS.map((t) => (
          <button
            key={t.key}
            onClick={() => setTab(t.key)}
            style={{
              border: 'none',
              background: 'transparent',
              padding: '0.6rem 1rem',
              cursor: 'pointer',
              fontSize: '0.95rem',
              borderBottom: tab === t.key ? '2px solid #8e44ad' : '2px solid transparent',
              color: tab === t.key ? '#8e44ad' : '#666',
              fontWeight: tab === t.key ? 600 : 400,
            }}
          >
            {t.label}
          </button>
        ))}
      </div>

      {tab === 'hypotheses' && <HypothesesTab />}
      {tab === 'reports' && <ReportsTab />}
      {tab === 'matrix' && <MatrixTab />}
      {tab === 'stats' && <StatsTab />}
    </div>
  );
};

// =============================================================================
// 가설 탭
// =============================================================================

const HypothesesTab = () => {
  const [filters, setFilters] = useState({
    company: '',
    direction: '',
    status: '',
    hit: '',
  });
  const [page, setPage] = useState(1);
  const [data, setData] = useState({ items: [], total: 0 });
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState(null);

  const load = async () => {
    setLoading(true);
    try {
      const params = { page, page_size: 30 };
      if (filters.company) params.company = filters.company;
      if (filters.direction) params.direction = filters.direction;
      if (filters.status) params.status = filters.status;
      if (filters.hit !== '') params.hit = filters.hit;
      const result = await adminApi.strategicIntel.listHypotheses(params);
      setData(result);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [filters, page]);

  return (
    <div>
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem', flexWrap: 'wrap' }}>
        <select
          value={filters.company}
          onChange={(e) => { setFilters({ ...filters, company: e.target.value }); setPage(1); }}
          style={selectStyle}
        >
          <option value="">전체 회사</option>
          {Object.entries(COMPANY_LABELS).map(([code, label]) => (
            <option key={code} value={code}>{label}</option>
          ))}
        </select>
        <select
          value={filters.direction}
          onChange={(e) => { setFilters({ ...filters, direction: e.target.value }); setPage(1); }}
          style={selectStyle}
        >
          <option value="">전체 방향</option>
          <option value="positive">긍정</option>
          <option value="neutral">중립</option>
          <option value="negative">위협</option>
        </select>
        <select
          value={filters.status}
          onChange={(e) => { setFilters({ ...filters, status: e.target.value }); setPage(1); }}
          style={selectStyle}
        >
          <option value="">전체 상태</option>
          {Object.entries(STATUS_LABELS).map(([k, v]) => (
            <option key={k} value={k}>{v}</option>
          ))}
        </select>
        <select
          value={filters.hit}
          onChange={(e) => { setFilters({ ...filters, hit: e.target.value }); setPage(1); }}
          style={selectStyle}
        >
          <option value="">전체 적중</option>
          <option value="true">적중</option>
          <option value="false">미적중</option>
        </select>
      </div>

      {loading && <p>불러오는 중...</p>}
      {!loading && (
        <div style={{ display: 'grid', gridTemplateColumns: selected ? '1.6fr 1fr' : '1fr', gap: '1rem' }}>
          <div style={cardStyle}>
            <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
              <thead>
                <tr style={{ background: '#fafafa', textAlign: 'left' }}>
                  <th style={thStyle}>일자</th>
                  <th style={thStyle}>회사</th>
                  <th style={thStyle}>방향</th>
                  <th style={thStyle}>impact</th>
                  <th style={thStyle}>T+5d</th>
                  <th style={thStyle}>적중</th>
                  <th style={thStyle}>트리거</th>
                </tr>
              </thead>
              <tbody>
                {data.items.map((h) => (
                  <tr
                    key={h.id}
                    onClick={() => setSelected(h)}
                    style={{
                      borderBottom: '1px solid #f0f0f0',
                      cursor: 'pointer',
                      background: selected?.id === h.id ? '#f3e5f5' : 'white',
                    }}
                  >
                    <td style={tdStyle}>{h.trigger_date}</td>
                    <td style={tdStyle}>{COMPANY_LABELS[h.company_code] || h.company_code}</td>
                    <td style={tdStyle}>
                      <DirectionPill direction={h.impact_direction} />
                    </td>
                    <td style={tdStyle}>{(h.impact_score ?? 0).toFixed(2)}</td>
                    <td style={tdStyle}>
                      <span style={{ color: (h.abnormal_t5d ?? 0) > 0 ? '#2e7d32' : '#c62828' }}>
                        {fmtPct(h.abnormal_t5d)}
                      </span>
                    </td>
                    <td style={tdStyle}>
                      {h.hit_t5d == null ? '—' : h.hit_t5d ? '✓' : '✗'}
                    </td>
                    <td style={{ ...tdStyle, maxWidth: '300px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                      {h.trigger_title || '(제목 없음)'}
                    </td>
                  </tr>
                ))}
                {!data.items.length && (
                  <tr>
                    <td colSpan={7} style={{ ...tdStyle, textAlign: 'center', color: '#999', padding: '2rem' }}>
                      가설이 없습니다.
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginTop: '0.75rem', fontSize: '0.875rem' }}>
              <div>총 {data.total}건</div>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <button onClick={() => setPage(Math.max(1, page - 1))} disabled={page <= 1} style={btnStyle}>이전</button>
                <span style={{ padding: '0.3rem 0.5rem' }}>{page}</span>
                <button
                  onClick={() => setPage(page + 1)}
                  disabled={page * 30 >= data.total}
                  style={btnStyle}
                >다음</button>
              </div>
            </div>
          </div>

          {selected && <HypothesisDetail hypothesis={selected} onClose={() => setSelected(null)} onReportGenerated={load} />}
        </div>
      )}
    </div>
  );
};

const HypothesisDetail = ({ hypothesis, onClose, onReportGenerated }) => {
  const [generating, setGenerating] = useState(false);
  const [error, setError] = useState(null);

  const generate = async () => {
    setGenerating(true);
    setError(null);
    try {
      await adminApi.strategicIntel.generateEventReport(hypothesis.id);
      onReportGenerated?.();
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally {
      setGenerating(false);
    }
  };

  return (
    <div style={cardStyle}>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '0.5rem' }}>
        <h3 style={{ margin: 0 }}>가설 #{hypothesis.id}</h3>
        <button onClick={onClose} style={{ ...btnStyle, padding: '0.2rem 0.5rem' }}>×</button>
      </div>
      <table style={{ width: '100%', fontSize: '0.875rem' }}>
        <tbody>
          <tr><td style={ktdStyle}>회사</td><td style={vtdStyle}>{COMPANY_LABELS[hypothesis.company_code]}</td></tr>
          <tr><td style={ktdStyle}>트리거</td><td style={vtdStyle}>{hypothesis.trigger_type} #{hypothesis.trigger_paper_id || hypothesis.trigger_news_id}</td></tr>
          <tr><td style={ktdStyle}>일자</td><td style={vtdStyle}>{hypothesis.trigger_date}</td></tr>
          <tr><td style={ktdStyle}>제목</td><td style={vtdStyle}>{hypothesis.trigger_title || '—'}</td></tr>
          <tr><td style={ktdStyle}>방향</td><td style={vtdStyle}><DirectionPill direction={hypothesis.impact_direction} /></td></tr>
          <tr><td style={ktdStyle}>impact</td><td style={vtdStyle}>{hypothesis.impact_score?.toFixed(2)}</td></tr>
          <tr><td style={ktdStyle}>fit</td><td style={vtdStyle}>{hypothesis.fit_score_snapshot?.toFixed(2) ?? '—'}</td></tr>
          <tr><td style={ktdStyle}>tech 카테고리</td><td style={vtdStyle}>
            {(hypothesis.tech_categories || []).map((c) => `${c.id} (${c.confidence})`).join(', ') || '—'}
          </td></tr>
          <tr><td style={ktdStyle}>T+1d</td><td style={vtdStyle}>{fmtPct(hypothesis.abnormal_t1d)}</td></tr>
          <tr><td style={ktdStyle}>T+5d</td><td style={vtdStyle}>{fmtPct(hypothesis.abnormal_t5d)}</td></tr>
          <tr><td style={ktdStyle}>T+30d</td><td style={vtdStyle}>{fmtPct(hypothesis.abnormal_t30d)}</td></tr>
          <tr><td style={ktdStyle}>적중(T+5d)</td><td style={vtdStyle}>{hypothesis.hit_t5d == null ? '—' : hypothesis.hit_t5d ? '적중' : '미적중'}</td></tr>
          <tr><td style={ktdStyle}>상태</td><td style={vtdStyle}>{STATUS_LABELS[hypothesis.validation_status] || hypothesis.validation_status}</td></tr>
          <tr><td style={ktdStyle}>벤치마크</td><td style={vtdStyle}>{hypothesis.benchmark_ticker || '—'}</td></tr>
          <tr><td style={ktdStyle}>거래량 z-score (T+1d)</td><td style={vtdStyle}>{fmtZScore(hypothesis.volume_zscore_t1d)}</td></tr>
          <tr><td style={ktdStyle}>시총 변화 (T+5d)</td><td style={vtdStyle}>{fmtPct(hypothesis.market_cap_change_t5d)}</td></tr>
        </tbody>
      </table>
      <div style={{ marginTop: '0.75rem', padding: '0.5rem', background: '#fafafa', borderLeft: '3px solid #ccc', fontSize: '0.875rem' }}>
        <strong>Rationale</strong>
        <p style={{ margin: '0.25rem 0 0', whiteSpace: 'pre-line' }}>{hypothesis.rationale}</p>
      </div>
      <button
        onClick={generate}
        disabled={generating}
        style={{ ...btnStyle, marginTop: '0.75rem', background: '#8e44ad', color: 'white', borderColor: '#8e44ad' }}
      >
        {generating ? '생성 중...' : '이벤트 리포트 발행'}
      </button>
      {error && <p style={{ color: '#c62828', fontSize: '0.85rem' }}>{error}</p>}
    </div>
  );
};

// =============================================================================
// 리포트 탭
// =============================================================================

const ReportsTab = () => {
  const [type, setType] = useState('');
  const [data, setData] = useState({ items: [], total: 0 });
  const [selected, setSelected] = useState(null);
  const [detail, setDetail] = useState(null);
  const [loading, setLoading] = useState(false);
  const [showMonthlyForm, setShowMonthlyForm] = useState(false);

  const load = async () => {
    setLoading(true);
    try {
      const params = { page: 1, page_size: 50 };
      if (type) params.report_type = type;
      const result = await adminApi.strategicIntel.listReports(params);
      setData(result);
    } finally { setLoading(false); }
  };

  useEffect(() => { load(); /* eslint-disable-next-line */ }, [type]);

  useEffect(() => {
    if (!selected) { setDetail(null); return; }
    adminApi.strategicIntel.getReport(selected).then(setDetail).catch(console.error);
  }, [selected]);

  return (
    <div>
      <div style={{ display: 'flex', gap: '0.5rem', marginBottom: '0.75rem' }}>
        <select value={type} onChange={(e) => setType(e.target.value)} style={selectStyle}>
          <option value="">전체</option>
          <option value="event">이벤트</option>
          <option value="monthly">월간</option>
        </select>
        <button onClick={() => setShowMonthlyForm(!showMonthlyForm)} style={btnStyle}>
          + 월간 리포트 발행
        </button>
      </div>
      {showMonthlyForm && <MonthlyForm onDone={() => { setShowMonthlyForm(false); load(); }} />}

      {loading && <p>불러오는 중...</p>}

      <div style={{ display: 'grid', gridTemplateColumns: detail ? '1fr 1.4fr' : '1fr', gap: '1rem' }}>
        <div style={cardStyle}>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.875rem' }}>
            <thead>
              <tr style={{ background: '#fafafa', textAlign: 'left' }}>
                <th style={thStyle}>유형</th>
                <th style={thStyle}>기간</th>
                <th style={thStyle}>제목</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((r) => (
                <tr
                  key={r.id}
                  onClick={() => setSelected(r.id)}
                  style={{ borderBottom: '1px solid #f0f0f0', cursor: 'pointer', background: selected === r.id ? '#f3e5f5' : 'white' }}
                >
                  <td style={tdStyle}>{r.report_type}</td>
                  <td style={tdStyle}>{r.period_start}</td>
                  <td style={tdStyle}>{r.title}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>

        {detail && (
          <div style={cardStyle}>
            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
              <h3 style={{ margin: 0 }}>{detail.title}</h3>
              <button onClick={() => setSelected(null)} style={{ ...btnStyle, padding: '0.2rem 0.5rem' }}>×</button>
            </div>
            <p style={{ color: '#777', margin: '0.25rem 0 1rem', fontSize: '0.85rem' }}>{detail.summary}</p>
            <pre style={{ whiteSpace: 'pre-wrap', fontFamily: 'inherit', fontSize: '0.875rem', lineHeight: 1.6 }}>
              {detail.content}
            </pre>
          </div>
        )}
      </div>
    </div>
  );
};

const MonthlyForm = ({ onDone }) => {
  const today = new Date();
  const [year, setYear] = useState(today.getFullYear());
  const [month, setMonth] = useState(today.getMonth() + 1);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState(null);

  const submit = async () => {
    setBusy(true); setError(null);
    try {
      await adminApi.strategicIntel.generateMonthlyReport(year, month);
      onDone?.();
    } catch (e) {
      setError(e.response?.data?.detail || e.message);
    } finally { setBusy(false); }
  };

  return (
    <div style={{ ...cardStyle, marginBottom: '1rem' }}>
      <div style={{ display: 'flex', gap: '0.5rem', alignItems: 'center' }}>
        <input
          type="number" value={year} onChange={(e) => setYear(parseInt(e.target.value, 10))}
          style={{ ...selectStyle, width: '90px' }}
        />
        <span>년</span>
        <input
          type="number" value={month} onChange={(e) => setMonth(parseInt(e.target.value, 10))}
          min={1} max={12} style={{ ...selectStyle, width: '70px' }}
        />
        <span>월</span>
        <button onClick={submit} disabled={busy} style={{ ...btnStyle, background: '#8e44ad', color: 'white', borderColor: '#8e44ad' }}>
          {busy ? '생성 중...' : '발행'}
        </button>
      </div>
      {error && <p style={{ color: '#c62828', fontSize: '0.85rem' }}>{error}</p>}
    </div>
  );
};

// =============================================================================
// Matrix 탭
// =============================================================================

const MatrixTab = () => {
  const [data, setData] = useState(null);

  useEffect(() => {
    adminApi.strategicIntel.matrix().then(setData).catch(console.error);
  }, []);

  if (!data) return <p>불러오는 중...</p>;

  const cellMap = useMemo(() => {
    const m = {};
    data.cells.forEach((c) => {
      m[`${c.company_code}__${c.tech_category_id}`] = c;
    });
    return m;
  }, [data.cells]);

  const companies = Object.keys(COMPANY_LABELS);

  return (
    <div style={cardStyle}>
      <p style={{ color: '#777', fontSize: '0.875rem', marginTop: 0 }}>
        기준일: {data.effective_on} · 점수: 0.0(무관) / 0.3(미보유) / 0.6(보유) / 0.9+(핵심)
      </p>
      <div style={{ overflowX: 'auto' }}>
        <table style={{ borderCollapse: 'collapse', fontSize: '0.85rem', minWidth: '100%' }}>
          <thead>
            <tr>
              <th style={thStyle}>기술 카테고리</th>
              {companies.map((c) => (
                <th key={c} style={thStyle}>{COMPANY_LABELS[c]}</th>
              ))}
            </tr>
          </thead>
          <tbody>
            {data.categories.map((cat) => (
              <tr key={cat.id} style={{ borderBottom: '1px solid #f0f0f0' }}>
                <td style={{ ...tdStyle, fontWeight: 500 }} title={cat.description}>
                  {cat.name_kr}
                </td>
                {companies.map((c) => {
                  const cell = cellMap[`${c}__${cat.id}`];
                  const score = cell ? cell.fit_score : 0;
                  return (
                    <td
                      key={c}
                      style={{
                        ...tdStyle,
                        textAlign: 'center',
                        background: heatColor(score),
                        color: score >= 0.7 ? 'white' : '#333',
                        fontWeight: score >= 0.7 ? 600 : 400,
                      }}
                      title={cell?.rationale || ''}
                    >
                      {score.toFixed(2)}
                    </td>
                  );
                })}
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

const heatColor = (score) => {
  if (score >= 0.85) return '#6a1b9a';
  if (score >= 0.7) return '#8e44ad';
  if (score >= 0.5) return '#ce93d8';
  if (score >= 0.35) return '#f3e5f5';
  return '#fafafa';
};

// =============================================================================
// Stats 탭
// =============================================================================

const StatsTab = () => {
  const [data, setData] = useState(null);
  const [unhit, setUnhit] = useState(null);

  useEffect(() => {
    adminApi.strategicIntel.stats().then(setData).catch(console.error);
    adminApi.strategicIntel.unhitClusters().then(setUnhit).catch(console.error);
  }, []);

  if (!data) return <p>불러오는 중...</p>;

  return (
    <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
      <div style={cardStyle}>
        <h3 style={{ marginTop: 0 }}>적중률 (T+5d 기준)</h3>
        <p style={{ color: '#777', fontSize: '0.85rem' }}>
          가설 {data.n_hypotheses}건 / 검증 완료 {data.n_validated}건<br />
          <span style={{ fontSize: '0.75rem' }}>
            Wilson 95% CI · 양측 이항검정 (H₀: p=0.5) · n&lt;30 시 판단 보류
          </span>
        </p>
        <table style={{ width: '100%', fontSize: '0.875rem', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#fafafa', textAlign: 'left' }}>
              <th style={thStyle}>회사</th>
              <th style={thStyle}>n</th>
              <th style={thStyle}>적중률 [95% CI]</th>
              <th style={thStyle}>p-value</th>
              <th style={thStyle}>판정</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(data.hit_rate).map(([code, b]) => (
              <tr key={code} style={{ borderBottom: '1px solid #f0f0f0' }}>
                <td style={tdStyle}>{COMPANY_LABELS[code] || code}</td>
                <td style={tdStyle}>{b.total}</td>
                <td style={tdStyle}>{fmtHitRateCI(b)}</td>
                <td style={tdStyle}>{b.p_value == null ? '—' : b.p_value.toFixed(3)}</td>
                <td style={tdStyle}>{fmtVerdict(b)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      <div style={cardStyle}>
        <h3 style={{ marginTop: 0 }}>Tech Pulse (트리거 빈도)</h3>
        <table style={{ width: '100%', fontSize: '0.875rem', borderCollapse: 'collapse' }}>
          <thead>
            <tr style={{ background: '#fafafa', textAlign: 'left' }}>
              <th style={thStyle}>기술 카테고리</th>
              <th style={thStyle}>빈도</th>
            </tr>
          </thead>
          <tbody>
            {Object.entries(data.tech_pulse || {})
              .sort((a, b) => b[1] - a[1])
              .map(([k, v]) => (
                <tr key={k} style={{ borderBottom: '1px solid #f0f0f0' }}>
                  <td style={tdStyle}>{k}</td>
                  <td style={tdStyle}>{v}</td>
                </tr>
              ))}
          </tbody>
        </table>
      </div>

      <div style={{ ...cardStyle, gridColumn: 'span 2' }}>
        <h3 style={{ marginTop: 0 }}>룰 캘리브레이션 후보 (Phase A-4)</h3>
        <p style={{ color: '#777', fontSize: '0.8rem', marginTop: 0 }}>
          n≥5 그룹 중 적중률 50% 이하 — 분기 룰 점검 시 우선 검토
        </p>
        {!unhit && <p style={{ color: '#999' }}>불러오는 중...</p>}
        {unhit && (unhit.by_tech?.length || unhit.by_company_direction?.length) ? (
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '1rem' }}>
            <div>
              <h4 style={{ margin: '0 0 0.5rem', fontSize: '0.9rem' }}>Tech 카테고리 축</h4>
              {unhit.by_tech?.length ? (
                <table style={{ width: '100%', fontSize: '0.85rem', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ background: '#fafafa', textAlign: 'left' }}>
                      <th style={thStyle}>카테고리</th>
                      <th style={thStyle}>n</th>
                      <th style={thStyle}>적중률 [CI]</th>
                    </tr>
                  </thead>
                  <tbody>
                    {unhit.by_tech.map((u) => (
                      <tr key={u.tech_id} style={{ borderBottom: '1px solid #f0f0f0' }}>
                        <td style={tdStyle}>{u.tech_id}</td>
                        <td style={tdStyle}>{u.total}</td>
                        <td style={tdStyle}>{fmtHitRateCI(u)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p style={{ color: '#999', fontSize: '0.85rem' }}>해당 그룹 없음</p>
              )}
            </div>
            <div>
              <h4 style={{ margin: '0 0 0.5rem', fontSize: '0.9rem' }}>회사 × 방향 축</h4>
              {unhit.by_company_direction?.length ? (
                <table style={{ width: '100%', fontSize: '0.85rem', borderCollapse: 'collapse' }}>
                  <thead>
                    <tr style={{ background: '#fafafa', textAlign: 'left' }}>
                      <th style={thStyle}>회사</th>
                      <th style={thStyle}>방향</th>
                      <th style={thStyle}>n</th>
                      <th style={thStyle}>적중률 [CI]</th>
                    </tr>
                  </thead>
                  <tbody>
                    {unhit.by_company_direction.map((u, i) => (
                      <tr key={`${u.company}-${u.direction}-${i}`} style={{ borderBottom: '1px solid #f0f0f0' }}>
                        <td style={tdStyle}>{COMPANY_LABELS[u.company] || u.company}</td>
                        <td style={tdStyle}>
                          <DirectionPill direction={u.direction} />
                        </td>
                        <td style={tdStyle}>{u.total}</td>
                        <td style={tdStyle}>{fmtHitRateCI(u)}</td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              ) : (
                <p style={{ color: '#999', fontSize: '0.85rem' }}>해당 그룹 없음</p>
              )}
            </div>
          </div>
        ) : (
          unhit && <p style={{ color: '#999', fontSize: '0.85rem' }}>표본 부족 — 미적중 클러스터 미식별</p>
        )}
      </div>
    </div>
  );
};

// =============================================================================
// 공용 컴포넌트
// =============================================================================

const DirectionPill = ({ direction }) => {
  const c = DIRECTION_COLORS[direction] || DIRECTION_COLORS.neutral;
  return (
    <span
      style={{
        display: 'inline-block',
        padding: '0.15rem 0.5rem',
        background: c.bg,
        color: c.fg,
        borderRadius: '999px',
        fontSize: '0.75rem',
        fontWeight: 500,
      }}
    >
      {c.label}
    </span>
  );
};

// =============================================================================
// 스타일
// =============================================================================

const cardStyle = {
  background: 'white',
  borderRadius: '8px',
  padding: '1rem',
  boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
  border: '1px solid #f0f0f0',
};

const thStyle = {
  padding: '0.5rem 0.6rem',
  fontWeight: 600,
  fontSize: '0.8rem',
  color: '#555',
  borderBottom: '1px solid #e0e0e0',
};

const tdStyle = {
  padding: '0.5rem 0.6rem',
  borderBottom: '1px solid #f5f5f5',
};

const ktdStyle = { ...tdStyle, color: '#777', width: '110px', fontSize: '0.8rem' };
const vtdStyle = { ...tdStyle, fontSize: '0.875rem' };

const selectStyle = {
  padding: '0.4rem 0.6rem',
  border: '1px solid #ddd',
  borderRadius: '4px',
  fontSize: '0.875rem',
  background: 'white',
};

const btnStyle = {
  padding: '0.4rem 0.75rem',
  border: '1px solid #ddd',
  borderRadius: '4px',
  background: 'white',
  cursor: 'pointer',
  fontSize: '0.875rem',
};

export default StrategicIntelPage;
