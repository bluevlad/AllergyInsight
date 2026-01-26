/**
 * Professional Patient Register Page - 신규 환자 등록
 */
import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { proApi } from '../services/proApi';

function PatientRegisterPage() {
  const navigate = useNavigate();

  const [mode, setMode] = useState('search'); // 'search' | 'new'
  const [searchPhone, setSearchPhone] = useState('');
  const [searchResults, setSearchResults] = useState([]);
  const [searching, setSearching] = useState(false);

  // 신규 환자 폼
  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    birthDate: '',
    patientNumber: '',
  });
  const [submitting, setSubmitting] = useState(false);

  const handleSearch = async (e) => {
    e.preventDefault();
    if (!searchPhone || searchPhone.length < 4) {
      alert('전화번호를 4자리 이상 입력해주세요.');
      return;
    }

    try {
      setSearching(true);
      const response = await proApi.patients.searchByPhone(searchPhone);
      setSearchResults(response.items || []);
    } catch (err) {
      console.error('검색 실패:', err);
      alert('검색에 실패했습니다.');
    } finally {
      setSearching(false);
    }
  };

  const handleRegisterExisting = async (userId) => {
    try {
      setSubmitting(true);
      await proApi.patients.create({
        patient_user_id: userId,
        patient_number: formData.patientNumber || null,
      });
      alert('환자가 등록되었습니다.');
      navigate('/pro/patients');
    } catch (err) {
      console.error('등록 실패:', err);
      alert('등록에 실패했습니다: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSubmitting(false);
    }
  };

  const handleRegisterNew = async (e) => {
    e.preventDefault();

    if (!formData.name || !formData.phone) {
      alert('이름과 전화번호는 필수입니다.');
      return;
    }

    try {
      setSubmitting(true);
      await proApi.patients.createNew({
        name: formData.name,
        phone: formData.phone,
        birth_date: formData.birthDate || null,
        patient_number: formData.patientNumber || null,
      });
      alert('신규 환자가 등록되었습니다.');
      navigate('/pro/patients');
    } catch (err) {
      console.error('등록 실패:', err);
      alert('등록에 실패했습니다: ' + (err.response?.data?.detail || err.message));
    } finally {
      setSubmitting(false);
    }
  };

  return (
    <div style={{ maxWidth: '800px', margin: '0 auto' }}>
      <h2>환자 등록</h2>

      {/* 모드 선택 */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <div style={{ display: 'flex', gap: '1rem' }}>
          <button
            className={`btn ${mode === 'search' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setMode('search')}
          >
            기존 사용자 검색
          </button>
          <button
            className={`btn ${mode === 'new' ? 'btn-primary' : 'btn-secondary'}`}
            onClick={() => setMode('new')}
          >
            신규 환자 등록
          </button>
        </div>
      </div>

      {mode === 'search' ? (
        <>
          {/* 기존 사용자 검색 */}
          <div className="card" style={{ marginBottom: '1rem' }}>
            <h3>전화번호로 사용자 검색</h3>
            <form onSubmit={handleSearch}>
              <div style={{ display: 'flex', gap: '0.5rem' }}>
                <input
                  type="tel"
                  placeholder="전화번호 입력 (예: 010-1234-5678)"
                  value={searchPhone}
                  onChange={(e) => setSearchPhone(e.target.value)}
                  className="form-control"
                  style={{ flex: 1 }}
                />
                <button type="submit" className="btn btn-primary" disabled={searching}>
                  {searching ? '검색 중...' : '검색'}
                </button>
              </div>
            </form>
          </div>

          {/* 검색 결과 */}
          {searchResults.length > 0 && (
            <div className="card">
              <h3>검색 결과</h3>
              <div className="form-group">
                <label>환자번호 (선택)</label>
                <input
                  type="text"
                  placeholder="병원 내 환자번호"
                  value={formData.patientNumber}
                  onChange={(e) => setFormData({ ...formData, patientNumber: e.target.value })}
                  className="form-control"
                  style={{ maxWidth: '200px' }}
                />
              </div>
              <div className="table-container">
                <table className="table">
                  <thead>
                    <tr>
                      <th>이름</th>
                      <th>전화번호</th>
                      <th>생년월일</th>
                      <th></th>
                    </tr>
                  </thead>
                  <tbody>
                    {searchResults.map((user) => (
                      <tr key={user.id}>
                        <td>{user.name}</td>
                        <td>{user.phone}</td>
                        <td>{user.birth_date || '-'}</td>
                        <td>
                          <button
                            className="btn btn-primary btn-sm"
                            onClick={() => handleRegisterExisting(user.id)}
                            disabled={submitting}
                          >
                            {submitting ? '등록 중...' : '등록'}
                          </button>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </div>
          )}

          {searchResults.length === 0 && searchPhone && !searching && (
            <div className="card" style={{ textAlign: 'center' }}>
              <p>검색 결과가 없습니다.</p>
              <button className="btn btn-primary" onClick={() => setMode('new')}>
                신규 환자로 등록
              </button>
            </div>
          )}
        </>
      ) : (
        /* 신규 환자 등록 */
        <div className="card">
          <h3>신규 환자 정보 입력</h3>
          <form onSubmit={handleRegisterNew}>
            <div className="form-group">
              <label>이름 *</label>
              <input
                type="text"
                placeholder="환자 이름"
                value={formData.name}
                onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                className="form-control"
                required
              />
            </div>
            <div className="form-group">
              <label>전화번호 *</label>
              <input
                type="tel"
                placeholder="010-1234-5678"
                value={formData.phone}
                onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
                className="form-control"
                required
              />
            </div>
            <div className="form-group">
              <label>생년월일</label>
              <input
                type="date"
                value={formData.birthDate}
                onChange={(e) => setFormData({ ...formData, birthDate: e.target.value })}
                className="form-control"
              />
            </div>
            <div className="form-group">
              <label>환자번호</label>
              <input
                type="text"
                placeholder="병원 내 환자번호"
                value={formData.patientNumber}
                onChange={(e) => setFormData({ ...formData, patientNumber: e.target.value })}
                className="form-control"
              />
            </div>
            <div style={{ display: 'flex', gap: '1rem', justifyContent: 'flex-end' }}>
              <button
                type="button"
                className="btn btn-secondary"
                onClick={() => navigate('/pro/patients')}
              >
                취소
              </button>
              <button type="submit" className="btn btn-primary" disabled={submitting}>
                {submitting ? '등록 중...' : '환자 등록'}
              </button>
            </div>
          </form>
        </div>
      )}

      <style>{`
        .btn-sm {
          padding: 0.25rem 0.5rem;
          font-size: 0.875rem;
        }
      `}</style>
    </div>
  );
}

export default PatientRegisterPage;
