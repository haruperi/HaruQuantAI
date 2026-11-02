import { expect, test, type Page } from '@playwright/test';
async function launch(page: Page, sources = ['yahoo'], missingLast = false) {
  const state = { fail: false, gate: null as Promise<void> | null, writes: [] as { targets: { id: string }[]; date_from: string; date_to: string; overwrite: boolean; connection_id?: string }[] };
  await page.addInitScript(() => {
    const original = window.fetch.bind(window);
    window.fetch = ((input: RequestInfo | URL, init?: RequestInit) => String(input).includes('/api/v1/events?')
      ? Promise.resolve(new Response(new ReadableStream<Uint8Array>({ start() {} }), { headers: { 'Content-Type': 'text/event-stream' } }))
      : original(input, init)) as typeof fetch;
  });
  await page.route('**/api/v1/**', async route => {
    const url = new URL(route.request().url()), path = url.pathname;
    let data: unknown = [];
    if (path.endsWith('/auth/login')) data = { token: 'isolated-review-session' };
    else if (path.endsWith('/settings')) data = { revision: 1, values: {} };
    else if (path.endsWith('/status')) data = { cpu_count: 4 };
    else if (path === '/api/v1/home') data = { recent_projects: [] };
    else if (path.endsWith('/data/workspace')) data = {
      tabs: ['data', 'symbols', 'sessions', 'brokers', 'custom-data', 'chart', 'home', 'stock-groups', 'log'].map((id, index) => ({ id, title: id, core: index < 5 })),
      active_tab: 'data', layout: { core_group: 'catalogs', chart_position: 'right' },
    };
    else if (path.includes('/workspace/tabs/')) data = { active_tab: path.split('/').at(-1), selection: null, preview: { state: 'unavailable', reason: 'Select a dataset.', rows: [], limit: 500 } };

    else if (path.endsWith('/home/datasets')) data = sources.map((source, index) => ({
      id: 'saved:' + index, symbol: 'TEST' + index, instrument: 'EURUSD', underlying: 'EURUSD',
      timeframe: source.startsWith('sq_') || source === 'yahoo' ? 'D1' : 'M1', timezone: 'UTC',
      date_from: '2021-01-01', date_to: missingLast ? null : index ? '2025-06-02' : '2025-06-01',
      total_records: 100, source, category: 'Forex', data_type: 'Forex', path: 'data/test/' + index, bar_type: 'start',
    }));
    else if (path.endsWith('/connections')) data = [{ connection_id: 'saved-connection', provider: sources[0], name: 'Research connection' }];
    else if (path.endsWith('/providers/download')) {
      state.writes.push(route.request().postDataJSON());
      await state.gate;
      if (state.fail) { await route.fulfill({ status: 503, json: { status: 'error', error: { code: 'UNAVAILABLE', message: 'Provider unavailable' } } }); return; }
      data = { job_id: 'download-1', status: 'COMPLETED', progress: 100, message: 'Done' };
    }
    await route.fulfill({ json: { status: 'success', data } });
  });
  await page.goto('/datamanager');
  const login = page.getByRole('dialog', { name: 'Connect to HaruQuantAI host' });
  await login.getByLabel('Host password').fill('fixture-password');
  await login.getByRole('button', { name: 'Connect', exact: true }).click();
  await expect(login).toHaveCount(0);
  for (let index = 0; index < sources.length; index++) await page.getByRole('checkbox', { name: 'Select TEST' + index, exact: true }).check();
  await page.getByRole('button', { name: 'Update selected', exact: true }).click();
  await expect(page.getByRole('dialog', { name: /^Download .* data for / })).toBeVisible();
  return state;
}
for (const provider of ['yahoo', 'binance', 'binance_coinm', 'binance_usdtm', 'bitfinex', 'coinbase', 'poloniex', 'darwinex', 'sq_equity', 'sq_futures', 'dukascopy', 'mt5']) {
  test('donor download and host submission: ' + provider, async ({ page }) => {
    const state = await launch(page, [provider]);
    const modal = page.getByRole('dialog', { name: /^Download .* data for TEST0/ });
    await expect(modal.getByText('Choose data range to download', { exact: true })).toBeVisible();
    await expect(modal.getByText('Redownload options', { exact: true })).toBeVisible();
    await expect(modal.getByRole('button', { name: 'All time', exact: true })).toBeDisabled();
    await modal.getByRole('button', { name: 'Since last date', exact: true }).click();
    await expect(modal.getByLabel('From', { exact: true })).toHaveValue('2025-06-01');
    await modal.getByRole('radio', { name: 'Overwrite existing data', exact: true }).check();
    await modal.getByText('Provider connection', { exact: true }).click();
    await modal.getByRole('combobox', { name: 'Saved provider connection' }).selectOption('saved-connection');
    await modal.getByRole('button', { name: 'Start download', exact: true }).click();
    await expect(modal).toHaveCount(0);
    expect(state.writes).toHaveLength(1);
    expect(state.writes[0]).toMatchObject({ targets: [{ id: 'saved:0' }], date_from: '2025-06-01', overwrite: true, connection_id: 'saved-connection' });
  });
}
test('mixed selections, validation, errors and pending submission protection', async ({ page }) => {
  const state = await launch(page, ['yahoo', 'binance']);
  const modal = page.getByRole('dialog', { name: 'Download historical data for multiple datasets', exact: true });
  await modal.getByRole('button', { name: 'Since last date' }).click();
  await expect(modal.getByLabel('From', { exact: true })).toHaveValue('2025-06-01');
  await modal.getByLabel('From', { exact: true }).fill('2025-06-02');
  await modal.getByLabel('To', { exact: true }).fill('2025-06-01');
  await modal.getByRole('button', { name: 'Start download' }).click();
  await expect(modal.getByRole('alert')).toContainText('valid date range');
  expect(state.writes).toHaveLength(0);
  await modal.getByLabel('To', { exact: true }).fill('2025-06-03');
  state.fail = true;
  await modal.getByRole('button', { name: 'Start download' }).click();
  await expect(modal.getByRole('alert')).toContainText('Provider unavailable');
  state.fail = false;
  let release!: () => void;
  state.gate = new Promise(resolve => { release = resolve; });
  await modal.getByRole('button', { name: 'Start download' }).click();
  await expect(modal.getByRole('button', { name: /^Starting/ })).toBeDisabled();
  await page.keyboard.press('Escape');
  await expect(modal).toBeVisible();
  expect(state.writes).toHaveLength(2);
  release();
  await expect(modal).toHaveCount(0);
});
test('presets, missing history, themes and responsive keyboard access', async ({ page }, info) => {
  await launch(page, ['yahoo'], true);
  const modal = page.getByRole('dialog', { name: /^Download Yahoo/ });
  await expect(modal.getByRole('button', { name: 'Since last date' })).toBeDisabled();
  for (const name of ['Last 6 months', 'Last year', 'Last 5 years', 'Last 10 years']) {
    await modal.getByRole('button', { name, exact: true }).click();
    await expect(modal.getByRole('button', { name, exact: true })).toHaveAttribute('aria-pressed', 'true');
  }
  await page.screenshot({ path: info.outputPath('download-dark.png') });
  await page.evaluate(() => document.documentElement.setAttribute('data-theme', 'light'));
  await page.screenshot({ path: info.outputPath('download-light.png') });
  await page.setViewportSize({ width: 390, height: 700 });
  await expect(modal.getByRole('button', { name: 'Start download' })).toBeInViewport();
  await page.screenshot({ path: info.outputPath('download-narrow.png') });
  await modal.getByRole('button', { name: 'Start download' }).focus();
  await page.keyboard.press('Tab');
  await expect(modal.getByRole('button', { name: 'Close', exact: true }).first()).toBeFocused();
  await page.keyboard.press('Escape');
  await expect(modal).toHaveCount(0);
});

for (const [source, label] of [['yahoo', 'Yahoo'], ['binance', 'Crypto'], ['darwinex', 'Darwinex Tick Data']]) {
  test('provider download menu uses donor dialog: ' + source, async ({ page }) => {
    await launch(page, [source]);
    await page.getByRole('dialog').getByRole('button', { name: 'Close', exact: true }).last().click();
    await page.getByRole('button', { name: label, exact: true }).click();
    await page.getByRole('menuitem', { name: source === 'darwinex' ? 'Download data for existing symbols' : 'Download data for existing symbol', exact: true }).click();
    const modal = page.getByRole('dialog', { name: /^Download .* data for TEST0/ });
    await expect(modal.getByText('Choose data range to download', { exact: true })).toBeVisible();
  });
}
