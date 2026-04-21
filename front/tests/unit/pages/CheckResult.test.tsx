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

  it('должен масштабировать score и показывать список рекомендаций для кастомной проверки', async () => {
    render(
      <SnackbarProvider maxSnack={3}>
        <MemoryRouter
          initialEntries={[
            {
              pathname: '/gost-check/result/777',
              state: {
                resultType: 'semantic',
                semanticResult: {
                  document_id: 777,
                  filename: 'custom.docx',
                  overall_score: 0.7,
                  status: 'completed',
                  findings: [
                    { severity: 'critical', message: 'Исправить структуру разделов' },
                    { severity: 'warning', message: 'Уточнить формат таблиц' },
                  ],
                },
              },
            },
          ]}
        >
          <Routes>
            <Route path="/gost-check/result/:id" element={<CheckResult />} />
          </Routes>
        </MemoryRouter>
      </SnackbarProvider>
    );

    expect(await screen.findByText(/Соответствие custom-правилам: 7\.0\/10 \(70%\)/i)).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Рекомендации по исправлению/i })).toBeInTheDocument();
    expect(screen.getByText(/Исправить структуру разделов/i)).toBeInTheDocument();
    expect(screen.getByRole('heading', { name: /Общие советы/i })).toBeInTheDocument();
  });
});