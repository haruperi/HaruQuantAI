import { expect, test, type Page } from '@playwright/test';
import { selectLightSkin } from './shellTestUtils';

async function launch(page: Page) { await page.goto('/'); await page.getByRole('button',{name:'Data Manager',exact:true}).click(); }
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
