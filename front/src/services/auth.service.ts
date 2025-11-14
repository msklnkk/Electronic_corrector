// src/services/auth.service.ts
import axios from '../api/axios.config';
import { decodeToken } from '../utils/jwt';
import { IToken, IClientResponse, IRegisterRequest } from '../types/auth.types';

export const AuthService = {
  async register(userData: IRegisterRequest): Promise<IClientResponse> {
    const response = await axios.post<IClientResponse>('/register', userData);
    const token = response.data.access_token;
    if (token) localStorage.setItem('access_token', token);
    return response.data;
  },

  async login(data: URLSearchParams): Promise<IToken> {
    const response = await axios.post<IToken>('/login', data, {
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

  async getCurrentUser(): Promise<IClientResponse> {
    return (await axios.get<IClientResponse>('/me')).data;
  },

  async getCurrentUserId(): Promise<number | null> {
    const token = this.getToken();
    if (!token) return null;
    const decoded = decodeToken(token);
    const email = decoded?.sub;
    if (!email) return null;
    const res = await axios.get<IClientResponse>(`/user/by-mail/${email}`);
    return res.data.clientid || null;
  },
};