/**
 * Admin 구독자 관리 페이지
 */
import React, { useState, useEffect } from 'react';
import { adminApi } from '../services/adminApi';

const SubscribersPage = () => {
  const [subscribers, setSubscribers] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [page, setPage] = useState(1);
  const [total, setTotal] = useState(0);
  const [search, setSearch] = useState('');
  const [filterVerified, setFilterVerified] = useState('');
  const [filterActive, setFilterActive] = useState('');
  const [editId, setEditId] = useState(null);
  const [editData, setEditData] = useState({});
  const pageSize = 20;

  useEffect(() => {
    loadSubscribers();
    loadStats();
  }, [page, filterVerified, filterActive]);

  const loadSubscribers = async () => {
    try {
      setLoading(true);
      const params = { page, page_size: pageSize };
      if (search) params.search = search;
      if (filterVerified !== '') params.is_verified = filterVerified === 'true';
      if (filterActive !== '') params.is_active = filterActive === 'true';

      const result = await adminApi.subscribers.list(params);
      setSubscribers(result.items || []);
      setTotal(result.total || 0);
    } catch (err) {
      console.error('Load subscribers failed:', err);
    } finally {
      setLoading(false);
    }
  };

  const loadStats = async () => {
    try {
      const result = await adminApi.subscribers.stats();
      setStats(result);
    } catch (err) {
      console.error('Load stats failed:', err);
    }
  };

  const handleSearch = (e) => {
    e.preventDefault();
    setPage(1);
    loadSubscribers();
  };

  const handleEdit = (subscriber) => {
    setEditId(subscriber.id);
    setEditData({
      name: subscriber.name || '',
      group_name: subscriber.group_name || 'general',
      is_active: subscriber.is_active,
    });
  };

  const handleSave = async () => {
    try {
      await adminApi.subscribers.update(editId, editData);
      setEditId(null);
      loadSubscribers();
      loadStats();
    } catch (err) {
      alert('수정 실패: ' + err.message);
    }
  };

  const handleDelete = async (id) => {
    if (!window.confirm('이 구독자를 삭제하시겠습니까?')) return;
    try {
      await adminApi.subscribers.delete(id);
      loadSubscribers();
      loadStats();
    } catch (err) {
      alert('삭제 실패: ' + err.message);
    }
  };

  const totalPages = Math.ceil(total / pageSize);

  return (
    <div style={{ padding: '1rem' }}>
      <h2>구독자 관리</h2>

      {stats && (
        <div style={{ display: 'flex', gap: '1rem', marginBottom: '1.5rem', flexWrap: 'wrap' }}>
          <StatCard label="전체" value={stats.total} />
          <StatCard label="인증" value={stats.verified} color="#27ae60" />
          <StatCard label="미인증" value={stats.unverified} color="#e67e22" />
          <StatCard label="활성" value={stats.active} color="#3498db" />
          <StatCard label="비활성" value={stats.inactive} color="#e74c3c" />
        </div>
      )}

      {/* 필터 */}
      <div style={{ display: 'flex', gap: '0.75rem', marginBottom: '1.5rem', flexWrap: 'wrap', alignItems: 'center' }}>
        <form onSubmit={handleSearch} style={{ display: 'flex', gap: '0.5rem', flex: 1, minWidth: '200px' }}>
          <input
            type="text"
            value={search}
            onChange={e => setSearch(e.target.value)}
            placeholder="이메일, 이름 검색..."
            style={{ flex: 1, padding: '0.5rem 1rem', border: '1px solid #ddd', borderRadius: '6px' }}
          />
          <button type="submit" style={{ padding: '0.5rem 1rem', background: '#667eea', color: 'white', border: 'none', borderRadius: '6px', cursor: 'pointer' }}>
            검색
          </button>
        </form>
        <select value={filterVerified} onChange={e => { setFilterVerified(e.target.value); setPage(1); }}
          style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '6px' }}>
          <option value="">전체 인증</option>
          <option value="true">인증됨</option>
          <option value="false">미인증</option>
        </select>
        <select value={filterActive} onChange={e => { setFilterActive(e.target.value); setPage(1); }}
          style={{ padding: '0.5rem', border: '1px solid #ddd', borderRadius: '6px' }}>
          <option value="">전체 상태</option>
          <option value="true">활성</option>
          <option value="false">비활성</option>
        </select>
      </div>

      {/* 목록 */}
      {loading ? (
        <p style={{ textAlign: 'center', color: '#888', padding: '2rem' }}>로딩 중...</p>
      ) : subscribers.length === 0 ? (
        <p style={{ textAlign: 'center', color: '#888', padding: '2rem' }}>구독자가 없습니다.</p>
      ) : (
        <>
          <table style={{ width: '100%', borderCollapse: 'collapse', background: 'white', borderRadius: '8px', overflow: 'hidden', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}>
            <thead>
              <tr style={{ background: '#f8f9fa', textAlign: 'left' }}>
                <th style={thStyle}>이메일</th>
                <th style={thStyle}>이름</th>
                <th style={thStyle}>인증</th>
                <th style={thStyle}>상태</th>
                <th style={thStyle}>그룹</th>
                <th style={thStyle}>키워드</th>
                <th style={thStyle}>가입일</th>
                <th style={thStyle}>관리</th>
              </tr>
            </thead>
            <tbody>
              {subscribers.map(sub => (
                <tr key={sub.id} style={{ borderBottom: '1px solid #eee' }}>
                  <td style={tdStyle}>{sub.email}</td>
                  <td style={tdStyle}>
                    {editId === sub.id ? (
                      <input value={editData.name} onChange={e => setEditData({...editData, name: e.target.value})}
                        style={{ padding: '0.25rem', width: '100px', border: '1px solid #ddd', borderRadius: '4px' }} />
                    ) : (sub.name || '-')}
                  </td>
                  <td style={tdStyle}>
                    <span style={{ color: sub.is_verified ? '#27ae60' : '#e67e22' }}>
                      {sub.is_verified ? 'O' : 'X'}
                    </span>
                  </td>
                  <td style={tdStyle}>
                    {editId === sub.id ? (
                      <select value={editData.is_active} onChange={e => setEditData({...editData, is_active: e.target.value === 'true'})}
                        style={{ padding: '0.25rem' }}>
                        <option value="true">활성</option>
                        <option value="false">비활성</option>
                      </select>
                    ) : (
                      <span style={{ color: sub.is_active ? '#27ae60' : '#e74c3c' }}>
                        {sub.is_active ? '활성' : '비활성'}
                      </span>
                    )}
                  </td>
                  <td style={tdStyle}>{sub.group_name}</td>
                  <td style={{ ...tdStyle, maxWidth: '150px', overflow: 'hidden', textOverflow: 'ellipsis' }}>
                    {(sub.keywords || []).join(', ') || '-'}
                  </td>
                  <td style={{ ...tdStyle, fontSize: '0.85rem', color: '#888' }}>
                    {sub.subscribed_at ? new Date(sub.subscribed_at).toLocaleDateString('ko-KR') : '-'}
                  </td>
                  <td style={tdStyle}>
                    {editId === sub.id ? (
                      <div style={{ display: 'flex', gap: '0.3rem' }}>
                        <button onClick={handleSave} style={btnSmStyle}>저장</button>
                        <button onClick={() => setEditId(null)} style={{ ...btnSmStyle, background: '#999' }}>취소</button>
                      </div>
                    ) : (
                      <div style={{ display: 'flex', gap: '0.3rem' }}>
                        <button onClick={() => handleEdit(sub)} style={btnSmStyle}>수정</button>
                        <button onClick={() => handleDelete(sub.id)} style={{ ...btnSmStyle, background: '#e74c3c' }}>삭제</button>
                      </div>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {totalPages > 1 && (
            <div style={{ display: 'flex', justifyContent: 'center', gap: '1rem', marginTop: '1.5rem' }}>
              <button onClick={() => setPage(p => Math.max(1, p - 1))} disabled={page <= 1}
                style={{ padding: '0.5rem 1rem', border: '1px solid #ddd', borderRadius: '6px', background: 'white', cursor: 'pointer' }}>
                이전
              </button>
              <span style={{ lineHeight: '2.5' }}>{page} / {totalPages} (총 {total}건)</span>
              <button onClick={() => setPage(p => Math.min(totalPages, p + 1))} disabled={page >= totalPages}
                style={{ padding: '0.5rem 1rem', border: '1px solid #ddd', borderRadius: '6px', background: 'white', cursor: 'pointer' }}>
                다음
              </button>
            </div>
          )}
        </>
      )}
    </div>
  );
};

const thStyle = { padding: '0.75rem', fontSize: '0.85rem' };
const tdStyle = { padding: '0.75rem' };
const btnSmStyle = { padding: '0.3rem 0.6rem', background: '#667eea', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: '0.8rem' };

const StatCard = ({ label, value, color }) => (
  <div style={{ background: 'white', padding: '0.75rem 1.25rem', borderRadius: '8px', boxShadow: '0 2px 8px rgba(0,0,0,0.08)' }}>
    <span style={{ fontSize: '0.85rem', color: '#888' }}>{label} </span>
    <span style={{ fontSize: '1.1rem', fontWeight: 700, color: color || '#333' }}>{value}</span>
  </div>
);

export default SubscribersPage;
