import { test, expect } from '@playwright/test';

test('DealBrief AI page loads', async ({ page }) => {
  const customersResponse = page.waitForResponse(
    (response) =>
      response.url().includes('/api/customers') &&
      response.request().method() === 'GET' &&
      response.status() === 200,
  );
  await page.goto('http://localhost:5173/');
  await customersResponse;
  await expect(page.getByRole('heading', { name: 'DealBrief AI' })).toBeVisible();
  await expect(page.getByLabel('Customer').first()).toContainText('ABC Bank');

  await page.getByRole('button', { name: 'Admin Data Management' }).click();
  const customerTable = page.locator('section.table-panel').filter({
    has: page.getByRole('heading', { name: 'Manage Customers' }),
  });
  const usageTable = page.locator('section.table-panel').filter({
    has: page.getByRole('heading', { name: 'Manage Usage Data' }),
  });
  await expect(customerTable).toContainText('ABC Bank');
  await expect(usageTable).toContainText('CRM Platform');
});
