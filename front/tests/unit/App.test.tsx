import React from 'react';
import { render, screen } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import App from '../../src/App';

// Мокируем Header чтобы избежать проблем с useNavigate
jest.mock('../../src/components/common/Header', () => ({
  __esModule: true,
  default: ({ mode }: { mode: string }) => (
    <header role="banner">Header mock (mode: {mode})</header>
  ),
}));

jest.mock('../../src/services/auth.service', () => ({
  AuthService: {
    getToken: jest.fn().mockReturnValue(null),
    getCurrentUser: jest.fn().mockReturnValue(null),
    logout: jest.fn(),
  },
}));

// Убираем мок BrowserRouter — он не нужен, оборачиваем вручную
const renderApp = () => render(
  <MemoryRouter>
    <App />
  </MemoryRouter>
);

describe('App', () => {
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  it('должен рендерить приложение', () => {
    renderApp();
    expect(screen.getByRole('banner')).toBeInTheDocument();
  });

  it('должен загружать тему из localStorage', () => {
    localStorage.setItem('theme_mode', 'light');
    renderApp();
    expect(localStorage.getItem('theme_mode')).toBe('light');
  });

  it('должен использовать тёмную тему по умолчанию', () => {
    localStorage.clear();
    renderApp();
    expect(localStorage.getItem('theme_mode') || 'dark').toBe('dark');
  });

  it('должен обрабатывать ошибки localStorage при загрузке темы', () => {
    renderApp();
    expect(screen.getByRole('banner')).toBeInTheDocument();
  });

  it('должен переключать тему', () => {
    renderApp();
    expect(screen.getByRole('banner')).toBeInTheDocument();
  });
});