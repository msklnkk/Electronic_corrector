// src/services/auth.service.ts
import axios from '../api/axios.config';
import { IToken, IRegisterRequest } from '../types/auth.types';

export const AuthService = {
  // Регистрация
  async register(userData: IRegisterRequest): Promise<IToken> {
    const response = await axios.post<IToken>('/register', userData);
    const token = response.data.access_token;
    if (token) localStorage.setItem('access_token', token);
    return response.data;
  },

  // Вход
  async login(data: URLSearchParams): Promise<IToken> {
    const response = await axios.post<IToken>('/token', data, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    });
    const token = response.data.access_token;
    localStorage.setItem('access_token', token);
    return response.data;
  },

  logout() {
    localStorage.removeItem('access_token');
  },

  getToken() {
    return localStorage.getItem('access_token');
  },

  // УБРАНО: getCurrentUser, getCurrentUserId
};