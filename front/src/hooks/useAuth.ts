// src/hooks/useAuth.ts
import { useState, useEffect } from 'react';
import { AuthService } from '../services/auth.service';

interface AuthState {
  user: any | null;
  loading: boolean;
  login: (login: string, password: string) => Promise<void>;
  register: (login: string, password: string) => Promise<void>;
  logout: () => void;
}

export const useAuth = (): AuthState => {
  const [user, setUser] = useState<any | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    const init = async () => {
      const token = AuthService.getToken();
      if (token) {
        try {
          const userData = await AuthService.getCurrentUser();
          setUser(userData);
        } catch {
          AuthService.logout();
        }
      }
      setLoading(false);
    };
    init();
  }, []);

  const loginUser = async (login: string, password: string) => {
    const params = new URLSearchParams();
    params.append('username', login);
    params.append('password', password);
    await AuthService.login(params);
    const userData = await AuthService.getCurrentUser();
    setUser(userData);
};

  const register = async (login: string, password: string) => {
    await AuthService.register({ login, password });
    await loginUser(login, password); 
};

  const logout = () => {
    AuthService.logout();
    setUser(null);
  };

  return { user, loading, login: loginUser, register, logout };
};