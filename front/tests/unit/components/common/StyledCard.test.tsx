// tests/unit/components/common/StyledCard.test.tsx
import React from 'react';
import { render, screen } from '@testing-library/react';
import { StyledCard } from '../../../../src/components/common/StyledCard';

describe('StyledCard', () => {
  it('должен рендерить содержимое', () => {
    render(
      <StyledCard>
        <h1>Test Content</h1>
      </StyledCard>
    );

    expect(screen.getByText('Test Content')).toBeInTheDocument();
  });

  it('должен рендерить карточку с текстом', () => {
    render(
      <StyledCard>
        <div>Test</div>
      </StyledCard>
    );

    expect(screen.getByText('Test')).toBeInTheDocument();
  });
});