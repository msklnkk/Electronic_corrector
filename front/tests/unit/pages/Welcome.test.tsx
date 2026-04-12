// tests/unit/pages/Welcome.test.tsx
import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import Welcome from '../../../src/pages/Welcome';

const renderWelcome = () => {
  return render(
    <BrowserRouter>
      <Welcome />
    </BrowserRouter>
  );
};

describe('Welcome page', () => {
  it('должен рендерить приветственную страницу с основным заголовком', () => {
    renderWelcome();

    expect(screen.getByText(/загрузите файл и получите отчёт об ошибках оформления/i)).toBeInTheDocument();
  });

  it('должен содержать описание приложения', () => {
    renderWelcome();

    expect(screen.getByText(/современная система проверки документов/i)).toBeInTheDocument();
  });

  it('должен иметь кнопку для начала работы', () => {
    renderWelcome();

    expect(screen.getByRole('button', { name: /попробовать бесплатно/i })).toBeInTheDocument();
  });
});