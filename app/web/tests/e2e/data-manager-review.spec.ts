import { expect, test, type Page } from '@playwright/test';

async function launch(page: Page) {
  const state = { failQuality: false, qualityRequests: [] as URL[], rowRequests: [] as URL[] };
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
    else if (path.endsWith('/home/datasets')) data = [{
      id: 'saved:EURUSD', symbol: 'EURUSD_DUKASCOPY', instrument: 'EURUSD', broker: 'Dukascopy', broker_name: 'Dukascopy', underlying: 'EURUSD',
      timeframe: 'M1', timezone: 'UTC', date_from: '2021-11-01', date_to: '2026-10-31', total_records: 2629440,
      source: 'dukascopy', category: 'Forex', data_type: 'Forex', path: 'data/market/dukascopy/m1/eurusd', bar_type: 'start',
    }];
    else if (path.endsWith('/review-data')) {
      state.rowRequests.push(url);
      data = { rows: [
        { id: '1', date: '2021-11-01T03:35:00Z', open: 1.1556, high: 1.1558, low: 1.1555, close: 1.1557, volume: 10, bid: 1.1556, ask: 1.1557 },
        { id: '2', date: '2021-11-01T03:36:00Z', open: 1.1557, high: 1.1559, low: 1.1556, close: 1.1556, volume: 12, bid: 1.1556, ask: 1.1557 },
      ], total: 2629440, revision: 'revision-1', price_digits: 5 };
    } else if (path.endsWith('/quality-details')) {
      state.qualityRequests.push(url);
      if (state.failQuality) {
        await route.fulfill({ status: 503, json: { status: 'error', error: { code: 'UNAVAILABLE', message: 'Quality service unavailable' } } }); return;
      }
      const offset = Number(url.searchParams.get('offset') ?? 0);
      data = {
        total: 2629440, issue_count: 601, counts: { Gap: 600, Spike: 1, 'Bad OHLC': 0 },
        percents: { Gap: 600 / 2629440 * 100, Spike: 1 / 2629440 * 100, 'Bad OHLC': 0 },
        gap_policy: 'saved session', spike_threshold: 0.1, offset, limit: 500,
        issues: Array.from({ length: offset ? 101 : 500 }, (_, index) => ({ date: `2021-11-01T${String(Math.floor(index / 60)).padStart(2, '0')}:${String(index % 60).padStart(2, '0')}:00Z`, kind: 'Gap' })),
        coverage: [
          { date: '2021-11-01', observed: 1000, expected: 1001, issues: 1 },
          { date: '2021-11-02', observed: 1000, expected: 1000, issues: 0 },
          { date: '2026-10-31', observed: 1000, expected: 1000, issues: 0 },
        ],
      };
    }
    await route.fulfill({ json: { status: 'success', data } });
  });
  await page.goto('/datamanager');
  const login = page.getByRole('dialog', { name: 'Connect to HaruQuantAI host' });
  await login.getByLabel('Host password').fill('fixture-password');
  await login.getByRole('button', { name: 'Connect', exact: true }).click();
  await expect(login).toHaveCount(0);
  await page.getByRole('checkbox', { name: 'Select EURUSD_DUKASCOPY', exact: true }).check();
  await page.getByRole('navigation', { name: 'Data Manager workspace navigation' }).getByRole('button', { name: 'Tools', exact: true }).click();
  await page.getByRole('button', { name: 'View & Analyze', exact: true }).click();
  await expect(page.getByRole('dialog', { name: "View data for 'EURUSD_DUKASCOPY'", exact: true })).toBeVisible();
  return state;
}

test('review chart keeps five instrument digits including trailing zeros', async ({ page }) => {
  const state = await launch(page);
  const dialog = page.getByRole('dialog', { name: "View data for 'EURUSD_DUKASCOPY'", exact: true });
  await dialog.getByRole('tab', { name: 'Chart', exact: true }).click();
  const chart = dialog.locator('.review-chart');
  await expect(chart).toHaveAttribute('data-price-digits', '5');
  await expect(chart.locator('canvas').first()).toBeVisible();
  await expect(chart.locator('aside tr').filter({ hasText: 'Close' }).locator('td').last()).toHaveText('1.15560');
  expect(state.qualityRequests).toHaveLength(0);
  await page.screenshot({ path: 'test-results/review-five-digits.png' });
});

test('quality shows complete summary, daily map and independent issue pages', async ({ page }) => {
  const state = await launch(page);
  const dialog = page.getByRole('dialog', { name: "View data for 'EURUSD_DUKASCOPY'", exact: true });
  await dialog.getByRole('tab', { name: 'Analyze data quality', exact: true }).click();
  await expect(dialog.getByRole('table', { name: 'Gap summary', exact: true })).toContainText('600');
  await expect(dialog.getByText('2,629,440 observations', { exact: false })).toBeVisible();
  await expect(dialog.getByLabel('2021-11-01: 1000 observations, 1 issues', { exact: true })).toHaveClass(/issue/);
  await expect(dialog.getByLabel('2021-11-02: 1000 observations, 0 issues', { exact: true })).toHaveClass(/recorded/);
  await expect(dialog.getByRole('table', { name: 'Quality issues' }).locator('tbody tr')).toHaveCount(500);
  const rowsBefore = state.rowRequests.length;
  await dialog.getByRole('button', { name: 'Next issues', exact: true }).click();
  await expect(dialog.getByRole('table', { name: 'Quality issues' }).locator('tbody tr')).toHaveCount(101);
  expect(state.qualityRequests.at(-1)?.searchParams.get('offset')).toBe('500');
  expect(state.rowRequests).toHaveLength(rowsBefore);
  await expect(dialog.getByRole('table', { name: 'Gap summary' })).toContainText('600');
  await page.screenshot({ path: 'test-results/review-quality-summary.png' });
  await dialog.getByRole('combobox', { name: 'View timeframe', exact: true }).selectOption('H1');
  await expect(dialog.getByRole('table', { name: 'Quality issues' }).locator('tbody tr')).toHaveCount(500);
  expect(state.qualityRequests.at(-1)?.searchParams.get('offset')).toBe('0');
  expect(state.qualityRequests.at(-1)?.searchParams.get('timeframe')).toBe('H1');
});

test('quality failure stays in its tab and can retry without breaking Chart', async ({ page }) => {
  const state = await launch(page); state.failQuality = true;
  const dialog = page.getByRole('dialog', { name: "View data for 'EURUSD_DUKASCOPY'", exact: true });
  await dialog.getByRole('tab', { name: 'Analyze data quality', exact: true }).click();
  await expect(dialog.getByRole('alert')).toContainText('Quality service unavailable');
  await dialog.getByRole('tab', { name: 'Chart', exact: true }).click();
  await expect(dialog.getByRole('alert')).toHaveCount(0);
  await expect(dialog.locator('.review-chart')).toHaveAttribute('data-price-digits', '5');
  await dialog.getByRole('tab', { name: 'Analyze data quality', exact: true }).click();
  await expect(dialog.getByRole('alert')).toContainText('Quality service unavailable');
  state.failQuality = false;
  await dialog.getByRole('button', { name: 'Retry quality analysis', exact: true }).click();
  await expect(dialog.getByRole('table', { name: 'Gap summary' })).toBeVisible();
  await expect(dialog.getByRole('alert')).toHaveCount(0);
});
