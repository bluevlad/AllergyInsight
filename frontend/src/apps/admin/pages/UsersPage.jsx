/**
 * Users Management Page
 */
import React, { useState, useEffect } from 'react';
import { adminApi } from '../services/adminApi';

const ROLE_OPTIONS = [
  { value: 'user', label: '일반 사용자' },
  { value: 'patient', label: '환자' },
  { value: 'doctor', label: '의사' },
  { value: 'nurse', label: '간호사' },
  { value: 'lab_tech', label: '검사 담당자' },
  { value: 'hospital_admin', label: '병원 관리자' },
  { value: 'admin', label: '관리자' },
  { value: 'super_admin', label: '최고 관리자' },
];

const STATUS_OPTIONS = [
  { value: true, label: '활성' },
  { value: false, label: '비활성' },
];

const UsersPage = () => {
  const [users, setUsers] = useState([]);
  const [editMap, setEditMap] = useState({}); // { userId: { name, email, role, is_active } }
  const [savingMap, setSavingMap] = useState({}); // { userId: true/false }
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [roleFilter, setRoleFilter] = useState('');
  const pageSize = 20;

  useEffect(() => {
    loadUsers();
  }, [page, roleFilter]);

  const loadUsers = async () => {
    try {
      setLoading(true);
      const params = { page, page_size: pageSize };
      if (search) params.search = search;
      if (roleFilter) params.role = roleFilter;

      const response = await adminApi.users.list(params);
      const items = response.items || [];
      setUsers(items);
      setTotal(response.total || 0);

      // Initialize edit map from loaded data
      const map = {};
      items.forEach(u => {
        map[u.id] = {
          name: u.name || '',
          email: u.email || '',
          role: u.role,
          is_active: u.is_active,
        };
      });
      setEditMap(map);
    } catch (err) {
      console.error('Users load failed:', err);
      setError('사용자 목록 로딩 실패');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    loadUsers();
  };

  const handleEditChange = (userId, field, value) => {
    setEditMap(prev => ({
      ...prev,
      [userId]: { ...prev[userId], [field]: value },
    }));
  };

  const hasChanges = (user) => {
    const edit = editMap[user.id];
    if (!edit) return false;
    return (
      edit.name !== (user.name || '') ||
      edit.email !== (user.email || '') ||
      edit.role !== user.role ||
      edit.is_active !== user.is_active
    );
  };

  const handleSave = async (user) => {
    const edit = editMap[user.id];
    if (!edit) return;

    setSavingMap(prev => ({ ...prev, [user.id]: true }));
    try {
      // Update name, email, is_active
      if (edit.name !== user.name || edit.email !== (user.email || '') || edit.is_active !== user.is_active) {
        await adminApi.users.update(user.id, {
          name: edit.name,
          email: edit.email || null,
          is_active: edit.is_active,
        });
      }
      // Update role separately
      if (edit.role !== user.role) {
        await adminApi.users.updateRole(user.id, edit.role);
      }
      loadUsers();
    } catch (err) {
      const detail = err.response?.data?.detail || '저장 실패';
      alert(detail);
    } finally {
      setSavingMap(prev => ({ ...prev, [user.id]: false }));
    }
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div className="users-page">
      <h2>사용자 관리</h2>

      {/* 검색 및 필터 */}
      <div className="toolbar">
        <form onSubmit={handleSearch} className="search-form">
          <input
            type="text"
            placeholder="이름, 이메일 검색..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <button type="submit">검색</button>
        </form>
        <select
          value={roleFilter}
          onChange={(e) => { setRoleFilter(e.target.value); setPage(1); }}
        >
          <option value="">전체 역할</option>
          {ROLE_OPTIONS.map(opt => (
            <option key={opt.value} value={opt.value}>{opt.label}</option>
          ))}
        </select>
      </div>

      {/* 사용자 목록 */}
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
                  <th>이름</th>
                  <th>이메일</th>
                  <th>역할</th>
                  <th>인증방식</th>
                  <th>상태</th>
                  <th>가입일</th>
                  <th>저장</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => {
                  const edit = editMap[user.id] || {};
                  const changed = hasChanges(user);
                  const saving = savingMap[user.id];
                  return (
                    <tr key={user.id} className={!edit.is_active ? 'inactive' : ''}>
                      <td>{user.id}</td>
                      <td>
                        <input
                          type="text"
                          className="edit-input"
                          value={edit.name || ''}
                          onChange={(e) => handleEditChange(user.id, 'name', e.target.value)}
                        />
                      </td>
                      <td>
                        <input
                          type="email"
                          className="edit-input edit-email"
                          value={edit.email || ''}
                          onChange={(e) => handleEditChange(user.id, 'email', e.target.value)}
                          placeholder="email@example.com"
                        />
                      </td>
                      <td>
                        <select
                          value={edit.role || 'user'}
                          onChange={(e) => handleEditChange(user.id, 'role', e.target.value)}
                          className="role-select"
                        >
                          {ROLE_OPTIONS.map(opt => (
                            <option key={opt.value} value={opt.value}>{opt.label}</option>
                          ))}
                        </select>
                      </td>
                      <td>{getAuthTypeName(user.auth_type)}</td>
                      <td>
                        <select
                          value={edit.is_active === false ? 'false' : 'true'}
                          onChange={(e) => handleEditChange(user.id, 'is_active', e.target.value === 'true')}
                          className={`status-select ${edit.is_active ? 'status-active' : 'status-inactive'}`}
                        >
                          {STATUS_OPTIONS.map(opt => (
                            <option key={String(opt.value)} value={String(opt.value)}>{opt.label}</option>
                          ))}
                        </select>
                      </td>
                      <td>{formatDate(user.created_at)}</td>
                      <td>
                        <button
                          onClick={() => handleSave(user)}
                          className={`btn-save ${changed ? 'btn-save-changed' : ''}`}
                          disabled={!changed || saving}
                        >
                          {saving ? '...' : '저장'}
                        </button>
                      </td>
                    </tr>
                  );
                })}
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
        .users-page {
          padding: 1rem;
        }

        .users-page h2 {
          margin-bottom: 1.5rem;
        }

        .toolbar {
          display: flex;
          gap: 1rem;
          margin-bottom: 1rem;
          flex-wrap: wrap;
        }

        .search-form {
          display: flex;
          gap: 0.5rem;
          flex: 1;
          min-width: 300px;
        }

        .search-form input {
          flex: 1;
          padding: 0.5rem 1rem;
          border: 1px solid #ddd;
          border-radius: 6px;
        }

        .search-form button,
        .toolbar select {
          padding: 0.5rem 1rem;
          border: 1px solid #ddd;
          border-radius: 6px;
          background: white;
          cursor: pointer;
        }

        .search-form button {
          background: #667eea;
          color: white;
          border: none;
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
          padding: 0.6rem 0.75rem;
          text-align: left;
          border-bottom: 1px solid #eee;
        }

        th {
          background: #f8f9fa;
          font-weight: 600;
          color: #333;
          white-space: nowrap;
        }

        tr.inactive {
          opacity: 0.6;
        }

        .edit-input {
          width: 100%;
          min-width: 80px;
          padding: 0.35rem 0.5rem;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 0.875rem;
          box-sizing: border-box;
        }

        .edit-email {
          min-width: 160px;
        }

        .edit-input:focus {
          outline: none;
          border-color: #667eea;
          box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.15);
        }

        .role-select,
        .status-select {
          padding: 0.35rem 0.5rem;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 0.875rem;
          cursor: pointer;
        }

        .status-select.status-active {
          background: #d4edda;
          color: #155724;
          border-color: #c3e6cb;
        }

        .status-select.status-inactive {
          background: #f8d7da;
          color: #721c24;
          border-color: #f5c6cb;
        }

        .btn-save {
          padding: 0.35rem 0.75rem;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 0.8rem;
          cursor: pointer;
          background: #f5f5f5;
          color: #999;
          white-space: nowrap;
        }

        .btn-save:disabled {
          cursor: not-allowed;
        }

        .btn-save-changed {
          background: #667eea;
          color: white;
          border-color: #667eea;
        }

        .btn-save-changed:hover:not(:disabled) {
          background: #5a6fd6;
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

        .error {
          color: #e74c3c;
        }
      `}</style>
    </div>
  );
};

const getAuthTypeName = (authType) => {
  const types = {
    simple: '간편 로그인',
    email: '이메일',
    google: 'Google',
  };
  return types[authType] || authType;
};

const formatDate = (dateStr) => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleDateString('ko-KR');
};

export default UsersPage;
