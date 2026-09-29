import { expect, test } from '@playwright/test';
import { installDataManagerBackend, savedConfiguration } from '../unit/workspace/DataManager/Common/browserHarness';

test('file dataset creation is unavailable until a backend operation is connected', async ({ page }) => {
  const backend = await installDataManagerBackend(page);
  await savedConfiguration(page);
  await page.goto('/datamanager');
  await expect(page.getByText('No data defined.', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'File import', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Add symbol', exact: true }).click();
  await expect(page.getByLabel('Data Manager progress')).toContainText('unavailable');
  await expect(page.getByRole('dialog')).toHaveCount(0);
  expect(backend.requests.filter(request => request.operation.startsWith('actions.') && request.operation !== 'actions.list_datasets')).toEqual([]);
  await page.getByRole('button', { name: 'Instruments', exact: true }).click();
  await expect(page.getByRole('table', { name: 'Instruments', exact: true })).toContainText('User configured instrument');
});

test('legacy file definitions stay preserved but are not a fallback inventory', async ({ page }) => {
  await installDataManagerBackend(page);
  await page.addInitScript(() => localStorage.setItem('sqx-file-symbols-v1', JSON.stringify({ version: 3, definitions: [{ id: 'file:OLD', symbol: 'OLD' }], instruments: [], overrides: {}, removed: [] })));
  await page.goto('/datamanager');
  await expect(page.getByText('No data defined.', { exact: true })).toBeVisible();
  expect(await page.evaluate(() => JSON.parse(localStorage.getItem('sqx-file-symbols-v1')!).definitions[0].symbol)).toBe('OLD');
  await expect(page.getByRole('checkbox', { name: 'Select OLD', exact: true })).toHaveCount(0);
});
