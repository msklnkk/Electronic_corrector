// tests/unit/components/auth/LoginForm.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor, within } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { BrowserRouter } from 'react-router-dom';
import { LoginForm } from '../../../../src/components/auth/LoginForm';
import { useAuth } from '../../../../src/hooks/useAuth';
import { api } from '../../../../src/api';
import { AuthService } from '../../../../src/services/auth.service';
import type { IToken } from '../../../../src/types/auth.types';

jest.mock('../../../../src/hooks/useAuth');
jest.mock('../../../../src/api');
jest.mock('../../../../src/services/auth.service');

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;
const mockApi = api as jest.Mocked<typeof api>;
const mockAuthService = AuthService as jest.Mocked<typeof AuthService>;

const renderLoginForm = (onSuccess?: jest.Mock) => {
  return render(
    <BrowserRouter>
      <LoginForm onSuccess={onSuccess} />
    </BrowserRouter>
  );
};

describe('LoginForm', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    mockUseAuth.mockReturnValue({
      user: null,
      loading: false,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
    } as any);
  });

  describe('Form rendering', () => {
    it('должен отображать форму входа по умолчанию', () => {
      renderLoginForm();

      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/пароль/i)).toBeInTheDocument();
      expect(screen.getByRole('button', { name: /войти/i })).toBeInTheDocument();
    });

    it('должен переключаться на форму регистрации при нажатии на ссылку', () => {
      renderLoginForm();

      const registerLink = screen.getByRole('button', { name: /зарегистрироваться/i });
      fireEvent.click(registerLink);

      expect(screen.getByLabelText(/имя/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/фамилия/i)).toBeInTheDocument();
      expect(screen.getByLabelText(/email/i)).toBeInTheDocument();
    });
  });

  describe('Login', () => {
    it('должен отправить форму входа с корректными данными', async () => {
      const mockLogin = jest.fn();
      mockUseAuth.mockReturnValue({
        user: null,
        loading: false,
        login: mockLogin,
        register: jest.fn(),
        logout: jest.fn(),
      } as any);

      mockApi.get.mockResolvedValue({
        data: { user_id: 1, email: 'test@example.com' },
      } as any);

      const onSuccess = jest.fn();
      renderLoginForm(onSuccess);

      const emailInput = screen.getByLabelText(/email/i) as HTMLInputElement;
      const passwordInput = screen.getByLabelText(/пароль/i) as HTMLInputElement;
      const submitButton = screen.getByRole('button', { name: /войти/i });

      await userEvent.type(emailInput, 'test@example.com');
      await userEvent.type(passwordInput, 'password123');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockLogin).toHaveBeenCalledWith('test@example.com', 'password123');
      });
    });

    it('должен показать сообщение об ошибке при неудачном входе', async () => {
      const mockLogin = jest.fn().mockRejectedValue({
        response: {
          data: { detail: 'Неверные учетные данные' },
        },
      });

      mockUseAuth.mockReturnValue({
        user: null,
        loading: false,
        login: mockLogin,
        register: jest.fn(),
        logout: jest.fn(),
      } as any);

      renderLoginForm();

      const emailInput = screen.getByLabelText(/email/i) as HTMLInputElement;
      const passwordInput = screen.getByLabelText(/пароль/i) as HTMLInputElement;
      const submitButton = screen.getByRole('button', { name: /войти/i });

      await userEvent.type(emailInput, 'test@example.com');
      await userEvent.type(passwordInput, 'wrongpassword');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(screen.getByText(/неверные учетные данные/i)).toBeInTheDocument();
      });
    });
  });

  describe('Register', () => {
    it('должен отправить форму регистрации с корректными данными', async () => {
      const mockRegister = jest.fn();
      mockUseAuth.mockReturnValue({
        user: null,
        loading: false,
        login: jest.fn(),
        register: mockRegister,
        logout: jest.fn(),
      } as any);

      mockApi.get.mockResolvedValue({
        data: { user_id: 1, email: 'newuser@example.com' },
      } as any);

      mockAuthService.register.mockResolvedValue({
        access_token: 'test-token',
        token_type: 'bearer'
      });

      const onSuccess = jest.fn();
      renderLoginForm(onSuccess);

      const registerLink = screen.getByRole('button', { name: /зарегистрироваться/i });
      fireEvent.click(registerLink);

      const firstNameInput = screen.getByLabelText(/имя/i) as HTMLInputElement;
      const surnameInput = screen.getByLabelText(/фамилия/i) as HTMLInputElement;
      const emailInput = screen.getByLabelText(/email/i) as HTMLInputElement;
      const passwordInput = screen.getByLabelText(/пароль/i) as HTMLInputElement;
      const submitButton = screen.getByRole('button', { name: /зарегистрироваться/i });

      await userEvent.type(firstNameInput, 'Иван');
      await userEvent.type(surnameInput, 'Иванов');
      await userEvent.type(emailInput, 'ivan@example.com');
      await userEvent.type(passwordInput, 'password123');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(mockAuthService.register).toHaveBeenCalledWith(
          expect.objectContaining({
            first_name: 'Иван',
            surname_name: 'Иванов',
            login: 'ivan@example.com',
            password: 'password123',
          })
        );
      });
    });
  });

  describe('onSuccess callback', () => {
    it('должен вызвать onSuccess callback после успешного входа', async () => {
      const mockLogin = jest.fn().mockResolvedValue(undefined);
      mockUseAuth.mockReturnValue({
        user: null,
        loading: false,
        login: mockLogin,
        register: jest.fn(),
        logout: jest.fn(),
      } as any);

      mockApi.get.mockResolvedValue({
        data: { user_id: 1, email: 'test@example.com' },
      } as any);

      const onSuccess = jest.fn();
      renderLoginForm(onSuccess);

      const emailInput = screen.getByLabelText(/email/i) as HTMLInputElement;
      const passwordInput = screen.getByLabelText(/пароль/i) as HTMLInputElement;
      const submitButton = screen.getByRole('button', { name: /войти/i });

      await userEvent.type(emailInput, 'test@example.com');
      await userEvent.type(passwordInput, 'password123');
      fireEvent.click(submitButton);

      await waitFor(() => {
        expect(onSuccess).toHaveBeenCalled();
      });
    });
  });
});
