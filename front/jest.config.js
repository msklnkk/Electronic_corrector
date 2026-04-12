module.exports = {
  preset: 'ts-jest',
  testEnvironment: 'jsdom',
  testTimeout: 10000,
  roots: ['<rootDir>/tests', '<rootDir>/src'],
  setupFilesAfterEnv: ['<rootDir>/tests/setupTests.ts'],
  moduleNameMapper: {
    '\\.(css|less|scss|sass)$': 'identity-obj-proxy',
    '^@/(.*)$': '<rootDir>/src/$1',
    '^api$': '<rootDir>/src/api/index.ts',
    '^api/(.*)$': '<rootDir>/src/api/$1',
    '^components$': '<rootDir>/src/components/index.ts',
    '^components/(.*)$': '<rootDir>/src/components/$1',
    '^services$': '<rootDir>/src/services/index.ts',
    '^services/(.*)$': '<rootDir>/src/services/$1',
    '^types$': '<rootDir>/src/types/index.ts',
    '^types/(.*)$': '<rootDir>/src/types/$1',
    '^utils$': '<rootDir>/src/utils/index.ts',
    '^utils/(.*)$': '<rootDir>/src/utils/$1',
    '^hooks$': '<rootDir>/src/hooks/index.ts',
    '^hooks/(.*)$': '<rootDir>/src/hooks/$1',
    '^config$': '<rootDir>/src/config/constants.ts',
    '^config/(.*)$': '<rootDir>/src/config/$1',
    '^assets/(.*)$': '<rootDir>/src/assets/$1'
  },
  collectCoverageFrom: [
    'src/**/*.{ts,tsx}',
    '!src/**/*.d.ts',
    '!src/index.tsx',
    '!src/reportWebVitals.ts',
    '!src/tests/**'
  ],
  coverageThreshold: {
    global: {
      branches: 70,
      functions: 70,
      lines: 70,
      statements: 70
    }
  },
  testMatch: [
    '<rootDir>/tests/**/*.{spec,test}.{ts,tsx}',
    '<rootDir>/src/**/__tests__/**/*.{ts,tsx}'
  ],
  moduleFileExtensions: ['ts', 'tsx', 'js', 'jsx', 'json', 'node'],
  transform: {
    '^.+\\.tsx?$': ['ts-jest', {
      tsconfig: '<rootDir>/tsconfig.test.json'
    }]
  },
  testPathIgnorePatterns: [
    '/node_modules/',
    '/build/',
    '/.next/'
  ]
};
