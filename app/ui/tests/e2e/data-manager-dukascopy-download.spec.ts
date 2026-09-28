import { expect, test } from '@playwright/test';

test('unqualified Dukascopy modes do not create mock progress or coverage', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Data Manager', exact: true }).click();
  await page.getByRole('checkbox', { name: 'Select EURUSD', exact: true }).check();
  await page.getByRole('button', { name: 'Dukascopy data', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Download data for existing symbol', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: /Download Dukascopy data for/ });
  await expect(dialog.getByRole('radio', { name: 'Standard download - Dukascopy servers' })).toBeChecked();
  await expect(dialog.getByRole('radio', { name: /StrategyQuant CDN/ })).toBeDisabled();
  await expect(dialog.getByRole('radio', { name: /StrategyQuant Hong Kong CDN/ })).toBeDisabled();
  await expect(dialog.getByRole('button', { name: 'Start download' })).toBeDisabled();
  await expect(dialog.getByText('Downloads are unavailable until the market catalog is provisioned.')).toBeVisible();
  expect(await page.evaluate(() => localStorage.getItem('sqx-data-download-v1'))).toBeNull();
});
