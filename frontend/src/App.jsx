import React from 'react';
import { BrowserRouter, Routes, Route, NavLink } from 'react-router-dom';
import Dashboard from './pages/Dashboard';
import SearchPage from './pages/SearchPage';
import QAPage from './pages/QAPage';
import PapersPage from './pages/PapersPage';

function App() {
  return (
    <BrowserRouter>
      <div className="app-container">
        {/* 헤더 */}
        <header className="header">
          <h1>🔬 AllergyInsight</h1>
          <p className="header-subtitle">알러지 논문 검색 및 Q&A 시스템</p>
          <nav className="nav">
            <NavLink to="/" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              대시보드
            </NavLink>
            <NavLink to="/search" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              논문 검색
            </NavLink>
            <NavLink to="/qa" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              Q&A
            </NavLink>
            <NavLink to="/papers" className={({ isActive }) => `nav-link ${isActive ? 'active' : ''}`}>
              논문 목록
            </NavLink>
          </nav>
        </header>

        {/* 메인 컨텐츠 */}
        <main className="main-content">
          <Routes>
            <Route path="/" element={<Dashboard />} />
            <Route path="/search" element={<SearchPage />} />
            <Route path="/qa" element={<QAPage />} />
            <Route path="/papers" element={<PapersPage />} />
          </Routes>
        </main>

        {/* 푸터 */}
        <footer style={{ textAlign: 'center', padding: '1rem', color: '#666', fontSize: '0.875rem' }}>
          AllergyInsight v1.0.0 | 논문 기반 알러지 정보 시스템
        </footer>
      </div>
    </BrowserRouter>
  );
}

export default App;
