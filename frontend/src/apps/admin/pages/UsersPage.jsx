/**
 * Users Management Page
 */
import React, { useState, useEffect } from 'react';
import { adminApi } from '../services/adminApi';

const UsersPage = () => {
  const [users, setUsers] = useState([]);
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
      setUsers(response.items || []);
      setTotal(response.total || 0);
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

  const handleRoleChange = async (userId, newRole) => {
    if (!window.confirm(`역할을 ${getRoleName(newRole)}(으)로 변경하시겠습니까?`)) return;

    try {
      await adminApi.users.updateRole(userId, newRole);
      loadUsers();
    } catch (err) {
      alert('역할 변경 실패');
    }
  };

  const handleToggleActive = async (userId, isActive) => {
    try {
      await adminApi.users.update(userId, { is_active: !isActive });
      loadUsers();
    } catch (err) {
      alert('상태 변경 실패');
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
            placeholder="이름, 이메일, 전화번호 검색..."
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
          <option value="user">일반 사용자</option>
          <option value="patient">환자</option>
          <option value="doctor">의사</option>
          <option value="nurse">간호사</option>
          <option value="lab_tech">검사 담당자</option>
          <option value="hospital_admin">병원 관리자</option>
          <option value="admin">관리자</option>
          <option value="super_admin">최고 관리자</option>
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
                  <th>전화번호</th>
                  <th>역할</th>
                  <th>인증방식</th>
                  <th>상태</th>
                  <th>가입일</th>
                  <th>액션</th>
                </tr>
              </thead>
              <tbody>
                {users.map((user) => (
                  <tr key={user.id} className={!user.is_active ? 'inactive' : ''}>
                    <td>{user.id}</td>
                    <td>{user.name}</td>
                    <td>{user.email || '-'}</td>
                    <td>{user.phone || '-'}</td>
                    <td>
                      <select
                        value={user.role}
                        onChange={(e) => handleRoleChange(user.id, e.target.value)}
                        className="role-select"
                      >
                        <option value="user">일반 사용자</option>
                        <option value="patient">환자</option>
                        <option value="doctor">의사</option>
                        <option value="nurse">간호사</option>
                        <option value="lab_tech">검사 담당자</option>
                        <option value="hospital_admin">병원 관리자</option>
                        <option value="admin">관리자</option>
                        <option value="super_admin">최고 관리자</option>
                      </select>
                    </td>
                    <td>{getAuthTypeName(user.auth_type)}</td>
                    <td>
                      <span className={`badge ${user.is_active ? 'active' : 'inactive'}`}>
                        {user.is_active ? '활성' : '비활성'}
                      </span>
                    </td>
                    <td>{formatDate(user.created_at)}</td>
                    <td>
                      <button
                        onClick={() => handleToggleActive(user.id, user.is_active)}
                        className={`btn-small ${user.is_active ? 'btn-warning' : 'btn-success'}`}
                      >
                        {user.is_active ? '비활성화' : '활성화'}
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
          padding: 0.75rem 1rem;
          text-align: left;
          border-bottom: 1px solid #eee;
        }

        th {
          background: #f8f9fa;
          font-weight: 600;
          color: #333;
        }

        tr.inactive {
          opacity: 0.6;
        }

        .role-select {
          padding: 0.25rem 0.5rem;
          border: 1px solid #ddd;
          border-radius: 4px;
          font-size: 0.875rem;
        }

        .badge {
          padding: 0.25rem 0.5rem;
          border-radius: 12px;
          font-size: 0.75rem;
          font-weight: 500;
        }

        .badge.active {
          background: #d4edda;
          color: #155724;
        }

        .badge.inactive {
          background: #f8d7da;
          color: #721c24;
        }

        .btn-small {
          padding: 0.25rem 0.75rem;
          border: none;
          border-radius: 4px;
          font-size: 0.75rem;
          cursor: pointer;
        }

        .btn-success {
          background: #28a745;
          color: white;
        }

        .btn-warning {
          background: #ffc107;
          color: #212529;
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

const getRoleName = (role) => {
  const roleNames = {
    user: '일반 사용자',
    patient: '환자',
    doctor: '의사',
    nurse: '간호사',
    lab_tech: '검사 담당자',
    hospital_admin: '병원 관리자',
    admin: '관리자',
    super_admin: '최고 관리자',
  };
  return roleNames[role] || role;
};

const getAuthTypeName = (authType) => {
  const types = {
    simple: '간편 로그인',
    google: 'Google',
    kakao: 'Kakao',
  };
  return types[authType] || authType;
};

const formatDate = (dateStr) => {
  if (!dateStr) return '-';
  return new Date(dateStr).toLocaleDateString('ko-KR');
};

export default UsersPage;
