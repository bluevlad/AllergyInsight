import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { hospitalApi } from '../../services/api';

const PatientRegisterPage = () => {
  const navigate = useNavigate();
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);
  const [success, setSuccess] = useState(null);

  const [formData, setFormData] = useState({
    name: '',
    phone: '',
    birthDate: '',
    patientNumber: '',
    assignedDoctorId: ''
  });

  const handleChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setSuccess(null);

    if (!formData.name.trim()) {
      setError('환자 이름을 입력해주세요');
      return;
    }

    if (!formData.phone.trim()) {
      setError('전화번호를 입력해주세요');
      return;
    }

    try {
      setLoading(true);
      const data = {
        name: formData.name.trim(),
        phone: formData.phone.trim(),
        birth_date: formData.birthDate || null,
        patient_number: formData.patientNumber || null,
        assigned_doctor_id: formData.assignedDoctorId ? parseInt(formData.assignedDoctorId) : null
      };

      const result = await hospitalApi.registerNewPatient(data);
      setSuccess('환자가 등록되었습니다');

      // 2초 후 환자 상세 페이지로 이동
      setTimeout(() => {
        navigate(`/hospital/patients/${result.id}`);
      }, 1500);
    } catch (err) {
      console.error('Registration error:', err);
      setError(err.response?.data?.detail || '환자 등록에 실패했습니다');
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{ padding: '1.5rem', maxWidth: '600px', margin: '0 auto' }}>
      <div style={{ marginBottom: '2rem' }}>
        <h2 style={{ fontSize: '1.5rem', fontWeight: 'bold', marginBottom: '0.5rem' }}>
          신규 환자 등록
        </h2>
        <p style={{ color: '#666' }}>새로운 환자 정보를 입력합니다</p>
      </div>

      {error && (
        <div style={{
          backgroundColor: '#fee2e2',
          border: '1px solid #fecaca',
          borderRadius: '8px',
          padding: '1rem',
          marginBottom: '1rem',
          color: '#dc2626'
        }}>
          {error}
        </div>
      )}

      {success && (
        <div style={{
          backgroundColor: '#dcfce7',
          border: '1px solid #bbf7d0',
          borderRadius: '8px',
          padding: '1rem',
          marginBottom: '1rem',
          color: '#16a34a'
        }}>
          {success}
        </div>
      )}

      <form onSubmit={handleSubmit} style={{
        backgroundColor: 'white',
        borderRadius: '12px',
        padding: '1.5rem',
        boxShadow: '0 1px 3px rgba(0,0,0,0.1)'
      }}>
        <div style={{ marginBottom: '1.5rem' }}>
          <label style={labelStyle}>
            환자 이름 <span style={{ color: '#dc2626' }}>*</span>
          </label>
          <input
            type="text"
            name="name"
            value={formData.name}
            onChange={handleChange}
            placeholder="홍길동"
            style={inputStyle}
            required
          />
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <label style={labelStyle}>
            전화번호 <span style={{ color: '#dc2626' }}>*</span>
          </label>
          <input
            type="tel"
            name="phone"
            value={formData.phone}
            onChange={handleChange}
            placeholder="010-1234-5678"
            style={inputStyle}
            required
          />
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <label style={labelStyle}>생년월일</label>
          <input
            type="date"
            name="birthDate"
            value={formData.birthDate}
            onChange={handleChange}
            style={inputStyle}
          />
        </div>

        <div style={{ marginBottom: '1.5rem' }}>
          <label style={labelStyle}>병원 내 환자번호</label>
          <input
            type="text"
            name="patientNumber"
            value={formData.patientNumber}
            onChange={handleChange}
            placeholder="P-12345"
            style={inputStyle}
          />
        </div>

        <div style={{
          display: 'flex',
          gap: '1rem',
          marginTop: '2rem'
        }}>
          <button
            type="button"
            onClick={() => navigate('/hospital/patients')}
            style={{
              flex: 1,
              padding: '0.75rem',
              border: '1px solid #d1d5db',
              borderRadius: '8px',
              backgroundColor: 'white',
              cursor: 'pointer',
              fontWeight: '500'
            }}
          >
            취소
          </button>
          <button
            type="submit"
            disabled={loading}
            style={{
              flex: 1,
              padding: '0.75rem',
              backgroundColor: loading ? '#9ca3af' : '#3b82f6',
              color: 'white',
              border: 'none',
              borderRadius: '8px',
              cursor: loading ? 'not-allowed' : 'pointer',
              fontWeight: '500'
            }}
          >
            {loading ? '등록 중...' : '환자 등록'}
          </button>
        </div>
      </form>

      <div style={{
        marginTop: '1.5rem',
        padding: '1rem',
        backgroundColor: '#f0f9ff',
        borderRadius: '8px',
        fontSize: '0.875rem',
        color: '#0369a1'
      }}>
        <strong>안내:</strong> 등록된 환자에게 SMS로 동의서 서명 링크가 발송됩니다.
        환자가 동의서에 서명하면 진단 결과를 조회하고 입력할 수 있습니다.
      </div>
    </div>
  );
};

const labelStyle = {
  display: 'block',
  marginBottom: '0.5rem',
  fontSize: '0.875rem',
  fontWeight: '500',
  color: '#374151'
};

const inputStyle = {
  width: '100%',
  padding: '0.75rem',
  border: '1px solid #d1d5db',
  borderRadius: '8px',
  fontSize: '1rem'
};

export default PatientRegisterPage;
