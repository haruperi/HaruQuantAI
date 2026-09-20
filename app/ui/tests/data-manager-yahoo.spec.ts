import { expect, test, type Page } from '@playwright/test';
import { selectLightSkin } from './shellTestUtils';

async function launch(page: Page) { await page.goto('/'); await page.getByRole('button', { name: 'Data Manager', exact: true }).click(); }
async function openAdd(page: Page) { await page.getByRole('button', { name: 'Yahoo', exact: true }).click(); await page.getByRole('menu', { name: 'Yahoo actions' }).getByRole('menuitem', { name: 'Add Yahoo symbols', exact: true }).click(); return page.getByRole('dialog', { name: 'Add Yahoo data' }); }
async function openDownload(page: Page) { await page.getByRole('button', { name: 'Yahoo', exact: true }).click(); await page.getByRole('menu', { name: 'Yahoo actions' }).getByRole('menuitem', { name: 'Download data for existing symbol', exact: true }).click(); return page.getByRole('dialog'); }
async function addSymbols(page: Page, symbols = 'AAPL', postfix = '_Y') { const dialog = await openAdd(page); await dialog.getByRole('textbox', { name: 'Yahoo symbols' }).fill(symbols); await dialog.getByRole('textbox', { name: 'Data postfix' }).fill(postfix); await dialog.getByRole('button', { name: 'Save', exact: true }).click(); }

test('uses the Yahoo label and icon and matches the Add popup behavior', async ({ page }, info) => {
  const requests: string[] = []; page.on('request', request => { if (/finance\.yahoo|query\d*\.finance\.yahoo|yahooapis/i.test(request.url())) requests.push(request.url()); });
  await launch(page); const provider = page.getByRole('button', { name: 'Yahoo', exact: true }); await expect(provider.locator('img.provider-image-icon')).toBeVisible(); await expect(provider.locator('img')).toHaveAttribute('src', /dm-yahoo/);
  const dialog = await openAdd(page); await expect(dialog.getByText('Please enter a list of stocks tickers you want to add, separated by comma, semicolon or newline.')).toBeVisible(); await expect(dialog.getByText('For example: AAPL, AMZN, TSLA')).toBeVisible();
  await dialog.getByRole('button', { name: 'Save', exact: true }).click(); await expect(dialog.getByRole('alert')).toContainText('at least one');
  await dialog.getByRole('textbox', { name: 'Yahoo symbols' }).fill('AAPL, MSFT;\nTSLA'); await dialog.getByRole('textbox', { name: 'Data postfix' }).fill('_Y'); await page.screenshot({ path: info.outputPath('yahoo-add-dark.png') }); await dialog.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(page.getByLabel('Status for AAPL_Y')).toHaveText('Completed', { timeout: 8000 }); const row = page.getByRole('row').filter({ has: page.getByRole('checkbox', { name: 'Select AAPL_Y', exact: true }) }); await expect(row.getByRole('cell').nth(5)).toHaveText('D1'); await expect(row.getByRole('cell').nth(11)).toHaveText('Yahoo'); await expect(row.getByRole('cell').nth(15)).toHaveText('Completed');
  await page.reload(); await expect(page.getByLabel('Status for AAPL_Y')).toHaveText('Completed'); expect(requests).toEqual([]);
});

test('matches selected-row Yahoo download, date presets and redownload policy', async ({ page }, info) => {
  await launch(page); await openDownload(page); await expect(page.getByLabel('Data Manager progress')).toContainText('at least one Yahoo');
  await addSymbols(page, 'AAPL;MSFT'); await expect(page.getByLabel('Status for AAPL_Y')).toHaveText('Completed', { timeout: 8000 }); await expect(page.getByLabel('Status for MSFT_Y')).toHaveText('Completed', { timeout: 8000 }); await page.getByRole('checkbox', { name: 'Select AAPL_Y', exact: true }).check(); await page.getByRole('checkbox', { name: 'Select MSFT_Y', exact: true }).check(); await page.getByRole('checkbox', { name: 'Select EURUSD', exact: true }).check();
  let dialog = await openDownload(page); await expect(dialog).toHaveAccessibleName('Download Yahoo data for multiple');
  for (const name of ['Since last date','Last 6 months','Last year','Last 5 years','Last 10 years','All time']) { await dialog.getByRole('button', { name, exact: true }).click(); await expect(dialog.getByRole('button', { name, exact: true })).toHaveAttribute('aria-pressed', 'true'); }
  await dialog.getByLabel('From', { exact: true }).fill('2025-01-03'); await dialog.getByLabel('To', { exact: true }).fill('2025-01-01'); await dialog.getByRole('button', { name: 'Start download', exact: true }).click(); await expect(dialog.getByRole('alert')).toContainText('valid date');
  await dialog.getByLabel('From', { exact: true }).fill('2025-01-01'); await dialog.getByLabel('To', { exact: true }).fill('2025-01-03'); await dialog.getByRole('radio', { name: 'Overwrite existing data' }).check(); await page.screenshot({ path: info.outputPath('yahoo-download-dark.png') }); await dialog.getByRole('button', { name: 'Start download', exact: true }).click();
  await expect(page.getByLabel('Data Manager progress')).toContainText('download completed', { timeout: 8000 }); const row = page.getByRole('row').filter({ has: page.getByRole('checkbox', { name: 'Select AAPL_Y', exact: true }) }); await expect(row.getByRole('cell').nth(8)).toHaveText('2025-01-03'); await expect(row.getByRole('cell').nth(15)).toHaveText('Completed');
});

test('supports pause/reload/resume, responsive themes, focus and storage failure', async ({ page }, info) => {
  await launch(page); await addSymbols(page, 'NVDA', '_P'); await page.getByRole('button', { name: 'Pause all' }).click(); await page.reload(); await expect(page.getByLabel('Data Manager progress')).toContainText('paused'); await page.getByRole('button', { name: 'Resume all' }).click(); await expect(page.getByLabel('Status for NVDA_P')).toHaveText('Completed', { timeout: 8000 });
  await selectLightSkin(page); await page.setViewportSize({ width: 620, height: 700 }); const dialog = await openAdd(page); await expect(dialog.getByRole('button', { name: 'Save' })).toBeInViewport(); await page.screenshot({ path: info.outputPath('yahoo-light-narrow.png') }); await dialog.getByRole('button', { name: 'Save' }).focus(); await page.keyboard.press('Tab'); await expect(dialog.getByRole('button', { name: 'Close' }).first()).toBeFocused();
  await dialog.getByRole('textbox', { name: 'Yahoo symbols' }).fill('SPY'); await page.evaluate(() => { Storage.prototype.setItem = () => { throw new Error('quota'); }; }); await dialog.getByRole('button', { name: 'Save' }).click(); await expect(dialog.getByRole('alert')).toContainText('Unable to save'); await page.keyboard.press('Escape'); await expect(page.getByRole('button', { name: 'Yahoo', exact: true })).toBeFocused();
});
