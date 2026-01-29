/**
 * Organizations Management Page
 */
import React, { useState, useEffect } from 'react';
import { adminApi } from '../services/adminApi';

const OrganizationsPage = () => {
  const [organizations, setOrganizations] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [statusFilter, setStatusFilter] = useState('');
  const [typeFilter, setTypeFilter] = useState('');
  const pageSize = 20;

  useEffect(() => {
    loadOrganizations();
  }, [page, statusFilter, typeFilter]);

  const loadOrganizations = async () => {
    try {
      setLoading(true);
      const params = { page, page_size: pageSize };
      if (statusFilter) params.status = statusFilter;
      if (typeFilter) params.org_type = typeFilter;

      const response = await adminApi.organizations.list(params);
      setOrganizations(response.items || []);
      setTotal(response.total || 0);
    } catch (err) {
      console.error('Organizations load failed:', err);
      setError('조직 목록 로딩 실패');
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (id) => {
    if (!window.confirm('조직을 승인하시겠습니까?')) return;

    try {
      await adminApi.organizations.approve(id);
      loadOrganizations();
    } catch (err) {
      alert('승인 실패');
    }
  };

  const handleReject = async (id) => {
    const reason = window.prompt('거절 사유를 입력하세요:');
    if (reason === null) return;

    try {
      await adminApi.organizations.reject(id, reason);
      loadOrganizations();
    } catch (err) {
      alert('거절 실패');
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('정말 삭제하시겠습니까? 이 작업은 되돌릴 수 없습니다.')) return;

    try {
      await adminApi.organizations.delete(id);
      loadOrganizations();
    } catch (err) {
      alert('삭제 실패');
    }
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="organizations-page">
      <h2>조직 관리</h2>

      {/* 필터 */}
      <div className="toolbar">
        <select
          value={statusFilter}
          onChange={(e) => { setStatusFilter(e.target.value); setPage(1); }}
        >
          <option value="">전체 상태</option>
          <option value="pending">승인 대기</option>
          <option value="active">활성</option>
          <option value="rejected">거절됨</option>
          <option value="suspended">정지</option>
        </select>
        <select
          value={typeFilter}
          onChange={(e) => { setTypeFilter(e.target.value); setPage(1); }}
        >
          <option value="">전체 타입</option>
          <option value="hospital">병원</option>
          <option value="clinic">클리닉</option>
          <option value="lab">검사기관</option>
          <option value="research">연구기관</option>
        </select>
      </div>

      {/* 조직 목록 */}
      {loading ? (
        <div className="loading">로딩 중...</div>
      ) : error ? (
        <div className="error">{error}</div>
      ) : (
        <>
          <div className="table-container">
            <table>
              <thead>
                <tr>
                  <th>ID</th>
                  <th>조직명</th>
                  <th>타입</th>
                  <th>상태</th>
                  <th>멤버 수</th>
                  <th>등록일</th>
                  <th>액션</th>
                </tr>
              </thead>
              <tbody>
                {organizations.map((org) => (
                  <tr key={org.id} className={org.status}>
                    <td>{org.id}</td>
                    <td>{org.name}</td>
                    <td>{getTypeName(org.org_type)}</td>
                    <td>
                      <span className={`badge ${org.status}`}>
                        {getStatusName(org.status)}
                      </span>
                    </td>
                    <td>{org.member_count}</td>
                    <td>{formatDate(org.created_at)}</td>
                    <td className="actions">
                      {org.status === 'pending' && (
                        <>
                          <button
                            onClick={() => handleApprove(org.id)}
                            className="btn-approve"
                          >
                            승인
                          </button>
                          <button
                            onClick={() => handleReject(org.id)}
                            className="btn-reject"
                          >
                            거절
                          </button>
                        </>
                      )}
                      <button
                        onClick={() => handleDelete(org.id)}
                        className="btn-delete"
                      >
                        삭제
                      </button>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>

          {/* 페이지네이션 */}
          <div className="pagination">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page <= 1}
            >
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
        </>
      )}

      <style>{`
        .organizations-page {
          padding: 1rem;
        }

        .organizations-page h2 {
          margin-bottom: 1.5rem;
        }

        .toolbar {
          display: flex;
          gap: 1rem;
          margin-bottom: 1rem;
        }

        .toolbar select {
          padding: 0.5rem 1rem;
          border: 1px solid #ddd;
          border-radius: 6px;
          background: white;
        }

        .table-container {
          overflow-x: auto;
          background: white;
          border-radius: 8px;
          box-shadow: 0 2px 8px rgba(0, 0, 0, 0.1);
        }

        table {
          width: 100%;
          border-collapse: collapse;
        }

        th, td {
          padding: 0.75rem 1rem;
          text-align: left;
          border-bottom: 1px solid #eee;
        }

        th {
          background: #f8f9fa;
          font-weight: 600;
          color: #333;
        }

        tr.pending {
          background: #fff3cd;
        }

        tr.rejected, tr.suspended {
          opacity: 0.6;
        }

        .badge {
          padding: 0.25rem 0.5rem;
          border-radius: 12px;
          font-size: 0.75rem;
          font-weight: 500;
        }

        .badge.pending {
          background: #fff3cd;
          color: #856404;
        }

        .badge.active {
          background: #d4edda;
          color: #155724;
        }

        .badge.rejected {
          background: #f8d7da;
          color: #721c24;
        }

        .badge.suspended {
          background: #e2e3e5;
          color: #383d41;
        }

        .actions {
          display: flex;
          gap: 0.5rem;
        }

        .btn-approve, .btn-reject, .btn-delete {
          padding: 0.25rem 0.75rem;
          border: none;
          border-radius: 4px;
          font-size: 0.75rem;
          cursor: pointer;
        }

        .btn-approve {
          background: #28a745;
          color: white;
        }

        .btn-reject {
          background: #ffc107;
          color: #212529;
        }

        .btn-delete {
          background: #dc3545;
          color: white;
        }

        .pagination {
          display: flex;
          justify-content: center;
          align-items: center;
          gap: 1rem;
          margin-top: 1rem;
        }

        .pagination button {
          padding: 0.5rem 1rem;
          border: 1px solid #ddd;
          border-radius: 6px;
          background: white;
          cursor: pointer;
        }

        .pagination button:disabled {
          opacity: 0.5;
          cursor: not-allowed;
        }

        .loading, .error {
          text-align: center;
          padding: 2rem;
          color: #666;
        }
      `}</style>
    </div>
  );
};

const getTypeName = (type) => {
  const types = {
    hospital: '병원',
    clinic: '클리닉',
    lab: '검사기관',
    research: '연구기관',
  };
  return types[type] || type;
};

const getStatusName = (status) => {
  const statuses = {
    pending: '승인 대기',
    active: '활성',
    rejected: '거절됨',
    suspended: '정지',
  };
  return statuses[status] || status;
};

const formatDate = (dateStr) => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleDateString('ko-KR');
};

export default OrganizationsPage;
