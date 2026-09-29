import { expect, test } from '@playwright/test';

test('Dukascopy catalogue is visible without a fabricated dataset add', async ({ page }) => {
  await page.goto('/');
  await page.getByRole('button', { name: 'Data Manager', exact: true }).click();
  await page.getByRole('button', { name: 'Dukascopy data', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Add new Dukascopy symbol', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Add Dukascopy data', exact: true });
  await expect(dialog.getByRole('checkbox', { name: /^Select symbol / })).toHaveCount(725);
  await expect(dialog.getByRole('button', { name: 'Save', exact: true })).toBeDisabled();
  await expect(dialog.getByText('Dataset storage is unavailable. Reconnect to the host or check the dataset catalog.')).toBeVisible();
  await dialog.getByLabel('Filter available symbols').fill('AUDUSD');
  await expect(dialog.getByRole('checkbox', { name: 'Select symbol AUDUSD' })).toBeVisible();
  await dialog.getByRole('button', { name: 'Close', exact: true }).first().click();
  await expect(dialog).toHaveCount(0);
});

for (const scenario of [
  { name: 'Dukascopy broker Tick', broker: '3', postfix: '_dukascopy', symbols: ['USDJPY'], kind: 'ticks' },
  { name: 'Default broker M1 batch', broker: '-1', postfix: '', symbols: ['USDJPY', 'EURUSD'], kind: 'm1' },
]) {
test(`broker catalog and direct save: ${scenario.name}`, async ({ page }) => {
  let finishLogin!: () => void;
  const loginReady = new Promise<void>(resolve => { finishLogin = resolve; });
  const boot = { state: 'STANDBY', stages: [], sequence: 0 };
  await page.routeWebSocket('**/ws/updates', socket => {
    socket.onMessage(() => socket.send(JSON.stringify({ type: 'snapshot', boot })));
  });
  await page.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith('/auth/login')) {
      await loginReady;
      return route.fulfill({ json: { status: 'success', data: { token: 'test-session' } } });
    }
    if (path.endsWith('/events')) return;
    const data = path.endsWith('/init-data')
      ? { settings: { revision: 0, values: {} }, boot, first_run: false }
      : { boot, cpu_count: 4 };
    await route.fulfill({ json: { status: 'success', data } });
  });
  await page.addInitScript(() => localStorage.setItem('sqx-data-manager-v1', JSON.stringify({
    version: 1,
    definitions: [],
    brokers: [{ id: 'mock', name: 'Browser Only', postfix: '_browser', timezone: 'UTC', mtUse: true, instruments: [] }],
  })));
  const existing = { id: 'existing', symbol: 'AUDCAD', source: 'Dukascopy', underlying: 'AUDCAD', instrument: 'AUDCAD', timeframe: 'M1', broker: '-1', brokerName: 'Default', timezone: 'UTC', category: 'Forex', from: '', to: '', bars: 0 };
  let savedDatasets: object[] = scenario.broker === '3' ? [existing] : [];
  let listCalls = 0;
  await page.route('**/actions.list_datasets', route => {
    listCalls += 1;
    return route.fulfill({ json: { status: 'success', data: savedDatasets } });
  });
  await page.route('**/api/v1/contributions/workspace.data_manager/sources.dukascopy.catalog', route => route.fulfill({
    json: { status: 'success', data: {
      definitions_available: true, source: 'dukascopy', formats: ['ticks', 'm1'],
      modes: { standard: 'unavailable', cdn: 'unavailable', 'cdn-cn': 'unavailable' },
      reason: 'market_catalog_migration_required', datasets: savedDatasets, broker_catalog_status: 'available',
      brokers: [
        { id: '2', name: 'RoboForex', postfix: '_robo', timezone: 'EET', mtUse: true, instruments: [] },
        { id: '3', name: 'Dukascopy', postfix: '_dukascopy', timezone: 'EETUS', mtUse: true, instruments: [] },
      ],
    } },
  }));
  await page.goto('/');
  await page.getByRole('button', { name: 'Data Manager', exact: true }).click();
  await page.getByRole('button', { name: 'Dukascopy data', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Add new Dukascopy symbol', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Add Dukascopy data', exact: true });
  const broker = dialog.getByRole('combobox', { name: 'Broker profile *' });
  const postfix = dialog.getByRole('textbox', { name: 'Data postfix' });
  // The dialog mounts before authentication, then updates without reopening.
  await expect(broker.locator('option')).toHaveText(['Default']);
  finishLogin();
  await expect(broker.locator('option')).toHaveText(['Default', 'RoboForex', 'Dukascopy']);
  await expect(broker.locator('option', { hasText: 'Browser Only' })).toHaveCount(0);
  await broker.selectOption('2');
  await expect(postfix).toHaveValue('_robo');
  await postfix.fill('_manual');
  await expect(postfix).toHaveValue('_manual');
  await broker.selectOption('3');
  await expect(postfix).toHaveValue('_dukascopy');
  await broker.selectOption('-1');
  await expect(postfix).toHaveValue('');
  await expect.poll(() => listCalls).toBeGreaterThan(0);
  const initialListCalls = listCalls;
  await broker.selectOption('2');
  await dialog.getByRole('button', { name: 'Close', exact: true }).first().click();
  await page.getByRole('button', { name: 'Dukascopy data', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Add new Dukascopy symbol', exact: true }).click();
  await expect(dialog.getByRole('combobox', { name: 'Broker profile *' })).toHaveValue('-1');
  await expect(dialog.getByRole('textbox', { name: 'Data postfix' })).toHaveValue('');
  const save = dialog.getByRole('button', { name: 'Save', exact: true });
  expect(listCalls).toBe(initialListCalls);
  await expect(save).toBeDisabled();
  await dialog.getByRole('checkbox', { name: 'Select symbol USDJPY', exact: true }).check();
  await expect(save).toBeDisabled();
  await dialog.getByRole('switch').check();
  await expect(save).toBeEnabled();
  await dialog.getByRole('combobox', { name: 'Broker profile *' }).selectOption(scenario.broker);
  for (const symbol of scenario.symbols.slice(1)) {
    await dialog.getByRole('checkbox', { name: `Select symbol ${symbol}`, exact: true }).check();
  }
  if (scenario.kind === 'm1') await dialog.getByRole('radio', { name: 'M1 data', exact: true }).check();
  let downloadRequests = 0;
  page.on('request', request => {
    if (request.url().includes('sources.dukascopy.download.start')) downloadRequests += 1;
  });
  let completeSave!: () => void;
  const saveGate = new Promise<void>(resolve => { completeSave = resolve; });
  await page.route('**/sources.dukascopy.definitions.add', async route => {
    expect(route.request().postDataJSON()).toEqual({ symbols: scenario.symbols, kind: scenario.kind, broker: scenario.broker, postfix: scenario.postfix, instruments: [] });
    await saveGate;
    await route.fulfill({ status: 409, json: { status: 'error', error: { code: 'DUPLICATE', message: 'Definition already exists' } } });
  });
  await page.getByRole('dialog').getByRole('button', { name: 'Save', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Saving...' })).toBeDisabled();
  await expect(dialog).toBeVisible();
  await expect(page.getByRole('table', { name: 'Instrument mappings' })).toHaveCount(0);
  completeSave();
  await expect(page.getByRole('alert')).toHaveText('Definition already exists');
  await expect(page.getByRole('dialog').getByRole('button', { name: 'Save', exact: true })).toBeEnabled();

  expect(listCalls).toBe(initialListCalls);
  await page.route('**/sources.dukascopy.definitions.add', async route => {
    expect(route.request().postDataJSON()).toEqual({ symbols: scenario.symbols, kind: scenario.kind, broker: scenario.broker, postfix: scenario.postfix, instruments: [] });
    savedDatasets = scenario.symbols.map(symbol => ({ id: `saved-${symbol}`, symbol: `${symbol}${scenario.postfix}`, source: 'Dukascopy', underlying: symbol, instrument: symbol, timeframe: scenario.kind === 'm1' ? 'M1' : 'TICK', broker: scenario.broker, brokerName: scenario.broker === '-1' ? 'Default' : 'Dukascopy', timezone: 'UTC', category: '', from: '', to: '', bars: 0 }));
    if (scenario.broker === '3') savedDatasets.unshift(existing);
    await route.fulfill({ json: { status: 'success', data: { ids: scenario.symbols.map(symbol => `saved-${symbol}`) } } });
  });
  await page.getByRole('dialog').getByRole('button', { name: 'Save', exact: true }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  for (const symbol of scenario.symbols) {
    await expect(page.getByRole('table', { name: 'Historical data' }).getByRole('checkbox', { name: `Select ${symbol}${scenario.postfix}`, exact: true })).toBeVisible();
  }
  await expect.poll(() => listCalls).toBeGreaterThan(initialListCalls);
  if (scenario.broker === '3') await expect(page.getByRole('checkbox', { name: 'Select AUDCAD', exact: true })).toBeVisible();
  expect(downloadRequests).toBe(0);
});
}

test('Delete refreshes the panel when the Dukascopy catalog still has the removed row', async ({ page }) => {
  const boot = { state: 'STANDBY', stages: [], sequence: 0 };
  const dataset = {
    id: 'saved-dataset', symbol: 'USDJPY_dukascopy', source: 'Dukascopy',
    underlying: 'USDJPY', instrument: 'USDJPY', timeframe: 'M1', broker: '3',
    brokerName: 'Dukascopy', timezone: 'UTC', category: 'Forex',
    from: '', to: '', bars: 0,
  };
  let databaseRows = [dataset];
  let listCalls = 0;
  let catalogCalls = 0;
  await page.routeWebSocket('**/ws/updates', socket => {
    socket.onMessage(() => socket.send(JSON.stringify({ type: 'snapshot', boot })));
  });
  await page.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith('/auth/login')) {
      return route.fulfill({ json: { status: 'success', data: { token: 'test-session' } } });
    }
    if (path.endsWith('/events')) return;
    const data = path.endsWith('/init-data')
      ? { settings: { revision: 0, values: {} }, boot, first_run: false }
      : { boot, cpu_count: 4 };
    await route.fulfill({ json: { status: 'success', data } });
  });
  await page.route('**/api/v1/contributions/workspace.data_manager/actions.list_datasets', route => {
    listCalls += 1;
    return route.fulfill({ json: { status: 'success', data: databaseRows } });
  });
  await page.route('**/api/v1/contributions/workspace.data_manager/sources.dukascopy.catalog', route => {
    catalogCalls += 1;
    return route.fulfill({ json: { status: 'success', data: {
      definitions_available: true, source: 'dukascopy', formats: ['ticks', 'm1'],
      modes: { standard: 'unavailable', cdn: 'unavailable', 'cdn-cn': 'unavailable' },
      reason: 'market_catalog_migration_required', datasets: [dataset],
      broker_catalog_status: 'available', brokers: [],
    } } });
  });
  await page.route('**/api/v1/contributions/workspace.data_manager/actions.delete', route => {
    databaseRows = [];
    return route.fulfill({ json: { status: 'success', data: {
      success: true, affected: 1, mode: 'remove', message: 'Deleted one dataset',
    } } });
  });

  await page.goto('/');
  await page.getByRole('button', { name: 'Data Manager', exact: true }).click();
  await expect.poll(() => catalogCalls).toBeGreaterThan(0);
  await expect(page.getByText('Records: 1', { exact: true })).toBeVisible();
  await page.getByRole('checkbox', { name: 'Select USDJPY_dukascopy', exact: true }).check();
  await page.getByLabel('Data source operations').getByRole('button', { name: 'Mass delete' }).click();
  const dialog = page.getByRole('dialog', { name: 'Delete data' });
  await dialog.getByRole('button', { name: 'Delete', exact: true }).click();

  await expect(dialog).toHaveCount(0);
  await expect.poll(() => listCalls).toBeGreaterThan(1);
  await expect(page.getByText('Records: 0', { exact: true })).toBeVisible();
  await expect(page.getByRole('checkbox', { name: 'Select USDJPY_dukascopy' })).toHaveCount(0);
});


test('dataset updates preserve filters, reject stale reads and recover refresh without repeating writes', async ({ page }) => {
  const boot = { state: 'STANDBY', stages: [], sequence: 0 };
  const dataset = { id: 'usd', symbol: 'USDJPY', source: 'Dukascopy', underlying: 'USDJPY', instrument: 'USDJPY', timeframe: 'M1', broker: '-1', brokerName: 'Default', timezone: 'UTC', category: 'Forex', from: '', to: '', bars: 1 };
  let rows = [dataset, { ...dataset, id: 'aud', symbol: 'AUDCAD' }];
  let listCalls = 0;
  let writes = 0;
  let failRead = false;
  let failWrite = false;
  let holdRead = false;
  let releaseRead!: () => void;
  const readGate = new Promise<void>(resolve => { releaseRead = resolve; });
  await page.routeWebSocket('**/ws/updates', socket => {
    socket.onMessage(() => socket.send(JSON.stringify({ type: 'snapshot', boot })));
  });
  await page.route('**/api/v1/**', route => {
    const path = new URL(route.request().url()).pathname;
    const data = path.endsWith('/auth/login') ? { token: 'test-session' }
      : path.endsWith('/init-data') ? { settings: { revision: 0, values: {} }, boot, first_run: false }
      : { boot, cpu_count: 4 };
    return route.fulfill({ json: { status: 'success', data } });
  });
  await page.route('**/actions.list_datasets', async route => {
    listCalls += 1;
    const snapshot = rows;
    if (holdRead) { holdRead = false; await readGate; }
    if (failRead) return route.fulfill({ status: 503, json: { status: 'error', error: { code: 'UNAVAILABLE', message: 'Read failed' } } });
    return route.fulfill({ json: { status: 'success', data: snapshot } });
  });
  await page.route('**/actions.update_selected', route => {
    writes += 1;
    expect(route.request().postDataJSON()).toEqual({ symbols: ['USDJPY'] });
    if (failWrite) return route.fulfill({ status: 409, json: { status: 'error', error: { code: 'FAILED', message: 'Update rejected' } } });
    rows = rows.map(row => row.id === 'usd' ? { ...row, bars: writes * 10 } : row);
    return route.fulfill({ json: { status: 'success', data: { success: true, queued: 1, datasets: [] } } });
  });
  await page.goto('/');
  await page.getByRole('button', { name: 'Data Manager', exact: true }).click();
  const table = page.getByRole('table', { name: 'Historical data' });
  const row = table.getByRole('row').filter({ has: page.getByRole('checkbox', { name: 'Select USDJPY', exact: true }) });
  await expect(page.getByText('Records: 2', { exact: true })).toBeVisible();
  const filter = page.getByPlaceholder('Filter items', { exact: true });
  await filter.fill('USDJPY');
  await table.getByRole('button', { name: 'Symbol Name' }).click();
  await page.getByRole('checkbox', { name: 'Select USDJPY', exact: true }).check();
  const update = page.getByRole('button', { name: 'Update selected', exact: true });
  const initialCalls = listCalls;
  holdRead = true;
  await update.click();
  await expect.poll(() => listCalls).toBe(initialCalls + 1);
  await update.click();
  await expect(row.getByRole('cell', { name: '20', exact: true })).toBeVisible();
  const oldResponse = page.waitForResponse('**/actions.list_datasets');
  releaseRead();
  await oldResponse;
  await expect(row.getByRole('cell', { name: '20', exact: true })).toBeVisible();
  await expect(filter).toHaveValue('USDJPY');
  await expect(table.locator('th[aria-sort]')).toHaveAttribute('aria-sort', 'descending');
  await expect(page.getByRole('checkbox', { name: 'Select USDJPY', exact: true })).toBeChecked();

  failRead = true;
  await update.click();
  await expect(page.getByRole('alert')).toContainText('Unable to refresh datasets');
  await expect(row.getByRole('cell', { name: '20', exact: true })).toBeVisible();
  const completedWrites = writes;
  failRead = false;
  await page.getByRole('button', { name: 'Retry dataset refresh' }).click();
  await expect(row.getByRole('cell', { name: '30', exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Retry dataset refresh' })).toHaveCount(0);
  expect(writes).toBe(completedWrites);

  failWrite = true;
  const callsBeforeFailure = listCalls;
  const failedResponse = page.waitForResponse('**/actions.update_selected');
  await update.click();
  await failedResponse;
  await page.getByRole('button', { name: 'Notifications', exact: true }).click();
  await expect(page.getByText('Update rejected', { exact: false })).toBeVisible();
  await page.getByRole('button', { name: 'Notifications', exact: true }).click();
  expect(listCalls).toBe(callsBeforeFailure);

  await page.route('**/actions.delete', route => {
    expect(route.request().postDataJSON()).toEqual({ symbols: ['USDJPY'], mode: 'clear' });
    rows = rows.map(row => row.id === 'usd' ? { ...row, bars: 0 } : row);
    return route.fulfill({ json: { status: 'success', data: { success: true, affected: 1 } } });
  });
  await page.getByRole('button', { name: 'Mass delete', exact: true }).click();
  await page.getByRole('dialog', { name: 'Delete data' }).getByRole('button', { name: 'Clear data', exact: true }).click();
  await expect(row.getByRole('cell', { name: '0', exact: true })).toHaveCount(2);
  await filter.fill('');
  await expect(page.getByRole('checkbox', { name: 'Select AUDCAD', exact: true })).toBeVisible();
});
