import { test, expect } from './frontendStructureFixtures';

test('data draft and primary Results view state survive panel switches', async ({ page }, info) => {
  await page.goto('/optimizer?tab=settings');
  await page.getByRole('tab', { name: 'Data', exact: true }).click();
  await page.getByLabel('Timeframe', { exact: true }).selectOption('H4');
  await page.getByRole('tab', { name: 'Results', exact: true }).click();
  await expect(page.locator('.sqr-info-line')).toContainText('— Main backtest');
  await page.getByRole('tab', { name: 'List of trades', exact: true }).click();
  const slot = page.locator('.sqr-panel-slot:not([hidden])');
  await slot.getByRole('button', { name: 'Lng', exact: true }).click();
  await slot.getByRole('button', { name: 'Profit', exact: true }).click();
  await expect(slot.getByRole('button', { name: 'Profit ↓', exact: true })).toBeVisible();
  const rows = await slot.locator('tbody tr').count();
  await page.getByRole('tab', { name: 'Overview', exact: true }).click();
  await page.getByRole('tab', { name: 'List of trades', exact: true }).click();
  await expect(slot.locator('tbody tr')).toHaveCount(rows);
  await page.screenshot({ path: info.outputPath('primary-results.png') });
  await page.getByRole('tab', { name: 'Full settings', exact: true }).click();
  await expect(page.getByLabel('Timeframe', { exact: true })).toHaveValue('H4');
  await page.screenshot({ path: info.outputPath('project-data.png') });
});
