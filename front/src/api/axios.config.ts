// src/api/axios.config.ts
import axios from 'axios';

const instance = axios.create({
  baseURL: 'http://localhost:8020',
  headers: {
    'Content-Type': 'application/json', // по умолчанию JSON
  },
  withCredentials: true,
});

// Интерцептор запросов
instance.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('access_token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }

    // Для /token — меняем Content-Type на form-data
    if (config.url?.includes('/token')) {
      config.headers['Content-Type'] = 'application/x-www-form-urlencoded';
    }

    console.log('Request:', config.method?.toUpperCase(), config.url);
    return config;
  },
  (error) => Promise.reject(error)
);

// Интерцептор ответов
instance.interceptors.response.use(
  (response) => {
    console.log('Response:', response.status, response.config.url);
    return response;
  },
  (error) => {
    // ВОТ ЭТО САМОЕ ГЛАВНОЕ — подробный вывод 422
    if (error.response?.status === 422) {
      console.error('%c422 — БЭКЕНД НЕ ПРИНЯЛ ДАННЫЕ РЕГИСТРАЦИИ:', 'color: red; font-size: 16px; font-weight: bold');
      console.error('Точное тело ошибки от FastAPI:');
      console.error(JSON.stringify(error.response.data, null, 2));
    } else {
      console.error('Ошибка:', error.response?.status, error.response?.data || error.message);
    }

    if (error.response?.status === 401) {
      localStorage.removeItem('access_token');
      window.location.href = '/login';
    }

    const message = error.response?.data?.detail || 'Ошибка сервера';
    return Promise.reject(new Error(message));
  }
);

export default instance;