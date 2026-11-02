import { expect, test, type Page } from '@playwright/test';
import { selectLightSkin } from './shellTestUtils';

async function launch(page: Page) { await page.goto('/'); await page.getByRole('button',{name:'Data Manager',exact:true}).and(page.locator('[aria-label]')).click(); }
async function openAdd(page: Page, exchange: string) {
  await page.getByRole('button',{name:'Crypto',exact:true}).click();
  await page.getByRole('menu',{name:'Crypto actions'}).getByRole('menuitem',{name:'Add crypto symbol',exact:true}).click();
  await page.getByRole('menu',{name:'Add crypto symbol exchanges'}).getByRole('menuitem',{name:exchange,exact:true}).click();
  return page.getByRole('dialog');
}
async function openDownload(page: Page) {
  await page.getByRole('button',{name:'Crypto',exact:true}).click();
  await page.getByRole('menu',{name:'Crypto actions'}).getByRole('menuitem',{name:'Download data for existing symbol',exact:true}).click();
  return page.getByRole('dialog');
}
async function addBitcoin(page: Page, postfix='_CR') {
  const dialog=await openAdd(page,'Binance spot');
  await dialog.getByRole('textbox',{name:'Filter items',exact:true}).fill('BTCUSDT');
  await dialog.getByRole('checkbox',{name:'Select symbol BTCUSDT',exact:true}).check();
  await dialog.getByRole('checkbox',{name:/I confirm/}).check();
  await dialog.getByRole('textbox',{name:'Data postfix',exact:true}).fill(postfix);
  await dialog.getByRole('button',{name:'Save',exact:true}).click();
  await expect(page.getByLabel(`Status for BTCUSDT${postfix}`,{exact:true})).toHaveText('Completed',{timeout:10000});
}

test('opens all six exact add variants with provider-specific timeframe lists',async({page})=>{
  await launch(page);
  const variants = [
    ['Binance spot','Add Binance symbol(s)',['M1','M3','M5','M15','M30','H1','H2','H4','H6','H8','H12','D1']],
    ['Binance Coin-M','Add Binance Coin-M symbol(s)',['M1','M3','M5','M15','M30','H1','H2','H4','H6','H8','H12','D1']],
    ['Binance USDT-M','Add Binance USDT-M symbol(s)',['M1','M3','M5','M15','M30','H1','H2','H4','H6','H8','H12','D1']],
    ['Bitfinex','Add Bitfinex symbol(s)',['M1','M5','M15','M30','H1','H3','H6','H12','D1']],
    ['Poloniex','Add Poloniex symbol(s)',['M5','M15','M30','H2','H4','D1']],
    ['Coinbase Pro','Add Coinbase Pro symbol(s)',['M1','M5','M15','H1','H6','D1']],
  ] as const;
  for(const [menu,title,timeframes] of variants){
    const dialog=await openAdd(page,menu); await expect(dialog).toHaveAccessibleName(title);
    await expect(dialog.getByRole('combobox',{name:'Timeframe'}).locator('option')).toHaveText([...timeframes]);
    await expect(dialog.getByText('Offline mock catalog. No exchange connection is made.')).toBeVisible();
    await dialog.getByRole('button',{name:'Close',exact:true}).last().click();
  }
});

test('filters, validates, adds, persists and reports status only in the trailing column',async({page},info)=>{
  await launch(page); const dialog=await openAdd(page,'Coinbase Pro');
  await dialog.getByRole('button',{name:'Save',exact:true}).click(); await expect(dialog.getByRole('alert')).toHaveText('No symbols selected');
  await dialog.getByRole('textbox',{name:'Filter items',exact:true}).fill('BTC-USD'); await dialog.getByRole('checkbox',{name:'Select all Coinbase Pro symbols'}).check();
  await dialog.getByRole('button',{name:'Save',exact:true}).click(); await expect(dialog.getByRole('alert')).toContainText('Data Disclaimer');
  await dialog.getByRole('textbox',{name:'Filter items',exact:true}).fill('ETH-USD'); await expect(dialog.getByRole('checkbox',{name:'Select symbol ETH-USD'})).not.toBeChecked();
  await dialog.getByRole('checkbox',{name:'Select symbol ETH-USD'}).check(); await dialog.getByRole('checkbox',{name:/I confirm/}).check(); await dialog.getByRole('combobox',{name:'Timeframe'}).selectOption('H6'); await dialog.getByRole('textbox',{name:'Data postfix'}).fill('_CB');
  await page.screenshot({path:info.outputPath('crypto-add-dark.png')}); await dialog.getByRole('button',{name:'Save',exact:true}).click();
  const status=page.getByLabel('Status for ETH-USD_CB',{exact:true}); await expect(status).toHaveText('Completed',{timeout:10000});
  const row=page.getByRole('row').filter({has:page.getByRole('checkbox',{name:'Select ETH-USD_CB',exact:true})}); await expect(row.getByRole('cell').nth(1)).toHaveText('ETH-USD_CB'); await expect(row.getByRole('cell').nth(5)).toHaveText('H6'); await expect(row.getByRole('cell').nth(13)).toHaveText('Crypto');
  await page.reload(); await expect(page.getByLabel('Status for ETH-USD_CB',{exact:true})).toHaveText('Completed');
});

test('download requires Crypto selection and supports presets, validation, progress and coverage',async({page},info)=>{
  await launch(page); await openDownload(page); await expect(page.getByLabel('Data Manager progress')).toContainText('at least one Crypto');
  await addBitcoin(page); await page.getByRole('checkbox',{name:'Select BTCUSDT_CR',exact:true}).check(); await page.getByRole('checkbox',{name:'Select EURUSD',exact:true}).check();
  let dialog=await openDownload(page); await expect(dialog).toHaveAccessibleName("Download crypto data for 'BTCUSDT_CR'");
  for(const name of ['Last 6 months','Last year','Last 5 years','Last 10 years','All time','Since last date']){await dialog.getByRole('button',{name,exact:true}).click();await expect(dialog.getByRole('button',{name,exact:true})).toHaveAttribute('aria-pressed','true');}
  await dialog.getByLabel('From',{exact:true}).fill('2025-01-03'); await dialog.getByLabel('To',{exact:true}).fill('2025-01-01'); await dialog.getByRole('button',{name:'Start download',exact:true}).click(); await expect(dialog.getByRole('alert')).toContainText('valid date');
  await dialog.getByLabel('From',{exact:true}).fill('2025-01-01'); await dialog.getByLabel('To',{exact:true}).fill('2025-01-03'); await dialog.getByRole('radio',{name:'Overwrite existing data'}).check(); await page.screenshot({path:info.outputPath('crypto-download-dark.png')}); await dialog.getByRole('button',{name:'Start download',exact:true}).click();
  await expect(page.getByLabel('Data Manager progress')).toContainText('download completed',{timeout:10000}); const row=page.getByRole('row').filter({has:page.getByRole('checkbox',{name:'Select BTCUSDT_CR',exact:true})}); await expect(row).toContainText('2025-01-03');
  dialog=await openDownload(page); await expect(dialog.getByText('This download is simulated.')).toBeVisible(); await dialog.getByRole('button',{name:'Close'}).last().click();
});

test('supports shared pause/reload/resume, light narrow layout, focus and storage failure',async({page},info)=>{
  await launch(page); let dialog=await openAdd(page,'Poloniex'); await dialog.getByRole('textbox',{name:'Filter items'}).fill('BTC_USDT'); await dialog.getByRole('checkbox',{name:'Select symbol BTC_USDT'}).check(); await dialog.getByRole('checkbox',{name:/I confirm/}).check(); await dialog.getByRole('textbox',{name:'Data postfix'}).fill('_P'); await dialog.getByRole('button',{name:'Save'}).click(); await page.getByRole('button',{name:'Pause all'}).click(); await page.reload(); await expect(page.getByLabel('Data Manager progress')).toContainText('paused'); await page.getByRole('button',{name:'Resume all'}).click(); await expect(page.getByLabel('Status for BTC_USDT_P')).toHaveText('Completed',{timeout:10000});
  await selectLightSkin(page); await page.setViewportSize({width:620,height:700}); dialog=await openAdd(page,'Bitfinex'); await expect(dialog.getByRole('button',{name:'Save'})).toBeInViewport(); await page.screenshot({path:info.outputPath('crypto-light-narrow.png')}); await dialog.getByRole('button',{name:'Save'}).focus(); await page.keyboard.press('Tab'); await expect(dialog.getByRole('button',{name:'Close'}).first()).toBeFocused();
  await dialog.getByRole('textbox',{name:'Filter items'}).fill('BTCUSD'); await dialog.getByRole('checkbox',{name:'Select symbol BTCUSD'}).check(); await dialog.getByRole('checkbox',{name:/I confirm/}).check(); await page.evaluate(()=>{Storage.prototype.setItem=()=>{throw new Error('quota');};}); await dialog.getByRole('button',{name:'Save'}).click(); await expect(dialog.getByRole('alert')).toContainText('Unable to save'); await page.keyboard.press('Escape'); await expect(page.getByRole('button',{name:'Crypto',exact:true})).toBeFocused();
});

test.describe('Backend crypto donor popup', () => {
  async function start(page: Page, failCatalogue = false, exchange = 'Binance spot', title = 'Add Binance symbol(s)') {
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
      if (endpoint.endsWith('/auth/login')) data = { token: 'isolated-binance-session' };
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
      else if (endpoint.endsWith('/catalog')) {
        if (state.failCatalogue) { await route.fulfill({ status: 503, json: { status: 'error', error: { code: 'UNAVAILABLE', message: 'Binance catalogue unavailable' } } }); return; }
        data = state.catalogue;
      } else if (endpoint.endsWith('/add')) {
        const body = route.request().postDataJSON(); state.writes.push(body);
        await state.saveGate;
        if (state.failSave) { await route.fulfill({ status: 409, json: { status: 'error', error: { code: 'CONFLICT', message: 'Binance datasets were not saved' } } }); return; }
        data = { records: body.definitions.map((row: { symbol: string; timeframe: string }) => ({ ...row, id: `saved:${row.symbol}`, source: 'binance' })) };
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
    await page.getByRole('button', { name: 'Crypto', exact: true }).click();
    await page.getByRole('menuitem', { name: 'Add crypto symbol', exact: true }).click();
    await page.getByRole('menuitem', { name: exchange, exact: true }).click();
    await expect(page.getByRole('dialog', { name: title, exact: true })).toBeVisible();
    return state;
  }

  test('host registration and refresh retry preserve the draft', async ({ page }) => {
    const state = await start(page);
    const modal = page.getByRole('dialog', { name: 'Add Binance symbol(s)', exact: true });
    await modal.getByRole('button', { name: 'Save', exact: true }).click();
    await expect(modal.getByRole('alert')).toContainText('at least one');
    await modal.getByRole('textbox', { name: 'Filter items' }).fill('BTC');
    await modal.getByRole('checkbox', { name: 'Select symbol BTCUSDT' }).check();
    await modal.getByRole('checkbox', { name: /I confirm/ }).check();
    await modal.getByRole('textbox', { name: 'Data postfix' }).fill('_TEST');
    state.failSave = true;
    await modal.getByRole('button', { name: 'Save', exact: true }).click();
    await expect(modal.getByRole('alert')).toContainText('not saved');
    state.failSave = false; state.failRefresh = true;
    await modal.getByRole('button', { name: 'Save', exact: true }).click();
    await expect(modal.getByRole('alert')).toContainText('Retry refresh');
    expect(state.writes).toHaveLength(2);
    expect(state.writes[1].definitions[0].symbol).toBe('BTCUSDT_TEST');
    state.failRefresh = false;
    await modal.getByRole('button', { name: 'Retry refresh', exact: true }).click();
    await expect(modal).toHaveCount(0);
    expect(state.writes).toHaveLength(2);
  });
  test('responsive donor layout', async ({ page }, info) => {
    await start(page);
    const modal = page.getByRole('dialog', { name: 'Add Binance symbol(s)', exact: true });
    await expect(modal.getByText('Choose from available data', { exact: true })).toBeVisible();
    await page.screenshot({ path: info.outputPath('crypto-dark.png') });
    await page.evaluate(() => document.documentElement.setAttribute('data-theme', 'light'));
    await page.screenshot({ path: info.outputPath('crypto-light.png') });
    await page.setViewportSize({ width: 390, height: 844 });
    await expect(modal.getByRole('button', { name: 'Save', exact: true })).toBeInViewport();
    await page.screenshot({ path: info.outputPath('crypto-narrow.png') });
  });
  for (const [exchange, title] of [['Binance Coin-M', 'Add Binance Coin-M symbol(s)'], ['Binance USDT-M', 'Add Binance USDT-M symbol(s)'], ['Bitfinex', 'Add Bitfinex symbol(s)'], ['Coinbase Pro', 'Add Coinbase Pro symbol(s)'], ['Poloniex', 'Add Poloniex symbol(s)']]) {
    test('host exchange catalogue: ' + exchange, async ({ page }) => {
      await start(page, false, exchange, title);
      const modal = page.getByRole('dialog', { name: title, exact: true });
      await expect(modal.getByRole('checkbox', { name: 'Select symbol BTCUSDT' })).toBeVisible();
      await expect(modal.getByRole('combobox', { name: 'Timeframe', exact: true })).toHaveValue('M1');
    });
  }
  test('failed and malformed catalogues can be retried', async ({ page }) => {
    const state = await start(page, true);
    const modal = page.getByRole('dialog', { name: 'Add Binance symbol(s)', exact: true });
    await expect(modal.getByRole('alert')).toContainText('unavailable');
    state.failCatalogue = false; state.catalogue = { invalid: true };
    await modal.getByRole('button', { name: 'Retry catalogue' }).click();
    await expect(modal.getByRole('alert')).toContainText('invalid symbol catalogue');
    state.catalogue = ['BTCUSDT'];
    await modal.getByRole('button', { name: 'Retry catalogue' }).click();
    await expect(modal.getByRole('checkbox', { name: 'Select symbol BTCUSDT' })).toBeVisible();
  });

});
