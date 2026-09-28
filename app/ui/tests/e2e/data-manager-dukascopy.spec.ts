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

test('broker choices come from the host catalog and fill the selected postfix', async ({ page }) => {
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
  let savedDatasets: object[] = [];
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
  await broker.selectOption('2');
  await dialog.getByRole('button', { name: 'Close', exact: true }).first().click();
  await page.getByRole('button', { name: 'Dukascopy data', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Add new Dukascopy symbol', exact: true }).click();
  await expect(dialog.getByRole('combobox', { name: 'Broker profile *' })).toHaveValue('-1');
  await expect(dialog.getByRole('textbox', { name: 'Data postfix' })).toHaveValue('');
  const save = dialog.getByRole('button', { name: 'Save', exact: true });
  await expect(save).toBeDisabled();
  await dialog.getByRole('checkbox', { name: 'Select symbol USDJPY', exact: true }).check();
  await expect(save).toBeDisabled();
  await dialog.getByRole('switch').check();
  await expect(save).toBeEnabled();
  await dialog.getByRole('combobox', { name: 'Broker profile *' }).selectOption('3');
  await save.click();
  await expect(page.getByRole('table', { name: 'Instrument mappings' })).toBeVisible();
  await page.getByRole('combobox', { name: 'Instrument for USDJPY' }).selectOption('-1');
  let completeSave!: () => void;
  const saveGate = new Promise<void>(resolve => { completeSave = resolve; });
  await page.route('**/sources.dukascopy.definitions.add', async route => {
    expect(route.request().postDataJSON()).toEqual({ symbols: ['USDJPY'], kind: 'ticks', broker: '3', postfix: '_dukascopy', instruments: ['-1'] });
    await saveGate;
    await route.fulfill({ status: 409, json: { status: 'error', error: { code: 'DUPLICATE', message: 'Definition already exists' } } });
  });
  await page.getByRole('dialog').getByRole('button', { name: 'Save', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Saving...' })).toBeDisabled();
  completeSave();
  await expect(page.getByRole('alert')).toHaveText('Definition already exists');
  await expect(page.getByRole('dialog').getByRole('button', { name: 'Save', exact: true })).toBeEnabled();

  await page.route('**/sources.dukascopy.definitions.add', async route => {
    savedDatasets = [{ id: 'saved-dataset', symbol: 'USDJPY_dukascopy', source: 'Dukascopy', underlying: 'USDJPY', instrument: 'USDJPY', timeframe: 'TICK', broker: '3', brokerName: 'Dukascopy', timezone: 'UTC', category: '', from: '', to: '', bars: 0 }];
    await route.fulfill({ json: { status: 'success', data: { ids: ['saved-dataset'] } } });
  });
  await page.getByRole('dialog').getByRole('button', { name: 'Save', exact: true }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(page.getByRole('table', { name: 'Historical data' }).getByText('USDJPY_dukascopy', { exact: true })).toBeVisible();

});

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
