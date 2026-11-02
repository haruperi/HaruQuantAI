import { expect, test, type Page } from '@playwright/test';
import { selectLightSkin } from './shellTestUtils';
import { mkdir, writeFile, readFile } from 'node:fs/promises';
import path from 'node:path';
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
async function open(page:Page, command='Add Darwinex data') { await page.getByRole('button',{name:'Darwinex Tick Data',exact:true}).click(); await page.getByRole('menuitem',{name:command,exact:true}).click(); return page.getByRole('dialog'); }
async function launch(page:Page) { await page.goto('/');await page.getByRole('button',{name:'Data Manager',exact:true}).and(page.locator('[aria-label]')).click(); }
async function add(page:Page) { const dialog=await open(page);await dialog.getByRole('textbox',{name:'Filter items',exact:true}).fill('AUDUSD');await dialog.getByRole('checkbox',{name:'Select symbol AUDUSD',exact:true}).check();await dialog.getByRole('checkbox',{name:/I confirm/}).check();await dialog.getByRole('textbox',{name:'Data postfix',exact:true}).fill('_D');await dialog.getByRole('button',{name:'Save',exact:true}).click();await expect(page.getByLabel('Status for AUDUSD_D',{exact:true})).toHaveText('Completed',{timeout:10000}); }
test('catalogue validation, filtering, selection, persistence and shared job recovery',async({page},info)=>{
 await launch(page);const dialog=await open(page);await expect(dialog.getByRole('checkbox',{name:/^Select symbol /})).toHaveCount(328);
 await dialog.getByRole('button',{name:'Save',exact:true}).click();await expect(dialog.getByRole('alert')).toHaveText('No symbols selected');
 await dialog.getByRole('textbox',{name:'Filter items',exact:true}).fill('AUDUSD');await dialog.getByRole('checkbox',{name:'Select all Darwinex symbols'}).check();await dialog.getByRole('button',{name:'Save',exact:true}).click();await expect(dialog.getByRole('alert')).toContainText('confirm');
 await dialog.getByRole('textbox',{name:'Filter items',exact:true}).fill('AUDCAD');await expect(dialog.getByRole('checkbox',{name:'Select symbol AUDCAD',exact:true})).not.toBeChecked();
 await dialog.getByRole('checkbox',{name:'Select symbol AUDCAD',exact:true}).check();await dialog.getByRole('checkbox',{name:/I confirm/}).check();await dialog.getByRole('textbox',{name:'Data postfix',exact:true}).fill('_D');await page.screenshot({path:info.outputPath('darwinex-add-dark.png')});
 await dialog.getByRole('button',{name:'Save',exact:true}).click();await page.getByRole('button',{name:'Pause all',exact:true}).click();await page.reload();await expect(page.getByLabel('Data Manager progress')).toContainText('paused');await page.getByRole('button',{name:'Resume all',exact:true}).click();await expect(page.getByLabel('Status for AUDCAD_D',{exact:true})).toHaveText('Completed',{timeout:10000});await page.reload();await expect(page.getByLabel('Status for AUDCAD_D',{exact:true})).toHaveText('Completed');
});
test('broker mapping, unresolved mass actions, Back and all-skipped validation',async({page})=>{
 await page.addInitScript(()=>localStorage.setItem('sqx-data-manager-v1',JSON.stringify({version:1,definitions:[],brokers:[{id:'b',name:'Test broker',postfix:'_B',timezone:'Europe/Prague',mtUse:true,symbols:[]}]})));
 await launch(page);let dialog=await open(page);await dialog.getByRole('textbox',{name:'Filter items',exact:true}).fill('AUDUSD');await dialog.getByRole('checkbox',{name:'Select symbol AUDUSD',exact:true}).check();await dialog.getByRole('combobox',{name:'Broker profile',exact:true}).selectOption('b');await expect(dialog.getByRole('textbox',{name:'Data postfix',exact:true})).toHaveValue('_B');await expect(dialog.getByRole('status')).toContainText('non-default');await dialog.getByRole('checkbox',{name:/I confirm/}).check();await dialog.getByRole('button',{name:'Save',exact:true}).click();
 dialog=page.getByRole('dialog',{name:'Add Darwinex data - identify symbols',exact:true});await dialog.getByRole('button',{name:'Save',exact:true}).click();await expect(dialog.getByRole('alert')).toContainText('proper symbol');await dialog.getByRole('button',{name:'Skip adding the symbol',exact:true}).click();await dialog.getByRole('button',{name:'Save',exact:true}).click();await expect(dialog.getByRole('alert')).toHaveText('No symbols selected');await dialog.getByRole('button',{name:'< Back',exact:true}).click();await expect(page.getByRole('checkbox',{name:'Select symbol AUDUSD',exact:true})).toBeChecked();await page.getByRole('dialog').getByRole('button',{name:'Save',exact:true}).click();await dialog.getByRole('button',{name:'Default symbol',exact:true}).click();await dialog.getByRole('button',{name:'Save',exact:true}).click();await expect(page.getByLabel('Status for AUDUSD_B',{exact:true})).toHaveText('Completed',{timeout:10000});await expect(page.getByRole('table',{name:'Historical data',exact:true})).toContainText('Europe/Prague');
});
test('folder import discovers compressed filenames, validates, cancels and persists',async({page},info)=>{
 const root=info.outputPath('Darwinex');await mkdir(path.join(root,'EURUSD'),{recursive:true});await mkdir(path.join(root,'GBPUSD'),{recursive:true});await writeFile(path.join(root,'EURUSD','a.log.gz'),'mock bytes');await writeFile(path.join(root,'GBPUSD','ignore.txt'),'not data');
 await launch(page);let dialog=await open(page,'Import data from a Darwinex folder');await dialog.getByRole('button',{name:'Start import',exact:true}).click();await expect(dialog.getByRole('alert')).toContainText('Select Darwinex');await dialog.getByLabel('Select Darwinex data folder',{exact:true}).setInputFiles(root);await expect(dialog.getByRole('checkbox',{name:/^Select symbol /})).toHaveCount(1);await dialog.getByRole('checkbox',{name:'Select all import symbols'}).check();await dialog.getByRole('button',{name:'Start import',exact:true}).click();await expect(dialog.getByRole('alert')).toContainText('exists');await dialog.getByRole('textbox',{name:'Data postfix',exact:true}).fill('_I');await dialog.getByRole('button',{name:'Start import',exact:true}).click();await page.getByRole('button',{name:'Stop all',exact:true}).click();await expect(page.getByRole('checkbox',{name:'Select EURUSD_I',exact:true})).toHaveCount(0);
 dialog=await open(page,'Import data from a Darwinex folder');await dialog.getByLabel('Select Darwinex data folder',{exact:true}).setInputFiles(root);await dialog.getByRole('checkbox',{name:'Select all import symbols'}).check();await dialog.getByRole('button',{name:'Start import',exact:true}).click();await expect(page.getByLabel('Status for EURUSD_I',{exact:true})).toHaveText('Completed',{timeout:10000});expect(await readFile(path.join(root,'EURUSD','a.log.gz'),'utf8')).toBe('mock bytes');await page.reload();dialog=await open(page,'Import data from a Darwinex folder');await expect(dialog.getByText('Select the folder again to access its available symbols.')).toBeVisible();
});
test('download selection, date presets, validation, intervals and restricted profile',async({page},info)=>{
 await launch(page);await open(page,'Download data for existing symbols');await expect(page.getByLabel('Data Manager progress')).toContainText('at least one Darwinex');await add(page);await page.getByRole('checkbox',{name:'Select AUDUSD_D',exact:true}).check();await page.getByRole('checkbox',{name:'Select EURUSD',exact:true}).check();let dialog=await open(page,'Download data for existing symbols');await expect(dialog).toHaveAccessibleName("Download Darwinex data for 'AUDUSD_D'");
 for(const name of ['Last 6 months','Last year','Last 5 years','Last 10 years','All time','Since last date']) {await dialog.getByRole('button',{name,exact:true}).click();await expect(dialog.getByRole('button',{name,exact:true})).toHaveAttribute('aria-pressed','true');}
 await dialog.getByLabel('From',{exact:true}).fill('2025-01-03');await dialog.getByLabel('To',{exact:true}).fill('2025-01-01');await dialog.getByRole('button',{name:'Start download',exact:true}).click();await expect(dialog.getByRole('alert')).toContainText('valid date');await dialog.getByLabel('From',{exact:true}).fill('2025-01-01');await dialog.getByLabel('To',{exact:true}).fill('2025-01-03');await dialog.getByRole('radio',{name:'Overwrite existing data',exact:true}).check();await page.screenshot({path:info.outputPath('darwinex-download-dark.png')});await dialog.getByRole('button',{name:'Start download',exact:true}).click();await expect(page.getByLabel('Data Manager progress')).toContainText('download completed',{timeout:10000});await expect(page.getByRole('row').filter({has:page.getByRole('checkbox',{name:'Select AUDUSD_D',exact:true})})).toContainText('2025-01-03');
 await setFeatureProfileFixture(page,'Starter');await page.getByRole('checkbox',{name:'Select AUDUSD_D',exact:true}).check();dialog=await open(page,'Download data for existing symbols');await expect(dialog.getByText('Darwinex CDN download is available only for users of full license.')).toBeVisible();await expect(dialog.getByRole('button',{name:'Start download'})).toHaveCount(0);await dialog.getByRole('button',{name:'Upgrade To Pro Version'}).click();await expect(dialog.getByRole('link')).toHaveCount(0);
});
test('light narrow layout, focus, quota failure and cancellation',async({page},info)=>{
 await launch(page);await selectLightSkin(page);await page.setViewportSize({width:620,height:700});const dialog=await open(page);await dialog.getByRole('textbox',{name:'Filter items',exact:true}).fill('AUDUSD');await dialog.getByRole('checkbox',{name:'Select symbol AUDUSD',exact:true}).check();await dialog.getByRole('checkbox',{name:/I confirm/}).check();await expect(dialog.getByRole('button',{name:'Save',exact:true})).toBeInViewport();await page.screenshot({path:info.outputPath('darwinex-light-narrow.png')});await dialog.getByRole('button',{name:'Save',exact:true}).focus();await page.keyboard.press('Tab');await expect(dialog.getByRole('button',{name:'Close',exact:true}).first()).toBeFocused();await page.evaluate(()=>{Storage.prototype.setItem=()=>{throw new Error('quota');};});await dialog.getByRole('button',{name:'Save',exact:true}).click();await expect(dialog.getByRole('alert')).toContainText('Unable to save');await page.keyboard.press('Escape');await expect(page.getByRole('button',{name:'Darwinex Tick Data',exact:true})).toBeFocused();
});


test.describe('Backend Darwinex donor popup', () => {
  async function start(page: Page, failCatalogue = false) {
    const state = { catalogue: ['AUDUSD', 'AUDCAD', 'EURUSD'] as unknown, failCatalogue, failSave: false, failRefresh: false, saveGate: null as Promise<void> | null, writes: [] as { definitions: { symbol: string; underlying: string; timeframe: string; broker?: string }[] }[] };
    await page.addInitScript(() => {
      const original = window.fetch.bind(window);
      window.fetch = ((input: RequestInfo | URL, init?: RequestInit) => String(input).includes('/api/v1/events?')
        ? Promise.resolve(new Response(new ReadableStream<Uint8Array>({ start() {} }), { headers: { 'Content-Type': 'text/event-stream' } }))
        : original(input, init)) as typeof fetch;
    });
    await page.route('**/api/v1/**', async route => {
      const url = new URL(route.request().url()), endpoint = url.pathname;
      let data: unknown = [];
      if (endpoint.endsWith('/auth/login')) data = { token: 'isolated-darwinex-session' };
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
      else if (endpoint.endsWith('/sources/darwinex/catalog')) {
        if (state.failCatalogue) { await route.fulfill({ status: 503, json: { status: 'error', error: { code: 'UNAVAILABLE', message: 'Darwinex catalogue unavailable' } } }); return; }
        data = state.catalogue;
      } else if (endpoint.endsWith('/sources/darwinex/add')) {
        const body = route.request().postDataJSON(); state.writes.push(body);
        await state.saveGate;
        if (state.failSave) { await route.fulfill({ status: 409, json: { status: 'error', error: { code: 'CONFLICT', message: 'Darwinex datasets were not saved' } } }); return; }
        data = { records: body.definitions.map((row: { symbol: string; timeframe: string }) => ({ ...row, id: `saved:${row.symbol}`, source: 'darwinex' })) };
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
    await page.getByRole('button', { name: 'Darwinex Tick Data', exact: true }).click();
    await page.getByRole('menuitem', { name: 'Add Darwinex data', exact: true }).click();
    await expect(page.getByRole('dialog', { name: 'Add Darwinex data', exact: true })).toBeVisible();
    return state;
  }

  test('donor layout, filter selection, broker postfix and backend Save', async ({ page }) => {
    const state = await start(page);
    const modal = page.getByRole('dialog', { name: 'Add Darwinex data', exact: true });
    await expect(modal.getByText('Choose from available data', { exact: true })).toBeVisible();
    await expect(modal.getByRole('checkbox', { name: /^Select symbol / })).toHaveCount(3);
    await expect(modal.getByRole('columnheader', { name: 'Available data range' })).toBeVisible();
    await modal.getByRole('button', { name: 'Save', exact: true }).click();
    await expect(modal.getByRole('alert')).toContainText('No symbols selected');
    await modal.getByRole('textbox', { name: 'Filter Darwinex symbols' }).fill('AUD');
    await modal.getByRole('checkbox', { name: 'Select all displayed Darwinex symbols' }).check();
    await modal.getByRole('textbox', { name: 'Filter Darwinex symbols' }).fill('EUR');
    await expect(modal.getByRole('checkbox', { name: 'Select symbol EURUSD' })).not.toBeChecked();
    await modal.getByRole('button', { name: 'Save', exact: true }).click();
    await expect(modal.getByRole('alert')).toContainText('confirm');
    await modal.getByRole('textbox', { name: 'Filter Darwinex symbols' }).fill('');
    await modal.getByRole('combobox', { name: 'Broker profile', exact: true }).selectOption('1');
    await expect(modal.getByRole('textbox', { name: 'Data postfix' })).toHaveValue('_R');
    await expect(modal.getByText('Timestamps remain in UTC', { exact: false })).toBeVisible();
    await modal.getByRole('checkbox', { name: /I confirm/ }).check();
    await page.screenshot({ path: 'test-results/darwinex-host-add-dark.png' });
    state.failRefresh = true;
    await modal.getByRole('button', { name: 'Save', exact: true }).click();
    await expect(modal.getByRole('button', { name: 'Retry refresh' })).toBeVisible();
    expect(state.writes).toHaveLength(1);
    expect(state.writes[0].definitions.map(row => row.underlying).sort()).toEqual(['AUDCAD', 'AUDUSD']);
    expect(state.writes[0].definitions.every(row => row.broker === 'Research broker' && row.timeframe === 'M1' && row.symbol.endsWith('_R'))).toBe(true);
    state.failRefresh = false;
    await modal.getByRole('button', { name: 'Retry refresh' }).click();
    await expect(modal).toHaveCount(0);
    expect(state.writes).toHaveLength(1);
  });

  test('catalogue retry, malformed response and save failures retain the draft', async ({ page }) => {
    const state = await start(page, true);
    const modal = page.getByRole('dialog', { name: 'Add Darwinex data', exact: true });
    await expect(modal.getByRole('alert')).toContainText('Darwinex catalogue unavailable');
    state.failCatalogue = false; state.catalogue = [{ symbol: 'EURUSD' }];
    await modal.getByRole('button', { name: 'Retry catalogue' }).click();
    await expect(modal.getByRole('alert')).toContainText('invalid Darwinex catalogue');
    state.catalogue = ['EURUSD'];
    await modal.getByRole('button', { name: 'Retry catalogue' }).click();
    await modal.getByRole('checkbox', { name: 'Select symbol EURUSD' }).check();
    await modal.getByRole('checkbox', { name: /I confirm/ }).check();
    state.failSave = true;
    await modal.getByRole('button', { name: 'Save', exact: true }).click();
    await expect(modal.getByRole('alert')).toContainText('Darwinex datasets were not saved');
    await expect(modal.getByRole('checkbox', { name: 'Select symbol EURUSD' })).toBeChecked();
    await page.keyboard.press('Escape');
    await expect(modal).toHaveCount(0);
    await expect(page.getByRole('button', { name: 'Darwinex Tick Data', exact: true })).toBeFocused();
  });

  test('light and narrow layouts keep keyboard actions accessible', async ({ page }) => {
    await start(page);
    const modal = page.getByRole('dialog', { name: 'Add Darwinex data', exact: true });
    await expect(modal.getByRole('checkbox', { name: /^Select symbol / })).toHaveCount(3);
    await page.evaluate(() => { document.documentElement.dataset.theme = 'light'; });
    await page.screenshot({ path: 'test-results/darwinex-host-add-light.png' });
    await page.setViewportSize({ width: 520, height: 700 });
    await expect(modal.getByRole('button', { name: 'Save', exact: true })).toBeInViewport();
    expect(await modal.evaluate(element => element.scrollWidth <= element.clientWidth)).toBe(true);
    await modal.getByRole('button', { name: 'Save', exact: true }).focus();
    await page.keyboard.press('Tab');
    await expect(modal.getByRole('button', { name: 'Close', exact: true }).first()).toBeFocused();
    await page.screenshot({ path: 'test-results/darwinex-host-add-narrow.png' });
  });

  test('pending registration prevents duplicate submits and accidental close', async ({ page }) => {
    const state = await start(page);
    const modal = page.getByRole('dialog', { name: 'Add Darwinex data', exact: true });
    await modal.getByRole('checkbox', { name: 'Select symbol EURUSD' }).check();
    await modal.getByRole('checkbox', { name: /I confirm/ }).check();
    let release: () => void = () => {};
    state.saveGate = new Promise<void>(resolve => { release = resolve; });
    await modal.getByRole('button', { name: 'Save', exact: true }).click();
    await expect(modal.getByRole('button', { name: 'Saving…' })).toBeDisabled();
    await page.keyboard.press('Escape');
    await expect(modal).toBeVisible();
    expect(state.writes).toHaveLength(1);
    release();
    await expect(modal).toHaveCount(0);
  });
});
