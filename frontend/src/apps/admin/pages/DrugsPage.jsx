/**
 * Drugs Management Page - Phase 1
 *
 * 약물 수집 현황 · 제품 목록 · 미매핑 성분 · 병태생리 엣지 감수.
 * 뒤의 Phase 2 (알러지-약물 매트릭스 뷰) 가 이 데이터를 소비한다.
 */
import React, { useCallback, useEffect, useState } from 'react';
import { adminApi } from '../services/adminApi';

const TABS = [
  { key: 'status', label: '수집 현황' },
  { key: 'products', label: '제품 목록' },
  { key: 'unmapped', label: '미매핑 성분' },
  { key: 'pathophys_atc', label: '병태생리 ↔ ATC' },
  { key: 'symptom_pathophys', label: '알러젠 ↔ 병태생리' },
];

const ROLE_LABELS = {
  first_line: '1차',
  adjunct: '보조',
  refractory: '난치성',
};

const formatDate = (iso) => {
  if (!iso) return '-';
  try {
    return new Date(iso).toLocaleString('ko-KR', { hour12: false });
  } catch {
    return iso;
  }
};

const DrugsPage = () => {
  const [activeTab, setActiveTab] = useState('status');
  const [status, setStatus] = useState(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  const loadStatus = useCallback(async () => {
    try {
      setLoading(true);
      const data = await adminApi.drugs.status();
      setStatus(data);
      setError(null);
    } catch (err) {
      console.error(err);
      setError('수집 현황 로딩 실패');
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    loadStatus();
  }, [loadStatus]);

  return (
    <div className="drugs-page">
      <div className="page-header">
        <h2>💊 약물 관리</h2>
        <p className="subtitle">
          수집 파이프라인 · 제품 · 병태생리 엣지 감수 (Phase 1)
        </p>
      </div>

      {status && <StatusBar status={status} />}

      <div className="tabs">
        {TABS.map((t) => (
          <button
            key={t.key}
            className={`tab ${activeTab === t.key ? 'active' : ''}`}
            onClick={() => setActiveTab(t.key)}
          >
            {t.label}
          </button>
        ))}
      </div>

      <div className="tab-content">
        {error && <div className="error">{error}</div>}
        {loading && !status && <div className="loading">로딩 중...</div>}

        {activeTab === 'status' && (
          <StatusPanel status={status} onReload={loadStatus} />
        )}
        {activeTab === 'products' && <ProductsPanel />}
        {activeTab === 'unmapped' && <UnmappedPanel />}
        {activeTab === 'pathophys_atc' && <PathophysAtcPanel />}
        {activeTab === 'symptom_pathophys' && <SymptomPathophysPanel />}
      </div>

      <style>{pageStyles}</style>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Status summary bar (상단 고정)
// ---------------------------------------------------------------------------

const StatusBar = ({ status }) => (
  <div className="stats-bar">
    <Stat label="전체 제품" value={status.total_products} />
    <Stat label="Raw 스냅샷" value={status.total_raws} />
    <Stat label="병태생리" value={status.total_pathophys} />
    <Stat label="ATC 엣지" value={status.pathophys_atc_edges} accent="#8e44ad" />
    <Stat
      label="알러젠 엣지"
      value={status.symptom_pathophys_edges}
      accent="#8e44ad"
    />
    <Stat label="미매핑 대기" value={status.unmapped_pending} accent="#e67e22" />
  </div>
);

const Stat = ({ label, value, accent }) => (
  <div className="stat-item">
    <span className="stat-label">{label}</span>
    <span className="stat-value" style={accent ? { color: accent } : undefined}>
      {value}
    </span>
  </div>
);

// ---------------------------------------------------------------------------
// Tab 1: 수집 현황 (소스별 카드 + 수동 트리거)
// ---------------------------------------------------------------------------

const StatusPanel = ({ status, onReload }) => {
  const [running, setRunning] = useState(false);
  const [source, setSource] = useState('');
  const [limit, setLimit] = useState(30);
  const [runResult, setRunResult] = useState(null);

  const handleRun = async () => {
    if (!window.confirm(
      source
        ? `${source} 소스를 지금 수집하시겠습니까?`
        : `등록된 모든 소스를 지금 수집하시겠습니까? (limit=${limit})`
    )) return;
    try {
      setRunning(true);
      const payload = { limit: Number(limit) || null };
      if (source) payload.source = source;
      const data = await adminApi.drugs.runIngest(payload);
      setRunResult(data.results || []);
      onReload();
    } catch (err) {
      console.error(err);
      alert('수집 실행 실패: ' + (err.response?.data?.detail || err.message));
    } finally {
      setRunning(false);
    }
  };

  if (!status) return <div className="loading">로딩 중...</div>;

  return (
    <div>
      <div className="run-toolbar">
        <select value={source} onChange={(e) => setSource(e.target.value)}>
          <option value="">전체 소스</option>
          {status.sources.map((s) => (
            <option key={s.source} value={s.source}>
              {s.source}
            </option>
          ))}
        </select>
        <label className="inline-label">
          limit
          <input
            type="number"
            min={1}
            max={500}
            value={limit}
            onChange={(e) => setLimit(e.target.value)}
          />
        </label>
        <button className="btn-primary" onClick={handleRun} disabled={running}>
          {running ? '수집 중...' : '지금 수집 실행'}
        </button>
        <button className="btn-ghost" onClick={onReload}>
          새로 고침
        </button>
      </div>

      <div className="source-grid">
        {status.sources.length === 0 ? (
          <div className="empty">등록된 소스가 없습니다.</div>
        ) : (
          status.sources.map((s) => <SourceCard key={s.source} source={s} />)
        )}
      </div>

      {runResult && (
        <div className="run-result">
          <h4>최근 실행 결과</h4>
          {runResult.map((r) => (
            <div
              key={r.source}
              className={`result-card ${r.ok ? 'ok' : 'fail'}`}
            >
              <div className="result-head">
                <strong>{r.source}</strong>
                <span>
                  성공 {r.success_count} · 실패 {r.failed_count}
                </span>
              </div>
              {r.fatal_error && (
                <div className="fatal">fatal: {r.fatal_error}</div>
              )}
              {r.failed_items && r.failed_items.length > 0 && (
                <details>
                  <summary>실패 항목 ({r.failed_items.length})</summary>
                  <ul>
                    {r.failed_items.map((f, i) => (
                      <li key={i}>
                        <code>{f.source_product_id}</code>: {f.error}
                      </li>
                    ))}
                  </ul>
                </details>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
  );
};

const SourceCard = ({ source }) => {
  const statusColor =
    source.last_status === 'success'
      ? '#27ae60'
      : source.last_status === 'error'
        ? '#e74c3c'
        : '#888';
  return (
    <div className="source-card">
      <div className="src-head">
        <strong>{source.source}</strong>
        <span className="src-status" style={{ color: statusColor }}>
          ● {source.last_status || '미실행'}
        </span>
      </div>
      <div className="src-metrics">
        <div>
          <span className="label">제품</span>
          <span className="value">{source.product_count}</span>
        </div>
        <div>
          <span className="label">Raw</span>
          <span className="value">{source.raw_count}</span>
        </div>
      </div>
      <div className="src-time">
        <div>
          마지막 수집: <code>{formatDate(source.last_run_at)}</code>
        </div>
        <div>
          커서 기준: <code>{formatDate(source.last_updated_at)}</code>
        </div>
      </div>
      {source.last_error && (
        <div className="src-error">⚠ {source.last_error}</div>
      )}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Tab 2: 제품 목록
// ---------------------------------------------------------------------------

const ProductsPanel = () => {
  const [items, setItems] = useState([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState('');
  const [searchInput, setSearchInput] = useState('');
  const [source, setSource] = useState('');
  const [atcPrefix, setAtcPrefix] = useState('');
  const [loading, setLoading] = useState(false);
  const [selected, setSelected] = useState(null);
  const pageSize = 20;

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const data = await adminApi.drugs.listProducts({
        page,
        page_size: pageSize,
        source: source || undefined,
        atc_prefix: atcPrefix || undefined,
        search: search || undefined,
      });
      setItems(data.items || []);
      setTotal(data.total || 0);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [page, source, atcPrefix, search]);

  useEffect(() => {
    load();
  }, [load]);

  const totalPages = Math.max(1, Math.ceil(total / pageSize));

  return (
    <div>
      <div className="toolbar">
        <form
          className="search-form"
          onSubmit={(e) => {
            e.preventDefault();
            setPage(1);
            setSearch(searchInput);
          }}
        >
          <input
            type="text"
            placeholder="제품명·source_product_id 검색"
            value={searchInput}
            onChange={(e) => setSearchInput(e.target.value)}
          />
          <button type="submit">검색</button>
        </form>
        <select
          value={source}
          onChange={(e) => {
            setSource(e.target.value);
            setPage(1);
          }}
        >
          <option value="">전체 소스</option>
          <option value="openfda">openfda</option>
          <option value="mfds_eyakeunyo">mfds_eyakeunyo</option>
        </select>
        <input
          type="text"
          placeholder="ATC prefix (예: R06A)"
          value={atcPrefix}
          onChange={(e) => {
            setAtcPrefix(e.target.value.toUpperCase());
            setPage(1);
          }}
          style={{ width: 160 }}
        />
      </div>

      {loading ? (
        <div className="loading">로딩 중...</div>
      ) : items.length === 0 ? (
        <div className="empty">제품이 없습니다. '수집 현황' 탭에서 수집을 실행하세요.</div>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Source</th>
              <th>제품명</th>
              <th>ATC</th>
              <th>RxCUI</th>
              <th>경로</th>
              <th>처방</th>
              <th>갱신</th>
              <th>원문</th>
            </tr>
          </thead>
          <tbody>
            {items.map((p) => (
              <tr key={p.id}>
                <td>{p.id}</td>
                <td>
                  <span className="badge">{p.source}</span>
                </td>
                <td className="name-cell" title={p.name_en || p.name_kr}>
                  {p.name_en || p.name_kr || '-'}
                </td>
                <td>
                  <code>{p.atc_code || '-'}</code>
                </td>
                <td>
                  <code>{p.rxcui || '-'}</code>
                </td>
                <td>{Array.isArray(p.routes) ? p.routes.join(', ') : '-'}</td>
                <td>{p.is_prescription ? 'Rx' : 'OTC'}</td>
                <td className="time">{formatDate(p.updated_at)}</td>
                <td>
                  <button
                    className="btn-ghost btn-sm"
                    onClick={async () => {
                      try {
                        const detail = await adminApi.drugs.getProduct(p.id);
                        setSelected(detail);
                      } catch (err) {
                        alert('상세 로딩 실패');
                      }
                    }}
                  >
                    보기
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}

      <div className="pagination">
        <button onClick={() => setPage((p) => Math.max(1, p - 1))} disabled={page <= 1}>
          이전
        </button>
        <span>
          {page} / {totalPages} (총 {total}건)
        </span>
        <button
          onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
          disabled={page >= totalPages}
        >
          다음
        </button>
      </div>

      {selected && <ProductDrawer product={selected} onClose={() => setSelected(null)} />}
    </div>
  );
};

const ProductDrawer = ({ product, onClose }) => (
  <div className="drawer-backdrop" onClick={onClose}>
    <div className="drawer" onClick={(e) => e.stopPropagation()}>
      <div className="drawer-head">
        <h3>{product.name_en || product.name_kr || '(이름 없음)'}</h3>
        <button className="btn-ghost" onClick={onClose}>
          닫기
        </button>
      </div>
      <dl className="kv">
        <dt>Source</dt>
        <dd>
          <span className="badge">{product.source}</span>{' '}
          <code>{product.source_product_id}</code>
        </dd>
        <dt>ATC</dt>
        <dd>
          <code>{product.atc_code || '-'}</code>
        </dd>
        <dt>RxCUI</dt>
        <dd>
          <code>{product.rxcui || '-'}</code>
        </dd>
        <dt>KFDA Seq</dt>
        <dd>
          <code>{product.kfda_item_seq || '-'}</code>
        </dd>
        <dt>종류</dt>
        <dd>
          {product.product_type} / {product.is_prescription ? 'Rx' : 'OTC'}
        </dd>
        <dt>경로</dt>
        <dd>
          {Array.isArray(product.routes) ? product.routes.join(', ') : '-'}
        </dd>
        <dt>적응증</dt>
        <dd className="long">{product.indications || '-'}</dd>
        <dt>용법</dt>
        <dd className="long">{product.dosage || '-'}</dd>
        <dt>경고</dt>
        <dd className="long">{product.warnings || '-'}</dd>
        <dt>Raw JSON</dt>
        <dd>
          <details>
            <summary>보기</summary>
            <pre className="raw">{JSON.stringify(product.raw_jsonb, null, 2)}</pre>
          </details>
        </dd>
      </dl>
    </div>
  </div>
);

// ---------------------------------------------------------------------------
// Tab 3: 미매핑 성분
// ---------------------------------------------------------------------------

const UnmappedPanel = () => {
  const [items, setItems] = useState([]);
  const [loading, setLoading] = useState(false);
  const [showResolved, setShowResolved] = useState(false);

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const data = await adminApi.drugs.listUnmapped({ resolved: showResolved });
      setItems(data.items || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, [showResolved]);

  useEffect(() => {
    load();
  }, [load]);

  const handleResolve = async (id) => {
    const rxcui = window.prompt('지정할 RxCUI (비워두면 보류 처리):', '');
    if (rxcui === null) return;
    try {
      await adminApi.drugs.resolveUnmapped(id, rxcui || null);
      load();
    } catch (err) {
      alert('처리 실패');
    }
  };

  return (
    <div>
      <div className="toolbar">
        <label className="checkbox-label">
          <input
            type="checkbox"
            checked={showResolved}
            onChange={(e) => setShowResolved(e.target.checked)}
          />
          처리된 항목 보기
        </label>
        <button className="btn-ghost btn-sm" onClick={load}>새로 고침</button>
      </div>
      {loading ? (
        <div className="loading">로딩 중...</div>
      ) : items.length === 0 ? (
        <div className="empty">
          {showResolved
            ? '처리된 미매핑 성분이 없습니다.'
            : '대기 중인 미매핑 성분이 없습니다. ✨'}
        </div>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Source</th>
              <th>Product ID</th>
              <th>성분 텍스트</th>
              <th>시도 시각</th>
              <th>RxCUI</th>
              <th>처리</th>
            </tr>
          </thead>
          <tbody>
            {items.map((u) => (
              <tr key={u.id}>
                <td>{u.id}</td>
                <td>
                  <span className="badge">{u.source}</span>
                </td>
                <td>
                  <code>{u.source_product_id}</code>
                </td>
                <td className="name-cell">{u.ingredient_text}</td>
                <td className="time">{formatDate(u.attempted_at)}</td>
                <td>
                  <code>{u.resolved_rxcui || '-'}</code>
                </td>
                <td>
                  {u.resolved ? (
                    <span className="tag-ok">처리됨</span>
                  ) : (
                    <button className="btn-primary btn-sm" onClick={() => handleResolve(u.id)}>
                      처리
                    </button>
                  )}
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Tab 4: 병태생리 ↔ ATC 엣지
// ---------------------------------------------------------------------------

const PathophysAtcPanel = () => {
  const [pathophys, setPathophys] = useState([]);
  const [selectedId, setSelectedId] = useState(null);
  const [edges, setEdges] = useState([]);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({ atc_prefix: '', role: 'first_line', review_comment: '' });

  useEffect(() => {
    (async () => {
      try {
        setLoading(true);
        const list = await adminApi.drugs.listPathophys();
        setPathophys(list || []);
        if (list && list.length && selectedId == null) {
          setSelectedId(list[0].id);
        }
      } finally {
        setLoading(false);
      }
    })();
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, []);

  const loadEdges = useCallback(async (id) => {
    if (!id) return;
    try {
      const data = await adminApi.drugs.listAtcEdges(id);
      setEdges(data || []);
    } catch (err) {
      console.error(err);
    }
  }, []);

  useEffect(() => {
    if (selectedId) loadEdges(selectedId);
  }, [selectedId, loadEdges]);

  const reloadList = async () => {
    const list = await adminApi.drugs.listPathophys();
    setPathophys(list || []);
  };

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!form.atc_prefix) return;
    try {
      await adminApi.drugs.createAtcEdge(selectedId, {
        atc_prefix: form.atc_prefix.toUpperCase(),
        role: form.role,
        review_comment: form.review_comment || null,
      });
      setForm({ atc_prefix: '', role: 'first_line', review_comment: '' });
      loadEdges(selectedId);
      reloadList();
    } catch (err) {
      alert(err.response?.data?.detail || '추가 실패');
    }
  };

  const handleDelete = async (edgeId) => {
    if (!window.confirm('엣지를 삭제하시겠습니까?')) return;
    try {
      await adminApi.drugs.deleteAtcEdge(edgeId);
      loadEdges(selectedId);
      reloadList();
    } catch {
      alert('삭제 실패');
    }
  };

  const handleVerify = async (edgeId) => {
    try {
      await adminApi.drugs.verifyAtcEdge(edgeId);
      loadEdges(selectedId);
    } catch {
      alert('검수 토글 실패');
    }
  };

  if (loading) return <div className="loading">로딩 중...</div>;

  const current = pathophys.find((p) => p.id === selectedId);

  return (
    <div className="split">
      <div className="side-list">
        <h4>병태생리 ({pathophys.length})</h4>
        {pathophys.map((p) => (
          <button
            key={p.id}
            className={`side-item ${selectedId === p.id ? 'active' : ''}`}
            onClick={() => setSelectedId(p.id)}
          >
            <div className="code">{p.code}</div>
            <div className="name">{p.name_kr}</div>
            <div className="counts">
              ATC {p.atc_edge_count} · 알러젠 {p.symptom_edge_count}
            </div>
          </button>
        ))}
      </div>

      <div className="side-main">
        {current ? (
          <>
            <div className="detail-head">
              <h3>
                {current.code} <span className="subtle">{current.name_en}</span>
              </h3>
              <p className="desc">{current.description}</p>
            </div>

            <form className="add-form" onSubmit={handleAdd}>
              <input
                type="text"
                placeholder="ATC prefix (예: R06A)"
                value={form.atc_prefix}
                onChange={(e) =>
                  setForm((f) => ({ ...f, atc_prefix: e.target.value }))
                }
                required
              />
              <select
                value={form.role}
                onChange={(e) => setForm((f) => ({ ...f, role: e.target.value }))}
              >
                <option value="first_line">1차</option>
                <option value="adjunct">보조</option>
                <option value="refractory">난치성</option>
              </select>
              <input
                type="text"
                placeholder="검토 코멘트 (선택)"
                value={form.review_comment}
                onChange={(e) =>
                  setForm((f) => ({ ...f, review_comment: e.target.value }))
                }
              />
              <button className="btn-primary" type="submit">엣지 추가</button>
            </form>

            {edges.length === 0 ? (
              <div className="empty">아직 ATC 엣지가 없습니다.</div>
            ) : (
              <table className="data-table">
                <thead>
                  <tr>
                    <th>ATC</th>
                    <th>역할</th>
                    <th>감수</th>
                    <th>감수자</th>
                    <th>코멘트</th>
                    <th></th>
                  </tr>
                </thead>
                <tbody>
                  {edges.map((e) => (
                    <tr key={e.id}>
                      <td>
                        <code>{e.atc_prefix}</code>
                      </td>
                      <td>{ROLE_LABELS[e.role] || e.role}</td>
                      <td>
                        <button
                          className={`tag ${e.is_verified ? 'ok' : ''}`}
                          onClick={() => handleVerify(e.id)}
                        >
                          {e.is_verified ? '✓ 감수됨' : '미감수'}
                        </button>
                      </td>
                      <td className="subtle">{e.verified_by || '-'}</td>
                      <td className="subtle">{e.review_comment || '-'}</td>
                      <td>
                        <button
                          className="btn-danger btn-sm"
                          onClick={() => handleDelete(e.id)}
                        >
                          삭제
                        </button>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            )}
          </>
        ) : (
          <div className="empty">병태생리를 선택하세요.</div>
        )}
      </div>
    </div>
  );
};

// ---------------------------------------------------------------------------
// Tab 5: 알러젠 ↔ 병태생리 엣지
// ---------------------------------------------------------------------------

const SymptomPathophysPanel = () => {
  const [edges, setEdges] = useState([]);
  const [pathophys, setPathophys] = useState([]);
  const [loading, setLoading] = useState(false);
  const [form, setForm] = useState({
    symptom_code: '',
    pathophys_id: '',
    weight: 3,
    review_comment: '',
  });

  const load = useCallback(async () => {
    try {
      setLoading(true);
      const [edgeList, pathList] = await Promise.all([
        adminApi.drugs.listSymptomEdges(),
        adminApi.drugs.listPathophys(),
      ]);
      setEdges(edgeList || []);
      setPathophys(pathList || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    load();
  }, [load]);

  const handleAdd = async (e) => {
    e.preventDefault();
    if (!form.symptom_code || !form.pathophys_id) return;
    try {
      await adminApi.drugs.createSymptomEdge({
        symptom_code: form.symptom_code.trim(),
        pathophys_id: Number(form.pathophys_id),
        weight: Number(form.weight),
        review_comment: form.review_comment || null,
      });
      setForm({ symptom_code: '', pathophys_id: '', weight: 3, review_comment: '' });
      load();
    } catch (err) {
      alert(err.response?.data?.detail || '추가 실패');
    }
  };

  const handleDelete = async (edgeId) => {
    if (!window.confirm('엣지를 삭제하시겠습니까?')) return;
    try {
      await adminApi.drugs.deleteSymptomEdge(edgeId);
      load();
    } catch {
      alert('삭제 실패');
    }
  };

  const handleVerify = async (edgeId) => {
    try {
      await adminApi.drugs.verifySymptomEdge(edgeId);
      load();
    } catch {
      alert('검수 토글 실패');
    }
  };

  return (
    <div>
      <form className="add-form row" onSubmit={handleAdd}>
        <input
          type="text"
          placeholder="알러젠 code (예: f13, d1)"
          value={form.symptom_code}
          onChange={(e) => setForm((f) => ({ ...f, symptom_code: e.target.value }))}
          required
        />
        <select
          value={form.pathophys_id}
          onChange={(e) => setForm((f) => ({ ...f, pathophys_id: e.target.value }))}
          required
        >
          <option value="">병태생리 선택</option>
          {pathophys.map((p) => (
            <option key={p.id} value={p.id}>
              {p.code} · {p.name_kr}
            </option>
          ))}
        </select>
        <label className="inline-label">
          weight
          <input
            type="number"
            min={1}
            max={5}
            value={form.weight}
            onChange={(e) => setForm((f) => ({ ...f, weight: e.target.value }))}
          />
        </label>
        <input
          type="text"
          placeholder="검토 코멘트 (선택)"
          value={form.review_comment}
          onChange={(e) => setForm((f) => ({ ...f, review_comment: e.target.value }))}
        />
        <button className="btn-primary" type="submit">엣지 추가</button>
      </form>

      {loading ? (
        <div className="loading">로딩 중...</div>
      ) : edges.length === 0 ? (
        <div className="empty">
          아직 알러젠 ↔ 병태생리 엣지가 없습니다.<br />
          알러젠 code (f13, d1 등) 와 병태생리를 매핑해 주세요.
        </div>
      ) : (
        <table className="data-table">
          <thead>
            <tr>
              <th>알러젠</th>
              <th>병태생리</th>
              <th>Weight</th>
              <th>감수</th>
              <th>감수자</th>
              <th>코멘트</th>
              <th></th>
            </tr>
          </thead>
          <tbody>
            {edges.map((e) => (
              <tr key={e.id}>
                <td>
                  <code>{e.symptom_code}</code> · {e.symptom_name_kr}
                </td>
                <td>{e.pathophys_code}</td>
                <td>{e.weight}</td>
                <td>
                  <button
                    className={`tag ${e.is_verified ? 'ok' : ''}`}
                    onClick={() => handleVerify(e.id)}
                  >
                    {e.is_verified ? '✓ 감수됨' : '미감수'}
                  </button>
                </td>
                <td className="subtle">{e.verified_by || '-'}</td>
                <td className="subtle">{e.review_comment || '-'}</td>
                <td>
                  <button
                    className="btn-danger btn-sm"
                    onClick={() => handleDelete(e.id)}
                  >
                    삭제
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
};

// ---------------------------------------------------------------------------
// Styles
// ---------------------------------------------------------------------------

const pageStyles = `
  .drugs-page { padding: 1rem; }
  .page-header h2 { margin: 0; }
  .page-header .subtitle {
    color: #666; margin: 0.25rem 0 1rem; font-size: 0.9rem;
  }

  .stats-bar {
    display: flex; gap: 0.75rem; margin-bottom: 1.25rem; flex-wrap: wrap;
  }
  .stat-item {
    background: white; padding: 0.75rem 1.25rem; border-radius: 8px;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
    display: flex; gap: 0.5rem; align-items: baseline;
  }
  .stat-label { font-size: 0.85rem; color: #888; }
  .stat-value { font-size: 1.2rem; font-weight: 700; color: #333; }

  .tabs { display: flex; gap: 0; margin-bottom: 1rem; border-bottom: 2px solid #eee; }
  .tab {
    padding: 0.75rem 1.25rem; background: none; border: none; cursor: pointer;
    font-size: 0.95rem; color: #888; border-bottom: 2px solid transparent;
    margin-bottom: -2px; transition: all 0.2s;
  }
  .tab:hover { color: #555; }
  .tab.active { color: #9b59b6; border-bottom-color: #9b59b6; font-weight: 600; }

  .tab-content { padding: 1rem 0; }

  .loading, .error, .empty {
    text-align: center; padding: 2rem 1rem; color: #888; font-size: 0.95rem;
  }
  .error { color: #e74c3c; }

  .toolbar {
    display: flex; gap: 0.75rem; margin-bottom: 1rem; flex-wrap: wrap;
    align-items: center;
  }
  .search-form { display: flex; gap: 0.5rem; flex: 1; min-width: 250px; }
  .search-form input {
    flex: 1; padding: 0.5rem 1rem; border: 1px solid #ddd; border-radius: 6px;
  }
  .search-form button {
    padding: 0.5rem 1rem; background: #667eea; color: white; border: none;
    border-radius: 6px; cursor: pointer;
  }
  .toolbar select, .toolbar input[type=text] {
    padding: 0.5rem 0.75rem; border: 1px solid #ddd; border-radius: 6px; background: white;
  }
  .checkbox-label { display: flex; align-items: center; gap: 0.4rem; font-size: 0.9rem; }

  .run-toolbar {
    display: flex; gap: 0.75rem; align-items: center; margin-bottom: 1rem;
    padding: 1rem; background: #faf7fc; border-radius: 8px;
  }
  .run-toolbar select, .run-toolbar input {
    padding: 0.5rem 0.75rem; border: 1px solid #ddd; border-radius: 6px;
  }
  .inline-label {
    display: flex; align-items: center; gap: 0.4rem; font-size: 0.9rem;
  }
  .inline-label input { width: 80px; }

  .btn-primary {
    padding: 0.55rem 1rem; background: #9b59b6; color: white; border: none;
    border-radius: 6px; cursor: pointer; font-weight: 600;
  }
  .btn-primary:hover { background: #8e44ad; }
  .btn-primary:disabled { opacity: 0.6; cursor: not-allowed; }
  .btn-ghost {
    padding: 0.5rem 1rem; background: white; color: #555; border: 1px solid #ddd;
    border-radius: 6px; cursor: pointer;
  }
  .btn-ghost:hover { background: #f5f5f5; }
  .btn-sm { padding: 0.3rem 0.6rem; font-size: 0.8rem; }
  .btn-danger {
    padding: 0.3rem 0.6rem; background: #fef2f2; color: #c0392b;
    border: 1px solid #fbb; border-radius: 4px; cursor: pointer; font-size: 0.8rem;
  }
  .btn-danger:hover { background: #fde7e7; }

  .source-grid {
    display: grid; grid-template-columns: repeat(auto-fill, minmax(260px, 1fr));
    gap: 1rem; margin-bottom: 1rem;
  }
  .source-card {
    background: white; border-radius: 8px; padding: 1rem 1.25rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.08);
  }
  .src-head {
    display: flex; justify-content: space-between; align-items: center;
    margin-bottom: 0.6rem;
  }
  .src-status { font-size: 0.85rem; }
  .src-metrics {
    display: flex; gap: 1rem; margin-bottom: 0.6rem;
  }
  .src-metrics .label { font-size: 0.75rem; color: #888; margin-right: 0.3rem; }
  .src-metrics .value { font-size: 1.1rem; font-weight: 700; }
  .src-time { font-size: 0.8rem; color: #666; line-height: 1.5; }
  .src-time code { background: #f5f5f5; padding: 1px 4px; border-radius: 3px; }
  .src-error {
    margin-top: 0.6rem; padding: 0.4rem 0.6rem; background: #fef2f2;
    color: #c0392b; border-radius: 4px; font-size: 0.8rem;
  }

  .run-result { margin-top: 1rem; }
  .run-result h4 { margin: 0 0 0.5rem; }
  .result-card {
    background: white; padding: 0.75rem 1rem; border-radius: 6px;
    margin-bottom: 0.5rem; border-left: 3px solid #27ae60;
  }
  .result-card.fail { border-left-color: #e74c3c; }
  .result-head { display: flex; justify-content: space-between; }
  .fatal { color: #c0392b; margin-top: 0.3rem; font-size: 0.85rem; }

  .data-table {
    width: 100%; border-collapse: collapse; background: white;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05); border-radius: 6px; overflow: hidden;
  }
  .data-table th, .data-table td {
    padding: 0.6rem 0.75rem; text-align: left; border-bottom: 1px solid #f0f0f0;
    font-size: 0.88rem;
  }
  .data-table th { background: #fafafa; color: #555; font-weight: 600; }
  .data-table tr:hover { background: #fafafa; }
  .data-table code {
    background: #f5f5f5; padding: 1px 4px; border-radius: 3px; font-size: 0.82rem;
  }
  .name-cell {
    max-width: 320px; overflow: hidden; text-overflow: ellipsis; white-space: nowrap;
  }
  .time { white-space: nowrap; color: #888; font-size: 0.8rem; }

  .badge {
    display: inline-block; padding: 0.15rem 0.5rem; border-radius: 4px;
    background: #f3e5f5; color: #7b1fa2; font-size: 0.75rem; font-weight: 500;
  }
  .tag {
    padding: 0.2rem 0.6rem; border-radius: 12px; background: #f5f5f5;
    border: 1px solid #ddd; cursor: pointer; font-size: 0.8rem;
  }
  .tag.ok { background: #e8f5e9; color: #2e7d32; border-color: #a5d6a7; }
  .tag-ok { color: #27ae60; font-weight: 600; }

  .pagination {
    display: flex; justify-content: center; align-items: center; gap: 1rem;
    margin-top: 1rem;
  }
  .pagination button {
    padding: 0.5rem 1rem; border: 1px solid #ddd; border-radius: 6px;
    background: white; cursor: pointer;
  }
  .pagination button:disabled { opacity: 0.5; cursor: not-allowed; }

  .drawer-backdrop {
    position: fixed; inset: 0; background: rgba(0,0,0,0.5); z-index: 100;
    display: flex; justify-content: flex-end;
  }
  .drawer {
    width: min(640px, 100%); background: white; overflow-y: auto; padding: 1.5rem;
  }
  .drawer-head {
    display: flex; justify-content: space-between; align-items: flex-start;
    margin-bottom: 1rem;
  }
  .drawer-head h3 { margin: 0; font-size: 1.1rem; line-height: 1.4; flex: 1; }
  .kv { display: grid; grid-template-columns: 120px 1fr; gap: 0.5rem 1rem; }
  .kv dt { color: #888; font-size: 0.85rem; }
  .kv dd { margin: 0; font-size: 0.9rem; }
  .kv dd.long { line-height: 1.5; white-space: pre-wrap; }
  .raw {
    background: #f5f5f5; padding: 0.75rem; border-radius: 4px; font-size: 0.75rem;
    max-height: 400px; overflow: auto;
  }

  .split {
    display: grid; grid-template-columns: 280px 1fr; gap: 1rem;
    min-height: 500px;
  }
  .side-list {
    background: white; border-radius: 8px; padding: 0.75rem; overflow-y: auto;
    max-height: 70vh; box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  }
  .side-list h4 { margin: 0 0 0.5rem; font-size: 0.9rem; color: #666; }
  .side-item {
    display: block; width: 100%; text-align: left; padding: 0.6rem 0.75rem;
    background: none; border: none; border-radius: 6px; cursor: pointer;
    margin-bottom: 0.2rem;
  }
  .side-item:hover { background: #faf7fc; }
  .side-item.active { background: #f3e5f5; }
  .side-item .code {
    font-size: 0.8rem; color: #7b1fa2; font-family: monospace; font-weight: 600;
  }
  .side-item .name { font-size: 0.9rem; color: #333; }
  .side-item .counts { font-size: 0.75rem; color: #888; margin-top: 0.2rem; }

  .side-main {
    background: white; border-radius: 8px; padding: 1.25rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
  }
  .detail-head h3 { margin: 0 0 0.25rem; }
  .detail-head .subtle { font-weight: 400; color: #888; font-size: 0.9rem; }
  .detail-head .desc { color: #555; font-size: 0.9rem; line-height: 1.5; }

  .add-form {
    display: flex; gap: 0.5rem; margin: 1rem 0; flex-wrap: wrap; align-items: center;
    padding: 0.75rem; background: #faf7fc; border-radius: 6px;
  }
  .add-form input, .add-form select {
    padding: 0.5rem 0.75rem; border: 1px solid #ddd; border-radius: 6px;
  }
  .add-form input[type=text] { flex: 1; min-width: 140px; }
  .add-form.row { margin-top: 0; margin-bottom: 1rem; }

  .subtle { color: #888; font-size: 0.85rem; }

  @media (max-width: 900px) {
    .split { grid-template-columns: 1fr; }
  }
`;

export default DrugsPage;
