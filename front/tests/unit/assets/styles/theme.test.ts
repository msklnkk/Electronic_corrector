// tests/unit/assets/styles/theme.test.ts
import { createAppTheme } from '../../../../src/assets/styles/theme';

describe('Theme', () => {
  it('должен создавать светлую тему', () => {
    const theme = createAppTheme('light');
    expect(theme.palette.mode).toBe('light');
    expect(theme.palette.primary.main).toBe('#7c3aed');
  });

  it('должен создавать тёмную тему', () => {
    const theme = createAppTheme('dark');
    expect(theme.palette.mode).toBe('dark');
    expect(theme.palette.primary.main).toBe('#8b5cf6');
  });

  it('светлая тема имеет правильные цвета', () => {
    const theme = createAppTheme('light');
    expect(theme.palette.background.default).toBe('#f8fafc');
    expect(theme.palette.text.primary).toBe('#1e293b');
  });

  it('тёмная тема имеет правильные цвета', () => {
    const theme = createAppTheme('dark');
    expect(theme.palette.background.default).toBe('#0E1018');
    expect(theme.palette.text.primary).toBe('#ffffff');
  });

  it('должен иметь все необходимые цветовые переменные', () => {
    const theme = createAppTheme('light');
    expect(theme.palette.secondary).toBeDefined();
    expect(theme.palette.success).toBeDefined();
    expect(theme.palette.error).toBeDefined();
    expect(theme.palette.warning).toBeDefined();
  });
});
