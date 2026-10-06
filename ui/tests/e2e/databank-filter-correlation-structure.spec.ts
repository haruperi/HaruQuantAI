import { expect, test, type Page } from '@playwright/test';
async function openFilter(page: Page) {
  await page.goto('/builder');
  await page.getByRole('button', { name: 'Expand databanks', exact: true }).click();
  await page.getByRole('button', { name: 'Filter by correlation', exact: true }).click();
  return page.getByRole('dialog', { name: 'Filter by correlation', exact: true });
}
test('filter controls preserve defaults, clamp, slider and period preview', async ({ page }, info) => {
  const dialog = await openFilter(page);
  await expect(dialog.getByRole('combobox')).toHaveValue('Day');
  const number = dialog.getByRole('spinbutton');
  await expect(number).toHaveValue('0.5');
  await number.fill('2');
  await expect(number).toHaveValue('1');
  await expect(dialog.getByRole('slider')).toHaveValue('1');
  await number.fill('-1');
  await expect(number).toHaveValue('0');
  await expect(dialog.getByRole('slider')).toHaveValue('0');
  await dialog.getByRole('slider').fill('0.25');
  await expect(number).toHaveValue('0.25');
  for (const period of ['Hour', 'Week', 'Month', 'Year', 'Day']) {
    await dialog.getByRole('combobox').selectOption(period);
    await expect(dialog.getByRole('combobox')).toHaveValue(period);
  }
  await page.screenshot({ path: info.outputPath('correlation-normal.png') });
  await page.setViewportSize({ width: 1000, height: 760 });
  await page.screenshot({ path: info.outputPath('correlation-narrow.png') });
});
test('Close and Escape preserve fixture counts and restore focus', async ({ page }) => {
  const dialog = await openFilter(page);
  const pane = page.locator('.sqn-databanks');
  await dialog.getByRole('button', { name: 'Close', exact: true }).last().click();
  await expect(dialog).toHaveCount(0);
  await expect(pane.locator('.sqx-records-count')).toContainText('40');
  const trigger = page.getByRole('button', { name: 'Filter by correlation', exact: true });
  await expect(trigger).toBeFocused();
  await trigger.click();
  await page.keyboard.press('Escape');
  await expect(dialog).toHaveCount(0);
  await expect(pane.locator('.sqx-records-count')).toContainText('40');
  await expect(trigger).toBeFocused();
});
test('apply matches preview removals and host notification', async ({ page }) => {
  const dialog = await openFilter(page);
  await dialog.getByRole('spinbutton').fill('0');
  const count = async (label: string) => Number(await dialog.getByText(label, { exact: true }).locator('..').locator('strong').textContent());
  const total = await count('Total strategies in databank:');
  const kept = await count('Strategies to keep:');
  const removed = await count('Correlated strategies to remove:');
  expect(total).toBe(40);
  expect(kept + removed).toBe(total);
  expect(removed).toBeGreaterThan(0);
  await dialog.getByRole('button', { name: `Filter (${removed} will be removed)`, exact: true }).click();
  await expect(dialog).toHaveCount(0);
  await expect(page.locator('.sqx-records-count')).toContainText(`Records: ${kept}`);
  await page.getByRole('button', { name: 'Notifications', exact: true }).click();
  await expect(page.locator('.notifications')).toContainText(`Correlation filter applied: removed ${removed} correlated strategies (kept ${kept})`);
});
