import { expect, test, type Page } from '@playwright/test';
import { selectLightSkin } from './shellTestUtils';
import { dataset, installDataManagerBackend } from '../unit/workspace/DataManager/Common/browserHarness';

async function openDataManager(page: Page) {
  await page.goto('/datamanager');
  await expect(page.getByRole('table', { name: 'Historical data', exact: true })).toBeVisible();
}

async function legacyRows(page: Page) {
  await page.addInitScript(() => {
    if (localStorage.getItem('test-legacy-installed')) return;
    localStorage.setItem('test-legacy-installed', 'true');
    const row = { id: 'darwinex:AUDCAD', symbol: 'AUDCAD', source: 'Darwinex', underlying: 'AUDCAD', instrument: 'AUDCAD', timeframe: 'TICK', broker: '-1', brokerName: 'Default', timezone: 'UTC', category: 'Tick data', from: '', to: '', bars: 0 };
    localStorage.setItem('sqx-data-manager-v1', JSON.stringify({ version: 2, definitions: [row], brokers: [], brokerJob: null }));
    localStorage.setItem('sqx-darwinex-v1', JSON.stringify({ version: 1, definitions: [row], ranges: {}, folder: '', postfix: '', job: { kind: 'add', definitions: [row], state: 'completed', completed: 1, progress: 100 } }));
    localStorage.setItem('sqx-stock-groups-v1', JSON.stringify({ version: 1, groups: [], generated: [{ ...row, id: 'stock-group:AUDCAD', from: '2000-01-01', to: '2026-01-01', bars: 99999 }], job: null }));
  });
}

test('database inventory is authoritative across grid, filtering, actions and reload', async ({ page }) => {
  const backend = await installDataManagerBackend(page, [dataset('EURUSD_dukascopy', 7), dataset('GBPUSD_dukascopy')]);
  await legacyRows(page);
  await openDataManager(page);
  const table = page.getByRole('table', { name: 'Historical data', exact: true });
  await expect(table.getByRole('row')).toHaveCount(3);
  await expect(page.getByText('Records: 2', { exact: true })).toBeVisible();
  await expect(table).not.toContainText('AUDCAD');
  const first = table.getByRole('row').filter({ hasText: 'EURUSD_dukascopy' });
  await expect(first.getByRole('cell').nth(10)).toHaveText('7');
  await expect(first.getByRole('cell').nth(7)).toHaveText('2026-01-01');
  await expect(first.getByRole('cell').nth(15)).toHaveText('Ready');
  await first.getByRole('checkbox', { name: 'Select EURUSD_dukascopy', exact: true }).check();
  await page.getByRole('button', { name: 'Update selected', exact: true }).click();
  await expect.poll(() => backend.requests.find(request => request.operation === 'actions.update_selected')?.body).toEqual({ symbols: ['EURUSD_dukascopy'] });
  await page.getByLabel('Filter items', { exact: true }).fill('GBP');
  await expect(page.getByText('Records: 1', { exact: true })).toBeVisible();
  await page.reload();
  await expect(table.getByRole('row')).toHaveCount(3);
  await expect(table).not.toContainText('AUDCAD');
  expect(await page.evaluate(() => JSON.parse(localStorage.getItem('sqx-data-manager-v1')!).definitions[0].symbol)).toBe('AUDCAD');
});

test('empty backend stays empty despite stale plugin and workspace definitions', async ({ page }) => {
  await installDataManagerBackend(page);
  await legacyRows(page);
  await openDataManager(page);
  await expect(page.getByText('No data defined.', { exact: true })).toBeVisible();
  await expect(page.getByText('Records: 0', { exact: true })).toBeVisible();
  await expect(page.getByRole('checkbox', { name: 'Select AUDCAD', exact: true })).toHaveCount(0);
  for (const tab of ['Instruments', 'Sessions']) {
    await page.getByRole('button', { name: tab, exact: true }).click();
    await expect(page.getByRole('table', { name: tab, exact: true }).getByRole('checkbox')).toHaveCount(1);
  }
});

test('inventory failure never restores mocks and retry loads the authoritative inventory', async ({ page }) => {
  const backend = await installDataManagerBackend(page, [dataset('EURUSD')]);
  backend.failInventory = true;
  await legacyRows(page);
  await openDataManager(page);
  await expect(page.getByRole('alert')).toContainText('Unable to refresh datasets');
  await expect(page.getByRole('table', { name: 'Historical data', exact: true })).not.toContainText('AUDCAD');
  await page.getByRole('button', { name: 'Update all', exact: true }).click();
  await expect(page.getByLabel('Data Manager progress')).toContainText('Refresh the dataset inventory');
  expect(backend.requests.some(request => request.operation === 'actions.update_all')).toBe(false);
  backend.failInventory = false;
  await page.getByRole('button', { name: 'Retry dataset refresh', exact: true }).click();
  await expect(page.getByRole('checkbox', { name: 'Select EURUSD', exact: true })).toBeVisible();
});

test('successful empty refresh clears selection and does not restore stale records', async ({ page }) => {
  const backend = await installDataManagerBackend(page, [dataset('EURUSD')]);
  await legacyRows(page);
  await openDataManager(page);
  await page.getByRole('checkbox', { name: 'Select EURUSD', exact: true }).check();
  backend.rows = [];
  await page.getByRole('button', { name: 'Update all', exact: true }).click();
  await expect(page.getByText('No data defined.', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Update selected', exact: true }).click();
  await expect(page.getByLabel('Data Manager progress')).toContainText('Select at least one dataset');
  expect(backend.requests.some(request => request.operation === 'actions.update_selected')).toBe(false);
});

test('disconnected providers report unavailable and cannot run simulated jobs', async ({ page }) => {
  await installDataManagerBackend(page);
  await legacyRows(page);
  await openDataManager(page);
  await expect(page.getByText('No data defined.', { exact: true })).toBeVisible();
  for (const [provider, command] of [
    ['Darwinex Tick Data', 'Add Darwinex data'], ['Yahoo', 'Add Yahoo symbols'],
    ['TickDownloader import', 'Import TickDownloader data'], ['File import', 'Add symbol'],
  ]) {
    await page.getByRole('button', { name: provider, exact: true }).click();
    await page.getByRole('menuitem', { name: command, exact: true }).click();
    await expect(page.getByLabel('Data Manager progress')).toContainText('unavailable');
    await expect(page.getByRole('dialog')).toHaveCount(0);
    await expect(page.getByLabel('Data Manager progress').getByRole('button', { name: 'Pause all' })).toBeDisabled();
  }
  await expect(page.getByText('Records: 0', { exact: true })).toBeVisible();
});

test('backend failure is visible without a fabricated completion', async ({ page }) => {
  const backend = await installDataManagerBackend(page, [dataset('EURUSD')]);
  await openDataManager(page);
  await expect(page.getByRole('checkbox', { name: 'Select EURUSD', exact: true })).toBeVisible();
  backend.failUpdates = true;
  await page.getByRole('button', { name: 'Update all', exact: true }).click();
  await expect(page.getByLabel('Data Manager progress')).toContainText('Update unavailable');
  await page.getByRole('button', { name: 'Log', exact: true }).click();
  await expect(page.getByRole('log')).not.toContainText('completed');
});

test('connected Dukascopy uses backend job progress and refreshes completed data', async ({ page }) => {
  const renderErrors: string[] = [];
  page.on('console', message => { if (message.type() === 'error') renderErrors.push(message.text()); });
  const backend = await installDataManagerBackend(page, [dataset('EURUSD')]);
  await page.route('**/sources.dukascopy.catalog', route => route.fulfill({ json: { status: 'success', data: {
    definitions_available: true, source: 'dukascopy', formats: ['m1'],
    modes: { standard: 'available', cdn: 'unavailable', 'cdn-cn': 'unavailable' },
    reason: '', datasets: backend.rows, broker_catalog_status: 'available', brokers: [],
  } } }));
  await page.route('**/sources.dukascopy.download.start', route => {
    expect(route.request().postDataJSON()).toMatchObject({ dataset_id: 'db:EURUSD', mode: 'standard' });
    return route.fulfill({ json: { status: 'success', data: { job_id: 'backend-job', request_id: 'test' } } });
  });
  let polled = 0;
  await page.route('**/sources.dukascopy.download.status', route => {
    polled++;
    backend.rows = [dataset('EURUSD', 17)];
    return route.fulfill({ json: { status: 'success', data: { job_id: 'backend-job', state: 'succeeded', completed_days: 2, published_days: 2, missing_days: 0, skipped_days: 0, progress: 1 } } });
  });
  await openDataManager(page);
  await page.getByRole('checkbox', { name: 'Select EURUSD', exact: true }).check();
  await expect(page.getByText(/Host online/)).toBeVisible();
  await page.getByRole('button', { name: 'Dukascopy data', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Download data for existing symbol', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: "Download Dukascopy data for 'EURUSD'", exact: true });
  await dialog.getByLabel('From', { exact: true }).fill('2026-01-01');
  await dialog.getByLabel('To', { exact: true }).fill('2026-01-02');
  await dialog.getByRole('button', { name: 'Start download', exact: true }).click();
  await expect.poll(() => renderErrors.length ? renderErrors.join('\n') : polled).toBe(1);
  await expect(page.getByLabel('Data Manager progress')).toContainText('completed 100%');
  const row = page.getByRole('table', { name: 'Historical data', exact: true }).getByRole('row').filter({ hasText: 'EURUSD' });
  await expect(row.getByRole('cell').nth(10)).toHaveText('17');
  await expect(row.getByRole('cell').nth(7)).toHaveText('2026-01-01');
});

test('Dukascopy disclaimer is informational and closes in both themes', async ({ page }) => {
  await installDataManagerBackend(page);
  await openDataManager(page);
  const openDisclaimer = async () => {
    await page.getByRole('button', { name: 'Dukascopy data', exact: true }).click();
    await page.getByRole('menuitem', { name: 'Dukascopy Data Disclaimer', exact: true }).click();
    return page.getByRole('dialog', { name: 'Dukascopy Data Disclaimer', exact: true });
  };
  const before = await page.evaluate(() => JSON.stringify(localStorage));
  for (const theme of ['dark', 'light']) {
    if (theme === 'light') await selectLightSkin(page);
    const dialog = await openDisclaimer();
    await expect(dialog.getByRole('heading', { name: 'Disclaimer', exact: true })).toBeVisible();
    const paragraphs = dialog.locator('.disclaimer-content p');
    await expect(paragraphs).toHaveCount(4);
    await expect(paragraphs.nth(0)).toContainText('NOT the actual values at a given point in time');
    await expect(paragraphs.nth(1)).toContainText('not an investment advice');
    await expect(paragraphs.nth(2)).toContainText('shall put a clear note to the public');
    await expect(paragraphs.nth(3)).toContainText('WITH ALL ITS FAULTS');
    await expect(dialog.getByRole('checkbox')).toHaveCount(0);
    await expect(dialog.getByRole('button')).toHaveCount(4);
    await expect(dialog.getByRole('button', { name: 'Close', exact: true }).last()).toBeInViewport();
    await page.screenshot({ path: `test-results/dukascopy-disclaimer-${theme}.png` });
    await dialog.getByRole('button', { name: 'Close', exact: true }).last().click();
    await expect(page.getByRole('button', { name: 'Dukascopy data', exact: true })).toBeFocused();
    if (theme === 'dark') expect(await page.evaluate(() => JSON.stringify(localStorage))).toBe(before);
  }
  const dialog = await openDisclaimer();
  await dialog.getByRole('button', { name: 'Close', exact: true }).first().click();
  await expect(dialog).toHaveCount(0);
  await openDisclaimer();
  await page.keyboard.press('Escape');
  await expect(dialog).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Dukascopy data', exact: true })).toBeFocused();
  await expect(page.getByLabel('Data Manager progress')).toContainText('No active operations');
});
