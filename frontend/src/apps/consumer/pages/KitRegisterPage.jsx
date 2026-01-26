/**
 * Consumer Kit Register Page - 키트 등록
 */
import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { consumerApi } from '../services/consumerApi';

function KitRegisterPage() {
  const navigate = useNavigate();

  const [serialNumber, setSerialNumber] = useState('');
  const [pin, setPin] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [myKits, setMyKits] = useState([]);
  const [loadingKits, setLoadingKits] = useState(true);

  useEffect(() => {
    loadMyKits();
  }, []);

  const loadMyKits = async () => {
    try {
      setLoadingKits(true);
      const data = await consumerApi.kit.getMyKits();
      setMyKits(data.items || []);
    } catch (err) {
      console.error(err);
    } finally {
      setLoadingKits(false);
    }
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!serialNumber || !pin) {
      alert('시리얼 번호와 PIN을 모두 입력해주세요.');
      return;
    }

    try {
      setSubmitting(true);
      const response = await consumerApi.kit.register({
        serialNumber,
        pin,
      });

      alert(response.message);

      if (response.success && response.diagnosis_id) {
        navigate(`/app/my-diagnosis/${response.diagnosis_id}`);
      } else {
        loadMyKits();
        setSerialNumber('');
        setPin('');
      }
    } catch (err) {
      console.error(err);
      alert(err.response?.data?.detail || '키트 등록에 실패했습니다.');
    } finally {
      setSubmitting(false);
    }
  };

  const handleCheckStatus = async () => {
    if (!serialNumber) {
      alert('시리얼 번호를 입력해주세요.');
      return;
    }

    try {
      const status = await consumerApi.kit.checkStatus(serialNumber);
      alert(status.message);
    } catch (err) {
      console.error(err);
      alert(err.response?.data?.detail || '상태 확인에 실패했습니다.');
    }
  };

  return (
    <div style={{ maxWidth: '600px', margin: '0 auto' }}>
      <h2>키트 등록</h2>
      <p style={{ color: '#666', marginBottom: '1.5rem' }}>
        알러지 검사 키트의 시리얼 번호와 PIN을 입력하여 검사 결과를 확인하세요.
      </p>

      {/* 등록 폼 */}
      <div className="card" style={{ marginBottom: '1.5rem' }}>
        <form onSubmit={handleSubmit}>
          <div className="form-group">
            <label>시리얼 번호</label>
            <input
              type="text"
              placeholder="키트 시리얼 번호 (예: SGT-12345678)"
              value={serialNumber}
              onChange={(e) => setSerialNumber(e.target.value.toUpperCase())}
              className="form-control"
              style={{ fontSize: '1.1rem', textAlign: 'center', letterSpacing: '2px' }}
            />
            <p style={{ fontSize: '0.875rem', color: '#666', marginTop: '0.5rem' }}>
              키트 포장에 인쇄된 시리얼 번호를 입력하세요
            </p>
          </div>

          <div className="form-group">
            <label>PIN</label>
            <input
              type="password"
              placeholder="4~6자리 PIN"
              value={pin}
              onChange={(e) => setPin(e.target.value)}
              className="form-control"
              maxLength={6}
              style={{ fontSize: '1.1rem', textAlign: 'center', letterSpacing: '4px' }}
            />
            <p style={{ fontSize: '0.875rem', color: '#666', marginTop: '0.5rem' }}>
              키트에 동봉된 PIN 번호를 입력하세요
            </p>
          </div>

          <div style={{ display: 'flex', gap: '0.5rem' }}>
            <button
              type="button"
              className="btn btn-secondary"
              onClick={handleCheckStatus}
              style={{ flex: 1 }}
            >
              상태 확인
            </button>
            <button
              type="submit"
              className="btn btn-primary"
              disabled={submitting}
              style={{ flex: 2 }}
            >
              {submitting ? '등록 중...' : '키트 등록'}
            </button>
          </div>
        </form>
      </div>

      {/* 안내 사항 */}
      <div className="card" style={{ marginBottom: '1.5rem', background: '#f8f9fa' }}>
        <h4>안내 사항</h4>
        <ul style={{ paddingLeft: '1.5rem', color: '#666' }}>
          <li>키트 등록은 검사 결과가 입력된 후에 가능합니다.</li>
          <li>검사 후 결과 입력까지 1-3일이 소요될 수 있습니다.</li>
          <li>시리얼 번호와 PIN은 1회만 사용 가능합니다.</li>
          <li>문의사항은 고객센터로 연락해주세요.</li>
        </ul>
      </div>

      {/* 내 키트 목록 */}
      <div className="card">
        <h3>등록된 키트</h3>
        {loadingKits ? (
          <p style={{ color: '#666', textAlign: 'center' }}>로딩 중...</p>
        ) : myKits.length > 0 ? (
          <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
            {myKits.map((kit, idx) => (
              <div
                key={idx}
                style={{
                  display: 'flex',
                  justifyContent: 'space-between',
                  alignItems: 'center',
                  padding: '1rem',
                  background: '#f8f9fa',
                  borderRadius: '8px',
                  cursor: kit.diagnosis_id ? 'pointer' : 'default',
                }}
                onClick={() => kit.diagnosis_id && navigate(`/app/my-diagnosis/${kit.diagnosis_id}`)}
              >
                <div>
                  <p style={{ fontWeight: '600' }}>{kit.serial_number}</p>
                  <p style={{ fontSize: '0.875rem', color: '#666' }}>
                    검사일: {kit.test_date ? new Date(kit.test_date).toLocaleDateString('ko-KR') : '-'}
                  </p>
                </div>
                {kit.diagnosis_id && (
                  <span style={{ color: '#667eea' }}>결과 보기 →</span>
                )}
              </div>
            ))}
          </div>
        ) : (
          <p style={{ color: '#666', textAlign: 'center', padding: '2rem' }}>
            등록된 키트가 없습니다.
          </p>
        )}
      </div>

      {/* 도움말 */}
      <div style={{
        marginTop: '1.5rem',
        padding: '1rem',
        background: '#e3f2fd',
        borderRadius: '8px',
        textAlign: 'center',
      }}>
        <p>키트 등록에 문제가 있으신가요?</p>
        <p style={{ fontSize: '0.875rem', color: '#666' }}>
          고객센터: 1588-1234 (평일 09:00 - 18:00)
        </p>
      </div>
    </div>
  );
}

export default KitRegisterPage;
