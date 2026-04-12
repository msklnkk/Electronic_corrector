// tests/unit/hooks/useAverageCheckTime.test.tsx
import { renderHook, waitFor } from '@testing-library/react';
import { useAverageCheckTime } from '../../../src/hooks/useAverageCheckTime';

describe('useAverageCheckTime', () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it('returns default values when localStorage is empty', async () => {
    const { result } = renderHook(() => useAverageCheckTime(1));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.averageTime).toBeNull();
    expect(result.current.totalChecks).toBe(0);
    expect(result.current.averageTimeFormatted).toBe('-');
  });

  it('calculates average time and total checks from stored values', async () => {
    localStorage.setItem('checkAnalysisTimes', JSON.stringify({
      101: 1.2,
      102: 2.8,
      103: 0.4,
    }));

    const { result } = renderHook(() => useAverageCheckTime(1));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.totalChecks).toBe(3);
    expect(result.current.averageTime).toBeCloseTo((1.2 + 2.8 + 0.4) / 3, 5);
    expect(result.current.averageTimeFormatted).toBe('1 сек');
  });

  it('ignores invalid values and returns default when no valid entries exist', async () => {
    localStorage.setItem('checkAnalysisTimes', JSON.stringify({
      a: "text",
      b: null,
      c: -5,
    }));

    const { result } = renderHook(() => useAverageCheckTime(1));

    await waitFor(() => expect(result.current.loading).toBe(false));

    expect(result.current.averageTime).toBeNull();
    expect(result.current.totalChecks).toBe(0);
    expect(result.current.averageTimeFormatted).toBe('-');
  });
});
