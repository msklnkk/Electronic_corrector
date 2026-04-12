// tests/unit/services/auth.service.test.ts
import { AuthService } from '../../../src/services/auth.service';
import { api } from '../../../src/api';
import { STORAGE_KEYS } from '../../../src/config/constants';
import type { UserProfile } from '../../../src/types/user.types';

// Мокируем API
jest.mock('../../../src/api');

const mockUserProfile: UserProfile = {
  user_id: 1,
  email: 'test@example.com',
  username: 'testuser',
  first_name: 'Test',
  surname_name: 'User',
  patronomic_name: 'Testovich',
  role: 'user' as const,
  theme: 'light' as const,
  is_push_enabled: false,
};

const mockToken = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxLCJlbWFpbCI6InRlc3RAZXhhbXBsZS5jb20iLCJyb2xlIjoidXNlciJ9.signature';

describe('AuthService', () => {
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  describe('register', () => {
    it('должен сохранить токен при успешной регистрации', async () => {
      const registerData = {
        email: 'newuser@example.com',
        password: 'password123',
        first_name: 'Иван',
        surname_name: 'Иванов',
        patronomic_name: 'Иванович',
        login: 'newuser',
        tg_username: 'newuser_tg',
      };

      (api.post as jest.Mock).mockResolvedValue({
        data: {
          access_token: mockToken,
        },
      });

      const result = await AuthService.register(registerData);

      expect(result.access_token).toBe(mockToken);
      expect(localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN)).toBe(mockToken);
      expect(api.post).toHaveBeenCalledWith(
        expect.stringContaining('register'),
        registerData
      );
    });

    it('должен возвращать ошибку при неудачной регистрации', async () => {
      const registerData = {
        email: 'newuser@example.com',
        password: 'password123',
        first_name: 'Иван',
        surname_name: 'Иванов',
        patronomic_name: 'Иванович',
        login: 'newuser',
        tg_username: 'newuser_tg',
      };

      const error = new Error('Registration failed');
      (api.post as jest.Mock).mockRejectedValue(error);

      await expect(AuthService.register(registerData)).rejects.toThrow(error);
    });
  });

  describe('login', () => {
    it('должен сохранить токен при успешном входе', async () => {
      const params = new URLSearchParams();
      params.append('username', 'test@example.com');
      params.append('password', 'password123');

      (api.post as jest.Mock).mockResolvedValue({
        data: {
          access_token: mockToken,
        },
      });

      const result = await AuthService.login(params);

      expect(result.access_token).toBe(mockToken);
      expect(localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN)).toBe(mockToken);
    });

    it('должен отправить правильные заголовки при входе', async () => {
      const params = new URLSearchParams();
      params.append('username', 'test@example.com');
      params.append('password', 'password123');

      (api.post as jest.Mock).mockResolvedValue({
        data: {
          access_token: mockToken,
        },
      });

      await AuthService.login(params);

      expect(api.post).toHaveBeenCalledWith(
        expect.stringContaining('token'),
        params,
        {
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
        }
      );
    });
  });

  describe('logout', () => {
    it('должен удалить токен и профиль из localStorage', () => {
      localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, mockToken);
      localStorage.setItem(STORAGE_KEYS.USER_PROFILE, JSON.stringify(mockUserProfile));

      AuthService.logout();

      expect(localStorage.getItem(STORAGE_KEYS.ACCESS_TOKEN)).toBeNull();
      expect(localStorage.getItem(STORAGE_KEYS.USER_PROFILE)).toBeNull();
    });
  });

  describe('getToken', () => {
    it('должен вернуть токен из localStorage', () => {
      localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, mockToken);

      const token = AuthService.getToken();

      expect(token).toBe(mockToken);
    });

    it('должен вернуть null если токена нет', () => {
      const token = AuthService.getToken();

      expect(token).toBeNull();
    });
  });

  describe('setUserProfile', () => {
    it('должен сохранить профиль в localStorage', () => {
      AuthService.setUserProfile(mockUserProfile);

      const saved = localStorage.getItem(STORAGE_KEYS.USER_PROFILE);
      expect(JSON.parse(saved!)).toEqual(mockUserProfile);
    });
  });

  describe('getUserProfile', () => {
    it('должен вернуть профиль из localStorage', () => {
      localStorage.setItem(STORAGE_KEYS.USER_PROFILE, JSON.stringify(mockUserProfile));

      const profile = AuthService.getUserProfile();

      expect(profile).toEqual(mockUserProfile);
    });

    it('должен вернуть null если профиля нет', () => {
      const profile = AuthService.getUserProfile();

      expect(profile).toBeNull();
    });
  });

  describe('getCurrentUser', () => {
    it('должен вернуть пользователя из сохраненного профиля', () => {
      localStorage.setItem(STORAGE_KEYS.USER_PROFILE, JSON.stringify(mockUserProfile));

      const user = AuthService.getCurrentUser();

      expect(user).toEqual(mockUserProfile);
    });

    it('должен вернуть пользователя из токена если профиля нет', () => {
      localStorage.setItem(STORAGE_KEYS.ACCESS_TOKEN, mockToken);

      const user = AuthService.getCurrentUser();

      expect(user).toBeDefined();
      expect(user?.user_id).toBe(1);
      expect(user?.email).toBe('test@example.com');
    });

    it('должен вернуть null если нет профиля и токена', () => {
      const user = AuthService.getCurrentUser();

      expect(user).toBeNull();
    });
  });

  describe('getCurrentUserEmail', () => {
    it('должен вернуть email текущего пользователя', () => {
      localStorage.setItem(STORAGE_KEYS.USER_PROFILE, JSON.stringify(mockUserProfile));

      const email = AuthService.getCurrentUserEmail();

      expect(email).toBe('test@example.com');
    });

    it('должен вернуть null если пользователя нет', () => {
      const email = AuthService.getCurrentUserEmail();

      expect(email).toBeNull();
    });
  });

  describe('getCurrentUserId', () => {
    it('должен вернуть ID текущего пользователя', () => {
      localStorage.setItem(STORAGE_KEYS.USER_PROFILE, JSON.stringify(mockUserProfile));

      const id = AuthService.getCurrentUserId();

      expect(id).toBe(1);
    });

    it('должен вернуть null если пользователя нет', () => {
      const id = AuthService.getCurrentUserId();

      expect(id).toBeNull();
    });
  });
});
