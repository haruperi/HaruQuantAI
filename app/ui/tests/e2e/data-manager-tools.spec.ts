import { expect, test, type Page } from '@playwright/test';

async function launch(page: Page): Promise<void> {
  await page.goto('/');
  await page.getByRole('button', { name:'Data Manager', exact:true }).click();
  await page.getByRole('button', { name:'Tools', exact:true }).click();
}

test('matches Clone to timezone popup and runs through shared progress and status', async ({ page }) => {
  await launch(page);
  await page.getByRole('button', { name:'Clone to timezone', exact:true }).click();
  await expect(page.getByLabel('Data Manager progress')).toContainText('select some symbol', { ignoreCase:true });
  await page.getByLabel('Select EURUSD', { exact:true }).check();
  await page.getByRole('button', { name:'Clone to timezone', exact:true }).click();
  const dialog = page.getByRole('dialog', { name:"Clone to Timezone for 'EURUSD'", exact:true });
  await expect(dialog.getByText('Data settings', { exact:true })).toBeVisible();
  await expect(dialog.getByText('Cloned data timezone', { exact:true })).toBeVisible();
  await expect(dialog.getByLabel('Cloned data symbol postfix', { exact:true })).toHaveValue('_{timeframe}_{cloneTime}');
  await dialog.getByLabel('Fixed timezone shift', { exact:true }).fill('7');
  await dialog.getByRole('button', { name:'Proceed', exact:true }).click();
  await expect(page.getByLabel('Data Manager progress')).toContainText('Clone to timezone running');
  await page.getByRole('button', { name:'Pause all', exact:true }).click();
  await expect(page.getByLabel('Status for EURUSD', { exact:true })).toContainText('Paused');
  await page.getByRole('button', { name:'Resume all', exact:true }).click();
  await expect(page.getByLabel('Select EURUSD_M1_+7', { exact:true })).toBeVisible({ timeout:10000 });
  await expect(page.getByLabel('Status for EURUSD_M1_+7', { exact:true })).toHaveText('Completed');
  await page.getByLabel('Select EURUSD', { exact:true }).uncheck();
  await page.getByLabel('Select EURUSD_M1_+7', { exact:true }).check();
  await page.getByRole('button', { name:'Clone to timezone', exact:true }).click();
  await expect(page.getByLabel('Data Manager progress')).toContainText('cannot clone it again', { ignoreCase:true });
  await page.reload();
  await expect(page.getByLabel('Select EURUSD_M1_+7', { exact:true })).toBeVisible();
});

test('matches View and Analyze tabs, edits data, and persists saved changes', async ({ page }) => {
  await launch(page); await page.getByLabel('Select EURUSD', { exact:true }).check();
  await page.getByRole('button', { name:'View & Analyze', exact:true }).click();
  const dialog = page.getByRole('dialog', { name:"View data for 'EURUSD'", exact:true });
  await expect(dialog.locator('input[value="EURUSD"]').first()).toBeVisible();
  await expect(dialog.getByRole('tab', { name:'Data', exact:true })).toHaveAttribute('aria-selected','true');
  const firstRow = dialog.locator('.review-grid-scroll button').first(); await firstRow.click();
  await dialog.getByRole('button', { name:'Edit line', exact:true }).click();
  await dialog.getByLabel('Edit close', { exact:true }).fill('1.23456');
  await expect(dialog.getByText('Data contains unsaved changes', { exact:true })).toBeVisible();
  await dialog.getByRole('tab', { name:'Chart', exact:true }).click();
  await expect(dialog.getByLabel('Historical candlestick chart')).toBeVisible();
  await dialog.getByRole('tab', { name:'Analyze data quality', exact:true }).click();
  await expect(dialog.getByText('Summary', { exact:true })).toBeVisible();
  await expect(dialog.getByText('Gaps', { exact:true })).toBeVisible();
  await expect(dialog.getByText('Spikes', { exact:true })).toBeVisible();
  await expect(dialog.getByText('Bad OHLC', { exact:true }).first()).toBeVisible();
  await dialog.getByRole('button', { name:'Save', exact:true }).click();
  await expect(dialog.getByText('Data contains unsaved changes', { exact:true })).toBeHidden();
  await dialog.locator('footer').getByRole('button', { name:'Close', exact:true }).click();
  await page.getByRole('button', { name:'View & Analyze', exact:true }).click();
  const reopened = page.getByRole('dialog', { name:"View data for 'EURUSD'", exact:true });
  await expect(reopened.locator('.review-grid-scroll button').first()).toContainText('1.23456');
  await reopened.locator('.review-grid-scroll button').first().click();
  await reopened.getByRole('button', { name:'Delete line', exact:true }).click();
  await reopened.locator('footer').getByRole('button', { name:'Close', exact:true }).click();
  const discard = page.getByRole('dialog', { name:'Unsaved data changes', exact:true });
  await expect(discard).toContainText('discard the unsaved row changes', { ignoreCase:true });
  await discard.getByRole('button', { name:'Discard changes', exact:true }).click();
});

test('shows tick-data limitations in Chart and quality tabs', async ({ page }) => {
  await launch(page); await page.getByLabel('Select NQ', { exact:true }).check();
  await page.getByRole('button', { name:'View & Analyze', exact:true }).click();
  const dialog = page.getByRole('dialog', { name:"View data for 'NQ'", exact:true });
  await expect(dialog.getByRole('combobox', { name:'View timeframe', exact:true })).toHaveValue('TICK');
  await dialog.getByRole('tab', { name:'Chart', exact:true }).click();
  await expect(dialog.getByText('Chart is not available for tick data.', { exact:true })).toBeVisible();
  await dialog.getByRole('tab', { name:'Analyze data quality', exact:true }).click();
  await expect(dialog.getByText('Analyze data quality is not available for Tick and Intraday data.', { exact:true })).toBeVisible();
});
