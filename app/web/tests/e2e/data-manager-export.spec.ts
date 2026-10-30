import { expect, test, type Page } from '@playwright/test';

async function launch(page: Page): Promise<void> {
  await page.goto('/');
  await page.getByRole('button', { name: 'Data Manager', exact: true }).click();
}

async function exportTab(page: Page): Promise<void> {
  await page.getByRole('button', { name: 'Export', exact: true }).click();
}

test('matches CSV popup, manages formats, downloads and uses shared status', async ({ page }) => {
  await launch(page); await exportTab(page);
  await page.getByRole('button', { name: 'Export to CSV', exact: true }).click();
  await expect(page.getByLabel('Data Manager progress')).toContainText('select at least one', { ignoreCase: true });
  await page.getByLabel('Select EURUSD', { exact: true }).check();
  await page.getByRole('button', { name: 'Export to CSV', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: "Export data for 'EURUSD'", exact: true });
  await expect(dialog.getByText('Choose data range to export', { exact: true })).toBeVisible();
  await expect(dialog.getByText('Select timeframe, session and target timezone', { exact: true })).toBeVisible();
  await expect(dialog.getByText('File format', { exact: true })).toBeVisible();
  await expect(dialog.getByText('Select target', { exact: true })).toBeVisible();
  await dialog.getByLabel('CSV row format', { exact: true }).fill('[Date:yyyyMMdd],[Close]');
  await dialog.getByRole('button', { name: 'Save as', exact: true }).click();
  const nested = page.getByRole('dialog', { name: 'New file format', exact: true });
  await nested.getByLabel('New CSV format name', { exact: true }).fill('My browser format');
  await nested.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(dialog.getByRole('group', { name: 'File format', exact: true }).getByRole('combobox').first()).toHaveValue('My browser format');
  const download = page.waitForEvent('download');
  await dialog.getByRole('button', { name: 'Export', exact: true }).click();
  await expect(page.getByLabel('Data Manager progress')).toContainText('CSV mock export running');
  await page.getByRole('button', { name: 'Pause all', exact: true }).click();
  await expect(page.getByLabel('Status for EURUSD', { exact: true })).toContainText('Paused');
  await page.getByRole('button', { name: 'Resume all', exact: true }).click();
  expect((await download).suggestedFilename()).toMatch(/EURUSD-M1-No_Session\.csv$/);
  await expect(page.getByLabel('Status for EURUSD', { exact: true })).toHaveText('Completed', { timeout: 10000 });
  await page.reload();
  await expect(page.getByLabel('Status for EURUSD', { exact: true })).toHaveText('Completed');
});

test('matches MT4 popup, accepts specification properties and exports a manifest', async ({ page }, info) => {
  await launch(page); await page.getByLabel('Select NQ', { exact: true }).check(); await exportTab(page);
  await page.getByRole('button', { name: 'Export MT4 (FXT & HST)', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: "Export to MetaTrader 4 FXT and HST for 'NQ'", exact: true });
  await expect(dialog.getByText('Output folder', { exact: true })).toBeVisible();
  await expect(dialog.getByText('MT4 data specification and properties', { exact: true })).toBeVisible();
  await expect(dialog.getByText(/Build 8xx/)).toBeVisible();
  const spec = info.outputPath('nq.properties');
  await import('node:fs/promises').then(fs => fs.writeFile(spec, 'SYMBOL=NQ100\nDIGITS=2\nSPREAD=10\n'));
  await dialog.getByLabel('Load MT4 specification file', { exact: true }).setInputFiles(spec);
  await expect(dialog.getByLabel('Name in MT4', { exact: true })).toHaveValue('NQ100');
  const download = page.waitForEvent('download'); await dialog.getByRole('button', { name: 'Start export', exact: true }).click();
  expect((await download).suggestedFilename()).toBe('NQ100-mt4-export-manifest.json');
  await expect(page.getByLabel('Status for NQ', { exact: true })).toHaveText('Completed', { timeout: 10000 });
});

test('matches MT5 popup, validates source selection and confirms overwrite', async ({ page }) => {
  await launch(page); await page.getByLabel('Select EURUSD', { exact: true }).check(); await exportTab(page);
  await page.getByRole('button', { name: 'Export to MT5 data (99% test)', exact: true }).click();
  const barDialog = page.getByRole('dialog', { name: /Export to MT5 data/ });
  await expect(barDialog.getByRole('radio', { name: 'Tick data', exact: true })).toBeDisabled();
  await expect(barDialog.getByRole('radio', { name: 'M1 data', exact: true })).toBeChecked();
  let download = page.waitForEvent('download'); await barDialog.getByRole('button', { name: 'Export', exact: true }).click();
  expect((await download).suggestedFilename()).toBe('EURUSD.csv');
  await expect(page.getByLabel('Status for EURUSD', { exact: true })).toHaveText('Completed', { timeout: 10000 });
  await page.getByRole('button', { name: 'Export to MT5 data (99% test)', exact: true }).click();
  await page.getByRole('dialog', { name: /Export to MT5 data/ }).getByRole('button', { name: 'Export', exact: true }).click();
  const overwrite = page.getByRole('dialog', { name: 'Export to MT5', exact: true });
  await expect(overwrite).toContainText("File 'EURUSD.csv' already exists");
  download = page.waitForEvent('download'); await overwrite.getByRole('button', { name: 'Yes', exact: true }).click();
  expect((await download).suggestedFilename()).toBe('EURUSD.csv');
});
