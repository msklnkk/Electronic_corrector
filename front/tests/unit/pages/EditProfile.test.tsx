// tests/unit/pages/EditProfile.test.tsx
import { render, screen, waitFor } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { MemoryRouter } from 'react-router-dom';

import EditProfilePage from '../../../src/pages/EditProfile';
import { api } from '../../../src/api';
import type { UserProfile } from '../../../src/types';

jest.mock('../../../src/api', () => ({
  api: {
    get: jest.fn(),
    put: jest.fn(),
  },
}));

jest.setTimeout(15000);

const mockedApi = api as jest.Mocked<typeof api>;
const mockedNavigate = jest.fn();

jest.mock('react-router-dom', () => {
  const actual = jest.requireActual('react-router-dom');
  return {
    ...actual,
    useNavigate: () => mockedNavigate,
  };
});

describe('EditProfilePage', () => {
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
    mockedApi.put.mockReset();
  });

  it('loads user data and sends update request to /update_me', async () => {
    mockedApi.get.mockResolvedValueOnce({ data: user } as any);
    mockedApi.put.mockResolvedValueOnce({ data: {} } as any);

    render(
      <MemoryRouter>
        <EditProfilePage />
      </MemoryRouter>
    );

    await waitFor(() => 
    expect(screen.getByRole('heading', { name: /редактирование профиля/i }))
      .toBeInTheDocument()
    );

    await waitFor(() => {
    expect(screen.getByDisplayValue('Иван')).toBeInTheDocument();
    });

    const emailInput = screen.getByLabelText(/email/i) as HTMLInputElement;
    const passwordInput = screen.getByLabelText(/пароль.*для обновления/i) as HTMLInputElement;

    await userEvent.clear(emailInput);
    await userEvent.type(emailInput, 'newuser@example.com');
    await userEvent.type(passwordInput, 'newPassword123');

    const saveButton = screen.getByRole('button', { name: /сохранить/i });
    await waitFor(() => {
        expect(saveButton).not.toBeDisabled();
    });

    await userEvent.click(saveButton);

    await waitFor(() => expect(mockedApi.put).toHaveBeenCalledTimes(1), {
    timeout: 3000
    });

    expect(mockedApi.put).toHaveBeenCalledWith(
        '/update_user/1',
        expect.objectContaining({
          email: 'newuser@example.com',
          password: 'newPassword123',
  })
);

    expect(mockedNavigate).toHaveBeenCalledWith('/profile');
});
});
