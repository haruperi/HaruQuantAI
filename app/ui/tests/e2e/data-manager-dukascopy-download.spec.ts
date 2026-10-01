import { expect, test, type Page } from '@playwright/test';
import { dataset, installDataManagerBackend } from '../unit/workspace/DataManager/Common/browserHarness';

async function installBackend(page: Page, rows: ReturnType<typeof dataset>[]) {
  const backend = await installDataManagerBackend(page, rows);
  await page.route(/\/sources\.(?!dukascopy\.)[^/]+\.catalog$/, route => route.fulfill({
    status: 503, json: { status: 'error', error: { code: 'MISSING_CAPABILITY', message: 'Peer provider absent in this isolated fixture' } },
  }));
  return backend;
}

test('unqualified Dukascopy modes do not create mock progress or coverage', async ({ page }) => {
  const backend = await installBackend(page, [dataset('EURUSD')]);
  await page.goto('/');
  await page.getByRole('button', { name: 'Data Manager', exact: true }).click();
  await page.getByRole('checkbox', { name: 'Select EURUSD', exact: true }).check();
  await page.getByRole('button', { name: 'Dukascopy data', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Download data for existing symbol', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: /Download Dukascopy data for/ });
  await expect(dialog.getByRole('radio', { name: 'Standard download - Dukascopy servers' })).toBeChecked();
  await dialog.getByRole('radio', { name: /StrategyQuant CDN/ }).check();
  await expect(dialog.getByRole('button', { name: 'Start download' })).toBeDisabled();
  await dialog.getByRole('radio', { name: /StrategyQuant Hong Kong CDN/ }).check();
  await expect(dialog.getByRole('button', { name: 'Start download' })).toBeDisabled();
  await expect(dialog.getByText('Downloads are unavailable until the market catalog is provisioned.')).toBeVisible();
  expect(await page.evaluate(() => localStorage.getItem('sqx-data-download-v1'))).toBeNull();
  expect(backend.requests.some(request => request.operation === 'sources.dukascopy.download.start')).toBe(false);
});

for (const scenario of [
  { name: 'complete standard', mode: 'standard', state: 'succeeded', outcome: 'complete', message: 'completed 100%' },
  { name: 'partial standard', mode: 'standard', state: 'succeeded', outcome: 'partial', message: 'partially completed 100%: Partial download; available rows retained; 1 failed and 0 missing chunks' },
  { name: 'failed standard', mode: 'standard', state: 'failed', outcome: 'pending', message: 'Remote transport exhausted' },
  { name: 'empty standard', mode: 'standard', state: 'succeeded', outcome: 'empty', message: 'finished without data 100%: No data downloaded' },
  { name: 'cancelled standard', mode: 'standard', state: 'cancelled', outcome: 'pending', message: 'cancelled 50%' },
  { name: 'complete CDN', mode: 'cdn', state: 'succeeded', outcome: 'complete', message: 'completed 100%' },
]) {
  test(`download keeps workspace and host progress visible: ${scenario.name}`, async ({ page }) => {
    const errors: string[] = [];
    page.on('pageerror', error => errors.push(error.message));
    page.on('console', message => {
      if (message.type() === 'error' && message.text().includes('in progress')) errors.push(message.text());
    });
    const backend = await installBackend(page, [dataset('CADCHF')]);
    await page.route('**/sources.dukascopy.catalog', route => route.fulfill({ json: { status: 'success', data: {
      definitions_available: true, source: 'dukascopy', formats: ['m1'],
      modes: { standard: 'available', cdn: 'available', 'cdn-cn': 'available' },
      reason: '', datasets: backend.rows, broker_catalog_status: 'available', brokers: [],
    } } }));
    let submitted = 0;
    let polls = 0;
    let finish = false;
    await page.route('**/sources.dukascopy.download.start', route => {
      submitted++;
      expect(route.request().postDataJSON()).toMatchObject({ dataset_id: 'db:CADCHF', mode: scenario.mode });
      return route.fulfill({ json: { status: 'success', data: { job_id: 'fixture-download', request_id: 'fixture' } } });
    });
    await page.route('**/sources.dukascopy.download.status', route => {
      polls++;
      if (finish && scenario.state === 'succeeded' && scenario.outcome !== 'empty') backend.rows = [dataset('CADCHF', 17)];
      return route.fulfill({ json: { status: 'success', data: {
        job_id: 'fixture-download', state: finish ? scenario.state : 'running',
        progress: finish && scenario.state === 'succeeded' ? 1 : .5,
        completed_days: finish ? 2 : 1, published_days: finish && scenario.state === 'succeeded' ? 2 : 0,
        missing_days: 0, skipped_days: 0, outcome: finish ? scenario.outcome : 'pending',
        failed_chunks: finish && scenario.outcome === 'partial' ? 1 : 0, missing_chunks: 0,
        ...(finish && scenario.state === 'failed' ? { error: 'Remote transport exhausted' } : {}),
      } } });
    });
    await page.goto('/datamanager');
    await expect(page.getByText('Host online')).toBeVisible();
    await page.getByRole('checkbox', { name: 'Select CADCHF', exact: true }).check();
    await page.getByRole('button', { name: 'Dukascopy data', exact: true }).click();
    await page.getByRole('menuitem', { name: 'Download data for existing symbol', exact: true }).click();
    const dialog = page.getByRole('dialog', { name: "Download Dukascopy data for 'CADCHF'", exact: true });
    await dialog.getByLabel('From', { exact: true }).fill('2026-01-01');
    await dialog.getByLabel('To', { exact: true }).fill('2026-01-02');
    if (scenario.mode === 'cdn') await dialog.getByRole('radio', { name: /StrategyQuant CDN \(/ }).check();
    await dialog.getByRole('button', { name: 'Start download', exact: true }).click();
    if (scenario.mode === 'cdn') await page.getByRole('button', { name: 'OK', exact: true }).click();
    await expect(page.getByRole('dialog')).toHaveCount(0);
    const progress = page.getByLabel('Data Manager progress');
    await expect(progress).toContainText('dukascopy data operation running 50%');
    await expect(progress.getByRole('button', { name: 'Stop all' })).toBeEnabled();
    await expect(progress.getByRole('button', { name: 'Pause all' })).toBeDisabled();
    await expect(page.getByRole('table', { name: 'Historical data', exact: true })).toBeVisible();
    expect(submitted).toBe(1);
    expect(polls).toBeGreaterThan(0);
    finish = true;
    await expect(progress).toContainText(scenario.message);
    await expect(progress.getByRole('button', { name: 'Stop all' })).toBeDisabled();
    await expect(page.getByText('This contribution is unavailable. Stored data is retained.', { exact: true })).toHaveCount(0);
    const row = page.getByRole('table', { name: 'Historical data', exact: true }).getByRole('row').filter({ hasText: 'CADCHF' });
    await expect(row.getByRole('cell').nth(10)).toHaveText(scenario.state === 'succeeded' && scenario.outcome !== 'empty' ? '17' : '0');
    // Completed display is transient; stored rows survive and another task is ready.
    await expect(progress).toContainText('No active operations', { timeout: 15000 });
    await expect(row.getByRole('cell').nth(10)).toHaveText(scenario.state === 'succeeded' && scenario.outcome !== 'empty' ? '17' : '0');
    await page.getByRole('button', { name: 'Dukascopy data', exact: true }).click();
    await page.getByRole('menuitem', { name: 'Download data for existing symbol', exact: true }).click();
    await expect(dialog).toBeVisible();
    expect(errors).toEqual([]);
    expect(submitted).toBe(1);
  });
}
