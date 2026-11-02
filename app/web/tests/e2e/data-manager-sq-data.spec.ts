import { expect, test, type Page } from '@playwright/test';
import { selectLightSkin } from './shellTestUtils';

for (const provider of ['Equity', 'Futures'] as const) {
const source = provider === 'Equity' ? 'sq_equity' : 'sq_futures';
const ticker = provider === 'Equity' ? 'AAP' : '@ES';
const query = provider === 'Equity' ? 'AAP; MSFT' : '@ES; @NQ';
test.describe(`Backend ${provider.toLowerCase()} search popup`, () => {
  async function launch(page: Page) {
    const state = { catalogue: (provider === 'Equity' ? ['AAPL', 'AAP', 'MSFT', 'AMZN'] : ['@ES', '@ESM', '@NQ', '@GC']) as unknown, fail: false, writes: [] as { path: string; body: unknown }[] };
    await page.addInitScript(() => {
      const original = window.fetch.bind(window);
      window.fetch = ((input: RequestInfo | URL, init?: RequestInit) => String(input).includes('/api/v1/events?')
        ? Promise.resolve(new Response(new ReadableStream<Uint8Array>({ start() {} }), { headers: { 'Content-Type': 'text/event-stream' } }))
        : original(input, init)) as typeof fetch;
    });
    await page.route('**/api/v1/**', async route => {
      const path = new URL(route.request().url()).pathname;
      let data: unknown = [];
      if (route.request().method() === 'POST') state.writes.push({ path, body: route.request().postDataJSON() });
      if (path.endsWith('/auth/login')) data = { token: 'isolated-equity-session' };
      else if (path.endsWith('/settings')) data = { revision: 1, values: {} };
      else if (path.endsWith('/status')) data = { cpu_count: 4 };
      else if (path === '/api/v1/home') data = { recent_projects: [] };
      else if (path.endsWith('/data/workspace')) data = {
        tabs: ['data', 'symbols', 'sessions', 'brokers', 'custom-data', 'chart', 'home', 'stock-groups', 'log'].map((id, index) => ({ id, title: id, core: index < 5 })),
        active_tab: 'data', layout: { core_group: 'catalogs', chart_position: 'right' },
      };
      else if (path.includes('/workspace/tabs/')) data = { active_tab: path.split('/').at(-1), selection: null, preview: { state: 'unavailable', reason: 'Select a dataset.', rows: [], limit: 500 } };
      else if (path.endsWith('/capabilities')) data = { timeframes: ['D1'], default_timeframe: 'D1' };
      else if (path.endsWith(`/sources/${source}/catalog`)) {
        if (state.fail) {
          await route.fulfill({ status: 503, json: { status: 'error', error: { code: 'UNAVAILABLE', message: `${provider} catalogue unavailable` } } }); return;
        }
        data = state.catalogue;
      } else if (path.endsWith(`/sources/${source}/add`)) {
        const body = route.request().postDataJSON() as { definitions: { symbol: string; underlying: string; timeframe: string }[] };
        data = { records: body.definitions.map(row => ({ ...row, id: `saved:${row.symbol}`, source })) };
      }
      await route.fulfill({ json: { status: 'success', data } });
    });
    await page.goto('/datamanager');
    const login = page.getByRole('dialog', { name: 'Connect to HaruQuantAI host' });
    await login.getByLabel('Host password').fill('fixture-password');
    await login.getByRole('button', { name: 'Connect', exact: true }).click();
    await expect(login).toHaveCount(0);
    await page.getByRole('button', { name: `${provider} data`, exact: true }).click();
    await page.getByRole('menuitem', { name: `Find and add ${provider.toLowerCase()} data`, exact: true }).click();
    await expect(page.getByRole('dialog', { name: `Add SQ ${provider} Data`, exact: true })).toBeVisible();
    state.writes.length = 0;
    return state;
  }

  test('reference layout, themes, narrow footer and keyboard closing', async ({ page }) => {
    await launch(page);
    const dialog = page.getByRole('dialog', { name: `Add SQ ${provider} Data`, exact: true });
    await expect(dialog.getByRole('heading', { name: 'Find data by' })).toBeVisible();
    await expect(dialog.getByRole('combobox', { name: 'Exchange' })).toBeDisabled();
    await expect(dialog.getByRole('combobox', { name: 'Exchange' })).toHaveValue('Any');
    await expect(dialog.getByRole('checkbox', { name: 'Search in ticker', exact: true })).toBeChecked();
    await expect(dialog.getByRole('checkbox', { name: 'Search in name', exact: true })).toBeDisabled();
    await expect(dialog.getByRole('checkbox', { name: 'Exact match' })).not.toBeChecked();
    if (provider === 'Futures') {
      await expect(dialog.getByRole('checkbox', { name: 'Only continuous futures' })).toBeDisabled();
      expect(await dialog.locator('textarea').evaluate(element => element.getBoundingClientRect().height)).toBe(200);
    }
    await expect(dialog.getByText('End of Day data supported; subscription status unavailable', { exact: false })).toBeVisible();
    await expect(dialog.getByRole('button', { name: 'Add symbols', exact: true })).toHaveCount(0);
    await dialog.getByRole('textbox', { name: 'Search text' }).pressSequentially(ticker);
    await expect(dialog.getByRole('textbox', { name: 'Search text' })).toHaveValue(ticker);
    await page.screenshot({ path: `test-results/${provider.toLowerCase()}-search-dark.png` });
    await page.evaluate(() => { document.documentElement.dataset.theme = 'light'; });
    await page.screenshot({ path: `test-results/${provider.toLowerCase()}-search-light.png` });
    await page.setViewportSize({ width: 520, height: 700 });
    await expect(dialog.getByRole('button', { name: 'Close', exact: true }).last()).toBeInViewport();
    expect(await dialog.evaluate(element => element.scrollWidth <= element.clientWidth)).toBe(true);
    const bounds = await dialog.boundingBox();
    expect(bounds!.x).toBeGreaterThanOrEqual(0);
    expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(520);
    await dialog.getByRole('button', { name: 'Close', exact: true }).last().focus();
    await page.keyboard.press('Tab');
    await expect(dialog.getByRole('button', { name: 'Close', exact: true }).first()).toBeFocused();
    await page.screenshot({ path: `test-results/${provider.toLowerCase()}-search-narrow.png` });
    await page.keyboard.press('Escape');
    await expect(dialog).toHaveCount(0);
    await expect(page.getByRole('button', { name: `${provider} data`, exact: true })).toBeFocused();
  });

  test('catalogue matching, consent and backend registration', async ({ page }) => {
    const state = await launch(page);
    const dialog = page.getByRole('dialog', { name: `Add SQ ${provider} Data`, exact: true });
    await dialog.getByRole('textbox', { name: 'Search text' }).fill(query);
    await dialog.getByRole('button', { name: 'Lookup', exact: true }).click();
    await expect(dialog.getByRole('status')).toHaveText('Found: 3, selected: 0');
    expect(state.writes).toEqual([]);
    await dialog.getByRole('button', { name: '‹ Search again' }).click();
    await expect(dialog.getByRole('textbox', { name: 'Search text' })).toHaveValue(query);
    await dialog.getByRole('checkbox', { name: 'Exact match' }).check();
    await dialog.getByRole('button', { name: 'Lookup', exact: true }).click();
    await expect(dialog.getByRole('status')).toHaveText('Found: 2, selected: 0');
    await dialog.getByRole('checkbox', { name: `Select ticker ${ticker}`, exact: true }).check();
    await expect(dialog.getByRole('button', { name: 'Continue' })).toBeDisabled();
    await dialog.getByRole('button', { name: 'HaruQuantAI Data Usage Conditions', exact: true }).click();
    await expect(page.getByRole('dialog', { name: 'HaruQuantAI Data Usage Conditions', exact: true })).toBeVisible();
    await page.keyboard.press('Escape');
    await expect(dialog.getByRole('checkbox', { name: `Select ticker ${ticker}`, exact: true })).toBeChecked();
    await dialog.getByRole('checkbox', { name: 'I confirm that I agree to' }).check();
    await dialog.getByRole('button', { name: 'Continue' }).click();
    const configure = page.getByRole('dialog', { name: `Add SQ ${provider} data`, exact: true });
    await expect(configure.getByRole('textbox', { name: 'Provider symbols' })).toHaveValue(ticker);
    await configure.getByRole('button', { name: 'Add symbols', exact: true }).click();
    await expect(configure).toHaveCount(0);
    const writes = state.writes.filter(write => write.path.endsWith(`/sources/${source}/add`));
    expect(writes).toHaveLength(1);
    expect(writes[0].body).toMatchObject({ definitions: [{ symbol: `${ticker}_${source}`, underlying: ticker, timeframe: 'D1' }] });
    expect(state.writes.some(write => write.path.includes('download-jobs'))).toBe(false);
  });

  test('failed and malformed catalogues can retry without mock results', async ({ page }) => {
    const state = await launch(page);
    const dialog = page.getByRole('dialog', { name: `Add SQ ${provider} Data`, exact: true });
    state.fail = true;
    await dialog.getByRole('button', { name: 'Lookup', exact: true }).click();
    await expect(dialog.getByRole('alert')).toContainText(`${provider} catalogue unavailable`);
    state.fail = false; state.catalogue = [{ ticker: 'AAPL' }];
    await dialog.getByRole('button', { name: 'Lookup', exact: true }).click();
    await expect(dialog.getByRole('alert')).toContainText(`invalid ${provider.toLowerCase()} catalogue`);
    state.catalogue = ['AAPL'];
    await dialog.getByRole('textbox', { name: 'Search text' }).fill('UNKNOWN');
    await dialog.getByRole('button', { name: 'Lookup', exact: true }).click();
    await expect(dialog.getByText('No tickers found.')).toBeVisible();
    await expect(dialog.getByRole('button', { name: 'Continue' })).toBeDisabled();
    expect(state.writes).toEqual([]);
  });

  test('lookup times out, closes safely and reopens Futures search', async ({ page }) => {
    await launch(page);
    await page.evaluate(source => {
      const original = window.fetch.bind(window);
      window.fetch = ((input: RequestInfo | URL, init?: RequestInit) => String(input).includes(`/sources/${source}/catalog`)
        ? new Promise<Response>((_resolve, reject) => init?.signal?.addEventListener('abort', () => reject(new DOMException('Cancelled', 'AbortError')), { once: true }))
        : original(input, init)) as typeof fetch;
    }, source);
    await page.clock.install();
    const dialog = page.getByRole('dialog', { name: `Add SQ ${provider} Data`, exact: true });
    await dialog.getByRole('button', { name: 'Lookup', exact: true }).click();
    await expect(dialog.getByRole('button', { name: 'Looking up…' })).toBeDisabled();
    await page.clock.runFor(15001);
    await expect(dialog.getByRole('alert')).toContainText(`${provider} lookup timed out`);
    await dialog.getByRole('button', { name: 'Lookup', exact: true }).click();
    await page.keyboard.press('Escape');
    await expect(dialog).toHaveCount(0);
    await page.clock.resume();
    await page.getByRole('button', { name: 'Futures data', exact: true }).click();
    await page.getByRole('menuitem', { name: 'Find and add futures data', exact: true }).click();
    const futures = page.getByRole('dialog', { name: 'Add SQ Futures Data', exact: true });
    await expect(futures.getByRole('heading', { name: 'Find data by' })).toBeVisible();
    await expect(futures.getByRole('checkbox', { name: 'Only continuous futures' })).toBeDisabled();
  });
});
}
/** Settings are intentionally not persisted by the current host. */
async function setFeatureProfileFixture(page: Page, profile: 'Full' | 'Starter'): Promise<void> {
  await page.evaluate(async nextProfile => {
    const modulePath = '/shell/store.ts';
    const { useAppStore } = await import(/* @vite-ignore */ modulePath);
    const state = useAppStore.getState();
    useAppStore.setState({ settings: { ...state.settings, profile: nextProfile } });
  }, profile);
  await page.waitForFunction(expected => document.documentElement.dataset.profile === expected, profile);
}
async function open(page: Page, provider: 'Equity' | 'Futures') {
  await page.getByRole('button', { name: `${provider} data`, exact: true }).click();
  await page.getByRole('menuitem', { name: `Find and add ${provider.toLowerCase()} data`, exact: true }).click();
  return page.getByRole('dialog', { name: `Add ${provider} Data`, exact: true });
}
test.describe('Existing SQ workflows', () => {
test.beforeEach(async ({ page }) => { await page.goto('/'); await page.getByRole('button', { name: 'Data Manager', exact: true }).and(page.locator('[aria-label]')).click(); });
test('equity search, conditions, validation, add, pause/reload/resume and row status', async ({ page }) => {
  const dialog = await open(page, 'Equity');
  await expect(dialog.getByRole('button', { name: 'Add', exact: true })).toHaveCount(0);
  await dialog.getByRole('textbox', { name: 'Search text' }).fill('AAPL;Microsoft');
  await dialog.getByRole('button', { name: 'Lookup', exact: true }).click();
  await expect(dialog.getByRole('status')).toHaveText('Found: 2, selected: 0');
  await dialog.getByRole('button', { name: 'Add', exact: true }).click(); await expect(dialog.getByRole('alert')).toContainText('agree');
  await dialog.getByRole('button', { name: 'HaruQuantAI Data Usage Conditions', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'HaruQuantAI Data Usage Conditions' }).first()).toBeVisible();
  await page.keyboard.press('Escape'); await expect(dialog.getByRole('button', { name: 'HaruQuantAI Data Usage Conditions', exact: true })).toBeFocused();
  await dialog.getByRole('checkbox', { name: 'I confirm' }).check();
  await dialog.getByRole('checkbox', { name: 'Select all available tickers' }).check();
  await dialog.getByRole('textbox', { name: 'Name postfix' }).fill('_sq');
  await dialog.getByRole('button', { name: 'Add', exact: true }).click();
  await page.getByRole('button', { name: 'Pause all', exact: true }).click(); await page.reload();
  await expect(page.getByRole('button', { name: 'Resume all', exact: true })).toBeEnabled();
  await page.getByRole('button', { name: 'Resume all', exact: true }).click();
  await expect(page.getByLabel('Status for AAPL_sq', { exact: true })).toHaveText('Completed', { timeout: 10000 });
  await expect(page.getByLabel('Status for MSFT_sq', { exact: true })).toHaveText('Completed');
  const row = page.getByRole('row').filter({ has: page.getByRole('checkbox', { name: 'Select AAPL_sq', exact: true }) });
  await expect(row).toContainText('End of bar'); await expect(row).toContainText('America/New_York');
  await page.reload(); await expect(page.getByLabel('Status for AAPL_sq', { exact: true })).toHaveText('Completed');
});
test('futures continuous filter, duplicate rejection, fixed shift and cancellation', async ({ page }) => {
  const dialog = await open(page, 'Futures');
  await dialog.getByRole('textbox', { name: 'Search text' }).fill('NQ');
  await dialog.getByRole('checkbox', { name: 'Only continuous futures' }).uncheck();
  await dialog.getByRole('button', { name: 'Lookup', exact: true }).click();
  await expect(dialog.getByRole('status')).toHaveText('Found: 2, selected: 0');
  await dialog.getByRole('checkbox', { name: 'Select ticker NQ', exact: true }).check();
  await dialog.getByRole('checkbox', { name: 'I confirm' }).check();
  await dialog.getByRole('button', { name: 'Add', exact: true }).click(); await expect(dialog.getByRole('alert')).toContainText('exists');
  await dialog.getByRole('textbox', { name: 'Name postfix' }).fill('_sq');
  await dialog.getByRole('radio', { name: 'add fixed shift' }).check();
  await dialog.getByRole('spinbutton', { name: 'Fixed shift hours' }).fill('24');
  await dialog.getByRole('button', { name: 'Add', exact: true }).click(); await expect(dialog.getByRole('alert')).toContainText('integer');
  await dialog.getByRole('spinbutton', { name: 'Fixed shift hours' }).fill('-2');
  await dialog.getByRole('button', { name: 'Add', exact: true }).click();
  await page.getByRole('button', { name: 'Stop all', exact: true }).click();
  await expect(page.getByRole('checkbox', { name: 'Select NQ_sq', exact: true })).toHaveCount(0);
});
test('empty results, disabled exact field and search again preserve draft', async ({ page }) => {
  const dialog = await open(page, 'Equity');
  await dialog.getByRole('checkbox', { name: 'Search in ticker', exact: true }).uncheck();
  await expect(dialog.getByRole('checkbox', { name: 'Exact match' })).toBeDisabled();
  await dialog.getByRole('textbox', { name: 'Search text' }).fill('not-a-symbol');
  await dialog.getByRole('button', { name: 'Lookup', exact: true }).click();
  await expect(dialog.getByText('No tickers found.')).toBeVisible();
  await expect(dialog.getByRole('button', { name: 'Add', exact: true })).toHaveCount(0);
  await dialog.getByRole('button', { name: '< Search again' }).click();
  await expect(dialog.getByRole('textbox', { name: 'Search text' })).toHaveValue('not-a-symbol');
});
test('Starter eligibility, theme, narrow layout and keyboard focus', async ({ page }) => {
  await setFeatureProfileFixture(page, 'Starter');
  await selectLightSkin(page);
  const dialog = await open(page, 'Equity');
  await expect(dialog.getByText('Data available without subscription:', { exact: false })).toBeVisible();
  await dialog.getByRole('textbox', { name: 'Search text' }).fill('AAPL,AMZN');
  await dialog.getByRole('button', { name: 'Lookup', exact: true }).click();
  await expect(dialog.getByRole('checkbox', { name: 'Select ticker AMZN' })).toBeDisabled();
  await dialog.getByRole('checkbox', { name: 'Select all available tickers' }).check();
  await expect(dialog.getByRole('status')).toHaveText('Found: 2, selected: 1');
  await dialog.getByRole('radio', { name: 'choose timezone' }).check();
  await dialog.getByRole('combobox', { name: 'Data timezone' }).selectOption('UTC');
  await page.screenshot({ path: 'test-results/sq-equity-light.png' });
  await page.setViewportSize({ width: 520, height: 700 });
  const bounds = await dialog.boundingBox(); expect(bounds!.x).toBeGreaterThanOrEqual(0); expect(bounds!.x + bounds!.width).toBeLessThanOrEqual(520);
  await expect(dialog.getByRole('button', { name: 'Add', exact: true })).toBeInViewport();
  await dialog.getByRole('button', { name: 'Add', exact: true }).focus(); await page.keyboard.press('Tab');
  await expect(dialog.getByRole('button', { name: 'Close', exact: true }).first()).toBeFocused();
  await page.screenshot({ path: 'test-results/sq-equity-narrow.png' });
});
test('futures adds timezone metadata, guards other jobs and stays offline', async ({ page }) => {
  const requests: string[] = []; page.on('request', request => { if (!request.url().startsWith('http://127.0.0.1:4173') && new URL(request.url()).hostname !== 'gc.kis.v2.scr.kaspersky-labs.com') requests.push(request.url()); });
  const dialog = await open(page, 'Futures');
  await dialog.getByRole('textbox', { name: 'Search text' }).fill('ES,6E');
  await dialog.getByRole('button', { name: 'Lookup', exact: true }).click();
  await dialog.getByRole('button', { name: /^Ticker/ }).click();
  await expect(dialog.getByRole('columnheader', { name: /^Ticker/ })).toHaveAttribute('aria-sort', 'descending');
  await dialog.getByRole('checkbox', { name: 'Select ticker ES', exact: true }).check();
  await dialog.getByRole('radio', { name: /^Timestamp is start/ }).check();
  await dialog.getByRole('radio', { name: 'choose timezone' }).check();
  await dialog.getByRole('combobox', { name: 'Data timezone' }).selectOption('UTC');
  await dialog.getByRole('checkbox', { name: 'I confirm' }).check();
  await dialog.getByRole('button', { name: 'Add', exact: true }).click();
  await page.getByRole('button', { name: 'Pause all', exact: true }).click();
  await page.getByRole('button', { name: 'Equity data', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Find and add equity data', exact: true }).click();
  await expect(page.getByRole('status', { name: 'Data Manager progress' })).toContainText('Finish or stop');
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await page.getByRole('button', { name: 'Resume all', exact: true }).click();
  await expect(page.getByLabel('Status for ES', { exact: true })).toHaveText('Completed', { timeout: 10000 });
  const row = page.getByRole('row').filter({ has: page.getByRole('checkbox', { name: 'Select ES', exact: true }) });
  await expect(row).toContainText('UTC'); await expect(row).toContainText('Start of bar');
  expect(requests).toEqual([]);
});

test('provider update callbacks preserve host progress and provider-job guard', async ({ page }) => {
  await page.getByRole('button', { name: 'Equity data', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Update Equity datasets', exact: true }).click();
  await expect(page.getByRole('status', { name: 'Data Manager progress' })).toContainText('Equity dataset update');
  await page.getByRole('button', { name: 'Pause all', exact: true }).click();
  await page.getByRole('button', { name: 'Futures data', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Update Futures datasets', exact: true }).click();
  await expect(page.getByRole('status', { name: 'Data Manager progress' })).toContainText('Futures dataset update');
  await expect(page.getByRole('status', { name: 'Data Manager progress' })).toContainText('complete');
  const dialog = await open(page, 'Equity');
  await dialog.getByRole('textbox', { name: 'Search text' }).fill('AAPL');
  await dialog.getByRole('button', { name: 'Lookup', exact: true }).click();
  await dialog.getByRole('checkbox', { name: 'Select ticker AAPL', exact: true }).check();
  await dialog.getByRole('checkbox', { name: 'I confirm' }).check();
  await dialog.getByRole('textbox', { name: 'Name postfix' }).fill('_guard');
  await dialog.getByRole('button', { name: 'Add', exact: true }).click();
  await page.getByRole('button', { name: 'Pause all', exact: true }).click();
  await page.getByRole('button', { name: 'Futures data', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Update Futures datasets', exact: true }).click();
  await expect(page.getByRole('status', { name: 'Data Manager progress' })).toContainText('Finish or stop');
});

});
