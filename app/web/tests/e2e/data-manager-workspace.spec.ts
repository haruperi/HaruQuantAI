import { normalizeSymbolContract } from '../../workspaces/data_manager/plugins/Common/symbolContract';
import { expect, test, type Page } from '@playwright/test';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const layout = {
  tabs: ['data', 'symbols', 'sessions', 'brokers', 'custom-data', 'chart', 'home', 'stock-groups', 'log'].map((id, index) => ({ id, title: ['Data', 'Symbols', 'Sessions', 'Brokers', 'Custom Data', 'Chart', 'Home', 'Stock groups', 'Log'][index], core: index < 5 })),
  active_tab: 'data', layout: { core_group: 'catalogs', chart_position: 'right' },
};
const datasets = ['M1', 'D1'].map((timeframe, index) => ({
  id: `saved:${timeframe}`, symbol: 'EURUSD', symbolDefinition: 'EURUSD', broker: 'b1', broker_name: 'Research', underlying: 'EURUSD', timeframe, timezone: 'UTC',
  date_from: '2026-01-01', date_to: '2026-01-02', total_days: 1, total_records: 2, bars: 2, source: 'recorded', category: 'Forex', data_type: 'Forex',
  path: '', bar_type: 'start', symbol_definition_id: index + 1, session_id: 7,
}));
function instrumentRecord(id: string, symbol: string, broker = 1) {
  return { id, symbol, broker_id: broker, description: 'Saved ' + symbol, data_type: 'Forex',
    point_value: 100, tick_size: 0.001, tick_step: 0.001, contract_size: 100000, pip_size: 0.001,
    margin_rate: 0.05, decimals: 3, tick_value_in_money: 1, min_volume: 0.01, max_volume: 100, lot_step: 0.01,
    default_spread: 361, default_slippage: 500, min_distance: 0, order_size_multiplier: 1, order_size_step: 0.01,
    commissions: '0', swap_long: -460.53, swap_short: 247.5, swap_3day_day: 2,
    swap_settings: { use: true, type: 'points', long: -460.53, short: 247.5, tripleSwapOn: 'WEDNESDAY', rolloutHour: '23:00' } };
}
const instrumentRecords = [instrumentRecord('1', 'EURUSD_RESEARCH'), { ...instrumentRecord('2', 'EURUSD_OTHER', 2), swap_settings: null }];
const recordedRows = [0, 60].map(offset => ({ time: 1767225600 + offset, open: 1, high: 3, low: 0.5, close: 2, volume: 30 }));

async function connect(page: Page, options: { failInit?: boolean; unlinked?: boolean; catalogue?: object[]; catalogueGate?: Promise<void>; datasetBroker?: string; profiles?: object[] } = {}) {
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
    else if (path === '/api/v1/data/home/datasets') data = options.unlinked ? datasets.map(row => ({ ...row, symbol: 'EURUSD_DUKASCOPY', symbol_definition_id: null, broker: options.datasetBroker ?? '1', broker_name: options.datasetBroker ?? 'Broker 1' })) : datasets;
    else if (path === '/api/v1/data/symbols') { await options.catalogueGate; data = options.catalogue ?? instrumentRecords; }
    else if (path === '/api/v1/data/brokers') data = options.profiles ?? [];
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


test('donor dataset editor preserves metadata and saves name and instrument link', async ({ page }) => {
  await connect(page);
  let submitted: Record<string, unknown> | undefined;
  await page.route('**/api/v1/data/datasets/**', async route => {
    if (route.request().method() !== 'PUT') return route.fallback();
    submitted = route.request().postDataJSON();
    await route.fulfill({json:{status:'success', data:{...datasets[0], ...submitted}}});
  });
  await page.getByRole('button', {name:'Edit dataset EURUSD', exact:true}).first().click();
  const modal = page.getByRole('dialog', {name:'Edit symbol', exact:true});
  await expect(modal).toBeVisible();
  await modal.getByLabel('Data symbol name', {exact:true}).fill('EURUSD_RENAMED');
  await modal.getByRole('combobox', { name: 'Instrument', exact: true }).selectOption('2');
  await modal.getByRole('button', {name:'Save', exact:true}).click();
  await expect(modal).toHaveCount(0);
  expect(submitted?.category).toBe('Forex');
  expect(submitted?.symbol_definition_id).toBe(2);
  expect(submitted?.session_id).toBe(7);
  expect(submitted?.timezone).toBe('UTC');
  expect(submitted).not.toHaveProperty('swap_settings');
  expect(submitted?.symbol).toBe('EURUSD_RENAMED');
});

test('dataset editor reference sections, broker filter, saved swaps and responsive layout', async ({ page }) => {
  await connect(page);
  await page.getByRole('button', { name: 'Edit dataset EURUSD', exact: true }).first().click();
  const modal = page.getByRole('dialog', { name: 'Edit symbol', exact: true });
  for (const section of ['Data settings', 'Choose instrument', 'Swap']) {
    await expect(modal.getByRole('heading', { name: section, exact: true })).toBeVisible();
  }
  await expect(modal.getByLabel('Bar type', { exact: true })).toBeDisabled();
  await expect(modal.getByLabel('Timezone', { exact: true })).toHaveValue('UTC');
  await expect(modal.getByLabel('Pip/Tick size *', { exact: true })).toHaveValue('0.001');
  await expect(modal.getByLabel('Point value in $ *', { exact: true })).toHaveValue('100');
  await expect(modal.getByLabel('Long', { exact: true })).toHaveValue('-460.53');
  await expect(modal.getByLabel('Rollout hour', { exact: true })).toHaveValue('23:00');
  await expect(modal.getByLabel('Use', { exact: true })).toBeChecked();
  await expect(modal.getByLabel('Use', { exact: true })).toBeDisabled();
  await page.screenshot({ path: join(tmpdir(), 'haru-dataset-edit-dark.png') });
  await modal.getByRole('combobox', { name: 'Filter instruments by broker' }).selectOption('2');
  await expect(modal.getByRole('combobox', { name: 'Instrument', exact: true })).toHaveValue('1');
  await modal.getByRole('combobox', { name: 'Instrument', exact: true }).selectOption('2');
  await expect(modal.getByLabel('Swap type', { exact: true })).toHaveValue('Not recorded');
  await expect(modal.getByLabel('Rollout hour', { exact: true })).toHaveValue('Not recorded');
  await expect(modal.getByText('Use, swap type and rollout hour were not recorded.', { exact: false })).toBeVisible();
  await modal.getByRole('button', { name: 'Help', exact: true }).click();
  await expect(page.getByRole('dialog', { name: 'Swap explanation', exact: true })).toBeVisible();
  await page.keyboard.press('Escape');
  await expect(modal.getByRole('combobox', { name: 'Instrument', exact: true })).toHaveValue('2');
  await page.evaluate(() => { document.documentElement.dataset.theme = 'light'; });
  await page.screenshot({ path: join(tmpdir(), 'haru-dataset-edit-light.png') });
  await page.setViewportSize({ width: 520, height: 700 });
  await expect(modal.getByRole('button', { name: 'Save', exact: true })).toBeInViewport();
  expect(await modal.evaluate(element => element.scrollWidth <= element.clientWidth)).toBe(true);
  const bounds = await modal.boundingBox();
  expect(bounds!.x).toBeGreaterThanOrEqual(0);
  expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(520);
  await page.screenshot({ path: join(tmpdir(), 'haru-dataset-edit-narrow.png') });
  await modal.getByRole('button', { name: 'Save', exact: true }).focus();
  await page.keyboard.press('Tab');
  await expect(modal.getByRole('button', { name: 'Close', exact: true }).first()).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(modal).toHaveCount(0);
});

test('dataset editor creates a host instrument and returns without losing dataset draft', async ({ page }) => {
  await connect(page);
  let created: Record<string, unknown> | undefined;
  await page.route('**/api/v1/data/instruments', async route => {
    if (route.request().method() !== 'POST') return route.fallback();
    created = route.request().postDataJSON();
    await route.fulfill({ json: { status: 'success', data: { ...instrumentRecord('3', 'NEW_INSTRUMENT', -1), ...created, id: '3' } } });
  });
  await page.getByRole('button', { name: 'Edit dataset EURUSD', exact: true }).first().click();
  const modal = page.getByRole('dialog', { name: 'Edit symbol', exact: true });
  await modal.getByLabel('Data symbol name', { exact: true }).fill('DRAFT_NAME');
  await modal.getByRole('button', { name: 'Add new instrument', exact: true }).click();
  const add = page.getByRole('dialog', { name: 'Add symbol', exact: true });
  await expect(modal).toHaveCount(0);
  await add.getByRole('button', { name: 'Close', exact: true }).first().click();
  await expect(modal.getByLabel('Data symbol name', { exact: true })).toHaveValue('DRAFT_NAME');
  await modal.getByRole('button', { name: 'Add new instrument', exact: true }).click();
  await add.getByRole('textbox', { name: 'Symbol', exact: true }).fill('NEW_INSTRUMENT');
  await add.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(add).toHaveCount(0);
  expect(created?.symbol).toBe('NEW_INSTRUMENT');
  await expect(modal.getByLabel('Data symbol name', { exact: true })).toHaveValue('DRAFT_NAME');
  await expect(modal.getByRole('combobox', { name: 'Instrument', exact: true })).toHaveValue('3');
});

test('dataset editor reports catalogue and save errors without changing shared instruments', async ({ page }) => {
  await connect(page);
  let failCatalogue = true;
  let writes = 0;
  await page.route('**/api/v1/data/instruments', async route => {
    await route.fulfill(failCatalogue
      ? { status: 503, json: { status: 'error', error: { code: 'UNAVAILABLE', message: 'Instrument catalogue offline' } } }
      : { json: { status: 'success', data: instrumentRecords } });
  });
  await page.evaluate(async () => {
    const path = '/workspaces/data_manager/plugins/Catalogs/Symbols/symbolsStore.ts';
    const { useSymbols } = await import(/* @vite-ignore */ path);
    await useSymbols.getState().refreshFromServer();
  });
  await page.getByRole('button', { name: 'Edit dataset EURUSD', exact: true }).first().click();
  const modal = page.getByRole('dialog', { name: 'Edit symbol', exact: true });
  await expect(modal.getByRole('alert')).toContainText('Instrument catalogue offline');
  await expect(modal.getByRole('button', { name: 'Save', exact: true })).toBeDisabled();
  failCatalogue = false;
  await modal.getByRole('button', { name: 'Retry instruments', exact: true }).click();
  await expect(modal.getByRole('button', { name: 'Save', exact: true })).toBeEnabled();
  await page.route('**/api/v1/data/datasets/**', async route => {
    if (route.request().method() !== 'PUT') return route.fallback();
    writes++;
    await route.fulfill({ status: 409, json: { status: 'error', error: { code: 'CONFLICT', message: 'Dataset was not saved' } } });
  });
  await modal.getByLabel('Data symbol name', { exact: true }).fill('RETRY_NAME');
  await modal.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(modal.getByRole('alert')).toContainText('Dataset was not saved');
  await expect(modal.getByLabel('Data symbol name', { exact: true })).toHaveValue('RETRY_NAME');
  expect(writes).toBe(1);
});

test('unlinked dataset pre-populates the unique exact instrument from its named broker', async ({ page }) => {
  await connect(page, {
    unlinked: true, datasetBroker: 'Dukascopy',
    profiles: [{ id: '1', name: 'Dukascopy', description: '', timezone: 'UTC', postfix: '', stockpicker_use: false, mt_use: true, is_system: false, stocks: [], customized_stocks: 0, customized_symbols: 0, total_symbols: 0, total_sessions: 0, spread_model: { model: 'inherit' }, commission_model: { model: 'inherit' } }],
    catalogue: [instrumentRecord('1', 'eurusd'), instrumentRecord('2', 'EURUSD_DUKASCOPY', 2)],
  });
  let submitted: Record<string, unknown> | undefined;
  await page.route('**/api/v1/data/datasets/**', async route => {
    if (route.request().method() !== 'PUT') return route.fallback();
    submitted = route.request().postDataJSON();
    await route.fulfill({ json: { status: 'success', data: { ...datasets[0], ...submitted } } });
  });
  await page.getByRole('button', { name: 'Edit dataset EURUSD_DUKASCOPY', exact: true }).first().click();
  const modal = page.getByRole('dialog', { name: 'Edit symbol', exact: true });
  await expect(modal.getByRole('combobox', { name: 'Instrument', exact: true })).toHaveValue('1');
  await expect(modal.getByLabel('Broker profile *', { exact: true })).toHaveValue('Dukascopy');
  await expect(modal.getByLabel('Pip/Tick size *', { exact: true })).toHaveValue('0.001');
  await expect(modal.getByLabel('Long', { exact: true })).toHaveValue('-460.53');
  await expect(modal.getByLabel('Data symbol name', { exact: true })).toHaveValue('EURUSD_DUKASCOPY');
  expect(submitted).toBeUndefined();
  await page.screenshot({ path: join(tmpdir(), 'haru-dataset-edit-prepopulated.png') });
  await modal.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(modal).toHaveCount(0);
  expect(submitted?.symbol_definition_id).toBe(1);
});

test('unlinked dataset waits for catalogue and preserves explicit choices across refresh', async ({ page }) => {
  let release: () => void = () => {};
  const gate = new Promise<void>(resolve => { release = resolve; });
  const catalogue = [instrumentRecord('1', 'EURUSD'), instrumentRecord('2', 'OTHER')];
  await connect(page, { unlinked: true, catalogue, catalogueGate: gate });
  await page.getByRole('button', { name: 'Edit dataset EURUSD_DUKASCOPY', exact: true }).first().click();
  const modal = page.getByRole('dialog', { name: 'Edit symbol', exact: true });
  await expect(modal.getByRole('status')).toContainText('Loading instrument catalogue');
  await expect(modal.getByLabel('Broker profile *', { exact: true })).toHaveValue('Broker 1');
  await expect(modal.getByLabel('Data type *', { exact: true })).toHaveValue('Forex');
  release();
  const picker = modal.getByRole('combobox', { name: 'Instrument', exact: true });
  await expect(picker).toHaveValue('1');
  await picker.selectOption('2');
  const refresh = async () => page.evaluate(async () => {
    const path = '/workspaces/data_manager/plugins/Catalogs/Symbols/symbolsStore.ts';
    const { useSymbols } = await import(/* @vite-ignore */ path);
    await useSymbols.getState().refreshFromServer();
  });
  await refresh();
  await expect(picker).toHaveValue('2');
  await picker.selectOption('');
  await refresh();
  await expect(picker).toHaveValue('');
});

for (const scenario of ['ambiguous', 'unmatched'] as const) {
  test(`unlinked dataset leaves ${scenario} instruments unresolved`, async ({ page }) => {
    const catalogue = scenario === 'ambiguous'
      ? [instrumentRecord('1', 'EURUSD'), instrumentRecord('2', 'EURUSD_DUKASCOPY')]
      : [instrumentRecord('1', 'USDJPY'), instrumentRecord('2', 'EURUSD', 2)];
    await connect(page, { unlinked: true, catalogue });
    await page.getByRole('button', { name: 'Edit dataset EURUSD_DUKASCOPY', exact: true }).first().click();
    const modal = page.getByRole('dialog', { name: 'Edit symbol', exact: true });
    await expect(modal.getByText(scenario === 'ambiguous' ? 'Multiple instruments match' : 'No exact instrument match', { exact: false })).toBeVisible();
    await expect(modal.getByRole('combobox', { name: 'Instrument', exact: true })).toHaveValue('__unresolved__');
    await expect(modal.getByLabel('Pip/Tick size *', { exact: true })).toHaveValue('Not recorded');
    await expect(modal.getByRole('button', { name: 'Save', exact: true })).toBeDisabled();
    await modal.getByRole('combobox', { name: 'Instrument', exact: true }).selectOption('');
    await expect(modal.getByRole('button', { name: 'Save', exact: true })).toBeEnabled();
  });
}

test('saved instrument ID remains authoritative when unavailable', async ({ page }) => {
  await connect(page, { catalogue: [instrumentRecord('2', 'EURUSD')] });
  await page.getByRole('button', { name: 'Edit dataset EURUSD', exact: true }).first().click();
  const modal = page.getByRole('dialog', { name: 'Edit symbol', exact: true });
  await expect(modal.getByRole('combobox', { name: 'Instrument', exact: true })).toHaveValue('1');
  await expect(modal.getByText('The linked instrument is unavailable.', { exact: false })).toBeVisible();
  await expect(modal.getByRole('button', { name: 'Save', exact: true })).toBeDisabled();
});
