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
  await expect(page.getByRole('heading', { name: 'Meeting Brief', exact: true })).toBeVisible();
  await expect(page.getByLabel('Customer').first()).toContainText('ABC Bank');

  await page.getByRole('button', { name: 'Customer Intelligence' }).click();
  await expect(page.getByRole('heading', { name: 'Customer Intelligence', exact: true })).toBeVisible();
  await expect(page.locator('.intelligence-section-header h2')).toHaveText([
    'Customer Overview',
    'Customer Engagement Timeline',
    'Next Best Action',
  ]);
  await expect(page.locator('.intelligence-section-header p')).toHaveText([
    'Latest customer profile, product usage, and account activity.',
    'Meeting history from generated briefs saved to the engagement log.',
    'Recommended follow-up actions based on usage and saved meeting history.',
  ]);
  await expect(page.getByText('Renewal Date', { exact: true })).toBeVisible();
  await expect(page.getByText('10/15/2026', { exact: true })).toBeVisible();
  await expect(page.getByText('Active Users', { exact: true })).toBeVisible();
  await expect(page.getByText('410', { exact: true })).toBeVisible();
  await expect(page.getByText('Renewal Risk', { exact: true })).toHaveCount(0);
  await expect(page.getByText('Expansion Signal', { exact: true })).toHaveCount(0);

  await page.getByRole('button', { name: 'Data Management' }).click();
  await expect(page.getByRole('heading', { name: 'Data Management', exact: true })).toBeVisible();
  const customerTable = page.locator('details.table-panel').filter({
    has: page.getByRole('heading', { name: 'Manage Customers' }),
  });
  const usageTable = page.locator('details.table-panel').filter({
    has: page.getByRole('heading', { name: 'Manage Usage Data' }),
  });
  const engagementTable = page.locator('details.table-panel').filter({
    has: page.getByRole('heading', { name: 'Manage Engagement Log' }),
  });
  await expect(customerTable).not.toHaveAttribute('open', '');
  await expect(usageTable).not.toHaveAttribute('open', '');
  await expect(engagementTable).not.toHaveAttribute('open', '');

  await customerTable.locator('summary').click();
  await expect(customerTable.getByText('ABC Bank')).toBeVisible();

  await usageTable.locator('summary').click();
  await expect(usageTable.getByText('CRM Platform').first()).toBeVisible();

  await engagementTable.locator('summary').click();
  await expect(engagementTable).toHaveAttribute('open', '');
});
