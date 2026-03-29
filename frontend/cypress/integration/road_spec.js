describe('Road AI Dashboard', () => {
  it('loads dashboard page', () => {
    cy.visit('/');
    cy.contains('Smart Road AI - Fleet Dashboard');
  });
});
