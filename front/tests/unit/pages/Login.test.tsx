// tests/unit/pages/Login.test.tsx
import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Login from '../../../src/pages/Login';

const renderLogin = () => {
  return render(
    <BrowserRouter>
      <Login />
    </BrowserRouter>
  );
};

describe('Login page', () => {
  it('должен рендерить страницу входа', () => {
    renderLogin();

    expect(screen.getByRole('heading', { name: /вход в аккаунт/i, level: 1 })).toBeInTheDocument();
  });

  it('должен содержать компонент LoginForm', () => {
    renderLogin();

    // Проверяем, что форма входа присутствует
    expect(screen.getByRole('textbox', { name: /email/i })).toBeInTheDocument();
    expect(screen.getByLabelText(/пароль/i)).toBeInTheDocument();
  });

  it('должен иметь ссылку на регистрацию', () => {
    renderLogin();

    expect(screen.getByText(/зарегистрироваться/i)).toBeInTheDocument();
  });
});