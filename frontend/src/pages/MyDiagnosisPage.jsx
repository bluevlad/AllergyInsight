/**
 * My Diagnosis Page - User's diagnosis history and results
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { myDiagnosisApi } from '../services/api';

const MyDiagnosisPage = () => {
  const navigate = useNavigate();
  const { user, registerKit, logout } = useAuth();
  const [diagnoses, setDiagnoses] = useState([]);
  const [selectedDiagnosis, setSelectedDiagnosis] = useState(null);
  const [allergenInfo, setAllergenInfo] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  // Kit registration modal
  const [showKitModal, setShowKitModal] = useState(false);
  const [kitForm, setKitForm] = useState({ serialNumber: '', pin: '' });
  const [kitError, setKitError] = useState('');
  const [kitLoading, setKitLoading] = useState(false);

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    try {
      const [diagnosesData, allergenData] = await Promise.all([
        myDiagnosisApi.getAll(),
        myDiagnosisApi.getAllergenInfo(),
      ]);
      setDiagnoses(diagnosesData);
      setAllergenInfo(allergenData);
      if (diagnosesData.length > 0) {
        setSelectedDiagnosis(diagnosesData[0]);
      }
    } catch (err) {
      console.error('Failed to fetch data:', err);
      setError('데이터를 불러오는데 실패했습니다.');
    } finally {
      setLoading(false);
    }
  };

  const handleKitRegister = async (e) => {
    e.preventDefault();
    setKitLoading(true);
    setKitError('');

    try {
      await registerKit(kitForm.serialNumber, kitForm.pin);
      setShowKitModal(false);
      setKitForm({ serialNumber: '', pin: '' });
      await fetchData();
    } catch (err) {
      const message = err.response?.data?.detail || '키트 등록에 실패했습니다.';
      setKitError(message);
    } finally {
      setKitLoading(false);
    }
  };

  const getGradeColor = (grade) => {
    if (!allergenInfo?.grades) return '#666';
    return allergenInfo.grades[grade]?.color || '#666';
  };

  const getGradeLabel = (grade) => {
    if (!allergenInfo?.grades) return `등급 ${grade}`;
    return allergenInfo.grades[grade]?.label || `등급 ${grade}`;
  };

  const formatDate = (dateStr) => {
    const date = new Date(dateStr);
    return date.toLocaleDateString('ko-KR', {
      year: 'numeric',
      month: 'long',
      day: 'numeric',
    });
  };

  const handleLogout = async () => {
    await logout();
    navigate('/login');
  };

  if (loading) {
    return (
      <div className="loading-container">
        <div className="spinner"></div>
        <p>로딩 중...</p>
      </div>
    );
  }

  return (
    <div className="my-diagnosis-container">
      {/* User Header */}
      <div className="user-header">
        <div className="user-info">
          {user?.profile_image && (
            <img src={user.profile_image} alt="" className="profile-image" />
          )}
          <div>
            <h2>{user?.name}님</h2>
            <p>{user?.email || '간편 로그인'}</p>
          </div>
        </div>
        <div className="header-actions">
          <button className="btn btn-outline" onClick={() => setShowKitModal(true)}>
            + 키트 등록
          </button>
          <button className="btn btn-text" onClick={handleLogout}>
            로그아웃
          </button>
        </div>
      </div>

      {error && <div className="error-message">{error}</div>}

      {diagnoses.length === 0 ? (
        <div className="empty-state">
          <h3>등록된 검사 결과가 없습니다</h3>
          <p>검사키트를 등록하여 알러지 검사 결과를 확인하세요.</p>
          <button className="btn btn-primary" onClick={() => setShowKitModal(true)}>
            검사키트 등록하기
          </button>
        </div>
      ) : (
        <div className="diagnosis-content">
          {/* Diagnosis List */}
          <div className="diagnosis-list">
            <h3>검사 이력</h3>
            {diagnoses.map((diag) => (
              <div
                key={diag.id}
                className={`diagnosis-item ${selectedDiagnosis?.id === diag.id ? 'selected' : ''}`}
                onClick={() => setSelectedDiagnosis(diag)}
              >
                <div className="diag-date">{formatDate(diag.diagnosis_date)}</div>
                {diag.kit_serial && (
                  <div className="diag-serial">{diag.kit_serial}</div>
                )}
              </div>
            ))}
          </div>

          {/* Diagnosis Detail */}
          {selectedDiagnosis && (
            <div className="diagnosis-detail">
              <h3>{formatDate(selectedDiagnosis.diagnosis_date)} 검사 결과</h3>

              {/* Food Allergens */}
              <div className="allergen-section">
                <h4>식품 알러젠</h4>
                <div className="allergen-grid">
                  {allergenInfo?.food?.map((allergen) => {
                    const grade = selectedDiagnosis.results[allergen.code] ?? 0;
                    return (
                      <div key={allergen.code} className="allergen-card">
                        <div className="allergen-name">{allergen.name_kr}</div>
                        <div
                          className="allergen-grade"
                          style={{ backgroundColor: getGradeColor(grade) }}
                        >
                          {grade}
                        </div>
                        <div className="allergen-label">{getGradeLabel(grade)}</div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* Inhalant Allergens */}
              <div className="allergen-section">
                <h4>흡입 알러젠</h4>
                <div className="allergen-grid">
                  {allergenInfo?.inhalant?.map((allergen) => {
                    const grade = selectedDiagnosis.results[allergen.code] ?? 0;
                    return (
                      <div key={allergen.code} className="allergen-card">
                        <div className="allergen-name">{allergen.name_kr}</div>
                        <div
                          className="allergen-grade"
                          style={{ backgroundColor: getGradeColor(grade) }}
                        >
                          {grade}
                        </div>
                        <div className="allergen-label">{getGradeLabel(grade)}</div>
                      </div>
                    );
                  })}
                </div>
              </div>

              {/* View Prescription Button */}
              <button
                className="btn btn-primary btn-large"
                onClick={() => navigate('/prescription', { state: { diagnosis: selectedDiagnosis } })}
              >
                상세 처방 권고 보기
              </button>
            </div>
          )}
        </div>
      )}

      {/* Kit Registration Modal */}
      {showKitModal && (
        <div className="modal-overlay" onClick={() => setShowKitModal(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()}>
            <h3>검사키트 등록</h3>
            <form onSubmit={handleKitRegister}>
              <div className="form-group">
                <label>시리얼번호</label>
                <input
                  type="text"
                  value={kitForm.serialNumber}
                  onChange={(e) => setKitForm({ ...kitForm, serialNumber: e.target.value })}
                  placeholder="SGT-2024-XXXXX-XXXX"
                  required
                />
              </div>
              <div className="form-group">
                <label>PIN</label>
                <input
                  type="password"
                  value={kitForm.pin}
                  onChange={(e) => setKitForm({ ...kitForm, pin: e.target.value })}
                  placeholder="6자리 PIN"
                  maxLength={6}
                  required
                />
              </div>
              {kitError && <div className="error-message">{kitError}</div>}
              <div className="modal-actions">
                <button type="button" className="btn btn-outline" onClick={() => setShowKitModal(false)}>
                  취소
                </button>
                <button type="submit" className="btn btn-primary" disabled={kitLoading}>
                  {kitLoading ? '등록 중...' : '등록'}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      <style>{`
        .my-diagnosis-container {
          max-width: 1200px;
          margin: 0 auto;
          padding: 1rem;
        }

        .user-header {
          display: flex;
          justify-content: space-between;
          align-items: center;
          background: white;
          padding: 1rem 1.5rem;
          border-radius: 12px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
          margin-bottom: 1.5rem;
        }

        .user-info {
          display: flex;
          align-items: center;
          gap: 1rem;
        }

        .profile-image {
          width: 48px;
          height: 48px;
          border-radius: 50%;
        }

        .user-info h2 {
          margin: 0;
          font-size: 1.25rem;
        }

        .user-info p {
          margin: 0;
          color: #666;
          font-size: 0.9rem;
        }

        .header-actions {
          display: flex;
          gap: 0.5rem;
        }

        .btn {
          padding: 0.5rem 1rem;
          border: none;
          border-radius: 6px;
          cursor: pointer;
          font-size: 0.9rem;
          transition: all 0.2s;
        }

        .btn-outline {
          background: white;
          border: 1px solid #2196F3;
          color: #2196F3;
        }

        .btn-text {
          background: transparent;
          color: #666;
        }

        .btn-primary {
          background: #2196F3;
          color: white;
        }

        .btn-primary:hover {
          background: #1976D2;
        }

        .btn-large {
          padding: 0.75rem 1.5rem;
          font-size: 1rem;
          width: 100%;
          margin-top: 1.5rem;
        }

        .loading-container {
          display: flex;
          flex-direction: column;
          align-items: center;
          justify-content: center;
          min-height: 50vh;
        }

        .spinner {
          width: 40px;
          height: 40px;
          border: 4px solid #f3f3f3;
          border-top: 4px solid #2196F3;
          border-radius: 50%;
          animation: spin 1s linear infinite;
        }

        @keyframes spin {
          0% { transform: rotate(0deg); }
          100% { transform: rotate(360deg); }
        }

        .error-message {
          color: #d32f2f;
          background: #ffebee;
          padding: 0.75rem;
          border-radius: 6px;
          margin-bottom: 1rem;
        }

        .empty-state {
          text-align: center;
          padding: 3rem;
          background: white;
          border-radius: 12px;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .empty-state h3 {
          color: #333;
        }

        .empty-state p {
          color: #666;
          margin-bottom: 1.5rem;
        }

        .diagnosis-content {
          display: grid;
          grid-template-columns: 300px 1fr;
          gap: 1.5rem;
        }

        @media (max-width: 768px) {
          .diagnosis-content {
            grid-template-columns: 1fr;
          }
        }

        .diagnosis-list {
          background: white;
          border-radius: 12px;
          padding: 1rem;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .diagnosis-list h3 {
          margin: 0 0 1rem;
          font-size: 1rem;
          color: #666;
        }

        .diagnosis-item {
          padding: 0.75rem;
          border-radius: 8px;
          cursor: pointer;
          transition: all 0.2s;
          margin-bottom: 0.5rem;
        }

        .diagnosis-item:hover {
          background: #f5f5f5;
        }

        .diagnosis-item.selected {
          background: #E3F2FD;
          border-left: 3px solid #2196F3;
        }

        .diag-date {
          font-weight: 500;
        }

        .diag-serial {
          font-size: 0.8rem;
          color: #666;
        }

        .diagnosis-detail {
          background: white;
          border-radius: 12px;
          padding: 1.5rem;
          box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }

        .diagnosis-detail h3 {
          margin: 0 0 1.5rem;
        }

        .allergen-section {
          margin-bottom: 1.5rem;
        }

        .allergen-section h4 {
          margin: 0 0 0.75rem;
          color: #666;
          font-size: 0.9rem;
        }

        .allergen-grid {
          display: grid;
          grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
          gap: 0.75rem;
        }

        .allergen-card {
          text-align: center;
          padding: 0.75rem;
          background: #f5f5f5;
          border-radius: 8px;
        }

        .allergen-name {
          font-size: 0.85rem;
          margin-bottom: 0.5rem;
        }

        .allergen-grade {
          width: 36px;
          height: 36px;
          border-radius: 50%;
          display: flex;
          align-items: center;
          justify-content: center;
          margin: 0 auto;
          color: white;
          font-weight: bold;
          font-size: 1.1rem;
        }

        .allergen-label {
          font-size: 0.75rem;
          color: #666;
          margin-top: 0.25rem;
        }

        .modal-overlay {
          position: fixed;
          top: 0;
          left: 0;
          right: 0;
          bottom: 0;
          background: rgba(0,0,0,0.5);
          display: flex;
          align-items: center;
          justify-content: center;
          z-index: 1000;
        }

        .modal-content {
          background: white;
          border-radius: 12px;
          padding: 1.5rem;
          width: 90%;
          max-width: 400px;
        }

        .modal-content h3 {
          margin: 0 0 1.5rem;
        }

        .form-group {
          margin-bottom: 1rem;
        }

        .form-group label {
          display: block;
          margin-bottom: 0.5rem;
          font-size: 0.9rem;
        }

        .form-group input {
          width: 100%;
          padding: 0.75rem;
          border: 1px solid #ddd;
          border-radius: 8px;
          font-size: 1rem;
          box-sizing: border-box;
        }

        .modal-actions {
          display: flex;
          gap: 0.5rem;
          margin-top: 1.5rem;
        }

        .modal-actions .btn {
          flex: 1;
        }
      `}</style>
    </div>
  );
};

export default MyDiagnosisPage;
