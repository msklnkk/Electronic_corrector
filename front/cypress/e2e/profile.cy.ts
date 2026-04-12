// cypress/e2e/profile.cy.ts
describe('Profile / Edit profile flow', () => {
  const user = {
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
    cy.intercept('GET', '/me', {
      statusCode: 200,
      body: user,
    }).as('getMe');

    cy.intercept('GET', '/all_checks', {
      statusCode: 200,
      body: [],
    }).as('getChecks');

    cy.visit('/profile', {
      onBeforeLoad(win) {
        win.localStorage.setItem('access_token', 'token');
      },
    });
  });

  it('opens edit page from profile page', () => {
    cy.contains('Редактировать профиль').click();
    cy.url().should('include', '/profile/edit');
    cy.contains('Редактирование профиля').should('be.visible');
  });
});
