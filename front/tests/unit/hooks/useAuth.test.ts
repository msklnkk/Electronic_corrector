import { renderHook, act, waitFor } from '@testing-library/react';
import { useAuth } from '../../../src/hooks/useAuth';
import { AuthService } from '../../../src/services/auth.service';

jest.mock('../../../src/services/auth.service');
jest.mock('../../../src/api', () => ({
  api: {
    get: jest.fn(),
    post: jest.fn(),
    interceptors: {
      request: { use: jest.fn() },
      response: { use: jest.fn() },
    },
  },
}));

import { api } from '../../../src/api';

const mockAuthService = AuthService as jest.Mocked<typeof AuthService>;
const mockApi = api as jest.Mocked<typeof api>;

describe('useAuth hook', () => {
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  it('должен инициализироваться с null пользователем когда токена нет', async () => {
    mockAuthService.getToken.mockReturnValue(null);

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.user).toBeNull();
  });

  it('должен загрузить пользователя если токен существует', async () => {
    mockAuthService.getToken.mockReturnValue('fake-token');
    mockApi.get.mockResolvedValueOnce({ data: { loggedIn: true } });

    const { result } = renderHook(() => useAuth());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.user).toEqual({ loggedIn: true });
  });

  it('должен выполнить вход и установить пользователя', async () => {
    mockAuthService.getToken.mockReturnValue(null);
    mockAuthService.login.mockResolvedValue({
      access_token: 'test-token',
      token_type: 'bearer',
    });

    const { result } = renderHook(() => useAuth());

    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      await result.current.login('test@example.com', 'password123');
    });

    expect(result.current.user).toEqual({ loggedIn: true });
    expect(mockAuthService.login).toHaveBeenCalledWith(expect.any(URLSearchParams));
  });

  it('должен выполнить регистрацию и установить пользователя', async () => {
    mockAuthService.getToken.mockReturnValue(null);
    mockAuthService.register.mockResolvedValue({
      access_token: 'test-token',
      token_type: 'bearer',
    });

    const { result } = renderHook(() => useAuth());

    await waitFor(() => expect(result.current.loading).toBe(false));

    const registerData = {
      email: 'newuser@example.com',
      password: 'password123',
      first_name: 'Test',
      surname_name: 'User',
      patronomic_name: 'Testovich',
      login: 'newuser',
      tg_username: 'newuser_tg',
    };

    await act(async () => {
      await result.current.register(registerData);
    });

    expect(result.current.user).toEqual({ loggedIn: true });
    expect(mockAuthService.register).toHaveBeenCalledWith(registerData);
  });

  it('должен выполнить выход и очистить пользователя', async () => {
    // Сначала логинимся
    mockAuthService.getToken.mockReturnValue('test-token');
    mockApi.get.mockResolvedValueOnce({ data: { loggedIn: true } });

    const { result } = renderHook(() => useAuth());

    // Ждём пока хук загрузит пользователя
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    expect(result.current.user).toEqual({ loggedIn: true });

    // Теперь выходим
    act(() => {
      result.current.logout();
    });

    expect(result.current.user).toBeNull();
    expect(mockAuthService.logout).toHaveBeenCalled();
  });

  it('должен обрабатывать ошибку при входе', async () => {
    mockAuthService.getToken.mockReturnValue(null);
    mockAuthService.login.mockRejectedValue(new Error('Login failed'));

    const { result } = renderHook(() => useAuth());

    await waitFor(() => expect(result.current.loading).toBe(false));

    await act(async () => {
      try {
        await result.current.login('test@example.com', 'wrongpassword');
      } catch (error) {
        expect(error).toBeDefined();
      }
    });

    expect(result.current.user).toBeNull();
  });
});