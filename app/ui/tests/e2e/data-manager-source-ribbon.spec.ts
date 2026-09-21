import { expect, test, type Page } from '@playwright/test';
import { selectLightSkin } from './shellTestUtils';

async function openDataManager(page: Page) {
  await page.goto('/');
  await page.getByRole('button', { name: 'Data Manager', exact: true }).click();
  await expect(page.getByRole('table', { name: 'Historical data' })).toBeVisible();
}

async function openProviderCommand(page: Page, provider: string, command: string, dialogTitle: string) {
  if (command === 'Download data for existing symbol' && provider === 'Dukascopy data') { await page.getByRole('checkbox', { name: 'Select EURUSD', exact: true }).check(); dialogTitle = "Download Dukascopy data for 'EURUSD'"; }
  if (command === 'Import one data file') { await page.getByRole('checkbox', { name: 'Select XAUUSD', exact: true }).check(); dialogTitle = "Data import for 'XAUUSD'"; }
  const ribbon = page.getByLabel('Data source operations');
  await ribbon.getByRole('button', { name: provider, exact: true }).click();
  const menu = page.getByRole('menu', { name: `${provider} actions` });
  await menu.getByRole('menuitem', { name: command, exact: true }).click();
  if (provider === 'Darwinex Tick Data' && command === 'Download data for existing symbols') { await expect(page.getByLabel('Data Manager progress')).toContainText('at least one Darwinex'); return; }
  await expect(page.getByRole('dialog', { name: dialogTitle })).toBeVisible();
  await page.getByRole('dialog', { name: dialogTitle }).getByRole('button', { name: 'Close' }).first().click();
  await expect(ribbon.getByRole('button', { name: provider, exact: true })).toBeFocused();
  if (command === 'Import one data file') await page.getByRole('checkbox', { name: 'Select XAUUSD', exact: true }).uncheck();
  if (provider === 'Dukascopy data' && command === 'Download data for existing symbol') await page.getByRole('checkbox', { name: 'Select EURUSD', exact: true }).uncheck();
}

test('Data sources exposes every provider workflow and remains mock-only', async ({ page }) => {
  const providerRequests: string[] = [];
  page.on('request', request => {
    if (!['127.0.0.1', 'localhost'].includes(new URL(request.url()).hostname) && /dukascopy|darwinex|yahoo|binance|bitfinex|poloniex|coinbase|metaquotes/i.test(request.url())) providerRequests.push(request.url());
  });
  await openDataManager(page);
  await page.getByRole('button', { name: 'Broker profiles', exact: true }).click();
  await expect(page.getByLabel('Broker profile operations').getByRole('button')).toHaveText([
    'Add new', 'Update data for broker (automatic)', 'Import broker instruments from JSON',
    'Import broker sessions from JSON', 'Edit stocks', 'Mass delete', 'Save', 'Load',
  ]);
  await expect(page.getByRole('table', { name: 'Broker profiles', exact: true }).getByRole('columnheader')).toHaveText([
    '', 'Name', 'Description', 'Postfix', 'Timezone', 'Customized stocks', 'Customized instruments', 'Customized sessions',
  ]);
    await expect(page.getByText('No brokers are defined.', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Stock groups', exact: true }).click();
  await expect(page.getByLabel('Stock group operations').getByRole('button')).toHaveText([
    'Add new', 'Update data in group (automatic)', 'Edit stocks', 'Mass delete', 'Save', 'Load',
  ]);
  await expect(page.getByRole('table', { name: 'Stock groups', exact: true }).getByRole('columnheader')).toHaveText([
    '', 'Name', 'Count', 'Description', 'Number of symbols', 'Downloaded', 'Ready to use?', 'Data from', 'Data to',
  ]);
  await expect(page.getByText('No groups of stocks are defined.', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'External indicators', exact: true }).click();
  await expect(page.getByLabel('External indicator operations').getByRole('button')).toHaveText([
    'Add new', 'Import indicator data', 'Recognize from file', 'View & Analyze', 'Mass delete', 'Save', 'Load',
  ]);
  await expect(page.getByRole('table', { name: 'External indicators', exact: true }).getByRole('columnheader')).toHaveText([
    '', 'Name', 'Values', 'Data type', 'Timeframe', 'Date from', 'Date to', 'Total Days', 'Total Records', '', '',
  ]);
  await expect(page.getByText('No External indicators defined.', { exact: true })).toBeVisible();
  await expect(page.getByText('Records: 0', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Instruments', exact: true }).click();
  await expect(page.getByLabel('Instrument operations').getByRole('button')).toHaveText([
    'Add Instrument', 'Clone Instrument', 'Mass Edit Instrument', 'Mass Delete', 'Save', 'Load',
  ]);
  await expect(page.getByRole('table', { name: 'Instruments', exact: true }).getByRole('columnheader')).toHaveText([
    '', 'Instrument ▴', 'Description', 'Broker profile', 'Point value', 'Pip/Tick size', 'Pip/Tick step',
    'Default spread', 'Default slippage', 'Commissions', 'Swap', 'Data type', 'Order size mult.', 'Order size step', '',
  ]);
  await page.getByRole('textbox', { name: 'Filter instruments' }).fill('Euro');
  await expect(page.getByRole('table', { name: 'Instruments', exact: true }).getByRole('row')).toHaveCount(2);
  await page.getByRole('checkbox', { name: 'Select all visible instruments' }).check();
  await expect(page.getByRole('checkbox', { name: 'Select instrument EURUSD', exact: true })).toBeChecked();
  await page.getByRole('button', { name: 'Sessions', exact: true }).click();
  await expect(page.getByLabel('Session operations').getByRole('button')).toHaveText([
    'Add Session', 'Clone Session', 'Mass Delete', 'Save', 'Load',
  ]);
  await expect(page.getByRole('table', { name: 'Sessions', exact: true })).toBeVisible();
  await expect(page.getByRole('table', { name: 'Sessions', exact: true }).getByRole('columnheader')).toHaveText([
    '', 'Session Name', 'Broker profile', '', '',
  ]);
  await page.getByRole('textbox', { name: 'Filter sessions' }).fill('Forex');
  await expect(page.getByRole('table', { name: 'Sessions', exact: true }).getByRole('row')).toHaveCount(2);
  await page.getByRole('checkbox', { name: 'Select all visible sessions' }).check();
  await expect(page.getByRole('checkbox', { name: 'Select session Forex 24/5', exact: true })).toBeChecked();
  await page.getByRole('textbox', { name: 'Filter sessions' }).fill('missing-session');
  await expect(page.getByText('No matching sessions.', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Tools', exact: true }).click();
  await expect(page.getByLabel('Data tools').getByRole('button')).toHaveText([
    'Clone to timezone', 'View & Analyze',
  ]);
  await page.getByRole('button', { name: 'Data sources', exact: true }).click();

  await expect(page.locator('.source-tree')).toHaveCount(0);
  await expect(page.getByRole('table', { name: 'Historical data' }).getByRole('columnheader')).toHaveText([
    '', 'Symbol Name ▴', 'Instrument', 'Broker profile', 'Underlying Symbol', 'Timeframe',
    'Timezone', 'Date from', 'Date to', 'Total Days', 'Total Records', 'Source', 'Bar type', 'Data type', 'Hide', '',
  ]);
  await page.getByRole('textbox', { name: 'Filter items' }).fill('EURUSD');
  await expect(page.getByText('Records: 1', { exact: true })).toBeVisible();
  await page.getByRole('checkbox', { name: 'Select EURUSD', exact: true }).check();
  await page.getByRole('button', { name: 'Export', exact: true }).click();
  await expect(page.getByRole('table', { name: 'Historical data' })).toBeVisible();
  await expect(page.getByRole('textbox', { name: 'Filter items' })).toHaveValue('EURUSD');
  await expect(page.getByRole('checkbox', { name: 'Select EURUSD', exact: true })).toBeChecked();
  await expect(page.getByLabel('Data export operations').getByRole('button')).toHaveText([
    'Export to CSV', 'Export MT4 (FXT & HST)', 'Export to MT5 data (99% test)',
  ]);
  await page.getByRole('button', { name: 'Tools', exact: true }).click();
  await expect(page.getByRole('table', { name: 'Historical data' })).toBeVisible();
  await expect(page.getByRole('textbox', { name: 'Filter items' })).toHaveValue('EURUSD');
  await expect(page.getByRole('checkbox', { name: 'Select EURUSD', exact: true })).toBeChecked();
  await page.getByRole('button', { name: 'Data sources', exact: true }).click();
  await expect(page.getByRole('textbox', { name: 'Filter items' })).toHaveValue('EURUSD');
  await expect(page.getByRole('checkbox', { name: 'Select EURUSD', exact: true })).toBeChecked();
  await page.getByRole('checkbox', { name: 'Select EURUSD', exact: true }).uncheck();
  await page.getByRole('textbox', { name: 'Filter items' }).fill('no-matching-symbol');
  await expect(page.getByText('No matching data.', { exact: true })).toBeVisible();
  await page.getByRole('textbox', { name: 'Filter items' }).clear();

  const ribbon = page.getByLabel('Data source operations');
  await ribbon.getByRole('button', { name: 'File import', exact: true }).click();
  const fileIconClasses = await page.getByRole('menu', { name: 'File import actions' })
    .locator('svg.command-icon').evaluateAll(nodes => nodes.map(node => node.getAttribute('class')));
  expect(new Set(fileIconClasses).size).toBe(3);
  await expect(page.getByRole('menuitem', { name: 'Import application data' })).toHaveCount(0);
  await ribbon.getByRole('button', { name: 'File import', exact: true }).click();

  const cryptoButton = ribbon.getByRole('button', { name: 'Crypto', exact: true });
  await expect(cryptoButton.locator('svg.lucide-bitcoin')).toBeVisible();
  await cryptoButton.click();
  await page.getByRole('menu', { name: 'Crypto actions' }).getByRole('menuitem', { name: 'Add crypto symbol' }).click();
  const exchangeIconClasses = await page.getByRole('menu', { name: 'Add crypto symbol exchanges' })
    .locator('svg.command-icon').evaluateAll(nodes => nodes.map(node => node.getAttribute('class')));
  expect(new Set(exchangeIconClasses).size).toBe(6);
  await ribbon.getByRole('button', { name: 'Crypto', exact: true }).click();

  const dialogCommands = [
    ['Dukascopy data', 'Add new Dukascopy symbol', 'Add Dukascopy data'],
    ['Dukascopy data', 'Download data for existing symbol', 'Download Dukascopy data'],
    ['Dukascopy data', 'Dukascopy Data Disclaimer', 'Dukascopy data disclaimer'],
    ['TickDownloader import', 'Import TickDownloader data', 'Import data from TickDownloader'],
    ['File import', 'Add symbol', 'Add symbol'],
    ['File import', 'Import one data file', 'Import one data file'],
    ['File import', 'Import multiple files from a folder', 'Mass import'],
    ['Equity data', 'Find and add equity data', 'Add Equity Data'],
    ['Futures data', 'Find and add futures data', 'Add Futures Data'],
    ['Darwinex Tick Data', 'Add Darwinex data', 'Add Darwinex data'],
    ['Darwinex Tick Data', 'Import data from a Darwinex folder', 'Import data from Darwinex'],
    ['Darwinex Tick Data', 'Download data for existing symbols', 'Download Darwinex data'],
    ['Yahoo', 'Add Yahoo symbols', 'Add Yahoo data'],
    ['MT5 import', 'Import data', 'Import data from MT5'],
  ] as const;
  for (const [provider, command, title] of dialogCommands) {
    await test.step(`${provider}: ${command}`, async () => openProviderCommand(page, provider, command, title));
  }

  const yahooButton = ribbon.getByRole('button', { name: 'Yahoo', exact: true });
  await expect(yahooButton.locator('img.provider-image-icon')).toBeVisible();
  await expect(ribbon.getByRole('button', { name: 'MT5 import', exact: true }).locator('img.provider-image-icon')).toBeVisible();
  await yahooButton.click();
  await page.getByRole('menu', { name: 'Yahoo actions' }).getByRole('menuitem', { name: 'Download data for existing symbol', exact: true }).click();
  await expect(page.getByLabel('Data Manager progress')).toContainText('at least one Yahoo');

  const exchanges = [
    ['Binance spot', 'Add Binance symbol(s)'], ['Binance Coin-M', 'Add Binance Coin-M symbol(s)'],
    ['Binance USDT-M', 'Add Binance USDT-M symbol(s)'], ['Bitfinex', 'Add Bitfinex symbol(s)'],
    ['Poloniex', 'Add Poloniex symbol(s)'], ['Coinbase Pro', 'Add Coinbase Pro symbol(s)'],
  ] as const;
  for (const [exchange, title] of exchanges) {
    await page.getByLabel('Data source operations').getByRole('button', { name: 'Crypto', exact: true }).click();
    await page.getByRole('menu', { name: 'Crypto actions' }).getByRole('menuitem', { name: 'Add crypto symbol' }).click();
    await page.getByRole('menu', { name: 'Add crypto symbol exchanges' }).getByRole('menuitem', { name: exchange, exact: true }).click();
    await expect(page.getByRole('dialog', { name: title })).toBeVisible();
    await page.getByRole('dialog', { name: title }).getByRole('button', { name: 'Close' }).last().click();
  }

  await page.getByLabel('Data source operations').getByRole('button', { name: 'Equity data', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Update Equity datasets' }).click();
  await expect(page.getByText(/Equity dataset update/)).toBeVisible();
  await page.getByLabel('Data source operations').getByRole('button', { name: 'Futures data', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Update Futures datasets' }).click();
  await expect(page.getByText(/Futures dataset update/)).toBeVisible();

  for (const name of ['Update selected', 'Mass delete', 'Save']) {
    const action = page.getByLabel('Data source operations').getByRole('button', { name, exact: true });
    await expect(action).toBeEnabled();
    await action.click();
    await expect(page.getByText('Select at least one dataset first').first()).toBeVisible();
    await expect(page.getByRole('dialog')).toHaveCount(0);
  }
  await page.getByRole('checkbox', { name: /Select EURUSD/ }).check();
  await expect(page.getByRole('button', { name: 'Update selected', exact: true })).toBeEnabled();

  await page.getByRole('button', { name: 'Mass delete', exact: true }).click();
  await expect(page.getByRole('dialog', { name: 'Remove or clear selected datasets' })).toBeVisible();
  await page.getByRole('button', { name: 'Review dependency warning' }).click();
  await expect(page.getByRole('dialog', { name: 'Dependent dataset warning' })).toBeVisible();
  await page.getByRole('dialog', { name: 'Dependent dataset warning' }).getByRole('button', { name: 'Close' }).click();

  await page.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(page.getByRole('dialog', { name: 'Save selected dataset definitions' })).toContainText('1 selected dataset');
  await page.getByRole('dialog', { name: 'Save selected dataset definitions' }).getByRole('button', { name: 'Close' }).click();
  await page.getByRole('button', { name: 'Load', exact: true }).click();
  await expect(page.getByRole('dialog', { name: 'Load dataset definitions' })).toContainText('validated');
  await page.getByRole('dialog', { name: 'Load dataset definitions' }).getByRole('button', { name: 'Close' }).click();

  expect(providerRequests).toEqual([]);
  await page.getByRole('button', { name: 'Update all', exact: true }).click();
  await page.getByRole('button', { name: 'Stop all', exact: true }).click();
  await page.getByRole('button', { name: 'Log', exact: true }).click();
  await expect(page.locator('.ribbon')).toBeHidden();
  await expect(page.getByRole('log', { name: 'Data Manager log' })).toContainText('cancelled (simulation)');
  await page.getByRole('button', { name: 'Clear log', exact: true }).click();
  await expect(page.getByRole('log', { name: 'Data Manager log' })).toBeEmpty();
  await page.getByRole('button', { name: 'Data sources', exact: true }).click();
  await page.getByRole('button', { name: 'Log', exact: true }).click();
  await expect(page.getByRole('log', { name: 'Data Manager log' })).toBeEmpty();
});


test('Dukascopy disclaimer is informational and closes in both themes', async ({ page }) => {
  await openDataManager(page);
  const openDisclaimer = async () => {
    await page.getByRole('button', { name: 'Dukascopy data', exact: true }).click();
    await page.getByRole('menuitem', { name: 'Dukascopy Data Disclaimer', exact: true }).click();
    return page.getByRole('dialog', { name: 'Dukascopy data disclaimer', exact: true });
  };
  const before = await page.evaluate(() => JSON.stringify(localStorage));
  for (const theme of ['dark', 'light']) {
    if (theme === 'light') await selectLightSkin(page);
    const dialog = await openDisclaimer();
    await expect(dialog.getByRole('heading', { name: 'Disclaimer', exact: true })).toBeVisible();
    const paragraphs = dialog.locator('section p');
    await expect(paragraphs).toHaveCount(4);
    await expect(paragraphs.nth(0)).toContainText('NOT the actual values at a given point in time');
    await expect(paragraphs.nth(1)).toContainText('not an investment advice');
    await expect(paragraphs.nth(2)).toContainText('shall put a clear note to the public');
    await expect(paragraphs.nth(3)).toContainText('WITH ALL ITS FAULTS');
    await expect(dialog.getByRole('checkbox')).toHaveCount(0);
    await expect(dialog.getByRole('button')).toHaveCount(2);
    await expect(dialog.getByRole('button', { name: 'Close', exact: true }).last()).toBeInViewport();
    await page.screenshot({ path: `test-results/dukascopy-disclaimer-${theme}.png` });
    await dialog.getByRole('button', { name: 'Close', exact: true }).last().click();
    await expect(page.getByRole('button', { name: 'Dukascopy data', exact: true })).toBeFocused();
    if (theme === 'dark') expect(await page.evaluate(() => JSON.stringify(localStorage))).toBe(before);
  }
  const dialog = await openDisclaimer();
  await dialog.getByRole('button', { name: 'Close', exact: true }).first().click();
  await expect(dialog).toHaveCount(0);
  await openDisclaimer();
  await page.keyboard.press('Escape');
  await expect(dialog).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Dukascopy data', exact: true })).toBeFocused();
  await expect(page.getByLabel('Data Manager progress')).toContainText('No active operations');
});
