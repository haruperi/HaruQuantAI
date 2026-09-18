import { expect, test } from '@playwright/test';

test('research settings persist and linked results navigate', async ({ page }) => {
  await page.goto('/');
  await expect(page.getByText('Builder', { exact: true }).first()).toBeVisible();
  await page.getByRole('button', { name: 'Full settings' }).click();
  await page.getByLabel('Maximum conditions').fill('7');
  await page.getByRole('button', { name: 'Results', exact: true }).click();
  await page.getByRole('button', { name: 'Trade list' }).click();
  await expect(page.getByRole('columnheader', { name: 'Profit/Loss' })).toBeVisible();
  await page.reload();
  await page.getByRole('button', { name: 'Full settings' }).click();
  await expect(page.getByLabel('Maximum conditions')).toHaveValue('7');
});

test('copy dialog preserves source semantics', async ({ page }) => {
  await page.goto('/');
  await page.locator('.grid-row input[type="checkbox"]').first().check();
  await page.getByRole('button', { name: 'Move / copy' }).click();
  await expect(page.getByText('remain in the source databank')).toBeVisible();
  await page.getByRole('button', { name: 'Copy', exact: true }).click();
  await page.getByTitle('Notifications').click();
  await expect(page.getByText(/Copied strategies/)).toBeVisible();
});
