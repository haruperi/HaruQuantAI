import { expect, test, type Page, type TestInfo } from '@playwright/test';
import { selectLightSkin } from './shellTestUtils';
import { mkdir, writeFile, readFile } from 'node:fs/promises';
import path from 'node:path';
async function fixture(info: TestInfo) {
  const root = info.outputPath('TD');
  for (const symbol of ['EURUSD', 'GBPUSD']) {
    await mkdir(path.join(root, 'tickdata', symbol), { recursive: true });
    await writeFile(path.join(root, 'tickdata', symbol, 'sample.bin'), 'offline mock fixture');
  }
  return root;
}
async function open(page: Page) {
  await page.goto('/');
  await page.getByRole('button', { name: 'Data Manager', exact: true }).and(page.locator('[aria-label]')).click();
  await page.getByRole('button', { name: 'TickDownloader import', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Import TickDownloader data', exact: true }).click();
  return page.getByRole('dialog', { name: 'Import data from TickDownloader', exact: true });
}
test('folder selection, import lifecycle and persisted trailing status', async ({ page }, info) => {
  await page.route('**/*', route => ['localhost','127.0.0.1'].includes(new URL(route.request().url()).hostname) ? route.continue() : route.abort());
  const dialog = await open(page);
  await expect(dialog.getByText('No symbols available.')).toBeVisible();
  await dialog.getByRole('button', { name: 'Start import' }).click();
  await expect(dialog.getByRole('alert')).toContainText('Select a TickDownloader');
  const folder = await fixture(info);
  const chooser = page.waitForEvent('filechooser');
  await dialog.getByRole('button', { name: 'Select', exact: true }).click();
  await (await chooser).setFiles(folder);
  await expect(dialog.getByLabel('TickDownloader Installation', { exact: true })).toHaveValue('TD');
  await expect(dialog.getByRole('checkbox', { name: /^Select symbol / })).toHaveCount(2);
  await dialog.getByRole('button', { name: 'Start import' }).click();
  await expect(dialog.getByRole('alert')).toContainText('at least one');
  await dialog.getByRole('checkbox', { name: 'Select all TickDownloader symbols' }).check();
  await dialog.getByRole('button', { name: 'Start import' }).click();
  await expect(dialog.getByRole('alert')).toContainText('already exists');
  await dialog.getByLabel('Data postfix', { exact: true }).fill('_TD');
  await dialog.getByRole('checkbox', { name: 'Select symbol GBPUSD', exact: true }).uncheck();
  await page.screenshot({ path: info.outputPath('tickdownloader-dark.png') });
  await dialog.getByRole('button', { name: 'Start import' }).click();
  const status = page.getByLabel('Data Manager progress');
  await expect(status).toContainText('TickDownloader mock import running');
  await page.getByRole('button', { name: 'Pause all', exact: true }).click();
  await page.reload();
  await expect(status).toContainText('paused');
  await page.getByRole('button', { name: 'Resume all', exact: true }).click();
  await expect(status).toContainText('completed', { timeout: 10000 });
  await expect(page.getByLabel('Status for EURUSD_TD', { exact: true })).toHaveText('Completed');
  await expect(page.getByRole('table', { name: 'Historical data', exact: true })).not.toContainText('GBPUSD_TD');
  await page.reload();
  await expect(page.getByLabel('Status for EURUSD_TD', { exact: true })).toHaveText('Completed');
  expect(await readFile(path.join(folder, 'tickdata', 'EURUSD', 'sample.bin'), 'utf8')).toBe('offline mock fixture');
  await page.getByRole('button', { name: 'TickDownloader import', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Import TickDownloader data', exact: true }).click();
  await expect(dialog.getByText('Select the folder again to access its available symbols.')).toBeVisible();
  await expect(dialog.getByText('No symbols available.')).toBeVisible();
});
test('light layout, empty folder, cancellation and failed storage', async ({ page }, info) => {
  const dialog = await open(page);
  await dialog.getByRole('button', { name: 'Close', exact: true }).first().click();
  await selectLightSkin(page);
  await page.getByRole('button', { name: 'TickDownloader import', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Import TickDownloader data', exact: true }).click();
  const empty = info.outputPath('empty'); await mkdir(empty, { recursive: true }); await writeFile(path.join(empty, 'readme.txt'), 'empty');
  await dialog.getByLabel('Select TickDownloader data folder').setInputFiles(empty);
  await expect(dialog.getByText('No symbols available.')).toBeVisible();
  await dialog.getByLabel('Select TickDownloader data folder').setInputFiles(await fixture(info));
  await dialog.getByRole('checkbox', { name: 'Select symbol GBPUSD', exact: true }).check();
  await dialog.getByLabel('Data postfix', { exact: true }).fill('_CANCEL');
  await page.setViewportSize({ width: 740, height: 650 });
  await expect(dialog.getByRole('button', { name: 'Start import' })).toBeInViewport();
  await page.screenshot({ path: info.outputPath('tickdownloader-light.png') });
  await dialog.getByRole('button', { name: 'Start import' }).click();
  await page.getByRole('button', { name: 'Stop all', exact: true }).click();
  await expect(page.getByLabel('Status for GBPUSD_CANCEL', { exact: true })).toContainText('Cancelled');
  await page.getByRole('button', { name: 'TickDownloader import', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Import TickDownloader data', exact: true }).click();
  await dialog.getByLabel('Select TickDownloader data folder').setInputFiles(await fixture(info));
  await dialog.getByRole('checkbox', { name: 'Select symbol GBPUSD', exact: true }).check();
  await dialog.getByLabel('Data postfix', { exact: true }).fill('_FAIL');
  await page.evaluate(() => { Storage.prototype.setItem = () => { throw new Error('quota'); }; });
  await dialog.getByRole('button', { name: 'Start import' }).click();
  await expect(dialog.getByRole('alert')).toContainText('No import was started');
  await page.keyboard.press('Escape');
  await expect(page.getByRole('table', { name: 'Historical data', exact: true })).not.toContainText('GBPUSD_FAIL');
});

test('initial focus, keyboard boundaries and Escape retain the import dialog workflow', async ({ page }) => {
  const dialog = await open(page);
  const first = dialog.getByRole('button', { name: 'Close', exact: true }).first();
  const last = dialog.getByRole('button', { name: 'Start import', exact: true });
  await expect(first).toBeFocused();
  await page.keyboard.press('Shift+Tab');
  await expect(last).toBeFocused();
  await page.keyboard.press('Tab');
  await expect(first).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(dialog).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'TickDownloader import', exact: true })).toBeEnabled();
});
