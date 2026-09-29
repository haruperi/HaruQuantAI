import { installDataManagerBackend, dataset, savedConfiguration } from '../unit/workspace/DataManager/Common/browserHarness';
import { expect, test, type Page } from '@playwright/test';
import { selectLightSkin } from './shellTestUtils';

test.beforeEach(async ({ page }) => { await installDataManagerBackend(page, [dataset('EURUSD')]); });
async function launch(page: Page) {
  await page.goto('/');
  await page.getByRole('button', { name: 'Data Manager', exact: true }).click();
  await page.getByRole('button', { name: 'Stock groups', exact: true }).click();
}
function groupRow(page: Page, name: string) {
  return page.getByRole('table', { name: 'Stock groups', exact: true }).getByRole('row').filter({ has: page.getByRole('checkbox', { name: `Select group ${name}`, exact: true }) });
}

test('adds, edits, imports, updates, persists, and removes a stock group', async ({ page }) => {
  await launch(page); const actions = page.getByLabel('Stock group operations');
  await actions.getByRole('button', { name: 'Edit stocks', exact: true }).click();
  await expect(page.getByLabel('Data Manager progress')).toContainText('You have to select some group.');

  await actions.getByRole('button', { name: 'Add new', exact: true }).click();
  let dialog = page.getByRole('dialog', { name: 'Add stocks group', exact: true });
  await dialog.getByLabel('Group name *').fill('Technology');
  await dialog.getByLabel('Description').fill('Technology constituents');
  await page.screenshot({ path: 'test-results/stock-groups-add-dark.png' });
  await dialog.getByRole('button', { name: 'Save', exact: true }).click();
  let row = groupRow(page, '[Technology]'); await expect(row).toBeVisible();
  await expect(row.getByRole('cell').nth(2)).toHaveText('0');

  await actions.getByRole('button', { name: 'Edit stocks', exact: true }).click();
  dialog = page.getByRole('dialog', { name: 'Edit stocks [Technology]', exact: true });
  await dialog.getByRole('textbox', { name: 'Stocks', exact: true }).fill('AAPL\nMSFT;01.12.2020\nOLD;15.04.2007;30.05.2015\nTSLA\nNVDA');
  await dialog.getByRole('button', { name: 'Save', exact: true }).click();
  row = groupRow(page, '[Technology]'); await expect(row.getByRole('cell').nth(2)).toHaveText('5');
  await expect(row.getByRole('cell').nth(6)).toHaveText('No');

  await actions.getByRole('button', { name: 'Edit stocks', exact: true }).click();
  dialog = page.getByRole('dialog', { name: 'Edit stocks [Technology]', exact: true });
  const memberDownload = page.waitForEvent('download'); await dialog.getByRole('button', { name: 'Export to file', exact: true }).click(); expect((await memberDownload).suggestedFilename()).toBe('GroupStocks.json');
  await actions.getByRole('button', { name: 'Edit stocks', exact: true }).click();
  dialog = page.getByRole('dialog', { name: 'Edit stocks [Technology]', exact: true });
  await dialog.getByLabel('Choose stocks CSV').setInputFiles({ name: 'stocks.csv', mimeType: 'text/csv', buffer: Buffer.from('AAPL\nNVDA;2020.01.02\nAMD\nTSLA\nMETA') });
  await expect(dialog).toHaveCount(0); row = groupRow(page, '[Technology]'); await expect(row.getByRole('cell').nth(2)).toHaveText('5');

  await actions.getByRole('button', { name: 'Update data in group (automatic)', exact: true }).click();
  await expect(page.getByLabel('Data Manager progress')).toContainText('Stock-group acquisition is unavailable');
  await expect(page.getByLabel('Data Manager progress').getByRole('button', { name: 'Pause all', exact: true })).toBeDisabled();
  await page.reload(); await page.getByRole('button', { name: 'Stock groups', exact: true }).click();
  row = groupRow(page, '[Technology]'); await expect(row.getByRole('cell').nth(6)).toHaveText('No');
  await page.getByRole('button', { name: 'Data sources', exact: true }).click();
  await expect(page.getByRole('checkbox', { name: 'Select AAPL', exact: true })).toHaveCount(0);
  await page.getByRole('button', { name: 'Stock groups', exact: true }).click();
  await row.getByRole('checkbox').check();
  await actions.getByRole('button', { name: 'Mass delete', exact: true }).click();
  dialog = page.getByRole('dialog', { name: 'Remove group', exact: true }); await expect(dialog).toContainText('selected groups (1)');
  await dialog.getByRole('button', { name: 'Yes', exact: true }).click(); await expect(row).toHaveCount(0);
});

test('saves and atomically loads Groups JSON with overwrite confirmation', async ({ page }) => {
  await launch(page); const actions = page.getByLabel('Stock group operations');
  await actions.getByRole('button', { name: 'Add new', exact: true }).click(); let dialog = page.getByRole('dialog', { name: 'Add stocks group' });
  await dialog.getByLabel('Group name *').fill('Index'); await dialog.getByRole('button', { name: 'Save' }).click();
  const row = groupRow(page, '[Index]'); await row.getByRole('checkbox').check();
  const downloadPromise = page.waitForEvent('download'); await actions.getByRole('button', { name: 'Save', exact: true }).click(); expect((await downloadPromise).suggestedFilename()).toBe('Groups.json');
  await selectLightSkin(page);
  await actions.getByRole('button', { name: 'Load', exact: true }).click(); dialog = page.getByRole('dialog', { name: 'Load groups', exact: true });
  const json = JSON.stringify({version:1,kind:'stock-groups',groups:[{name:'[Index]',description:'Imported description',members:[{ticker:'SPY'}]}]});
  await dialog.getByLabel('Groups JSON file').setInputFiles({ name: 'Groups.json', mimeType: 'application/json', buffer: Buffer.from(json) });
  const confirm = page.getByRole('dialog', { name: 'Overwrite confirm', exact: true }); await expect(confirm).toContainText("Group '[Index]' already exists");
  await page.screenshot({ path: 'test-results/stock-groups-overwrite-light.png' });
  await confirm.getByRole('button', { name: 'Overwrite', exact: true }).click(); await dialog.getByRole('button', { name: 'Load', exact: true }).click();
  await expect(groupRow(page, '[Index]')).toContainText('Imported description');
  await actions.getByRole('button', { name: 'Load', exact: true }).click(); dialog = page.getByRole('dialog', { name: 'Load groups', exact: true });
  await dialog.getByLabel('Groups JSON file').setInputFiles({ name: 'bad.json', mimeType: 'application/json', buffer: Buffer.from('{"version":1,"kind":"wrong"}') });
  await expect(dialog.getByRole('alert')).toContainText('Choose a valid Groups JSON file.');
});

test('ignores disconnected folder-import groups and fails closed on corrupt stock-group storage', async ({ page }) => {
  await page.goto('/');
  await page.evaluate(() => localStorage.setItem('sqx-file-import-v1', JSON.stringify({ version:1, formats:[], records:[], groups:[{name:'Folder group',symbols:['AAPL']}], timezone:'EETUS', job:null })));
  await page.reload(); await page.getByRole('button', { name:'Data Manager', exact:true }).click(); await page.getByRole('button', { name:'Stock groups', exact:true }).click();
  await expect(groupRow(page, '[Folder group]')).toHaveCount(0);
  await page.evaluate(() => localStorage.setItem('sqx-stock-groups-v1', '{bad'));
  await page.reload(); await page.getByRole('button', { name:'Data Manager', exact:true }).click(); await page.getByRole('button', { name:'Stock groups', exact:true }).click(); await page.getByLabel('Stock group operations').getByRole('button', { name:'Add new', exact:true }).click();
  const dialog = page.getByRole('dialog', { name:'Add stocks group', exact:true }); await dialog.getByLabel('Group name *').fill('Blocked'); await dialog.getByRole('button', { name:'Save', exact:true }).click();
  await expect(dialog.getByRole('alert')).toContainText('could not be read');
});
