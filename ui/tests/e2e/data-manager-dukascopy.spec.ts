import { expect, test, type Page } from '@playwright/test';

async function host(page: Page, options: {direct?: boolean; brokerFailure?: boolean} = {}) {
  const rows: Array<Record<string, unknown>> = [];
  const posts: Array<Record<string, unknown>> = [];
  const state = {failSymbol: '', hold: null as Promise<void> | null,
    brokerFailure: options.brokerFailure ?? false, brokerHold: null as Promise<void> | null, brokerReads: 0,
    brokers: [{id: '1', name: 'Test broker', description: '', timezone: 'Europe/London', postfix: '_B', stockpicker_use: false, mt_use: true, is_system: false, stocks: [] as string[], customized_stocks: 0, total_instruments: 0, total_sessions: 0, spread_model: {model: 'inherit'}, commission_model: {model: 'inherit'}}],
  };
  await page.addInitScript(() => {
    const original = window.fetch.bind(window);
    window.fetch = ((input: RequestInfo | URL, init?: RequestInit) => String(input).includes('/api/v1/events?')
      ? Promise.resolve(new Response(new ReadableStream<Uint8Array>({start() {}}), {headers: {'Content-Type': 'text/event-stream'}}))
      : original(input, init)) as typeof fetch;
  });
  await page.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname;
    if (path === '/api/v1/data/brokers') {
      state.brokerReads++;
      if (state.brokerHold) await state.brokerHold;
      await route.fulfill(state.brokerFailure
        ? {status: 503, json: {status: 'error', error: {code: 'BROKER_STORAGE', message: 'Broker catalog unavailable.'}}}
        : {json: {status: 'success', data: state.brokers}});
      return;
    }
    if (path === '/api/v1/data/datasets' && route.request().method() === 'POST') {
      const body = route.request().postDataJSON();
      posts.push(body);
      if (state.hold) await state.hold;
      if (body.symbol === state.failSymbol) {
        await route.fulfill({status: 503, json: {status: 'error', error: {code: 'DATASET_STORAGE', message: 'Dataset storage is unavailable. Retry the operation.'}}});
        return;
      }
      const id = `dukascopy:${body.symbol}:${body.timeframe}`;
      if (rows.some(row => row.id === id)) {
        await route.fulfill({status: 409, json: {status: 'error', error: {code: 'DATASET_REQUEST', message: 'Dataset already exists.'}}});
        return;
      }
      const row = {...body, id, broker: body.broker === '-1' ? 'default' : body.broker,
        broker_name: body.broker === '-1' ? 'Default' : 'Test broker', timezone: body.broker === '-1' ? 'UTC' : 'Europe/London',
        instrument: body.instrument === '-1' ? body.underlying : body.instrument,
        category: 'Forex', bars: 0, date_from: '', date_to: '', path: `data/market/dukascopy/${body.timeframe === 'TICK' ? 'ticks' : 'm1'}/${body.underlying.toLowerCase()}`};
      rows.push(row);
      await route.fulfill({status: 201, json: {status: 'success', data: row}});
      return;
    }
    const ids = ['data', 'instruments', 'sessions', 'brokers', 'custom-data', 'chart', 'home', 'stock-groups', 'log'];
    const data = path === '/api/v1/data/home/datasets' ? rows
      : path === '/api/v1/data/workspace' ? {tabs: ids.map((id, index) => ({id, title: ['Data', 'Instruments', 'Sessions', 'Brokers', 'Custom Data', 'Chart', 'Home', 'Stock groups', 'Log'][index], core: index < 5})), active_tab: 'data', layout: {core_group: 'catalogs', chart_position: 'right'}}
      : path.startsWith('/api/v1/data/workspace/tabs/') ? {active_tab: path.split('/').at(-1), selection: null, preview: {state: 'unavailable', reason: 'Select a saved dataset.', rows: [], limit: 500}}
      : path.endsWith('/auth/login') ? {token: 'dukascopy-test-session', expires_at: '2099-01-01T00:00:00.000Z'}
      : path.endsWith('/settings') ? {revision: 1, values: {}}
      : path.endsWith('/status') ? {cpu_count: 4}
      : path === '/api/v1/home' ? {recent_projects: []} : [];
    await route.fulfill({json: {status: 'success', data}});
  });
  await page.goto(options.direct ? '/datamanager' : '/');
  const login = page.getByRole('dialog', {name: 'Connect to HaruQuantAI host'});
  await login.getByLabel('Host password').fill('test-password');
  await login.getByRole('button', {name: 'Connect', exact: true}).click();
  await expect(login).toHaveCount(0);
  if (!options.direct) await page.getByRole('button', {name: 'Data Manager', exact: true}).click();
  await expect(page.getByRole('table', {name: 'Historical data'})).toBeVisible();
  return {rows, posts, state};
}

async function open(page: Page) {
  await page.getByRole('button', {name: 'Dukascopy data', exact: true}).click();
  await page.getByRole('menuitem', {name: 'Add new Dukascopy symbol', exact: true}).click();
  return page.getByRole('dialog', {name: 'Add Dukascopy data', exact: true});
}

async function select(page: Page, symbol = 'EURUSD') {
  const dialog = await open(page);
  await dialog.getByLabel('Filter available symbols').fill(symbol);
  await dialog.getByRole('checkbox', {name: `Select symbol ${symbol}`, exact: true}).check();
  await dialog.getByRole('switch').check();
  return dialog;
}

test('catalogue validation, host registration and reload', async ({page}) => {
  const api = await host(page);
  const dialog = await open(page);
  await expect(dialog.getByRole('checkbox', {name: /^Select symbol /})).toHaveCount(725);
  await expect(dialog.getByRole('radio', {name: 'Tick data', exact: true})).toBeChecked();
  await dialog.getByRole('button', {name: 'Save', exact: true}).click();
  await expect(dialog.getByRole('alert')).toHaveText('No symbols selected');
  await dialog.getByLabel('Show types').selectOption('Forex - Majors');
  await dialog.getByRole('checkbox', {name: 'Select Forex - Majors', exact: true}).check();
  await expect(dialog.getByRole('checkbox', {name: 'Select all available symbols'})).toBeChecked();
  await dialog.getByLabel('Filter available symbols').fill('AUD');
  await expect(dialog.getByRole('checkbox', {name: /^Select symbol /})).toHaveCount(1);
  await dialog.getByRole('checkbox', {name: 'Select symbol AUDUSD', exact: true}).check();
  await dialog.getByRole('button', {name: 'Save', exact: true}).click();
  await expect(dialog.getByRole('alert')).toContainText('I confirm');
  expect(api.posts).toHaveLength(0);
  await dialog.getByRole('switch').check();
  await dialog.getByRole('radio', {name: 'M1 data', exact: true}).check();
  await dialog.getByLabel('Data postfix').fill('_TEST');
  await dialog.getByRole('button', {name: 'Save', exact: true}).click();
  await expect(dialog).toHaveCount(0);
  expect(api.posts).toEqual([{source: 'dukascopy', symbol: 'AUDUSD_TEST', underlying: 'AUDUSD', timeframe: 'M1', broker: '-1', instrument: '-1'}]);
  const row = page.getByRole('table', {name: 'Historical data'}).getByRole('row').filter({hasText: 'AUDUSD_TEST'});
  await expect(row).toContainText('Default');
  await expect(row).toContainText('M1');
  await expect(row.getByRole('cell').nth(10)).toHaveText('0');
  await page.reload();
  await expect(row).toHaveCount(1);
});

test('saved broker defaults and tick data registration', async ({page}) => {
  const api = await host(page);
  const dialog = await select(page);
  await dialog.getByLabel('Broker profile *', {exact: true}).selectOption('1');
  await expect(dialog.getByLabel('Data postfix')).toHaveValue('_B');
  await dialog.getByRole('button', {name: 'Save', exact: true}).click();
  await expect(dialog).toHaveCount(0);
  expect(api.posts[0]).toMatchObject({symbol: 'EURUSD_B', timeframe: 'TICK', broker: '1'});
  const table = page.getByRole('table', {name: 'Historical data'});
  await expect(table).toContainText('Test broker');
  await expect(table).toContainText('Europe/London');
});

test('errors retain the dialog and partial retry skips confirmed symbols', async ({page}) => {
  const api = await host(page);
  const dialog = await open(page);
  await dialog.getByRole('checkbox', {name: 'Select symbol EURUSD', exact: true}).check();
  await dialog.getByRole('checkbox', {name: 'Select symbol GBPUSD', exact: true}).check();
  await dialog.getByRole('switch').check();
  api.state.failSymbol = 'GBPUSD';
  await dialog.getByRole('button', {name: 'Save', exact: true}).click();
  await expect(dialog.getByRole('alert')).toContainText('1 of 2 symbols confirmed');
  await expect(dialog.getByRole('checkbox', {name: 'Select symbol EURUSD', exact: true})).not.toBeChecked();
  await expect(dialog.getByRole('checkbox', {name: 'Select symbol GBPUSD', exact: true})).toBeChecked();
  expect(api.rows).toHaveLength(1);
  api.state.failSymbol = '';
  await dialog.getByRole('button', {name: 'Save', exact: true}).click();
  await expect(dialog).toHaveCount(0);
  expect(api.posts.map(row => row.symbol)).toEqual(['EURUSD', 'GBPUSD', 'GBPUSD']);
  expect(api.rows).toHaveLength(2);
  const duplicate = await select(page);
  await duplicate.getByRole('button', {name: 'Save', exact: true}).click();
  await expect(duplicate.getByRole('alert')).toContainText('already exists');
  expect(api.posts).toHaveLength(3);
});

test('pending registration disables submission and closure', async ({page}) => {
  const api = await host(page);
  let finish!: () => void;
  api.state.hold = new Promise<void>(resolve => {finish = resolve;});
  const dialog = await select(page);
  await dialog.getByRole('button', {name: 'Save', exact: true}).click();
  await expect(dialog).toHaveAttribute('aria-busy', 'true');
  await expect(dialog.getByRole('button', {name: 'Saving…', exact: true})).toBeDisabled();
  await expect(dialog.getByRole('button', {name: 'Close', exact: true}).first()).toBeDisabled();
  await page.keyboard.press('Escape');
  await expect(dialog).toBeVisible();
  finish();
  await expect(dialog).toHaveCount(0);
  expect(api.posts).toHaveLength(1);
});

test('popup layout, keyboard closure and themes', async ({page}) => {
  await host(page);
  const dialog = await open(page);
  const font = await page.locator('.app-shell').evaluate(node => getComputedStyle(node).fontFamily);
  await expect(dialog).toHaveCSS('font-family', font);
  await expect(dialog).toHaveCSS('background-color', 'rgb(32, 37, 45)');
  await page.screenshot({path: 'test-results/dukascopy-popup.png'});
  await expect(dialog.getByRole('button', {name: 'Close', exact: true}).first()).toBeFocused();
  await page.keyboard.press('Shift+Tab');
  await expect(dialog.getByRole('button', {name: 'Save', exact: true})).toBeFocused();
  await page.setViewportSize({width: 740, height: 650});
  await expect(dialog.getByRole('button', {name: 'Save', exact: true})).toBeInViewport();
  await page.screenshot({path: 'test-results/dukascopy-small.png'});
  await page.keyboard.press('Escape');
  await expect(dialog).toHaveCount(0);
  await expect(page.getByRole('button', {name: 'Dukascopy data', exact: true})).toBeFocused();
  await page.evaluate(async () => {const modulePath = '/app/host/store.ts'; const {useAppStore} = await import(modulePath); useAppStore.getState().updateSettings({theme: 'light'});});
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
  await open(page);
  await expect(dialog).toHaveCSS('background-color', 'rgb(255, 255, 255)');
  await page.screenshot({path: 'test-results/dukascopy-light.png'});
});


test('opening refreshes the broker table catalog after initial failure and shows disabled profiles', async ({page}) => {
  const api = await host(page, {direct: true, brokerFailure: true});
  await expect.poll(() => api.state.brokerReads).toBeGreaterThan(0);
  const before = api.state.brokerReads;
  api.state.brokerFailure = false;
  api.state.brokers = [
    {...api.state.brokers[0], id: '2', name: '[[Fresh broker]]', postfix: '_FRESH'},
    {...api.state.brokers[0], id: '3', name: 'Inactive broker', mt_use: false},
  ];
  const dialog = await select(page);
  const brokers = dialog.getByLabel('Broker profile *', {exact: true});
  await expect(brokers.locator('option')).toHaveText(['Default', 'Fresh broker', 'Inactive broker (disabled for data management)']);
  await expect(brokers.locator('option[value="3"]')).toHaveJSProperty('disabled', true);
  await expect.poll(() => api.state.brokerReads).toBeGreaterThan(before);
  await brokers.selectOption('2');
  await expect(dialog.getByLabel('Data postfix')).toHaveValue('_FRESH');
  await page.screenshot({path: 'test-results/dukascopy-brokers-loaded.png'});
  await dialog.getByRole('button', {name: 'Save', exact: true}).click();
  await expect(dialog).toHaveCount(0);
  expect(api.posts[0]).toMatchObject({broker: '2', symbol: 'EURUSD_FRESH'});
  expect(api.state.brokers[0].name).toBe('[[Fresh broker]]');
});

test('broker loading and failure are visible and retry reloads the saved catalog', async ({page}) => {
  const api = await host(page);
  let finish!: () => void;
  api.state.brokerHold = new Promise<void>(resolve => {finish = resolve;});
  api.state.brokerFailure = true;
  const dialog = await open(page);
  const broker = dialog.getByLabel('Broker profile *', {exact: true});
  await expect(dialog.getByText('Loading broker profiles...', {exact: true})).toBeVisible();
  await expect(broker).toBeDisabled();
  await expect(dialog.getByRole('button', {name: 'Save', exact: true})).toBeDisabled();
  await page.screenshot({path: 'test-results/dukascopy-brokers-loading.png'});
  finish();
  await expect(dialog.getByRole('alert')).toContainText('Broker catalog unavailable.');
  await page.screenshot({path: 'test-results/dukascopy-brokers-error.png'});
  expect(api.posts).toHaveLength(0);
  api.state.brokerHold = null;
  api.state.brokerFailure = false;
  await dialog.getByRole('button', {name: 'Retry broker profiles', exact: true}).click();
  await expect(broker).toBeEnabled();
  await expect(broker.locator('option[value="1"]')).toHaveText('Test broker');
  await expect(dialog.getByRole('alert')).toHaveCount(0);
});

test('empty saved broker catalog retains Default and stale selections block registration', async ({page}) => {
  const api = await host(page);
  const dialog = await select(page);
  const broker = dialog.getByLabel('Broker profile *', {exact: true});
  await broker.selectOption('1');
  await dialog.getByRole('button', {name: 'Close', exact: true}).last().click();
  api.state.brokers = [];
  await open(page);
  await expect(dialog.getByRole('alert')).toContainText('selected broker is no longer available');
  await expect(dialog.getByRole('button', {name: 'Save', exact: true})).toBeDisabled();
  expect(api.posts).toHaveLength(0);
  await broker.selectOption('-1');
  await expect(dialog.getByText('No saved broker profiles. Default is available.', {exact: true})).toBeVisible();
  await expect(dialog.getByLabel('Data postfix')).toHaveValue('');
  await expect(dialog.getByRole('button', {name: 'Save', exact: true})).toBeEnabled();
});
