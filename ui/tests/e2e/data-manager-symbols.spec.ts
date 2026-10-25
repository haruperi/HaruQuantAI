import { expect, test, type Page } from '@playwright/test';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

function record(id: string, symbol: string) {
  return { id, symbol, description: symbol + ' saved', broker_id: -1, data_type: 'Forex',
    point_value: Number(id) * 12, point_size: .00001, tick_size: .0001, tick_step: .00001,
    contract_size: 250, pip_size: .0001, margin_rate: Number(id) * .1, decimals: 5,
    tick_value_in_money: 7, min_volume: .01, max_volume: 100, lot_step: .01,
    default_spread: Number(id), default_slippage: 0, min_distance: 0, order_size_multiplier: 1, order_size_step: 0,
    commissions: '4.75', swap_long: -2, swap_short: 1, swap_3day_day: 0, swap_settings: null,
    connection: 'saved', created_at_utc: '2020-01-01', updated_at_utc: '2020-01-01' };
}
async function connect(page: Page, initial = [record('1', 'RECORDED_A'), record('2', 'RECORDED_B')]) {
  let rows: Record<string, any>[] = structuredClone(initial);
  const state = { failRead: false, failWrite: false, delayWrite: false, writes: [] as { path: string; body: any }[] };
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  page.on('close', () => expect(errors).toEqual([]));
  await page.addInitScript(() => {
    localStorage.setItem('sqx-symbols-catalog-v1', JSON.stringify({ symbols: [{ symbol: 'CACHED_FAKE' }] }));
    const original = window.fetch.bind(window);
    window.fetch = ((input: RequestInfo | URL, init?: RequestInit) => String(input).includes('/api/v1/events?')
      ? Promise.resolve(new Response(new ReadableStream<Uint8Array>({ start() {} }), { headers: { 'Content-Type': 'text/event-stream' } })) : original(input, init)) as typeof fetch;
  });
  await page.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname.replace('/instruments', '/symbols');
    let data: unknown = [];
    if (path.endsWith('/auth/login')) data = { token: 'symbol-session', expires_at: '2099-01-01T00:00:00Z' };
    else if (path.endsWith('/settings')) data = { revision: 1, values: {} };
    else if (path.endsWith('/status')) data = { cpu_count: 4 };
    else if (path === '/api/v1/home') data = { recent_projects: [] };
    else if (path.endsWith('/data/workspace')) data = {
      tabs: ['data','symbols','sessions','brokers','custom-data','chart','home','stock-groups','log'].map((id, index) => ({ id, title: id, core: index < 5 })),
      active_tab: 'data', layout: { core_group: 'catalogs', chart_position: 'right' },
    };
    else if (path.includes('/workspace/tabs/')) data = { active_tab: path.split('/').at(-1), selection: null, preview: { state: 'unavailable', reason: 'Select a saved dataset.', rows: [], limit: 500 } };
    else if (path === '/api/v1/data/symbols' && route.request().method() === 'GET') {
      if (state.failRead) { await route.fulfill({ status: 503, json: { status: 'error', error: { code: 'UNAVAILABLE', message: 'Catalog unavailable' } } }); return; }
      data = rows;
    } else if (path.startsWith('/api/v1/data/symbols') && route.request().method() === 'POST') {
      const rawBody = route.request().postDataJSON();
      const { instrument_ids, ...body } = rawBody;
      if (instrument_ids !== undefined) body.symbol_ids = instrument_ids;
      state.writes.push({ path, body });
      if (state.delayWrite) await new Promise(resolve => setTimeout(resolve, 600));
      if (state.failWrite) { await route.fulfill({ status: 409, json: { status: 'error', error: { code: 'CONFLICT', message: 'Symbol was not saved: conflict' } } }); return; }
      if (path.endsWith('/save')) {
        data = { count: rows.length, content: 'name,description\n' + rows.map(row => `${row.symbol},${row.description}`).join('\n') };
      } else if (path.endsWith('/load')) {
        rows.push(record(String(rows.length + 1), 'CSV_IMPORTED'));
        data = { loaded_count: 1, total: 2, errors: [{ row: 2, error: 'Duplicate symbol' }] };
      } else if (path.endsWith('/delete')) {
        rows = rows.filter(row => !body.symbol_ids.includes(row.id));
        data = { deleted_count: body.symbol_ids.length };
      } else if (path.endsWith('/refresh')) {
        data = { deleted_count: 0, inserted_count: rows.length };
      } else if (path.endsWith('/mass-edit')) {
        rows = rows.map(row => body.symbol_ids.includes(row.id) ? { ...row, ...body.updates } : row);
        data = { updated_count: body.symbol_ids.length, symbols: rows.filter(row => body.symbol_ids.includes(row.id)) };
      } else {
        const id = String(rows.length + 1);
        const created = path.endsWith('/clone') ? { ...rows.find(row => row.id === body.source_id), id, symbol: body.new_symbol } : { ...record(id, body.symbol), ...body, id };
        rows.push(created); data = created;
      }
    }
    await route.fulfill({ json: { status: 'success', data } });
  });
  await page.goto('/');
  const login = page.getByRole('dialog', { name: 'Connect to HaruQuantAI host' });
  await login.getByLabel('Host password').fill('fixture-password');
  await login.getByRole('button', { name: 'Connect', exact: true }).click();
  await expect(login).toHaveCount(0);
  await page.getByRole('button', { name: 'Data Manager', exact: true }).click();
  await page.getByRole('navigation', { name: 'Data Manager workspace navigation' }).getByRole('button', { name: 'Symbols', exact: true }).click();
  await expect(page.getByRole('table', { name: 'Symbols', exact: true })).toBeVisible();
  return { state, rows: () => rows };
}
const table = (page: Page) => page.getByRole('table', { name: 'Symbols', exact: true });
const operations = (page: Page) => page.getByLabel('Symbol operations', { exact: true });

test('lists server specifications, awaits add confirmation, and retains records on reload', async ({ page }) => {
  const { state } = await connect(page);
  await expect(table(page)).toContainText('RECORDED_A');
  await expect(table(page)).not.toContainText('CACHED_FAKE');
  await expect(table(page)).not.toContainText('EURUSD');
  await expect(table(page).getByRole('columnheader', { name: 'Point value', exact: true })).toBeVisible();
  await expect(operations(page).getByRole('button', { name: 'Mass Delete', exact: true })).toBeEnabled();
  await expect(operations(page).getByRole('button', { name: 'Load', exact: true })).toBeEnabled();
  await operations(page).getByRole('button', { name: 'Add Symbol', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Add symbol', exact: true });
  await dialog.getByLabel('Symbol', { exact: true }).fill('NEW_SPEC');
  await dialog.getByLabel('Contract size', { exact: true }).fill('75');
  await dialog.getByLabel('Pip size', { exact: true }).fill('0.001');
  await dialog.getByLabel('Margin rate (fraction)', { exact: true }).fill('0');
  state.delayWrite = true;
  await dialog.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(dialog.getByRole('button', { name: 'Saving…', exact: true })).toBeDisabled();
  await expect(table(page)).not.toContainText('NEW_SPEC');
  await expect(dialog).toHaveCount(0);
  await expect(table(page)).toContainText('NEW_SPEC');
  expect(state.writes.at(-1)?.body).toMatchObject({ contract_size: 75, pip_size: .001, margin_rate: 0 });
  await page.reload();
  await page.getByRole('button', { name: 'Data Manager', exact: true }).click();
  await page.getByRole('navigation', { name: 'Data Manager workspace navigation' }).getByRole('button', { name: 'Symbols', exact: true }).click();
  await expect(table(page)).toContainText('NEW_SPEC');
});

test('bulk edit changes checked fields only; clone retains complete stored metadata', async ({ page }) => {
  const { state, rows } = await connect(page);
  await table(page).getByLabel('Select symbol RECORDED_A', { exact: true }).check();
  await table(page).getByLabel('Select symbol RECORDED_B', { exact: true }).check();
  await operations(page).getByRole('button', { name: 'Mass Edit Symbol', exact: true }).click();
  let dialog = page.getByRole('dialog', { name: 'Mass-Edit symbol', exact: true });
  await dialog.getByLabel('Change Margin rate (fraction)', { exact: true }).check();
  await dialog.getByLabel('Margin rate (fraction)', { exact: true }).fill('0');
  await dialog.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(dialog).toHaveCount(0);
  expect(state.writes.at(-1)?.body).toEqual({ symbol_ids: ['1','2'], updates: { margin_rate: 0 } });
  expect(rows().map(row => row.point_value)).toEqual([12,24]);
  expect(rows().map(row => row.commissions)).toEqual(['4.75','4.75']);
  await table(page).getByLabel('Select symbol RECORDED_B', { exact: true }).uncheck();
  await operations(page).getByRole('button', { name: 'Clone Symbol', exact: true }).click();
  dialog = page.getByRole('dialog', { name: 'Clone symbol', exact: true });
  await dialog.getByLabel('New symbol name').fill('CLONED_SPEC');
  await dialog.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(dialog).toHaveCount(0);
  await expect(table(page)).toContainText('CLONED_SPEC');
  expect(state.writes.at(-1)?.body).toEqual({ source_id: '1', new_symbol: 'CLONED_SPEC' });
  expect(rows().at(-1)).toMatchObject({ point_value: 12, margin_rate: 0, commissions: '4.75', contract_size: 250, swap_long: -2 });
  await page.screenshot({ path: join(tmpdir(), 'haru-symbols-authoritative.png'), fullPage: true });
});

test('failed edits and clones remain open and never create local success rows', async ({ page }) => {
  const { state } = await connect(page);
  state.failWrite = true;
  await table(page).getByRole('row').filter({ hasText: 'RECORDED_A' }).dblclick();
  let dialog = page.getByRole('dialog', { name: 'Edit symbol', exact: true });
  await dialog.getByLabel('Description', { exact: true }).fill('UNSAVED_DESCRIPTION');
  await dialog.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(dialog.getByRole('alert')).toContainText('conflict');
  await expect(table(page)).not.toContainText('UNSAVED_DESCRIPTION');
  await dialog.getByRole('button', { name: 'Close', exact: true }).last().click();
  await operations(page).getByRole('button', { name: 'Clone Symbol', exact: true }).click();
  dialog = page.getByRole('dialog', { name: 'Clone symbol', exact: true });
  await dialog.getByLabel('New symbol name').fill('FAILED_CLONE');
  await dialog.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(dialog.getByRole('alert')).toContainText('conflict');
  await expect(table(page)).not.toContainText('FAILED_CLONE');
});

test('empty reads clear rows and failures have visible stale/retry state', async ({ page }) => {
  const { state, rows } = await connect(page);
  await expect(table(page)).toContainText('RECORDED_A');
  await table(page).getByLabel('Select all visible symbols', { exact: true }).check();
  state.failRead = true;
  await page.getByRole('button', { name: 'Refresh symbols', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Showing the last server snapshot');
  state.failRead = false;
  rows().splice(0);
  await page.getByRole('button', { name: 'Refresh symbols', exact: true }).click();
  await expect(table(page)).not.toContainText('RECORDED_A');
  await expect(table(page)).toContainText('No matching symbols.');
});

test('pages and filters the catalog while retaining selections across pages', async ({ page }) => {
  await connect(page, Array.from({ length: 120 }, (_, index) => record(String(index + 1), `PAGE_${String(index).padStart(3, '0')}`)));
  await expect(page.getByLabel('Symbol pagination')).toContainText('Page 1 of 3');
  await table(page).getByLabel('Select symbol PAGE_000', { exact: true }).check();
  await page.getByRole('button', { name: 'Next', exact: true }).click();
  await expect(page.getByLabel('Symbol pagination')).toContainText('Symbols 51-100 of 120');
  await expect(table(page)).toContainText('PAGE_050');
  await expect(table(page)).not.toContainText('PAGE_000');
  await page.getByLabel('Filter symbols', { exact: true }).fill('PAGE_119');
  await expect(page.getByLabel('Symbol pagination')).toContainText('Page 1 of 1');
  await expect(table(page)).toContainText('PAGE_119');
  await expect(page.getByLabel('Symbol pagination')).toContainText('1 selected');
});

test('downloads CSV, imports with a skipped row report, and deletes multiple symbols', async ({ page }) => {
  const { rows } = await connect(page);
  await operations(page).getByRole('button', { name: 'Save', exact: true }).click();
  const save = page.getByRole('dialog', { name: 'Save symbols', exact: true });
  const downloadPromise = page.waitForEvent('download');
  await save.getByRole('button', { name: 'Download CSV', exact: true }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe('Symbols.csv');
  await expect(save).toHaveCount(0);
  await operations(page).getByRole('button', { name: 'Load', exact: true }).click();
  const load = page.getByRole('dialog', { name: 'Load symbols', exact: true });
  await load.getByLabel('CSV file', { exact: true }).setInputFiles({ name: 'symbols.csv', mimeType: 'text/csv', buffer: Buffer.from('name\nCSV_IMPORTED\nRECORDED_A') });
  await load.getByRole('button', { name: 'Load CSV', exact: true }).click();
  await expect(load.getByRole('status')).toContainText('Loaded 1 of 2 symbols.');
  await expect(load.getByRole('status')).toContainText('Skipped row 2: Duplicate symbol');
  await load.getByRole('button', { name: 'Close', exact: true }).last().click();
  await expect(table(page)).toContainText('CSV_IMPORTED');
  await table(page).getByLabel('Select symbol RECORDED_A', { exact: true }).check();
  await table(page).getByLabel('Select symbol RECORDED_B', { exact: true }).check();
  await operations(page).getByRole('button', { name: 'Mass Delete', exact: true }).click();
  await page.getByRole('dialog', { name: 'Removing symbols', exact: true }).getByRole('button', { name: 'Yes', exact: true }).click();
  await expect(table(page)).not.toContainText('RECORDED_A');
  await expect(table(page)).not.toContainText('RECORDED_B');
  expect(rows().map(row => row.symbol)).toEqual(['CSV_IMPORTED']);
});
