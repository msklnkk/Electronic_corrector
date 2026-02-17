// src/services/auth.service.ts
import { api } from "api";
import type { IToken, IRegisterRequest } from "types/auth.types";
import type { UserProfile } from "types/user.types";
import { API_ROUTES, STORAGE_KEYS } from "config/constants";
import { decodeToken } from "utils/jwt";

// Вспомогательный тип для декодированного JWT (вынести в types/jwt.types.ts)
interface JwtPayload {
  sub?: string;
  email?: string;
  user_id?: number;
  [key: string]: any;
}

export const AuthService = {
  // Регистрация
  async register(userData: IRegisterRequest): Promise<IToken> {
    const response = await api.post<IToken>(API_ROUTES.AUTH.REGISTER, userData);
    const token = response.data.access_token;
    if (token) {
      localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, token);
    }
    return response.data;
  },

  // Вход
  async login(data: URLSearchParams): Promise<IToken> {
    const response = await api.post<IToken>(API_ROUTES.AUTH.LOGIN, data, {
      headers: { "Content-Type": "application/x-www-form-urlencoded" },
    });
    const token = response.data.access_token;
    if (token) {
      localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, token);
    }
    return response.data;
  },

  logout() {
    localStorage.removeItem(STORAGE_KEYS.ACCESS_TOKEN);
    localStorage.removeItem(STORAGE_KEYS.USER_PROFILE);
  },

  getToken(): string | null {
    return localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN);
  },

  setUserProfile(profile: UserProfile) {
    localStorage.setItem(STORAGE_KEYS.USER_PROFILE, JSON.stringify(profile));
  },

  getUserProfile(): UserProfile | null {
    const data = localStorage.getItem(STORAGE_KEYS.USER_PROFILE);
    return data ? JSON.parse(data) : null;
  },

  getCurrentUser(): UserProfile | null {
    const profile = this.getUserProfile();
    if (profile) return profile;

    const token = this.getToken();
    if (!token) return null;

    const decoded = decodeToken(token);
    return decoded ? (decoded as UserProfile) : null;
  },

  getCurrentUserEmail(): string | null {
    const user = this.getCurrentUser();
    return user?.email ?? null;
  },

  getCurrentUserId(): number | null {
    const user = this.getCurrentUser();
    return user?.user_id ?? null;
  },
};