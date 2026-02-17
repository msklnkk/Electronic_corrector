// src/config/env.ts

const getEnvVar = (key: string, fallback?: string): string => {
  const value = process.env[key];
  
  if (!value && !fallback) {
    console.warn(`Environment variable ${key} is not set`);
    return '';
  }
  
  return value || fallback || '';
};

export const ENV = {
  API_BASE_URL: getEnvVar('REACT_APP_API_BASE_URL', 'http://localhost:8020'),
  TELEGRAM_BOT_USERNAME: getEnvVar('REACT_APP_TELEGRAM_BOT_USERNAME', 'elecrtonic_corrector_bot'),
  TELEGRAM_CHANNEL_URL: getEnvVar('REACT_APP_TELEGRAM_CHANNEL_URL', 'https://t.me/electronic_corrector'),
  MAX_FILE_SIZE_MB: Number(getEnvVar('REACT_APP_MAX_FILE_SIZE_MB', '50')),
} as const;

// Валидация критичных переменных при запуске
export const validateEnv = (): void => {
  const requiredVars = ['REACT_APP_API_BASE_URL'];
  
  const missing = requiredVars.filter(key => !process.env[key]);
  
  if (missing.length > 0) {
    console.error('Missing required environment variables:', missing);
  }
};
