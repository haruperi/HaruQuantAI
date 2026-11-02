import { expect, test, type Page } from '@playwright/test';
import { selectLightSkin } from './shellTestUtils';

async function launch(page: Page) { await page.goto('/'); await page.getByRole('button', { name: 'Data Manager', exact: true }).and(page.locator('[aria-label]')).click(); }
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

test.describe('Backend yahoo donor popup', () => {
  async function start(page: Page, failCatalogue = false) {
    const state = { catalogue: ['BTCUSDT', 'ETHUSDT', 'BNBUSDT'] as unknown, failCatalogue, failSave: false, failRefresh: false, saveGate: null as Promise<void> | null, writes: [] as { definitions: { symbol: string; underlying: string; timeframe: string; broker?: string }[] }[] };
    await page.addInitScript(() => {
      const original = window.fetch.bind(window);
      window.fetch = ((input: RequestInfo | URL, init?: RequestInit) => String(input).includes('/api/v1/events?')
        ? Promise.resolve(new Response(new ReadableStream<Uint8Array>({ start() {} }), { headers: { 'Content-Type': 'text/event-stream' } }))
        : original(input, init)) as typeof fetch;
    });
    await page.route('**/api/v1/**', async route => {
      const url = new URL(route.request().url()), endpoint = url.pathname;
      let data: unknown = [];
      if (endpoint.endsWith('/auth/login')) data = { token: 'isolated-yahoo-session' };
      else if (endpoint.endsWith('/settings')) data = { revision: 1, values: {} };
      else if (endpoint.endsWith('/status')) data = { cpu_count: 4 };
      else if (endpoint === '/api/v1/home') data = { recent_projects: [] };
      else if (endpoint.endsWith('/data/workspace')) data = {
        tabs: ['data', 'symbols', 'sessions', 'brokers', 'custom-data', 'chart', 'home', 'stock-groups', 'log'].map((id, index) => ({ id, title: id, core: index < 5 })),
        active_tab: 'data', layout: { core_group: 'catalogs', chart_position: 'right' },
      };
      else if (endpoint.includes('/workspace/tabs/')) data = { active_tab: endpoint.split('/').at(-1), selection: null, preview: { state: 'unavailable', reason: 'Select a dataset.', rows: [], limit: 500 } };
      else if (endpoint.endsWith('/capabilities')) data = { timeframes: ['M1'], default_timeframe: 'M1' };
      else if (endpoint.endsWith('/data/brokers')) data = [{ id: '1', name: 'Research broker', description: '', timezone: 'Europe/London', postfix: '_R', stockpicker_use: false, mt_use: true, is_system: false, stocks: [], customized_stocks: 0, customized_symbols: 0, total_symbols: 0, total_sessions: 0, spread_model: { model: 'inherit' }, commission_model: { model: 'inherit' } }];
      else if (endpoint.endsWith('/sources/yahoo/catalog')) {
        if (state.failCatalogue) { await route.fulfill({ status: 503, json: { status: 'error', error: { code: 'UNAVAILABLE', message: 'Yahoo catalogue unavailable' } } }); return; }
        data = state.catalogue;
      } else if (endpoint.endsWith('/sources/yahoo/add')) {
        const body = route.request().postDataJSON(); state.writes.push(body);
        await state.saveGate;
        if (state.failSave) { await route.fulfill({ status: 409, json: { status: 'error', error: { code: 'CONFLICT', message: 'Yahoo datasets were not saved' } } }); return; }
        data = { records: body.definitions.map((row: { symbol: string; timeframe: string }) => ({ ...row, id: `saved:${row.symbol}`, source: 'yahoo' })) };
      } else if (endpoint.endsWith('/home/datasets') && state.failRefresh && state.writes.length) {
        await route.fulfill({ status: 503, json: { status: 'error', error: { code: 'UNAVAILABLE', message: 'Dataset catalogue unavailable' } } }); return;
      }
      await route.fulfill({ json: { status: 'success', data } });
    });
    await page.goto('/datamanager');
    const login = page.getByRole('dialog', { name: 'Connect to HaruQuantAI host' });
    await login.getByLabel('Host password').fill('fixture-password');
    await login.getByRole('button', { name: 'Connect', exact: true }).click();
    await expect(login).toHaveCount(0);
    await page.getByRole('button', { name: 'Yahoo', exact: true }).click();
    await page.getByRole('menuitem', { name: 'Add Yahoo symbols', exact: true }).click();
    await expect(page.getByRole('dialog', { name: 'Add Yahoo data', exact: true })).toBeVisible();
    return state;
  }

  test('host registration and refresh retry preserve the draft', async ({ page }) => {
    const state = await start(page);
    const modal = page.getByRole('dialog', { name: 'Add Yahoo data', exact: true });
    await modal.getByRole('button', { name: 'Save', exact: true }).click();
    await expect(modal.getByRole('alert')).toContainText('at least one');
    await modal.getByRole('textbox', { name: 'Yahoo symbols' }).fill('AAPL;\nMSFT,EURUSD=X');
    await modal.getByRole('textbox', { name: 'Data postfix' }).fill('_TEST');
    state.failSave = true;
    await modal.getByRole('button', { name: 'Save', exact: true }).click();
    await expect(modal.getByRole('alert')).toContainText('not saved');
    state.failSave = false; state.failRefresh = true;
    await modal.getByRole('button', { name: 'Save', exact: true }).click();
    await expect(modal.getByRole('alert')).toContainText('Retry refresh');
    expect(state.writes).toHaveLength(2);
    expect(state.writes[1].definitions[0].symbol).toBe('AAPL_TEST');
    state.failRefresh = false;
    await modal.getByRole('button', { name: 'Retry refresh', exact: true }).click();
    await expect(modal).toHaveCount(0);
    expect(state.writes).toHaveLength(2);
  });
  test('responsive donor layout', async ({ page }, info) => {
    await start(page);
    const modal = page.getByRole('dialog', { name: 'Add Yahoo data', exact: true });
    await expect(modal.getByText('Add data to download', { exact: true })).toBeVisible();
    await page.screenshot({ path: info.outputPath('yahoo-dark.png') });
    await page.evaluate(() => document.documentElement.setAttribute('data-theme', 'light'));
    await page.screenshot({ path: info.outputPath('yahoo-light.png') });
    await page.setViewportSize({ width: 390, height: 844 });
    await expect(modal.getByRole('button', { name: 'Save', exact: true })).toBeInViewport();
    await page.screenshot({ path: info.outputPath('yahoo-narrow.png') });
  });
});
