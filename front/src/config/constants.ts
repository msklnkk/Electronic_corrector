// src/config/constants.ts

export const API_ROUTES = {
  AUTH: {
    LOGIN: '/token',
    REGISTER: '/register',
    ME: '/me',
    LOGOUT: '/logout',
  },
  DOCUMENTS: {
    UPLOAD: '/upload',
    CHECK_START: '/gost-check/start',
    CHECK_RESULT: (id: string) => `/gost-check/result/${id}`,
  },
  TELEGRAM: {
    AUTH: '/telegram-auth',
    CHECK_SUBSCRIPTION: '/check-tg-subscription',
  },
} as const;

export const STORAGE_KEYS = {
  ACCESS_TOKEN: 'access_token',
  USER_PROFILE: 'user_profile',
} as const;

export const FILE_CONFIG = {
  ALLOWED_TYPES: ['.pdf', '.doc', '.docx'],
  ALLOWED_MIME_TYPES: ['application/pdf', 'application/msword', 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
  MAX_SIZE_MB: Number(process.env.REACT_APP_MAX_FILE_SIZE_MB) || 50,
  MAX_SIZE_BYTES: (Number(process.env.REACT_APP_MAX_FILE_SIZE_MB) || 50) * 1024 * 1024,
} as const;

export const CHECK_TYPES = {
  GOST: 'gost',
  INTERNAL: 'internal',
  CUSTOM: 'custom',
} as const;

export const ROUTES = {
  HOME: '/',
  LOGIN: '/login',
  CHECK: '/check',
  CHECK_RESULT: (id: string) => `/check-result/${id}`,
  PROFILE: '/profile',
} as const;

export const TELEGRAM_CONFIG = {
  BOT_USERNAME: process.env.REACT_APP_TELEGRAM_BOT_USERNAME || 'elecrtonic_corrector_bot',
  CHANNEL_URL: process.env.REACT_APP_TELEGRAM_CHANNEL_URL || 'https://t.me/electronic_corrector',
} as const;

export const THEME_MODE = {
  LIGHT: 'light',
  DARK: 'dark',
} as const;
