// tests/unit/components/common/GlobalLoader.test.tsx
import React from 'react';
import { render, screen } from '@testing-library/react';
import { GlobalLoader } from '../../../../src/components/common/GlobalLoader';

describe('GlobalLoader', () => {
  it('должен рендерить загрузчик когда open=true', () => {
    render(<GlobalLoader open={true} />);

    expect(screen.getByRole('progressbar', { hidden: true })).toBeInTheDocument();
  });

  it('должен рендерить сообщение если передано', () => {
    render(<GlobalLoader open={true} message='Загрузка данных' />);

    expect(screen.getByText('Загрузка данных')).toBeInTheDocument();
  });
});