import { expect, test, type Page } from '@playwright/test';
import { selectLightSkin } from './shellTestUtils';
import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';

async function launch(page: Page) {
  await page.goto('/');
  await page.getByRole('button', { name: 'Data Manager', exact: true }).and(page.locator('[aria-label]')).click();
}

async function open(page: Page) {
  await page.getByRole('button', { name: 'MT5 import', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Import data', exact: true }).click();
  return page.getByRole('dialog', { name: 'Import data from MT5', exact: true });
}

async function fixture(root: string) {
  await mkdir(path.join(root, 'MQL5', 'Profiles'), { recursive: true });
  await writeFile(path.join(root, 'terminal64.exe'), '');
  await writeFile(path.join(root, 'MQL5', 'Profiles', 'mock.ini'), 'metadata');
  return root;
}

test('matches the active MT5 popup, discovers symbols and validates input', async ({ page }, info) => {
  const invalid = info.outputPath('Files');
  await mkdir(invalid, { recursive: true });
  await writeFile(path.join(invalid, 'readme.txt'), 'not an MT5 folder');
  const root = await fixture(info.outputPath('MockMT5'));
  await launch(page);
  const dialog = await open(page);
  await expect(dialog.getByLabel('MT5 install folder', { exact: true })).toBeVisible();
  await expect(dialog.getByRole('radio')).toHaveCount(0);
  await expect(dialog.getByText('Data Availability Disclaimer', { exact: true })).toBeVisible();
  await dialog.getByRole('button', { name: 'More details', exact: true }).click();
  await expect(dialog.getByRole('link')).toHaveCount(0);
  await expect(dialog.getByRole('button', { name: 'Since last date', exact: true })).toHaveAttribute('aria-pressed', 'true');
  for (const name of ['Last 6 months', 'Last year', 'Last 5 years', 'Last 10 years', 'All time']) {
    await dialog.getByRole('button', { name, exact: true }).click();
    await expect(dialog.getByRole('button', { name, exact: true })).toHaveAttribute('aria-pressed', 'true');
  }
  await dialog.getByRole('button', { name: 'Start import', exact: true }).click();
  await expect(dialog.getByRole('alert')).toContainText('Select an MT5');
  await dialog.getByLabel('Select MT5 installation folder', { exact: true }).setInputFiles(invalid);
  await expect(dialog.getByRole('alert')).toContainText('does not look like');
  await dialog.getByLabel('Select MT5 installation folder', { exact: true }).setInputFiles(root);
  await dialog.getByRole('button', { name: 'Fetch symbols', exact: true }).click();
  await expect(dialog.getByRole('checkbox', { name: /^Select MT5 symbol / })).toHaveCount(12);
  await expect(dialog.getByRole('row').filter({ hasText: 'Forex\\Majors' })).toBeVisible();
  await dialog.getByLabel('Show types', { exact: true }).selectOption({ label: 'Forex\\Majors' });
  await expect(dialog.getByRole('checkbox', { name: /^Select MT5 symbol / })).toHaveCount(3);
  await dialog.getByRole('checkbox', { name: 'Select group Forex\\Majors', exact: true }).check();
  await expect(dialog.getByRole('checkbox', { name: 'Select MT5 symbol EURUSD', exact: true })).toBeChecked();
  await dialog.getByLabel('Filter items', { exact: true }).fill('apple');
  await expect(dialog.getByRole('checkbox', { name: /^Select MT5 symbol / })).toHaveCount(0);
  await dialog.getByLabel('Show types', { exact: true }).selectOption('');
  await expect(dialog.getByRole('checkbox', { name: 'Select MT5 symbol AAPL', exact: true })).toBeVisible();
  await page.screenshot({ path: info.outputPath('mt5-import-dark.png') });
});

test('imports through shared progress, restores paused work and persists results', async ({ page }, info) => {
  const root = await fixture(info.outputPath('Terminal'));
  await launch(page);
  let dialog = await open(page);
  await dialog.getByLabel('Select MT5 installation folder', { exact: true }).setInputFiles(root);
  await dialog.getByRole('button', { name: 'Fetch symbols', exact: true }).click();
  await expect(dialog.getByRole('checkbox', { name: 'Select MT5 symbol EURUSD', exact: true })).toBeVisible();
  await dialog.getByRole('checkbox', { name: 'Select MT5 symbol EURUSD', exact: true }).check();
  await dialog.getByRole('checkbox', { name: 'Select MT5 symbol AAPL', exact: true }).check();
  await dialog.getByLabel('Data postfix', { exact: true }).fill('_M');
  await dialog.getByRole('button', { name: 'Start import', exact: true }).click();
  await expect(page.getByLabel('Data Manager progress')).toContainText('MT5 mock import running');
  await page.getByRole('button', { name: 'Pause all', exact: true }).click();
  await page.getByRole('button', { name: 'Yahoo', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Add Yahoo symbols', exact: true }).click();
  await expect(page.getByLabel('Data Manager progress')).toContainText('Finish or stop the active data operation first.');
  await expect(page.getByRole('dialog', { name: 'Add Yahoo data', exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Resume all', exact: true }).click();
  await page.reload();
  await expect(page.getByLabel('Data Manager progress')).toContainText('MT5 mock import paused');
  await page.getByRole('button', { name: 'Resume all', exact: true }).click();
  await expect(page.getByLabel('Status for AAPL_M', { exact: true })).toHaveText('Completed', { timeout: 10000 });
  await expect(page.getByRole('row').filter({ has: page.getByRole('checkbox', { name: 'Select AAPL_M', exact: true }) })).toContainText('MT5');
  await page.reload();
  await expect(page.getByLabel('Status for AAPL_M', { exact: true })).toHaveText('Completed');

  dialog = await open(page);
  await expect(dialog.getByText('Select the folder again to fetch its available symbols.')).toBeVisible();
  await dialog.getByLabel('Select MT5 installation folder', { exact: true }).setInputFiles(root);
  await dialog.getByRole('button', { name: 'Fetch symbols', exact: true }).click();
  await expect(dialog.getByRole('checkbox', { name: 'Select MT5 symbol AAPL', exact: true })).toBeVisible();
  await dialog.getByRole('checkbox', { name: 'Select MT5 symbol AAPL', exact: true }).check();
  await expect(dialog.getByLabel('Data postfix', { exact: true })).toHaveValue('_M');
  await dialog.getByRole('button', { name: 'Start import', exact: true }).click();
  await expect(page.getByLabel('Status for AAPL_M_1', { exact: true })).toHaveText('Completed', { timeout: 10000 });
});

test('contains work within the browser and reports storage failure', async ({ page }, info) => {
  const root = await fixture(info.outputPath('MT5'));
  const requests: string[] = [];
  page.on('request', request => {
    if (!request.url().startsWith('http://127.0.0.1:4173') && !request.url().includes('kaspersky-labs.com')) requests.push(request.url());
  });
  await launch(page);
  await selectLightSkin(page);
  await page.setViewportSize({ width: 620, height: 700 });
  const dialog = await open(page);
  await dialog.getByLabel('Select MT5 installation folder', { exact: true }).setInputFiles(root);
  await dialog.getByRole('button', { name: 'Fetch symbols', exact: true }).click();
  await expect(dialog.getByRole('checkbox', { name: 'Select MT5 symbol BTCUSD', exact: true })).toBeVisible();
  await dialog.getByRole('checkbox', { name: 'Select MT5 symbol BTCUSD', exact: true }).check();
  await expect(dialog.getByRole('button', { name: 'Start import', exact: true })).toBeInViewport();
  await page.screenshot({ path: info.outputPath('mt5-import-light-narrow.png') });
  await dialog.getByRole('button', { name: 'Start import', exact: true }).focus();
  await page.keyboard.press('Tab');
  await expect(dialog.getByRole('button', { name: 'Close', exact: true }).first()).toBeFocused();
  await page.evaluate(() => { Storage.prototype.setItem = () => { throw new Error('quota'); }; });
  await dialog.getByRole('button', { name: 'Start import', exact: true }).click();
  await expect(dialog.getByRole('alert')).toContainText('Unable to save MT5');
  await page.keyboard.press('Escape');
  await expect(dialog).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'MT5 import', exact: true })).toBeFocused();
  expect(requests).toEqual([]);
});

test('Escape during a pending mock fetch cancels the timer and restores focus', async ({ page }, info) => {
  const root = await fixture(info.outputPath('MT5'));
  await launch(page);
  const dialog = await open(page);
  await dialog.getByLabel('Select MT5 installation folder', { exact: true }).setInputFiles(root);
  await page.evaluate(() => {
    const schedule = window.setTimeout.bind(window);
    const cancel = window.clearTimeout.bind(window);
    const pending = new Set<number>();
    window.setTimeout = ((handler: TimerHandler, delay?: number, ...args: unknown[]) => {
      const id = schedule(handler, delay === 180 ? 60000 : delay, ...args);
      if (delay === 180) pending.add(id);
      document.documentElement.dataset.mockMt5Fetches = String(pending.size);
      return id;
    }) as typeof window.setTimeout;
    window.clearTimeout = id => {
      if (id !== undefined) pending.delete(id);
      document.documentElement.dataset.mockMt5Fetches = String(pending.size);
      cancel(id);
    };
  });
  await dialog.getByRole('button', { name: 'Fetch symbols', exact: true }).click();
  await expect(dialog.getByRole('button', { name: 'Fetching…', exact: true })).toBeDisabled();
  await expect(page.locator('html')).toHaveAttribute('data-mock-mt5-fetches', '1');
  await page.keyboard.press('Escape');
  await expect(dialog).toHaveCount(0);
  await expect(page.locator('html')).toHaveAttribute('data-mock-mt5-fetches', '0');
  await expect(page.getByRole('button', { name: 'MT5 import', exact: true })).toBeFocused();
});
