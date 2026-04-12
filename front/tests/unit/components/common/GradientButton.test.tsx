// tests/unit/components/common/GradientButton.test.tsx
import React from 'react';
import { render, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';
import { GradientButton } from '../../../../src/components/common/GradientButton';

describe('GradientButton', () => {
  it('должен рендерить текст кнопки', () => {
    render(<GradientButton>Click me</GradientButton>);

    expect(screen.getByText(/click me/i)).toBeInTheDocument();
  });

  it('должен вызывать onClick при клике', async () => {
    const handleClick = jest.fn();
    const user = userEvent.setup();

    render(<GradientButton onClick={handleClick}>Click me</GradientButton>);

    await user.click(screen.getByText(/click me/i));

    expect(handleClick).toHaveBeenCalledTimes(1);
  });

  it('должен рендерить с разными цветами', () => {
    render(<GradientButton color="cyan">Click me</GradientButton>);

    expect(screen.getByText(/click me/i)).toBeInTheDocument();
  });
});