import { expect, test, type Page } from '@playwright/test';
import { selectLightSkin } from './shellTestUtils';
import { mkdtemp, writeFile, readFile, rm } from 'node:fs/promises';
import { tmpdir } from 'node:os';
import { join } from 'node:path';
const csv = 'Date,Open,High,Low,Close,Volume\n2026-09-18,1,3,0,2,4\n2026-09-19,2,4,1,3,5';
async function launch(page: Page) { await page.goto('/'); await page.getByRole('button', { name: 'Data Manager', exact: true }).click(); }
async function command(page: Page, name: string) { await page.getByRole('button', { name: 'File import', exact: true }).click(); await page.getByRole('menuitem', { name, exact: true }).click(); }
async function single(page: Page) { await page.getByRole('checkbox', { name: 'Select XAUUSD', exact: true }).check(); await command(page, 'Import one data file'); return page.getByRole('dialog', { name: "Data import for 'XAUUSD'" }); }
async function load(page: Page, text = csv) { await page.getByLabel('Choose data file', { exact: true }).setInputFiles({ name: 'history.csv', mimeType: 'text/csv', buffer: Buffer.from(text) }); await expect(page.getByLabel('Data file', { exact: true })).toHaveValue('history.csv'); }
const progress = (page: Page) => page.getByRole('status', { name: 'Data Manager progress' });

test('single file eligibility, preview, format CRUD, import recovery and deduplication', async ({ page }) => {
  await launch(page);
  await command(page, 'Import one data file'); await expect(progress(page)).toContainText('select at least one File record');
  await page.getByRole('checkbox', { name: 'Select EURUSD', exact: true }).check();
  await command(page, 'Import one data file'); await expect(page.getByRole('dialog')).toHaveCount(0);
  const dialog = await single(page);
  await dialog.getByRole('button', { name: 'Start Import', exact: true }).click(); await expect(dialog.getByRole('alert')).toContainText('Choose a data file');
  await load(page); await expect(dialog.getByRole('table', { name: 'Data preview' }).getByRole('row')).toHaveCount(3);
  await dialog.getByRole('button', { name: 'Save as', exact: true }).click();
  await page.getByLabel('Name', { exact: true }).fill('My daily format'); await page.getByRole('dialog').getByRole('button', { name: 'Save', exact: true }).click();
  await expect(dialog.getByLabel('Predefined file format')).toHaveValue('My daily format');
  await dialog.getByRole('button', { name: 'Delete', exact: true }).click(); await page.keyboard.press('Escape');
  await expect(dialog.getByLabel('Predefined file format')).toHaveValue('My daily format');
  await page.screenshot({ path: 'test-results/file-import-dark.png' });
  await dialog.getByRole('button', { name: 'Start Import', exact: true }).click();
  await page.getByRole('button', { name: 'Pause all', exact: true }).click(); await expect(progress(page)).toContainText('paused');
  await page.reload(); await expect(progress(page)).toContainText('paused');
  await command(page, 'Import multiple files from a folder'); await expect(progress(page)).toContainText('Finish or stop'); await expect(page.getByRole('dialog')).toHaveCount(0);
  await page.getByRole('button', { name: 'Resume all', exact: true }).click();
  // Clear the selection notice by changing selection.
  await page.getByRole('checkbox', { name: 'Select XAUUSD', exact: true }).check();
  await expect(page.getByLabel('Status for XAUUSD', { exact: true })).toHaveText('Completed', { timeout: 10000 });
  await expect(page.getByLabel('Status for EURUSD', { exact: true })).toBeEmpty();
  const count = await page.getByRole('row').filter({ has: page.getByRole('checkbox', { name: 'Select XAUUSD', exact: true }) }).locator('td').nth(10).innerText();
  const again = await single(page); await load(page); await again.getByRole('button', { name: 'Start Import', exact: true }).click();
  await expect(page.getByLabel('Status for XAUUSD', { exact: true })).toHaveText('Completed', { timeout: 10000 });
  await expect(page.getByRole('row').filter({ has: page.getByRole('checkbox', { name: 'Select XAUUSD', exact: true }) }).locator('td').nth(10)).toHaveText(count);
  await single(page); await page.getByLabel('Predefined file format').selectOption('My daily format');
  await page.getByRole('button', { name: 'Delete', exact: true }).click(); await page.getByRole('dialog', { name: 'Delete data format' }).getByRole('button', { name: 'Delete', exact: true }).click();
  await expect(page.getByLabel('Predefined file format').locator('option')).not.toContainText(['My daily format']);
});

test('errors, ignore invalid lines, stop and quota failures do not claim success', async ({ page }) => {
  await launch(page); await single(page); await load(page, csv + '\ninvalid,1,3,0,2,4');
  await page.getByRole('button', { name: 'Start Import', exact: true }).click();
  await expect(progress(page)).toContainText('failed', { timeout: 10000 }); await expect(progress(page)).toContainText('Row 4');
  await single(page); await load(page, csv + '\ninvalid,1,3,0,2,4'); await page.getByRole('radio', { name: 'Ignore lines with errors' }).check();
  await page.getByRole('button', { name: 'Start Import', exact: true }).click();
  await expect(progress(page)).toContainText('completed', { timeout: 10000 }); await expect(progress(page)).toContainText('1 invalid rows ignored');
  await single(page); await load(page); await page.getByRole('button', { name: 'Start Import', exact: true }).click(); await page.getByRole('button', { name: 'Stop all', exact: true }).click(); await expect(progress(page)).toContainText('cancelled');
  await single(page); await load(page);
  await page.evaluate(() => { const original = Storage.prototype.setItem; Storage.prototype.setItem = function(key, value) { if (key === 'sqx-file-import-v1') throw new DOMException('Quota', 'QuotaExceededError'); original.call(this, key, value); }; });
  await page.getByRole('button', { name: 'Start Import', exact: true }).click(); await expect(page.getByRole('dialog').getByRole('alert')).toContainText('Unable to save');
});

test('folder imports, instrument reuse, stock group, skip, numbered copy and overwrite', async ({ page }) => {
  const folder = await mkdtemp(join(tmpdir(), 'haru-import-'));
  try {
    await writeFile(join(folder, 'ALPHA.csv'), '18092026,1,3,0,2,4\n19092026,2,4,1,3,5');
    await writeFile(join(folder, 'BETA.csv'), '19092026,2,4,1,3,5');
    await launch(page); await command(page, 'Import multiple files from a folder');
    let dialog = page.getByRole('dialog', { name: 'Mass import', exact: true });
    await expect(dialog.getByLabel('Imported timeframe')).toHaveValue('D1');
    await dialog.getByRole('button', { name: 'Save', exact: true }).click(); await expect(dialog.getByRole('alert')).toContainText('source data folder');
    await dialog.getByLabel('Choose source folder').setInputFiles(folder);
    await dialog.getByRole('checkbox', { name: 'Create a new stockgroup from imported symbols' }).check();
    await dialog.getByLabel('Data postfix').fill('_file');
    await dialog.getByRole('button', { name: /Add new instrument/ }).click(); await page.getByLabel('Instrument name', { exact: true }).fill('FOLDER_INST'); await page.getByRole('dialog').getByRole('button', { name: 'Save', exact: true }).click();
    await expect(dialog.getByLabel('Instrument', { exact: true })).toHaveValue('FOLDER_INST');
    await dialog.getByRole('button', { name: 'Help', exact: true }).click(); await page.keyboard.press('Escape');
    await dialog.getByLabel('Source data folder').scrollIntoViewIfNeeded();
    await page.screenshot({ path: 'test-results/file-mass-import-dark.png' });
    await dialog.getByRole('button', { name: 'Save', exact: true }).click();
    await expect(dialog).toHaveCount(0);
    await expect(progress(page)).toContainText('completed', { timeout: 10000 });
    await page.reload(); await expect(page.getByRole('row').filter({ hasText: 'ALPHA_file' })).toContainText('FOLDER_INST');
    const groupName = await page.getByLabel('Stock group', { exact: true }).locator('option').nth(1).innerText();
    await page.getByLabel('Stock group', { exact: true }).selectOption(groupName); await expect(page.getByRole('table', { name: 'Historical data' }).getByRole('row')).toHaveCount(3);
    await page.getByRole('button', { name: 'Stock groups', exact: true }).click(); await expect(page.getByRole('table', { name: 'Stock groups', exact: true })).toContainText(groupName);
    await page.getByRole('button', { name: 'Data sources', exact: true }).click();
    for (const policy of ['Skip', 'Create new ticker in data - adds postfix 2 or 3 etc.', 'Overwrite']) {
      await command(page, 'Import multiple files from a folder'); dialog = page.getByRole('dialog', { name: 'Mass import', exact: true });
      await dialog.getByLabel('Choose source folder').setInputFiles(folder); await dialog.getByLabel('Data postfix').fill('_file'); await dialog.getByRole('radio', { name: policy, exact: true }).check();
      await dialog.getByRole('button', { name: 'Save', exact: true }).click();
      if (policy === 'Skip') { await expect(dialog.getByRole('alert')).toContainText('All 2 files were skipped'); await page.keyboard.press('Escape'); }
      else { await expect(dialog).toHaveCount(0); await expect(progress(page)).toContainText('completed', { timeout: 10000 }); }
    }
    await expect(page.getByRole('checkbox', { name: 'Select ALPHA_file2', exact: true })).toBeVisible();
    expect(await readFile(join(folder, 'BETA.csv'), 'utf-8')).toBe('19092026,2,4,1,3,5');
  } finally { if (!folder.startsWith(join(tmpdir(), 'haru-import-'))) throw new Error('Unexpected fixture path'); await rm(folder, { recursive: true, force: true }); }
});

test('theme, narrow layout, cancellation and removed menu item', async ({ page }) => {
  await launch(page); await page.getByRole('button', { name: 'File import', exact: true }).click(); await expect(page.getByRole('menuitem', { name: 'Import application data' })).toHaveCount(0); await page.keyboard.press('Escape');
  await selectLightSkin(page);
  await page.setViewportSize({ width: 550, height: 760 });
  await single(page); await load(page);
  await page.screenshot({ path: 'test-results/file-import-light-narrow.png' });
  const dialog = page.getByRole('dialog'); const box = await dialog.boundingBox(); expect(box!.width).toBeLessThanOrEqual(550);
  await page.keyboard.press('Escape'); await expect(dialog).toHaveCount(0);
  await expect(progress(page)).toContainText('No active operations');
});

test('custom delimiter, skipped columns, manual mappings and saved-format update drive imports', async ({ page }) => {
  await launch(page); const dialog = await single(page);
  await load(page, 'metadata\nignore;Date;Open;High;Low;Close;Volume\nignore;20092026;1;3;0;2;5');
  await dialog.getByLabel('Separator', { exact: true }).selectOption(';');
  await dialog.getByLabel('Skip rows', { exact: true }).fill('2'); await dialog.getByLabel('Skip columns', { exact: true }).fill('1');
  await dialog.getByLabel('Date format', { exact: true }).fill('ddMMyyyy');
  await dialog.getByRole('button', { name: 'Start Import', exact: true }).click(); await expect(dialog.getByRole('alert')).toContainText('Choose a type');
  for (const [index, type] of ['Date', 'Open', 'High', 'Low', 'Close', 'Volume'].entries()) await dialog.getByLabel(`Column ${index + 1} type`, { exact: true }).selectOption(type);
  await expect(dialog.getByRole('table', { name: 'Data preview' }).getByRole('row')).toHaveCount(2);
  await dialog.getByRole('button', { name: 'Save as', exact: true }).click();
  await page.getByLabel('Name', { exact: true }).fill('Custom semicolon'); await page.getByRole('dialog').getByRole('button', { name: 'Save', exact: true }).click();
  await dialog.getByRole('button', { name: 'Save', exact: true }).click();
  await dialog.getByRole('button', { name: 'Start Import', exact: true }).click(); await expect(progress(page)).toContainText('completed', { timeout: 10000 });
  await page.reload(); await single(page); await page.getByLabel('Predefined file format').selectOption('Custom semicolon');
  await expect(page.getByLabel('Skip rows', { exact: true })).toHaveValue('2'); await expect(page.getByLabel('Skip columns', { exact: true })).toHaveValue('1');
  await expect(page.getByLabel('Separator', { exact: true })).toHaveValue(';');
  await page.getByLabel('Predefined file format').selectOption('Generic OHLCV');
  await expect(page.getByRole('dialog').getByRole('button', { name: 'Save', exact: true })).toBeDisabled();
  await expect(page.getByRole('dialog').getByRole('button', { name: 'Delete', exact: true })).toBeDisabled();
});
