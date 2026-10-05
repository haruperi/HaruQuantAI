import { installDataManagerBackend, dataset, savedConfiguration } from '../unit/workspace/DataManager/Common/browserHarness';
import { expect, test, type Page } from '@playwright/test';
import { selectLightSkin } from './shellTestUtils';

test.beforeEach(async ({ page }) => { await installDataManagerBackend(page, [dataset('EURUSD')]); });
async function launch(page: Page) {
  await page.goto('/');
  await page.getByRole('button', { name: 'Data Manager', exact: true }).click();
  await page.getByRole('button', { name: 'Instruments', exact: true }).click();
}
function instrumentRow(page: Page, symbol: string) {
  return page.getByRole('table', { name: 'Instruments', exact: true }).getByRole('row')
    .filter({ has: page.getByRole('checkbox', { name: `Select instrument ${symbol}`, exact: true }) });
}

test('add, edit, clone, mass edit, delete, help, and reload instruments', async ({ page }) => {
  await launch(page);
  const actions = page.getByLabel('Instrument operations');
  await actions.getByRole('button', { name: 'Add Instrument', exact: true }).click();
  let dialog = page.getByRole('dialog', { name: 'Add instrument', exact: true });
  await dialog.getByLabel('Instrument', { exact: true }).fill('TEST_INST');
  await dialog.getByLabel('Description', { exact: true }).fill('Original description');
  await dialog.getByRole('combobox', { name: 'Commission model', exact: true }).selectOption('Stockpicker');
  await dialog.getByRole('button', { name: 'Help', exact: true }).click();
  await expect(page.getByRole('dialog', { name: 'Commission & Swap Explanation' })).toContainText('overnight');
  await page.keyboard.press('Escape');
  await page.screenshot({ path: 'test-results/instruments-add-dark.png' });
  await dialog.getByRole('button', { name: 'Save', exact: true }).click();

  const table = page.getByRole('table', { name: 'Instruments', exact: true });
  let sourceRow = instrumentRow(page, 'TEST_INST');
  await expect(sourceRow).toContainText('Original description');
  await sourceRow.dblclick();
  dialog = page.getByRole('dialog', { name: 'Edit instrument', exact: true });
  await expect(dialog.getByLabel('Instrument', { exact: true })).toBeDisabled();
  await dialog.getByLabel('Description', { exact: true }).fill('Edited description');
  await dialog.getByRole('button', { name: 'Save', exact: true }).click();
  sourceRow = instrumentRow(page, 'TEST_INST');
  await expect(sourceRow).toContainText('Edited description');

  await sourceRow.getByRole('checkbox', { name: 'Select instrument TEST_INST' }).check();
  await actions.getByRole('button', { name: 'Clone Instrument', exact: true }).click();
  dialog = page.getByRole('dialog', { name: "Clone instrument 'TEST_INST'", exact: true });
  await expect(dialog.getByLabel('New instrument name')).toHaveValue('TEST_INSTClone');
  await dialog.getByRole('button', { name: 'Save', exact: true }).click();
  const cloneRow = instrumentRow(page, 'TEST_INSTClone');
  await expect(cloneRow).toContainText('Edited description');

  await cloneRow.getByRole('checkbox', { name: 'Select instrument TEST_INSTClone' }).check();
  await actions.getByRole('button', { name: 'Mass Edit Instrument', exact: true }).click();
  dialog = page.getByRole('dialog', { name: 'Mass-Edit instrument', exact: true });
  await dialog.getByRole('checkbox', { name: 'Change Default spread * pips', exact: true }).check();
  await dialog.getByLabel('Default spread * pips', { exact: true }).fill('7');
  await page.screenshot({ path: 'test-results/instruments-mass-edit-dark.png' });
  await dialog.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(instrumentRow(page, 'TEST_INST').getByRole('cell').filter({ hasText: /^7$/ })).toHaveCount(1);
  await expect(instrumentRow(page, 'TEST_INSTClone').getByRole('cell').filter({ hasText: /^7$/ })).toHaveCount(1);

  await cloneRow.getByRole('button', { name: 'Delete instrument TEST_INSTClone' }).click();
  dialog = page.getByRole('dialog', { name: 'Remove instrument', exact: true });
  await expect(dialog).toContainText("delete instrument 'TEST_INSTClone'");
  await dialog.getByRole('button', { name: 'Yes', exact: true }).click();
  await expect(table.getByText('TEST_INSTClone', { exact: true })).toHaveCount(0);
  await page.reload();
  await page.getByRole('button', { name: 'Instruments', exact: true }).click();
  await expect(instrumentRow(page, 'TEST_INST')).toContainText('Edited description');
});

test('selection rules, JSON save/load conflicts, and referenced deletion are explicit', async ({ page }) => {
  await savedConfiguration(page);
  await launch(page);
  const actions = page.getByLabel('Instrument operations');
  await actions.getByRole('button', { name: 'Clone Instrument', exact: true }).click();
  await expect(page.getByLabel('Data Manager progress')).toContainText('select some record');

  const table = page.getByRole('table', { name: 'Instruments', exact: true });
  const firstRow = table.getByRole('row').nth(1);
  const firstName = (await firstRow.getByRole('cell').nth(1).innerText()).trim();
  await firstRow.getByRole('checkbox').check();
  await selectLightSkin(page);
  const downloadPromise = page.waitForEvent('download');
  await actions.getByRole('button', { name: 'Save', exact: true }).click();
  let dialog = page.getByRole('dialog', { name: 'Save instruments', exact: true });
  await page.screenshot({ path: 'test-results/instruments-save-light.png' });
  await dialog.getByRole('button', { name: 'Download JSON', exact: true }).click();
  const download = await downloadPromise;
  expect(download.suggestedFilename()).toBe('Instruments.json');

  await actions.getByRole('button', { name: 'Load', exact: true }).click();
  dialog = page.getByRole('dialog', { name: 'Load instruments', exact: true });
  const json = JSON.stringify({version:1,kind:'instruments',brokers:[],instruments:[{symbol:firstName,name:'Imported description',broker:'-1',brokerName:'Default',type:'Forex',pointValue:100000,tickSize:.0001,tickStep:.00001,spread:3,slippage:0,minDistance:0,multiplier:1,sizeStep:1,timezone:'UTC',commission:{model:'None',value:0,unit:'share',min:.35,minUnit:'money',max:1,maxUnit:'equity'},swap:{use:false,type:'money',long:0,short:0,tripleSwapOn:'WEDNESDAY',rolloutHour:'23:00'}}]});
  await dialog.getByLabel('Instrument JSON file').setInputFiles({ name: 'Instruments.json', mimeType: 'application/json', buffer: Buffer.from(json) });
  await dialog.getByRole('button', { name: 'Validate and load', exact: true }).click();
  dialog = page.getByRole('dialog', { name: 'Overwrite confirm', exact: true });
  await expect(dialog).toContainText(`Instrument '${firstName}' already exists`);
  await dialog.getByRole('button', { name: 'Overwrite all', exact: true }).click();
  await expect(table.getByRole('row').filter({ hasText: firstName })).toContainText('Imported description');

  const importedRow = table.getByRole('row').filter({ hasText: firstName });
  await importedRow.getByRole('button', { name: `Delete instrument ${firstName}` }).click();
  await page.getByRole('dialog', { name: 'Remove instrument', exact: true }).getByRole('button', { name: 'Yes', exact: true }).click();
  await expect(page.getByRole('dialog', { name: 'Remove instrument', exact: true }).getByRole('alert')).toContainText('used by existing data');
});

test('version 1 custom instruments migrate without data loss', async ({ page }) => {
  await page.goto('/');
  await page.evaluate(() => localStorage.setItem('sqx-file-symbols-v1', JSON.stringify({
    version: 1,
    definitions: [],
    instruments: [{
      symbol: 'V1_CUSTOM', name: 'Version one instrument', type: 'Forex', broker: '-1', brokerName: 'Default',
      pointValue: 100000, tickSize: 0.0001, tickStep: 0.00001, spread: 2, slippage: 0,
      minDistance: 0, multiplier: 1, sizeStep: 1, timezone: 'UTC',
      commission: { model: 'None', value: 0, unit: 'share', min: 0.35, minUnit: 'money', max: 1, maxUnit: 'equity' },
      swap: { use: false, type: 'money', long: 0, short: 0, tripleSwapOn: 'WEDNESDAY', rolloutHour: '23:00' },
    }],
  })));
  await page.reload();
  await page.getByRole('button', { name: 'Data Manager', exact: true }).click();
  await page.getByRole('button', { name: 'Instruments', exact: true }).click();
  await expect(instrumentRow(page, 'V1_CUSTOM')).toContainText('Version one instrument');
  await instrumentRow(page, 'V1_CUSTOM').dblclick();
  await page.getByRole('dialog', { name: 'Edit instrument', exact: true }).getByLabel('Description').fill('Migrated instrument');
  await page.getByRole('dialog', { name: 'Edit instrument', exact: true }).getByRole('button', { name: 'Save', exact: true }).click();
  const migrated=await page.evaluate(() => JSON.parse(localStorage.getItem('sqx-file-symbols-v1')!));expect(migrated.version).toBe(3);expect(Object.keys(migrated.instruments[0]).sort()).toEqual(['broker','brokerName','commission','minDistance','multiplier','name','pointValue','sizeStep','slippage','spread','swap','symbol','tickSize','tickStep','timezone','type'].sort());
});

test('corrupt saved instrument data fails closed', async ({ page }) => {
  await page.goto('/');
  await page.evaluate(() => localStorage.setItem('sqx-file-symbols-v1', '{not-json'));
  await page.reload();
  await page.getByRole('button', { name: 'Data Manager', exact: true }).click();
  await page.getByRole('button', { name: 'Instruments', exact: true }).click();
  await page.getByLabel('Instrument operations').getByRole('button', { name: 'Add Instrument', exact: true }).click();
  await expect(page.getByRole('dialog', { name: 'Add instrument', exact: true }).getByRole('alert')).toContainText('could not be read');
});
