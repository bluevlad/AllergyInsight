import React, { useState, useEffect, useCallback } from 'react';
import { Link, Navigate } from 'react-router-dom';
import { useAuth } from '../../shared/contexts/AuthContext';
import './GatewayLanding.css';

const FEATURES = [
  {
    icon: '🤖',
    name: 'AI 상담',
    desc: 'MLX EXAONE-3.5 + ChromaDB RAG 기반 논문 Q&A (공개, 10회/분)',
    level: 'public',
    to: '/ai/consult',
  },
  {
    icon: '💡',
    name: 'AI 인사이트',
    desc: '알러젠별 논문·뉴스·트렌드를 한 페이지에 집약한 공개 허브',
    level: 'public',
    to: '/ai/insight',
  },
  {
    icon: '📈',
    name: '분석 대시보드',
    desc: '종합 트렌드·알러젠 분석·논문 수집정보·알러젠뉴스 4개 공개 탭',
    level: 'public',
    to: '/analytics',
  },
  {
    icon: '📝',
    name: '인사이트 리포트',
    desc: '매월 1일 03:00 자동 생성되는 알러젠별 AI 마크다운 리포트',
    level: 'public',
    to: '/analytics/insights',
  },
  {
    icon: '📄',
    name: '알러지 리포트',
    desc: '알러젠별 등급(0-6)과 환자 맞춤 관리 가이드를 한 번에 생성',
    level: 'public',
    to: '/report',
  },
  {
    icon: '📬',
    name: '뉴스레터',
    desc: '알러지 뉴스·논문·인사이트 주간 정기 구독 (이메일 인증)',
    level: 'public',
    to: '/subscribe',
  },
  {
    icon: '📚',
    name: 'Wiki',
    desc: '아키텍처·API 명세·ADR·운영 가이드 MkDocs 문서',
    level: 'public',
    to: '/wiki/',
    external: true,
  },
  {
    icon: '🩺',
    name: 'Professional',
    desc: '의료진 전용 콘솔 — 환자 관리·진단 입력·임상보고서·논문 검색·Q&A (7메뉴)',
    level: 'member',
    to: '/pro',
  },
  {
    icon: '🧍',
    name: 'Consumer',
    desc: '환자용 앱 — 내 검사결과·식품 가이드·생활 관리·응급 대처·키트 등록',
    level: 'member',
    to: '/app',
  },
  {
    icon: '🔐',
    name: '관리자',
    desc: '사용자·알러젠·논문·조직·경쟁사 뉴스·구독자·약물 통합 운영 (super_admin)',
    level: 'admin',
    to: '/admin',
  },
  {
    icon: '💊',
    name: '약물 관리',
    desc: '[NEW] 공개 약물 DB(openFDA·MFDS) 수집 + 병태생리 지식 그래프 감수 — Phase 1',
    level: 'admin',
    to: '/admin/drugs',
  },
];

const TECH_STACK = [
  { name: 'React 18 + Vite', dot: '#61dafb' },
  { name: 'FastAPI', dot: '#009688' },
  { name: 'Python 3.10+', dot: '#3776ab' },
  { name: 'PostgreSQL 15', dot: '#336791' },
  { name: 'ChromaDB', dot: '#ff6f61' },
  { name: 'MLX · EXAONE-3.5', dot: '#d97706' },
  { name: 'APScheduler', dot: '#10b981' },
  { name: 'Google OAuth · JWT', dot: '#eab308' },
  { name: 'Docker Compose', dot: '#2496ed' },
  { name: 'Nginx', dot: '#f97316' },
  { name: 'MkDocs', dot: '#526cfe' },
];

const CONNECTED_SERVICES = [
  {
    name: 'NewsLetterPlatform',
    role: '뉴스레터 발송 연동',
    href: 'https://newsletter.unmong.com/intro.html',
    dot: '#ec4899',
  },
  {
    name: 'InfraWatcher',
    role: '컨테이너 모니터링',
    href: 'https://infrawatcher.unmong.com/intro.html',
    dot: '#06b6d4',
  },
  {
    name: 'QA-Agent',
    role: '품질 자동 테스트',
    href: 'https://qadashboard.unmong.com/intro.html',
    dot: '#8b5cf6',
  },
];

function accessFor(level, { isAuthenticated, isAdmin }) {
  if (level === 'public') return 'granted';
  if (level === 'member') return isAuthenticated ? 'granted' : 'member-locked';
  if (level === 'admin') return isAdmin ? 'granted' : 'admin-locked';
  return 'granted';
}

function tagInfo(state, level) {
  if (state === 'granted' && level === 'public') {
    return { label: '🌐 공개', variant: 'public' };
  }
  if (state === 'granted') {
    return { label: '✓ 사용 가능', variant: 'granted' };
  }
  if (state === 'member-locked') {
    return { label: '🔒 회원전용', variant: 'member-locked' };
  }
  if (state === 'admin-locked') {
    return { label: '🔐 관리자 전용', variant: 'admin-locked' };
  }
  return { label: '', variant: '' };
}

function lockedToastFor(state) {
  if (state === 'member-locked') {
    return {
      icon: '🔒',
      message: '회원전용 서비스입니다',
      actionLabel: '로그인',
      actionTo: '/login',
    };
  }
  if (state === 'admin-locked') {
    return {
      icon: '🔐',
      message: '관리자 전용입니다',
      actionLabel: '관리자 로그인',
      actionTo: '/admin/login',
    };
  }
  return null;
}

function FeatureCard({ feature, accessState, onLocked }) {
  const locked = accessState !== 'granted';
  const { label, variant } = tagInfo(accessState, feature.level);

  const handleClick = (e) => {
    if (locked) {
      e.preventDefault();
      onLocked(accessState);
    }
  };

  const inner = (
    <>
      {locked && (
        <span className="sl-feature-lock" aria-hidden="true">
          🔒
        </span>
      )}
      <span className="sl-feature-icon" aria-hidden="true">
        {feature.icon}
      </span>
      <div className="sl-feature-name">{feature.name}</div>
      <div className="sl-feature-desc">{feature.desc}</div>
      <span className={`sl-feature-tag sl-feature-tag--${variant}`}>{label}</span>
    </>
  );

  const commonProps = {
    className: 'sl-feature',
    'data-locked': locked ? 'true' : 'false',
    onClick: handleClick,
  };

  if (feature.external) {
    return (
      <a {...commonProps} href={feature.to} target="_blank" rel="noopener noreferrer">
        {inner}
      </a>
    );
  }
  if (locked) {
    return (
      <a {...commonProps} href={feature.to}>
        {inner}
      </a>
    );
  }
  return (
    <Link {...commonProps} to={feature.to}>
      {inner}
    </Link>
  );
}

function Toast({ toast, onClose }) {
  if (!toast) return null;
  return (
    <div className="sl-toast" role="status" aria-live="polite">
      <span className="sl-toast-icon" aria-hidden="true">
        {toast.icon}
      </span>
      <span className="sl-toast-msg">{toast.message}</span>
      <Link className="sl-toast-action" to={toast.actionTo} onClick={onClose}>
        {toast.actionLabel} →
      </Link>
      <button
        type="button"
        className="sl-toast-close"
        onClick={onClose}
        aria-label="닫기"
      >
        ×
      </button>
    </div>
  );
}

const GatewayLanding = () => {
  const { isAuthenticated, isAdmin, getDefaultApp, loading } = useAuth();
  const [toast, setToast] = useState(null);

  useEffect(() => {
    if (!toast) return undefined;
    const timer = setTimeout(() => setToast(null), 4500);
    return () => clearTimeout(timer);
  }, [toast]);

  const handleLocked = useCallback((accessState) => {
    const next = lockedToastFor(accessState);
    if (next) setToast(next);
  }, []);

  if (loading) {
    return (
      <div
        style={{
          display: 'flex',
          justifyContent: 'center',
          alignItems: 'center',
          minHeight: '100vh',
          background: '#0f172a',
          color: '#94a3b8',
        }}
      >
        <p>로딩 중...</p>
      </div>
    );
  }

  if (isAuthenticated) {
    const defaultApp = getDefaultApp();
    const appRoutes = { admin: '/admin', professional: '/pro', consumer: '/app' };
    return <Navigate to={appRoutes[defaultApp] || '/app'} replace />;
  }

  const authState = { isAuthenticated, isAdmin };

  return (
    <div className="gateway-landing-root">
      <div className="sl-container">
        <section className="sl-hero">
          <h1>AllergyInsight</h1>
          <p className="tagline">Allergy AI Portal · 4-Service Gateway</p>
          <p className="desc">
            논문 기반 RAG AI 상담과 알러젠 인사이트, 진단 레포트, 공개 분석 대시보드, 월별 자동 생성 리포트까지 — 의료진·환자·일반 사용자·운영자를 하나의 게이트웨이로 통합 지원하는 알러지 전문 플랫폼
          </p>
        </section>

        <section className="sl-section">
          <div className="sl-section-title">Features</div>
          <div className="sl-features">
            {FEATURES.map((feature) => (
              <FeatureCard
                key={feature.name}
                feature={feature}
                accessState={accessFor(feature.level, authState)}
                onLocked={handleLocked}
              />
            ))}
          </div>
        </section>

        <section className="sl-section sl-arch">
          <div className="sl-section-title">Architecture</div>
          <div className="sl-arch-diagram">
            <div className="sl-arch-node">
              <div className="sl-arch-node-label">Frontend</div>
              <div className="sl-arch-node-tech">
                React + Vite
                <br />
                <span className="sl-arch-node-tech-sub">4-Service Gateway</span>
              </div>
            </div>
            <div className="sl-arch-arrow">→</div>
            <div className="sl-arch-node highlight">
              <div className="sl-arch-node-label">Backend</div>
              <div className="sl-arch-node-tech">
                FastAPI
                <br />
                <span className="sl-arch-node-tech-sub">+ APScheduler</span>
              </div>
            </div>
            <div className="sl-arch-arrow">→</div>
            <div className="sl-arch-node">
              <div className="sl-arch-node-label">Data Layer</div>
              <div className="sl-arch-node-tech">
                PostgreSQL 15
                <br />
                <span className="sl-arch-node-tech-sub">+ ChromaDB</span>
              </div>
            </div>
            <div className="sl-arch-arrow">←</div>
            <div className="sl-arch-node">
              <div className="sl-arch-node-label">AI Engine</div>
              <div className="sl-arch-node-tech">
                MLX Server
                <br />
                <span className="sl-arch-node-tech-sub">EXAONE-3.5 7.8B</span>
              </div>
            </div>
          </div>
        </section>

        <section className="sl-section sl-flow">
          <div className="sl-section-title">Service Flow</div>
          <div className="sl-flow-steps">
            <div className="sl-flow-step">
              <div className="sl-flow-step-num">1</div>
              <div className="sl-flow-step-label">수집</div>
              <div className="sl-flow-step-desc">PubMed · S2 · News API</div>
            </div>
            <div className="sl-flow-arrow">→</div>
            <div className="sl-flow-step">
              <div className="sl-flow-step-num">2</div>
              <div className="sl-flow-step-label">AI 분석</div>
              <div className="sl-flow-step-desc">알러젠 태깅 · RAG 임베딩</div>
            </div>
            <div className="sl-flow-arrow">→</div>
            <div className="sl-flow-step">
              <div className="sl-flow-step-num">3</div>
              <div className="sl-flow-step-label">인사이트 생성</div>
              <div className="sl-flow-step-desc">월별 자동 리포트 (AI)</div>
            </div>
            <div className="sl-flow-arrow">→</div>
            <div className="sl-flow-step">
              <div className="sl-flow-step-num">4</div>
              <div className="sl-flow-step-label">사용자 제공</div>
              <div className="sl-flow-step-desc">상담 · 대시보드 · 뉴스레터</div>
            </div>
          </div>
        </section>

        <section className="sl-section sl-tech">
          <div className="sl-section-title">Tech Stack</div>
          <div className="sl-tech-list">
            {TECH_STACK.map((tech) => (
              <span className="sl-tech-badge" key={tech.name}>
                <span className="sl-tech-dot" style={{ background: tech.dot }} />
                {tech.name}
              </span>
            ))}
          </div>
        </section>

        <section className="sl-section sl-connected">
          <div className="sl-section-title">Connected Services</div>
          <div className="sl-connected-grid">
            {CONNECTED_SERVICES.map((svc) => (
              <a
                key={svc.name}
                href={svc.href}
                target="_blank"
                rel="noopener noreferrer"
                className="sl-connected-card"
              >
                <span className="sl-connected-dot" style={{ background: svc.dot }} />
                <div className="sl-connected-info">
                  <div className="sl-connected-name">{svc.name}</div>
                  <div className="sl-connected-role">{svc.role}</div>
                </div>
                <span className="sl-connected-arrow">→</span>
              </a>
            ))}
          </div>
        </section>
      </div>

      <Toast toast={toast} onClose={() => setToast(null)} />
    </div>
  );
};

export default GatewayLanding;
