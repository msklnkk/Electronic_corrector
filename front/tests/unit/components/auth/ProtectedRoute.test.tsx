// tests/unit/components/auth/ProtectedRoute.test.tsx
import React from 'react';
import { render, screen } from '@testing-library/react';
import { BrowserRouter } from 'react-router-dom';
import { ProtectedRoute } from '../../../../src/components/auth/ProtectedRoute';
import { useAuth } from '../../../../src/hooks/useAuth';
import { MemoryRouter, Routes, Route } from 'react-router-dom';

jest.mock('../../../../src/hooks/useAuth');

const mockUseAuth = useAuth as jest.MockedFunction<typeof useAuth>;

const TestComponent = () => <div>Protected Content</div>;

const renderProtectedRoute = (
  children: React.ReactNode = <TestComponent />,
  initialRoute = '/'
) => {
  return render(
    <MemoryRouter initialEntries={[initialRoute]}>
      <Routes>
        <Route
          path="/"
          element={<ProtectedRoute>{children}</ProtectedRoute>}
        />
        <Route path="/login" element={<div>Login Page</div>} />
      </Routes>
    </MemoryRouter>
  );
};

describe('ProtectedRoute', () => {
  beforeEach(() => {
    jest.clearAllMocks();
    // Дефолтное значение, чтобы не было undefined при инициализации
    mockUseAuth.mockReturnValue({
      user: null,
      loading: true,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
    });
  });

  it('должен рендерить содержимое для авторизованного пользователя', () => {
    mockUseAuth.mockReturnValue({
      user: { loggedIn: true },
      loading: false,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
    });

    renderProtectedRoute();

    expect(screen.getByText('Protected Content')).toBeInTheDocument();
  });

  it('должен показывать загрузчик при loading=true', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      loading: true,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
    });

    renderProtectedRoute();
    
    expect(screen.getByText(/загрузка/i)).toBeInTheDocument();
  });

  it('должен перенаправлять неавторизованного пользователя', () => {
    mockUseAuth.mockReturnValue({
      user: null,
      loading: false,
      login: jest.fn(),
      register: jest.fn(),
      logout: jest.fn(),
    });

    renderProtectedRoute();

    // Проверяем, что контент не отображается
    expect(screen.queryByText('Protected Content')).not.toBeInTheDocument();
  });
});