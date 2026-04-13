// tests/unit/pages/CheckResult.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import { MemoryRouter, Routes, Route } from 'react-router-dom';
import { SnackbarProvider } from 'notistack';
import CheckResult from '../../../src/pages/CheckResult';
import { api } from '../../../src/api';

jest.mock('../../../src/api', () => ({
  api: {
    get: jest.fn(),
  },
}));

const mockedApi = api as jest.Mocked<typeof api>;

const renderCheckResult = (checkId: string = '123') => {
  return render(
    <SnackbarProvider maxSnack={3}>
      <MemoryRouter initialEntries={[`/gost-check/result/${checkId}`]}>
        <Routes>
          <Route path="/gost-check/result/:id" element={<CheckResult />} />
        </Routes>
      </MemoryRouter>
    </SnackbarProvider>
  );
};

describe('CheckResult page', () => {
  beforeEach(() => {
    localStorage.clear();
    jest.clearAllMocks();
  });

  it('должен показывать ошибку при отсутствии ID', async () => {
  render(
    <SnackbarProvider maxSnack={3}>
      <MemoryRouter initialEntries={["/gost-check/result/"]}>
        <Routes>
          <Route path="/gost-check/result/" element={<CheckResult />} />
          <Route path="/gost-check/result/:id" element={<CheckResult />} />
        </Routes>
      </MemoryRouter>
    </SnackbarProvider>
  );

  expect(screen.getByRole('heading', { name: /id проверки не найден/i })).toBeInTheDocument();
});

  it('должен загружать и отображать результаты проверки', async () => {
    const mockResult = {
      check_id: '123',
      document_id: '456',
      status: 'completed',
      total_checks: 10,
      passed_checks: 8,
      errors: [],
      checked_at: '2024-01-01T10:00:00'
    };

    mockedApi.get.mockResolvedValue({ data: mockResult });

    renderCheckResult('123');

    await waitFor(() => {
      expect(mockedApi.get).toHaveBeenCalled();
    });
  });
});