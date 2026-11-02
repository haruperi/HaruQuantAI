import { normalizeSymbolContract } from '../../workspaces/data_manager/plugins/Common/symbolContract';
import { expect, test, type Page } from '@playwright/test';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const layout = {
  tabs: ['data', 'symbols', 'sessions', 'brokers', 'custom-data', 'chart', 'home', 'stock-groups', 'log'].map((id, index) => ({ id, title: ['Data', 'Symbols', 'Sessions', 'Brokers', 'Custom Data', 'Chart', 'Home', 'Stock groups', 'Log'][index], core: index < 5 })),
  active_tab: 'data', layout: { core_group: 'catalogs', chart_position: 'right' },
};
const datasets = ['M1', 'D1'].map((timeframe) => ({
  id: `saved:${timeframe}`, symbol: 'EURUSD', symbolDefinition: 'EURUSD', broker: 'b1', broker_name: 'Research', underlying: 'EURUSD', timeframe, timezone: 'UTC',
  date_from: '2026-01-01', date_to: '2026-01-02', total_days: 1, total_records: 2, bars: 2, source: 'recorded', category: 'Forex', data_type: 'Forex',
  path: '', bar_type: 'start',
}));
const recordedRows = [0, 60].map(offset => ({ time: 1767225600 + offset, open: 1, high: 3, low: 0.5, close: 2, volume: 30 }));

async function connect(page: Page, options: { failInit?: boolean } = {}) {
  const calls: string[] = [];
  const browserErrors: string[] = [];
  page.on('pageerror', error => browserErrors.push(error.message));
  page.on('close', () => expect(browserErrors).toEqual([]));
  let initFailures = options.failInit ? 2 : 0;
  await page.addInitScript(() => {
    const original = window.fetch.bind(window);
    window.fetch = ((input: RequestInfo | URL, init?: RequestInit) => String(input).includes('/api/v1/events?')
      ? Promise.resolve(new Response(new ReadableStream<Uint8Array>({ start() {} }), { headers: { 'Content-Type': 'text/event-stream' } })) : original(input, init)) as typeof fetch;
  });
  await page.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname.replace(/\/instruments(?=\/|$)/g, '/symbols').replace('/import-instruments', '/import-symbols');
    calls.push(path);
    let data: unknown = [];
    if (path.endsWith('/auth/login')) data = { token: 'workspace-test-session' };
    else if (path.endsWith('/settings')) data = { revision: 1, values: {} };
    else if (path.endsWith('/status')) data = { cpu_count: 4 };
    else if (path === '/api/v1/home') data = { recent_projects: [] };
    else if (path === '/api/v1/data/home/overview') data = { datasets_count: 2, symbols_count: 1, sessions_count: 1, baskets_count: 1, active_providers_count: 1, total_bars: 4 };
    else if (path === '/api/v1/data/home/datasets') data = datasets;
    else if (path === '/api/v1/data/workspace') {
      if (initFailures > 0) { initFailures--; await route.fulfill({ status: 503, json: { status: 'error', error: { code: 'UNAVAILABLE', message: 'Workspace unavailable' } } }); return; }
      data = layout;
    } else if (path.startsWith('/api/v1/data/workspace/tabs/')) {
      const id = normalizeSymbolContract(route.request().postDataJSON())?.context?.dataset_id;
      const selection = datasets.find(row => row.id === id) ?? null;
      data = { active_tab: path.split('/').at(-1), selection, preview: {
        state: selection ? 'ready' : 'unavailable',
        reason: selection ? 'No recorded history path in catalog.' : 'Select a saved dataset.',
        rows: selection ? recordedRows : [], limit: 500,
      } };
    }
    await route.fulfill({ json: { status: 'success', data } });
  });
  await page.goto('/');
  const dialog = page.getByRole('dialog', { name: 'Connect to HaruQuantAI host' });
  await dialog.getByLabel('Host password').fill('test-password');
  await dialog.getByRole('button', { name: 'Connect', exact: true }).click();
  await expect(dialog).toHaveCount(0);
  await page.getByRole('button', { name: 'Data Manager', exact: true }).click();
  return calls;
}

test('top navigation activates every panel, Arrange docks/closes without lower tab headers, and chart opens explicitly', async ({ page }) => {
  await connect(page);
  const nav = page.getByRole('navigation', { name: 'Data Manager workspace navigation', exact: true });
  await expect(nav).toBeVisible();
  await expect(page.getByRole('tab')).toHaveCount(0);
  await expect(page.locator('.dv-tabs-and-actions-container:visible')).toHaveCount(0);
  const host = page.locator('.dm-dock-host');
  await expect(host).toHaveAttribute('data-open-panels', 'data,symbols,sessions,brokers,custom-data');
  await expect(page.locator('[data-workspace-panel="data"]')).toBeVisible();
  await nav.getByRole('button', { name: 'Export', exact: true }).click();
  await expect(page.getByLabel('Data export operations')).toBeVisible();
  await expect(page.getByRole('table', { name: 'Historical data', exact: true })).toBeVisible();
  await nav.getByRole('button', { name: 'Tools', exact: true }).click();
  await expect(page.getByLabel('Data tools')).toBeVisible();
  await expect(page.getByRole('table', { name: 'Historical data', exact: true })).toBeVisible();
  for (const [buttonName, panelId, tableName] of [
    ['Symbols', 'symbols', 'Symbols'],
    ['Sessions', 'sessions', 'Sessions'],
    ['External indicators', 'custom-data', 'External indicators'],
    ['Stock groups', 'stock-groups', 'Stock groups'],
    ['Broker profiles', 'brokers', 'Broker profiles'],
  ] as const) {
    await nav.getByRole('button', { name: buttonName, exact: true }).click();
    await expect(page.locator(`[data-workspace-panel="${panelId}"]`)).toBeVisible();
    await expect(page.getByRole('table', { name: tableName, exact: true })).toBeVisible();
  }
  await nav.getByRole('button', { name: 'Home', exact: true }).click();
  await expect(page.locator('[data-workspace-panel="home"]')).toBeVisible();
  await nav.getByRole('button', { name: 'Log', exact: true }).click();
  await expect(page.getByRole('log', { name: 'Data Manager log', exact: true })).toBeVisible();
  await nav.getByRole('button', { name: 'Symbols', exact: true }).click();
  await expect(page.getByRole('table', { name: 'Symbols', exact: true })).toBeVisible();
  await nav.getByRole('button', { name: 'Arrange', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Close panel', exact: true }).click();
  await expect(page.locator('[data-workspace-panel="symbols"]')).toHaveCount(0);
  await expect(host).not.toHaveAttribute('data-open-panels', /symbols/);
  await nav.getByRole('button', { name: 'Symbols', exact: true }).click();
  await expect(page.locator('[data-workspace-panel="symbols"]')).toHaveCount(1);
  await expect(host).toHaveAttribute('data-open-panels', /symbols/);
  await expect(page.getByRole('table', { name: 'Symbols', exact: true })).toBeVisible();
  await nav.getByRole('button', { name: 'Data sources', exact: true }).click();
  await nav.getByRole('button', { name: 'Chart', exact: true }).click();
  const preview = page.getByRole('main', { name: 'Linked recorded data preview' });
  await expect(preview).toContainText('Select a saved dataset.');
  await expect(preview.getByRole('table', { name: 'Recorded bars' })).toHaveCount(0);
  const dataBox = await page.locator('[data-workspace-panel="data"]').boundingBox();
  const chartBox = await page.locator('[data-workspace-panel="chart"]').boundingBox();
  expect(dataBox && chartBox && chartBox.x >= dataBox.x + dataBox.width - 8).toBeTruthy();
  const sashes = page.locator('.dv-sash');
  for (const sash of await sashes.all()) {
    const box = await sash.boundingBox();
    if (box && box.height > 100 && box.width < 15) {
      await page.mouse.move(box.x + box.width / 2, box.y + box.height / 2);
      await page.mouse.down(); await page.mouse.move(box.x - 80, box.y + box.height / 2, { steps: 8 }); await page.mouse.up();
      break;
    }
  }
  await expect.poll(async () => (await page.locator('[data-workspace-panel="chart"]').boundingBox())?.width).not.toBe(chartBox?.width);
  const groupsBefore = await page.locator('.dv-groupview').count();
  await nav.getByRole('button', { name: 'Symbols', exact: true }).click();
  await nav.getByRole('button', { name: 'Arrange', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Move panel below', exact: true }).click();
  await expect(page.locator('.dv-groupview')).toHaveCount(groupsBefore + 1);
  await expect(page.locator('.dv-tabs-and-actions-container:visible')).toHaveCount(0);
  await page.screenshot({ path: join(tmpdir(), 'haru-datamanager-dockview-recorded.png') });
  await nav.getByRole('button', { name: 'Arrange', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Return to main group', exact: true }).click();
  await expect(page.locator('.dv-groupview')).toHaveCount(groupsBefore);
  await nav.getByRole('button', { name: 'Chart', exact: true }).click();
  await nav.getByRole('button', { name: 'Arrange', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Close panel', exact: true }).click();
  await expect(page.locator('[data-workspace-panel="chart"]')).toHaveCount(0);
  await nav.getByRole('button', { name: 'Chart', exact: true }).click();
  await expect(preview).toContainText('Select a saved dataset.');
  await expect(page.locator('[data-workspace-panel="chart"]')).toHaveCount(1);
  await expect(page.getByRole('tab')).toHaveCount(0);
});

test('symbol clicks and double clicks leave selection and workspace unchanged', async ({ page }) => {
  const calls = await connect(page);
  const table = page.getByRole('table', { name: 'Historical data', exact: true });
  await expect(table.getByRole('row')).toHaveCount(3);
  const host = page.locator('.dm-dock-host');
  const before = await host.getAttribute('data-open-panels');
  const requests = calls.filter(path => path.includes('/workspace/tabs/')).length;
  for (const row of await table.locator('tbody tr').all()) {
    const symbol = row.getByRole('cell').nth(1);
    await expect(symbol.getByRole('button')).toHaveCount(0);
    await symbol.click();
    await symbol.dblclick();
    await expect(row.getByRole('checkbox')).not.toBeChecked();
    await expect(row).not.toHaveClass(/selected/);
    await expect(host).toHaveAttribute('data-open-panels', before!);
    await expect(page.locator('[data-workspace-panel="chart"]')).toHaveCount(0);
  }
  await expect(table.getByRole('button', { name: /^Preview / })).toHaveCount(0);
  expect(calls.filter(path => path.includes('/workspace/tabs/'))).toHaveLength(requests);
  const checkbox = table.getByRole('checkbox', { name: 'Select EURUSD', exact: true }).first();
  await checkbox.check();
  await table.getByRole('row').nth(1).getByRole('cell').nth(1).click();
  await expect(checkbox).toBeChecked();
  await expect(page.locator('[data-workspace-panel="chart"]')).toHaveCount(0);
  await page.screenshot({ path: join(tmpdir(), 'haru-datamanager-inert-symbols.png') });
});

test('host initialization can retry and chart opens without a dataset selection', async ({ page }) => {
  await connect(page, { failInit: true });
  await expect(page.getByRole('alert')).toContainText('Workspace unavailable');
  await page.getByRole('button', { name: 'Retry workspace', exact: true }).click();
  await page.getByRole('navigation', { name: 'Data Manager workspace navigation' }).getByRole('button', { name: 'Chart', exact: true }).click();
  const preview = page.getByRole('main', { name: 'Linked recorded data preview' });
  await expect(preview).toContainText('Select a saved dataset.');
  await expect(preview.getByRole('table', { name: 'Recorded bars' })).toHaveCount(0);
  await expect(preview.locator('canvas')).toHaveCount(0);
});


test('dataset properties submits the edited catalog fields to the host', async ({ page }) => {
  await connect(page);
  let submitted: Record<string, unknown> | undefined;
  await page.route('**/api/v1/data/datasets/**', async route => {
    if (route.request().method() !== 'PUT') return route.fallback();
    submitted = route.request().postDataJSON();
    await route.fulfill({json:{status:'success', data:{...datasets[0], ...submitted}}});
  });
  await page.getByRole('button', {name:'Edit dataset EURUSD', exact:true}).first().click();
  const modal = page.getByRole('dialog', {name:'Dataset properties', exact:true});
  await expect(modal).toBeVisible();
  await modal.getByLabel('Category', {exact:true}).fill('CFD');
  await modal.getByRole('button', {name:'Save properties', exact:true}).click();
  await expect(modal).toHaveCount(0);
  expect(submitted?.category).toBe('CFD');
  expect(submitted?.symbol).toBe('EURUSD');
});
