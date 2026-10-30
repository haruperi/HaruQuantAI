import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  await page.addInitScript(() => {
    localStorage.setItem(
      'haruquantai.host-session.v1:http://127.0.0.1:4173/api/v1',
      JSON.stringify({
        version: 1,
        token: 'offline-token',
        expires_at: '2099-01-01T00:00:00.000Z',
      }),
    );
  });
  await page.route('**/*', (route) =>
    ['127.0.0.1', 'localhost'].includes(new URL(route.request().url()).hostname)
      ? route.continue()
      : route.abort(),
  );
  await page.route('**/api/v1/**', (route) => route.abort());
  await page.goto('/datamanager');
});

test('standalone disclaimer keeps content, Escape and launcher focus across themes', async ({
  page,
}) => {
  const launcher = page.getByRole('button', { name: 'Dukascopy data', exact: true });
  for (const theme of ['dark', 'light']) {
    if (theme === 'light')
      await page.evaluate(async () => {
        const modulePath = '/shell/store.ts';
        const { useAppStore } = await import(modulePath);
        useAppStore.getState().updateSettings({ theme: 'light' });
      });
    await expect(page.locator('html')).toHaveAttribute('data-theme', theme);
    await launcher.click();
    await page.getByRole('menuitem', { name: 'Dukascopy Data Disclaimer', exact: true }).click();
    const dialog = page.getByRole('dialog', { name: 'Dukascopy data disclaimer', exact: true });
    await expect(dialog).toContainText('AS IS');
    await expect(dialog.getByRole('button', { name: 'Close', exact: true }).first()).toBeFocused();
    await page.screenshot({ path: `test-results/dukascopy-disclaimer-${theme}.png` });
    await page.keyboard.press('Escape');
    await expect(dialog).toHaveCount(0);
    await expect(launcher).toBeFocused();
  }
});

test('saved broker postfix is preserved through confirmed registration', async ({ page }) => {
  const rows:Array<Record<string,unknown>>=[];
  await page.route('**/api/v1/data/brokers',route=>route.fulfill({json:{status:'success',data:[{id:'1',name:'Pilot broker',description:'',timezone:'UTC',postfix:'_P',stockpicker_use:false,mt_use:true,is_system:false,stocks:[],customized_stocks:0,total_symbols:0,total_sessions:0,spread_model:{model:'inherit'},commission_model:{model:'inherit'}}]}}));
  await page.route('**/api/v1/data/home/datasets',route=>route.fulfill({json:{status:'success',data:rows}}));
  await page.route('**/api/v1/data/datasets',async route=>{
    const body=route.request().postDataJSON();const row={...body,id:`dukascopy:${body.symbol}:${body.timeframe}`,broker:'Pilot broker',timezone:'UTC',category:'Forex',bars:0,date_from:'',date_to:'',symbolDefinition:body.instrument??'-1',path:`data/market/dukascopy/m1/${body.symbol.toLowerCase()}`};rows.push(row);
    await route.fulfill({json:{status:'success',data:row}});
  });
  await page.addInitScript(() =>
    localStorage.setItem(
      'sqx-data-manager-v1',
      JSON.stringify({
        version: 1,
        definitions: [],
        brokers: [
          {
            id: '1',
            name: 'Pilot broker',
            postfix: '_P',
            timezone: 'UTC',
            mtUse: true,
            symbols: [],
          },
        ],
      }),
    ),
  );
  await page.goto('/datamanager');
  await page.getByRole('button', { name: 'Dukascopy data', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Add new Dukascopy symbol', exact: true }).click();
  const add = page.getByRole('dialog', { name: 'Add Dukascopy data', exact: true });
  await add.getByLabel('Filter available symbols').fill('AUDUSD');
  await add.getByRole('checkbox', { name: 'Select symbol AUDUSD', exact: true }).check();
  await add.getByLabel('Broker profile *', { exact: true }).selectOption('1');
  await add.getByRole('switch').check();
  await add.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(add).toHaveCount(0);
  expect(rows).toHaveLength(1);
  expect(rows[0]).toMatchObject({symbol:'AUDUSD_P',broker:'Pilot broker'});
});
