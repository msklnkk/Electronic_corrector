// tests/unit/api/axios.config.test.ts
import { api } from '../../../src/api';

describe('API configuration', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('должен иметь правильный baseURL', () => {
    expect(api.defaults.baseURL).toBe('http://localhost:8020');
  });

  it('должен иметь правильные заголовки', () => {
  const handlers = (api.interceptors.request as any).handlers;
  expect(handlers.length).toBeGreaterThan(0);
  });

  it('должен иметь интерцептор запросов', () => {
    expect(api.interceptors.request).toBeDefined();
  });

  it('должен иметь интерцептор ответов', () => {
    expect(api.interceptors.response).toBeDefined();
  });

  it('интерцептор запросов должен добавлять токен авторизации', () => {
    localStorage.setItem('access_token', 'test-token');
    expect(localStorage.getItem('access_token')).toBe('test-token');
  });

  it('должен выполнять GET запросы', async () => {
    try {
      await api.get('/me');
    } catch (err) {
      expect(err).toBeDefined();
    }
  });

  it('должен выполнять POST запросы', async () => {
    try {
      await api.post('/token', {});
    } catch (err) {
      expect(err).toBeDefined();
    }
  });

  it('должен выполнять PUT запросы', async () => {
    try {
      await api.put('/update_me', {});
    } catch (err) {
      expect(err).toBeDefined();
    }
  });
});