// tests/unit/pages/CheckDocument.test.tsx
import React from 'react';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import userEvent from '@testing-library/user-event';
import CheckDocument from '../../../src/pages/CheckDocument';
import { ProtectedRoute } from '../../../src/components/auth';
import { useAuth } from '../../../src/hooks/useAuth';

jest.mock('../../../src/hooks/useAuth');

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

const renderCheckDocument = () => {
  mockUseAuth.mockReturnValue({
    user: { loggedIn: true },
    loading: false,
    login: jest.fn(),
    register: jest.fn(),
    logout: jest.fn(),
  });

  return render(
    <BrowserRouter>
      <ProtectedRoute>
        <CheckDocument />
      </ProtectedRoute>
    </BrowserRouter>
  );
};

describe('CheckDocument page', () => {
  beforeEach(() => {
    jest.clearAllMocks();
  });

  it('должен рендерить страницу проверки документов с инструкцией загрузки', () => {
    renderCheckDocument();
    expect(screen.getByText(/перетащите pdf или docx/i)).toBeInTheDocument();
  });

  it('должен содержать область для загрузки файла с кнопкой выбора', () => {
    renderCheckDocument();
    expect(screen.getByRole('button', { name: /выбрать файл/i })).toBeInTheDocument();
  });

  it('должен иметь кнопку для проверки документа', () => {
    renderCheckDocument();
    expect(screen.getByRole('button', { name: /начать проверку/i })).toBeInTheDocument();
  });

  it('кнопка проверки должна быть отключена без файла', () => {
    renderCheckDocument();
    const startButton = screen.getByRole('button', { name: /начать проверку/i });
    expect(startButton).toBeDisabled();
  });

  it('должен содержать опции для типов проверки', () => {
    renderCheckDocument();
    expect(screen.getByText(/гост/i)).toBeInTheDocument();
    expect(screen.getByText(/внутренний стандарт/i)).toBeInTheDocument();
  });

  it('должен содержать пример отчёта', () => {
    renderCheckDocument();
    expect(screen.getByText(/пример отчёта/i)).toBeInTheDocument();
  });
});