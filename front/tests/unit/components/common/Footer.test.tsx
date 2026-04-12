// tests/unit/components/common/Footer.test.tsx
import React from 'react';
import { render, screen } from '@testing-library/react';
import Footer from '../../../../src/components/common/Footer';

describe('Footer', () => {
  it('должен рендерить footer с названием', () => {
    render(<Footer />);

    expect(screen.getAllByText(/электронный корректор/i)[0]).toBeInTheDocument();
  });

  it('должен содержать ссылку на Telegram', () => {
    render(<Footer />);

    const telegramLink = screen.getByRole('link', { name: /telegram/i });
    expect(telegramLink).toHaveAttribute('href', 'https://t.me/electronic_corrector');
  });
});