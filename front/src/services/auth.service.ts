// src/services/auth.service.ts
import axios from '../api/axios.config';
import { IToken, IRegisterRequest } from '../types/auth.types';

// Интерфейс полного профиля пользователя
export interface UserProfile {
  user_id: number;
  email: string;
  username: string;
  first_name?: string;
  surname_name?: string;
  patronomic_name?: string;
  role: string;
  theme: string;
  is_push_enabled: boolean;
  tg_username?: string | null;
  telegram_id?: number | null;
  is_tg_subscribed?: boolean;
  [key: string]: any;
}

// Вспомогательная функция для декодирования JWT
function decodeToken(token: string): any {
  try {
    const payload = token.split('.')[1];
    return JSON.parse(atob(payload));
  } catch (e) {
    console.error('Ошибка декодирования токена:', e);
    return null;
  }
}

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
    localStorage.removeItem('user_profile'); // чистится кэш профиля
  },

  getToken(): string | null {
    return localStorage.getItem('access_token');
  },

  // Сохраняем полный профиль из /me
  setUserProfile(profile: UserProfile) {
    localStorage.setItem('user_profile', JSON.stringify(profile));
  },

  // Получаем кэшированный профиль
  getUserProfile(): UserProfile | null {
    const data = localStorage.getItem('user_profile');
    return data ? JSON.parse(data) : null;
  },

  // Основной метод — сначала из кэша, потом из токена
  getCurrentUser(): UserProfile | any | null {
    const profile = this.getUserProfile();
    if (profile) return profile;

    const token = this.getToken();
    if (!token) return null;
    return decodeToken(token);
  },

  getCurrentUserEmail(): string | null {
    const user = this.getCurrentUser();
    return user?.email || user?.sub || null;
  },

  getCurrentUserId(): number | null {
    const user = this.getCurrentUser();
    return user?.user_id ?? null;
  },
};