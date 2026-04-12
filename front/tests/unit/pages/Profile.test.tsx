// tests/unit/pages/Profile.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';

import Profile from '../../../src/pages/Profile';
import { api } from '../../../src/api';
import type { UserProfile } from '../../../src/types';

jest.mock('../../../src/api', () => ({
  api: {
    get: jest.fn(),
  },
}));

const mockedApi = api as jest.Mocked<typeof api>;
const mockedNavigate = jest.fn();

jest.mock('react-router-dom', () => {
  const actual = jest.requireActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockedNavigate,
  };
});

describe('Profile page', () => {
  const user: UserProfile = {
    user_id: 1,
    email: 'user@example.com',
    username: 'user1',
    first_name: 'Иван',
    surname_name: 'Иванов',
    patronomic_name: 'Иванович',
    role: 'user',
    theme: 'light',
    is_push_enabled: false,
  };

  beforeEach(() => {
    localStorage.clear();
    localStorage.setItem('access_token', 'token');
    mockedNavigate.mockReset();
    mockedApi.get.mockReset();
  });

  it('renders profile data and navigates to edit page', async () => {
    mockedApi.get.mockImplementation((url: string) => {
      if (url === '/me') {
        return Promise.resolve({ data: user } as any);
      }

      if (url === '/all_checks') {
        return Promise.resolve({ data: [] } as any);
      }

      return Promise.resolve({ data: {} } as any);
    });

    render(
      <MemoryRouter>
        <Profile />
      </MemoryRouter>
    );

    await waitFor(() => {
    const emailElements = screen.getAllByText(user.email);
    expect(emailElements.length).toBeGreaterThan(0);
    });

    expect(screen.getByText(/администратор|пользователь/i)).toBeInTheDocument();
    const editButton = screen.getByRole('button', { name: /редактировать профиль/i });
    await userEvent.click(editButton);

    await waitFor(() => {
      expect(mockedNavigate).toHaveBeenCalledWith('/profile/edit');
    });
  });
});
