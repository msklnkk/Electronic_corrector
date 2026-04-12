// tests/unit/types/index.test.ts
// Тест просто проверяет что все типы были успешно экспортированы
describe('Types', () => {
  it('должен экспортировать auth типы', () => {
    const types = require('../../../src/types/index.ts');
    expect(types).toBeDefined();
  });

  it('должен экспортировать auth и user типы', async () => {
    const authTypes = await import('../../../src/types/auth.types');
    const userTypes = await import('../../../src/types/user.types');
    
    expect(authTypes).toBeDefined();
    expect(userTypes).toBeDefined();
  });
});
