// tests/unit/components/common/Header.test.tsx
import React from 'react';
import { render, screen, fireEvent } from '@testing-library/react';
import { MemoryRouter } from 'react-router-dom';
import Header from '../../../../src/components/common/Header';
import { AuthService } from '../../../../src/services/auth.service';

jest.mock('../../../../src/services/auth.service');

const mockedAuthService = AuthService as jest.Mocked<typeof AuthService>;

const renderHeader = (mode: 'light' | 'dark' = 'light') => {
  const onThemeToggle = jest.fn();
  return {
    ...render(
      <MemoryRouter>
        <Header mode={mode} onThemeToggle={onThemeToggle} />
      </MemoryRouter>
    ),
    onThemeToggle,
  };
};

describe('Header', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    localStorage.clear();
    mockedAuthService.getToken.mockReturnValue(null);
    mockedAuthService.getCurrentUser.mockReturnValue(null);
  });

  it('должен рендерить логотип', () => {
    renderHeader();
    expect(screen.getByAltText('Логотип')).toBeInTheDocument();
  });

  it('должен содержать кнопку Главная', () => {
    renderHeader();
    expect(screen.getByRole('button', { name: /главная/i })).toBeInTheDocument();
  });

  it('должен содержать кнопку входа когда пользователь не авторизован', () => {
    mockedAuthService.getToken.mockReturnValue(null);
    renderHeader();
    expect(screen.getByRole('button', { name: /войти/i })).toBeInTheDocument();
  });

  it('должен переключать тему при клике на кнопку темы', () => {
    const { onThemeToggle } = renderHeader('light');
    
    const themeButtons = screen.getAllByRole('button');
    const themeButton = themeButtons[0] as HTMLElement;
    
    fireEvent.click(themeButton);
    expect(onThemeToggle).toHaveBeenCalled();
  });

  it('должен рендерить в светлом режиме', () => {
    renderHeader('light');
    expect(screen.getByAltText('Логотип')).toBeInTheDocument();
  });

  it('должен рендерить в тёмном режиме', () => {
    renderHeader('dark');
    expect(screen.getByAltText('Логотип')).toBeInTheDocument();
  });

  it('должен содержать кнопку "Проверить документ"', () => {
    renderHeader();
    expect(screen.getByRole('button', { name: /проверить документ/i })).toBeInTheDocument();
  });
});