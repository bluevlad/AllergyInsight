/** @type {import('jest').Config} */
const config = {
  // 테스트 환경
  testEnvironment: 'jsdom',

  // 설정 파일
  setupFilesAfterEnv: ['<rootDir>/src/setupTests.js'],

  // 모듈 경로 매핑
  moduleNameMapper: {
    // CSS 모듈 처리
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    // 이미지 파일 처리
    '\\.(jpg|jpeg|png|gif|webp|svg)$': '<rootDir>/__mocks__/fileMock.js',
    // 절대 경로 별칭 (필요시 추가)
    '^@/(.*)$': '<rootDir>/src/$1',
  },

  // Vite import.meta.env를 위한 globals
  globals: {
    'import.meta': {
      env: {
        VITE_API_URL: '',
        MODE: 'test',
      },
    },
  },

  // 변환 설정 (커스텀 트랜스포머로 import.meta.env 지원)
  transform: {
    '^.+\\.(js|jsx)$': '<rootDir>/jest.transform.js',
  },

  // 테스트 파일 패턴
  testMatch: [
    '<rootDir>/src/**/__tests__/**/*.{js,jsx}',
    '<rootDir>/src/**/*.{test,spec}.{js,jsx}',
  ],

  // 커버리지 수집 대상
  collectCoverageFrom: [
    'src/**/*.{js,jsx}',
    '!src/main.jsx',
    '!src/**/*.d.ts',
    '!src/**/__tests__/**',
    '!**/node_modules/**',
  ],

  // 커버리지 리포터
  coverageReporters: ['text', 'lcov', 'html'],

  // 커버리지 임계값 (점진적으로 높여감)
  coverageThreshold: {
    global: {
      branches: 20,
      functions: 20,
      lines: 20,
      statements: 20,
    },
  },

  // 무시할 패턴
  testPathIgnorePatterns: ['/node_modules/'],

  // 변환 무시 패턴
  transformIgnorePatterns: [
    '/node_modules/',
    '\\.pnp\\.[^\\/]+$',
  ],

  // 테스트 타임아웃 (ms)
  testTimeout: 10000,

  // 상세 출력
  verbose: true,
};

module.exports = config;
