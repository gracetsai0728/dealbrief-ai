import { test, expect } from '@playwright/test';

test('DealBrief AI page loads', async ({ page }) => {
  await page.goto('http://localhost:5173/');
  await page.getByLabel('Email').fill('admin@dealbrief.ai');
  await page.getByLabel('Password').fill('Admin123!');
  const customersResponse = page.waitForResponse(
    (response) =>
      response.url().includes('/api/customers') &&
      response.request().method() === 'GET' &&
      response.status() === 200,
  );
  await page.getByRole('button', { name: 'Sign In' }).click();
  await customersResponse;
  await expect(page.getByRole('heading', { name: 'DealBrief AI' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Add Data' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Manage Data' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Meeting Brief' })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Customer Intelligence' })).toHaveCount(0);
  await expect(page.getByRole('heading', { name: 'Admin Data Management', exact: true })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Add Customer' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Add Product' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Add Subscription' })).toBeVisible();
  await expect(page.getByLabel('Opportunity Stage')).toHaveCount(0);
  await expect(page.getByLabel('Renewal Date')).toHaveCount(0);
  await expect(page.getByText('Salesforce Account ID')).toHaveCount(0);
  await expect(page.getByText('Account Owner')).toHaveCount(0);
  await expect(page.getByLabel('Snapshot Date')).toHaveCount(0);
  await expect(page.getByLabel('Active Users')).toHaveCount(0);
  await expect(page.getByLabel('License Utilization (%)')).toHaveCount(0);
  await expect(page.getByLabel('Licensed Seats')).toBeVisible();
  const adminSelectBackgrounds = await page.locator('select').evaluateAll(
    (selects) => selects.map((select) => getComputedStyle(select).backgroundColor),
  );
  expect(adminSelectBackgrounds.every((color) => color === 'rgb(239, 246, 255)')).toBeTruthy();
  await expect(page.getByRole('heading', { name: 'Manage Customers' })).toHaveCount(0);

  await page.getByRole('button', { name: 'Manage Data' }).click();
  await expect(page.getByRole('heading', { name: 'Add Customer' })).toHaveCount(0);
  const customerTable = page.locator('details.table-panel').filter({
    has: page.getByRole('heading', { name: 'Manage Customers' }),
  });
  const subscriptionTable = page.locator('details.table-panel').filter({
    has: page.getByRole('heading', { name: 'Manage Subscriptions' }),
  });
  await expect(customerTable).not.toHaveAttribute('open', '');
  await expect(subscriptionTable).not.toHaveAttribute('open', '');
  await expect(page.getByRole('heading', { name: 'Manage Engagement Log' })).toHaveCount(0);

  await customerTable.locator('summary').click();
  await expect(customerTable.getByText('ABC Bank')).toBeVisible();

  await subscriptionTable.locator('summary').click();
  await expect(subscriptionTable.getByText('CRM Platform').first()).toBeVisible();

  await page.getByRole('button', { name: 'Sign Out' }).click();
  await page.getByLabel('Email').fill('user@dealbrief.ai');
  await page.getByLabel('Password').fill('User123!');
  await page.getByRole('button', { name: 'Sign In' }).click();

  await expect(page.getByRole('button', { name: 'Subscription' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Intelligence', exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Meeting Brief' })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Add Data' })).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Manage Data' })).toHaveCount(0);
  await expect(page.getByRole('heading', { name: 'Subscription', exact: true })).toBeVisible();
  await expect(page.locator('.timeline-panel select')).toHaveCSS('background-color', 'rgb(239, 246, 255)');
  const subscriptionCustomerSelect = page.locator('.timeline-panel .centered-customer-select');
  await expect(subscriptionCustomerSelect).toBeVisible();
  const subscriptionCustomerSelectBox = await subscriptionCustomerSelect.boundingBox();
  expect(subscriptionCustomerSelectBox.width).toBeLessThanOrEqual(360);
  const firstSubscriptionCard = page.locator('.subscription-summary-card').first();
  const subscriptionChart = page.getByRole('img', { name: 'Licensed seats by product over time' });
  await expect(firstSubscriptionCard).toBeVisible();
  await expect(subscriptionChart).toBeVisible();
  const cardBox = await firstSubscriptionCard.boundingBox();
  const chartBox = await subscriptionChart.boundingBox();
  expect(cardBox.y).toBeLessThan(chartBox.y);

  await page.getByRole('button', { name: 'Intelligence', exact: true }).click();
  const intelligenceControls = page.locator('.intelligence-controls');
  const intelligenceSignal = page.locator('.intelligence-signal');
  const intelligenceCustomerSelect = intelligenceControls.locator('.centered-customer-select');
  const refreshIntelligenceButton = intelligenceControls.getByRole('button', { name: 'Refresh Intelligence' });
  await expect(intelligenceControls).toBeVisible();
  await expect(intelligenceSignal).toBeVisible();
  await expect(intelligenceSignal).toHaveCSS('background-color', 'rgb(51, 65, 85)');
  await expect(intelligenceSignal.locator('span')).toHaveCSS('color', 'rgb(191, 219, 254)');
  await expect(intelligenceSignal.locator('strong')).toHaveCount(0);
  await expect(intelligenceSignal.getByText(/licensed seats across/i)).toHaveCount(0);
  await expect(refreshIntelligenceButton).toBeVisible();
  const signalBox = await intelligenceSignal.boundingBox();
  const intelligenceSelectBox = await intelligenceCustomerSelect.boundingBox();
  const refreshButtonBox = await refreshIntelligenceButton.boundingBox();
  expect(intelligenceSelectBox.width).toBeLessThanOrEqual(360);
  expect(Math.abs(
    intelligenceSelectBox.width - subscriptionCustomerSelectBox.width,
  )).toBeLessThan(1);
  expect(refreshButtonBox.x).toBeGreaterThan(
    intelligenceSelectBox.x + intelligenceSelectBox.width,
  );
  expect(Math.abs(
    refreshButtonBox.y + refreshButtonBox.height
      - (intelligenceSelectBox.y + intelligenceSelectBox.height),
  )).toBeLessThan(2);
  expect(refreshButtonBox.y + refreshButtonBox.height).toBeLessThan(signalBox.y);
  await expect(page.getByRole('heading', { name: 'Industry Dynamics' })).toBeVisible();
  const industrySection = page.locator('.intelligence-block').first();
  await expect(industrySection.locator('.intelligence-signal')).toHaveCount(1);
  await expect(industrySection.locator('.insight-card')).toHaveCount(2);
  const industryGridBox = await industrySection.locator('.intelligence-card-grid').boundingBox();
  expect(Math.abs(signalBox.x - industryGridBox.x)).toBeLessThan(1);
  expect(Math.abs(signalBox.width - industryGridBox.width)).toBeLessThan(1);
  const firstIndustryCardBox = await industrySection.locator('.insight-card').first().boundingBox();
  expect(signalBox.y).toBeLessThan(firstIndustryCardBox.y);
  await expect(page.getByRole('heading', { name: 'Recent Company News' })).toBeVisible();
  const newsSection = page.locator('.intelligence-block').nth(1);
  await expect(newsSection.locator('.news-card')).toHaveCount(2);
  await expect(newsSection.locator('.news-card a')).toHaveCount(0);
  await expect(newsSection.getByText('Demo Newswire (Mock)', { exact: false })).toHaveCount(0);
  await expect(page.getByRole('heading', { name: 'Recommended Next Steps' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Cross-sell' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Upsell' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Renewal' })).toBeVisible();
  await expect(page.getByRole('heading', { name: 'Winback' })).toBeVisible();
});
