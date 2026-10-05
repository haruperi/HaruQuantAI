import type { Page } from '@playwright/test';
import type { DatasetRow } from '../../../../../app/workspace/DataManager/Actions/actionsClient';

/** Isolated HTTP fixtures: no browser test can mutate the operational backend. */
export async function installDataManagerBackend(page: Page, initialRows: DatasetRow[] = []) {
  const state = { rows: initialRows, failInventory: false, failUpdates: false, requests: [] as { operation: string; body: any }[] };
  let settings = { revision: 0, values: {} as Record<string, Record<string, unknown>> };
  const boot = { schema_version: 2, state: 'SERVER_READY', stages: [], sequence: 0 };
  await page.routeWebSocket('**/ws/updates', socket => {
    socket.onMessage(() => socket.send(JSON.stringify({ type: 'snapshot', boot })));
  });
  await page.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname;
    const operation = path.split('/').at(-1)!;
    if (operation === 'events') return;
    if (operation === 'settings' && route.request().method() === 'PUT') {
      const changes = route.request().postDataJSON().changes;
      settings = { revision: settings.revision + 1, values: { ...settings.values } };
      for (const [key, value] of Object.entries(changes)) settings.values[key] = { ...settings.values[key], ...(value as object) };
    }
    if (path.includes('/contributions/')) {
      state.requests.push({ operation, body: route.request().postDataJSON() });
    }
    if (operation === 'actions.list_datasets' && state.failInventory) {
      return route.fulfill({ status: 503, json: { status: 'error', error: { code: 'UNAVAILABLE', message: 'Inventory unavailable' } } });
    }
    if (operation.startsWith('actions.update') && state.failUpdates) {
      return route.fulfill({ status: 503, json: { status: 'error', error: { code: 'UNAVAILABLE', message: 'Update unavailable' } } });
    }
    const data = operation === 'login' ? { token: 'isolated-test-session' }
      : operation === 'init-data' ? { settings, boot, first_run: false }
      : operation === 'settings' ? settings
      : operation === 'sources.dukascopy.catalog' ? {
        definitions_available: true, source: 'dukascopy', formats: ['ticks', 'm1'],
        modes: { standard: 'unavailable', cdn: 'unavailable', 'cdn-cn': 'unavailable' },
        reason: 'market_catalog_migration_required', datasets: state.rows,
        broker_catalog_status: 'available', brokers: [],
      }
      : operation === 'actions.list_datasets' ? state.rows
      : operation === 'actions.broker_data_update' ? { success: true, updatedDatasets: 0, brokerProfiles: 0 }
      : operation.startsWith('actions.update') ? { success: true, queued: state.rows.length, datasets: [] }
      : { boot, cpu_count: 4 };
    await route.fulfill({ json: { status: 'success', data } });
  });
  return state;
}

export function dataset(symbol: string, bars = 0): DatasetRow {
  return { id: `db:${symbol}`, symbol, source: 'Dukascopy', underlying: symbol,
    instrument: symbol, timeframe: 'M1', broker: '-1', brokerName: 'Default',
    timezone: 'UTC', category: 'Forex', from: bars ? '2026-01-01' : '',
    to: bars ? '2026-01-02' : '', bars, status: 'Ready' };
}

export async function savedConfiguration(page: Page) {
  await page.addInitScript(() => {
    if (localStorage.getItem('test-configuration-installed')) return;
    localStorage.setItem('test-configuration-installed', 'true');
    const instrument = { symbol: 'EURUSD', name: 'User configured instrument', type: 'Forex', broker: '-1', brokerName: 'Default',
      pointValue: 100000, tickSize: .0001, tickStep: .00001, spread: 1, slippage: 0, minDistance: 0, multiplier: 1, sizeStep: 1, timezone: 'UTC', session: 'Forex 24/5',
      commission: { model: 'None', value: 0, unit: 'share', min: .35, minUnit: 'money', max: 1, maxUnit: 'equity' },
      swap: { use: false, type: 'money', long: 0, short: 0, tripleSwapOn: 'WEDNESDAY', rolloutHour: '23:00' } };
    localStorage.setItem('sqx-file-symbols-v1', JSON.stringify({ version: 3, definitions: [], instruments: [instrument], overrides: {}, removed: [] }));
    localStorage.setItem('haru-data-sessions-v1', JSON.stringify({ version: 1, sessions: [{ name: 'Forex 24/5', broker: '-1', brokerName: 'Default', elements: [{ dayFrom: 'Mon', dayTo: 'Mon', timeFrom: '08:00', timeTo: '17:00', eod: true }] }], overrides: {}, removed: [] }));
  });
}
