import { test, expect } from '@playwright/test';

test('DealBrief AI page loads', async ({ page }) => {
  await page.goto('http://localhost:5173/');
  await expect(page.locator('body')).toContainText('DealBrief');
});
