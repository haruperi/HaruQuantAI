import { expect, test, type Page } from '@playwright/test';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const dataset = {
  id: 'server:EURUSD', symbol: 'EURUSD_REAL', instrument: 'EURUSD.fx',
  broker: 'broker-1', broker_name: 'Research Broker', underlying: 'EUR/USD Spot',
  timeframe: 'M1', timezone: 'UTC', date_from: '2026-01-01T00:00:00',
  date_to: '2026-01-05T00:00:00', total_days: 4, total_records: 12345,
  bars: 12345, source: 'Dukascopy', category: 'Forex', data_type: 'Forex',
  path: 'data/history/dukascopy/EURUSD/M1.parquet', bar_type: 'end',
};

async function openCatalog(page: Page, catalog: () => object | Promise<object>) {
  const paths: string[] = [];
  await page.addInitScript(() => {
    localStorage.setItem('sqx-data-manager-v1', JSON.stringify({
      version: 1, brokers: [], definitions: [{
        id: 'cached:fake', symbol: 'CACHED_FAKE', source: 'Yahoo', underlying: 'CACHED_FAKE',
        instrument: 'CACHED_FAKE', timeframe: 'D1', broker: 'default', brokerName: 'Default',
        timezone: 'UTC', category: 'Stock', from: '', to: '', bars: 999,
      }],
    }));
    const original = window.fetch.bind(window);
    window.fetch = ((input: RequestInfo | URL, init?: RequestInit) => String(input).includes('/api/v1/events?')
      ? Promise.resolve(new Response(new ReadableStream<Uint8Array>({ start() {} }), { headers: { 'Content-Type': 'text/event-stream' } }))
      : original(input, init)) as typeof fetch;
  });
  await page.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname;
    paths.push(path);
    if (path === '/api/v1/data/home/datasets') {
      const result = await catalog();
      await route.fulfill({ json: result });
      return;
    }
    const data = path.endsWith('/auth/login') ? { token: 'catalog-test-session' }
      : path.endsWith('/settings') ? { revision: 1, values: {} }
      : path.endsWith('/status') ? { cpu_count: 4 }
      : path === '/api/v1/home' ? { recent_projects: [] }
      : [];
    await route.fulfill({ json: { status: 'success', data } });
  });
  await page.goto('/');
  const dialog = page.getByRole('dialog', { name: 'Connect to HaruQuantAI host' });
  await dialog.getByLabel('Host password').fill('test-password');
  await dialog.getByRole('button', { name: 'Connect', exact: true }).click();
  await expect(dialog).toHaveCount(0);
  await page.getByRole('button', { name: 'Data Manager', exact: true }).click();
  await expect(page.getByRole('table', { name: 'Historical data' })).toBeVisible();
  return paths;
}

test('Historical data renders only Home catalog rows and clears a refreshed empty catalog', async ({ page }) => {
  let items = [dataset];
  const paths = await openCatalog(page, () => ({ status: 'success', data: items }));
  const table = page.getByRole('table', { name: 'Historical data' });
  const row = table.getByRole('row').filter({ hasText: 'EURUSD_REAL' });
  await expect(row).toHaveCount(1);
  await expect(row.getByRole('cell')).toHaveText([
    '', 'EURUSD_REAL', 'EURUSD.fx', 'Research Broker', 'EUR/USD Spot', 'M1', 'UTC',
    '2026-01-01', '2026-01-05', '4', '12,345', 'Dukascopy', 'End of bar', 'Forex',
    'data/history/dukascopy/EURUSD/M1.parquet', 'Ready', '×',
  ]);
  await expect(table).not.toContainText('CACHED_FAKE');
  expect(paths).toContain('/api/v1/data/home/datasets');
  expect(paths).not.toContain('/api/v1/data/datasets');
  const filter = page.getByRole('textbox', { name: 'Filter items' });
  await filter.fill('absent');
  await expect(table).toContainText('No matching data.');
  await filter.fill('');
  await page.getByRole('combobox', { name: 'Broker profile', exact: true }).selectOption('Research Broker');
  await expect(row).toBeVisible();
  await page.getByRole('checkbox', { name: 'Select EURUSD_REAL', exact: true }).check();
  items = [];
  await page.getByRole('button', { name: 'Refresh dataset catalog', exact: true }).click();
  await expect(table).toContainText('No saved datasets found in catalog.');
  await expect(page.getByRole('checkbox', { name: 'Select all visible datasets' })).not.toBeChecked();
  await page.screenshot({ path: join(tmpdir(), 'haru-datamanager-empty-catalog.png') });
});

test('initial load excludes cache, failures are visible, and retry recovers', async ({ page }) => {
  let finishLoad: (result: object) => void = () => { throw new Error('Catalog request not started'); };
  let initial = true;
  let failure = false;
  await openCatalog(page, () => {
    if (initial) return new Promise<object>(resolve => { finishLoad = resolve; });
    return failure ? { status: 'error', error: { code: 'UNAVAILABLE', message: 'Catalog unavailable' } }
      : { status: 'success', data: [dataset] };
  });
  const table = page.getByRole('table', { name: 'Historical data' });
  await expect(table).toContainText('Loading saved dataset catalog…');
  await expect(table).not.toContainText('CACHED_FAKE');
  initial = false;
  finishLoad({ status: 'error', error: { code: 'UNAVAILABLE', message: 'Catalog unavailable' } });
  await expect(page.getByRole('alert')).toContainText('Catalog unavailable');
  await expect(table).toContainText('Saved dataset catalog unavailable.');
  await page.getByRole('button', { name: 'Retry dataset catalog', exact: true }).click();
  await expect(table).toContainText('EURUSD_REAL');
  await expect(page.getByRole('alert')).toHaveCount(0);
  failure = true;
  await page.getByRole('button', { name: 'Refresh dataset catalog', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Showing the last successful catalog; it may be out of date.');
  await expect(table).toContainText('EURUSD_REAL');
  await page.screenshot({ path: join(tmpdir(), 'haru-datamanager-stale-catalog.png') });
});
