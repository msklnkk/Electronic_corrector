// src/hooks/useAuth.ts
import { useState, useEffect } from 'react';

import { AuthService } from 'services';                   
import type { IRegisterRequest } from 'types';          

interface AuthState {
  user: { loggedIn: boolean } | null;
  loading: boolean;
  login: (email: string, password: string) => Promise<void>;
  register: (data: IRegisterRequest) => Promise<void>;
  logout: () => void;
}

export const useAuth = (): AuthState => {
  const [user, setUser] = useState<{ loggedIn: boolean } | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const token = AuthService.getToken();
    if (token) {
      setUser({ loggedIn: true });
    }
    setLoading(false);
  }, []);

  const loginUser = async (email: string, password: string) => {
    const params = new URLSearchParams();
    params.append('username', email);
    params.append('password', password);
    await AuthService.login(params);
    setUser({ loggedIn: true });
  };

  const register = async (data: IRegisterRequest) => {
    await AuthService.register(data);
    setUser({ loggedIn: true });
  };

  const logout = () => {
    AuthService.logout();
    setUser(null);
  };

  return { user, loading, login: loginUser, register, logout };
};