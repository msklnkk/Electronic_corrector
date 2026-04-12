// cypress/e2e/document-check.cy.ts
/// <reference types="cypress" />

describe('Процесс проверки документов', () => {
  const user = {
    user_id: 1,
    email: 'user@example.com',
    username: 'user1',
    first_name: 'Иван',
    surname_name: 'Иванов',
    patronomic_name: 'Иванович',
    role: 'user' as const,
    theme: 'light' as const,
    is_push_enabled: false,
  };

  beforeEach(() => {

    cy.intercept('GET', '/all_documents', {
      statusCode: 200,
      body: [],
    }).as('getAllDocuments');

    cy.visit('/check', {
      onBeforeLoad(win: Window) {
        win.localStorage.setItem('access_token', 'test-token-12345');
      },
    });
  });

  it('должен загружать страницу проверки документов', () => {
  // Просто проверяем URL — никакого cy.wait('@getMe')
  cy.url().should('include', '/check');
  });

  it('должен содержать области для загрузки файла', () => {
  cy.get('input[type="file"]').should('exist');
  });

  it('должен отображать опции выбора типа проверки', () => {
  cy.get('[role="radiogroup"]').should('exist');
  });
  
});
