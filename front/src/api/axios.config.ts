// src/api/axios.config.ts
import axios from 'axios';

const api = axios.create({
  baseURL: 'http://localhost:8020', 
  withCredentials: true,         
});

// ────────────────────────────────
// Интерцептор запросов
// ────────────────────────────────
api.interceptors.request.use(
  (config) => {
    // Добавляем токен из localStorage
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Для логина — application/x-www-form-urlencoded
    if (config.url?.includes('/token')) {
      config.headers['Content-Type'] = 'application/x-www-form-urlencoded';
    }

    // Для загрузки файлов
    if (config.data instanceof FormData) {
      delete config.headers['Content-Type']; 
    }

    // Красивый лог в консоль
    console.log(
      `%c→ ${config.method?.toUpperCase()} ${config.url}`,
      'color: #8b5cf6; font-weight: bold;',
      config.data instanceof FormData ? '[FormData]' : config.data || ''
    );

    return config;
  },
  (error) => Promise.reject(error)
);

// ────────────────────────────────
// Интерцептор ответов
// ────────────────────────────────
api.interceptors.response.use(
  (response) => {
    console.log(
      `%c← ${response.status} ${response.config.url}`,
      'color: #10b981; font-weight: bold;',
      response.data
    );
    return response;
  },
  (error) => {
    const status = error.response?.status;
    const url = error.config?.url;

    // 422 — ошибки с бэкенда
    if (status === 422) {
      console.error('%c422 Unprocessable Entity', 'color: red; font-size: 18px; font-weight: bold;');
      console.error('URL:', url);
      console.error('Ошибки валидации от FastAPI:');
      console.table(error.response.data.detail);
    } 
    // 401 — ошибки токена
    else if (status === 401) {
      console.warn('401 — Токен недействителен, редиректим на логин');
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    } 
    // Любая другая ошибка
    else {
      console.error(`%cОшибка ${status || 'Network'}`, 'color: red; font-weight: bold;');
      console.error('URL:', url);
      console.error('Сообщение:', error.response?.data?.detail || error.message);
    }

    // Пробрасываем дальше, чтобы catch в компоненте сработал
    return Promise.reject(error);
  }
);

export default api;