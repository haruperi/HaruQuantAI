import { expect, test, type Page } from './frontendStructureFixtures';
async function openViews(page: Page) {
  await page.goto('/builder');
  await page.getByRole('button', { name: 'Expand databanks', exact: true }).click();
  await page.getByRole('button', { name: 'Manage databank views' }).click();
  return page.getByRole('dialog', { name: 'Manage views', exact: true });
}
test('view editor preserves create, columns, save, apply and reload persistence', async ({ page }, info) => {
  const dialog = await openViews(page);
  await expect(dialog.getByRole('button', { name: 'Save changes', exact: true })).toBeDisabled();
  await expect(dialog.getByRole('button', { name: 'Delete this view', exact: true })).toBeDisabled();
  await expect(dialog.getByRole('button', { name: 'Create', exact: true })).toBeDisabled();
  await expect(dialog.getByRole('button', { name: 'Clone', exact: true })).toBeDisabled();
  await dialog.getByPlaceholder('View name', { exact: true }).fill('Reviewed view');
  await dialog.getByRole('button', { name: 'Create', exact: true }).click();
  await expect(dialog.locator('select').first().locator('option:checked')).toHaveText('Reviewed view');
  const width = dialog.locator('input[type=number]').first();
  await width.fill('210');
  await dialog.getByTitle('Move Down', { exact: true }).first().click();
  await dialog.getByTitle('Move Up', { exact: true }).nth(1).click();
  await dialog.getByRole('button', { name: 'Add columns', exact: true }).click();
  const chooser = page.getByRole('dialog', { name: 'Add columns to view', exact: true });
  await chooser.getByPlaceholder('Filter 100+ metrics...').fill('Drawdown');
  await expect(chooser.locator('tbody tr').first()).toContainText(/Drawdown/i);
  await chooser.getByRole('button', { name: '+ Add', exact: true }).first().click();
  await chooser.getByRole('button', { name: 'Done', exact: true }).click();
  await expect(dialog.locator('tbody tr')).toHaveCount(6);
  await dialog.getByTitle('Remove Column', { exact: true }).last().click();
  await expect(dialog.locator('tbody tr')).toHaveCount(5);
  await dialog.getByTitle('Column Properties', { exact: true }).first().click();
  const properties = page.getByRole('dialog', { name: 'Column properties', exact: true });
  await expect(properties).toContainText('Column ID');
  await properties.getByRole('button', { name: 'Close', exact: true }).last().click();
  await dialog.getByRole('button', { name: 'Save changes', exact: true }).click();
  await expect(dialog.getByRole('button', { name: 'Save changes', exact: true })).toBeDisabled();
  await page.screenshot({ path: info.outputPath('views-normal.png') });
  await dialog.getByRole('button', { name: 'Close & Apply', exact: true }).click();
  await expect(page.getByRole('combobox', { name: 'Databank view' })).toHaveValue('Reviewed view');
  await page.reload();
  await page.getByRole('button', { name: 'Expand databanks', exact: true }).click();
  await expect(page.getByRole('combobox', { name: 'Databank view' })).toHaveValue('Reviewed view');
  await page.getByRole('button', { name: 'Manage databank views' }).click();
  await expect(dialog.locator('input[type=number]').first()).toHaveValue('210');
});
test('clone, delete and reset retain existing protections', async ({ page }, info) => {
  const dialog = await openViews(page);
  await dialog.getByPlaceholder('Clone name', { exact: true }).fill('Reviewed clone');
  await dialog.getByRole('button', { name: 'Clone', exact: true }).click();
  await expect(dialog.locator('select').first().locator('option:checked')).toHaveText('Reviewed clone');
  await dialog.getByRole('button', { name: 'Delete this view', exact: true }).click();
  await expect(dialog.locator('select').first().locator('option')).toHaveCount(5);
  await dialog.getByRole('button', { name: 'Reset all', exact: true }).click();
  await expect(dialog.getByRole('button', { name: 'Delete this view', exact: true })).toBeDisabled();
  await page.setViewportSize({ width: 1000, height: 760 });
  await page.screenshot({ path: info.outputPath('views-narrow.png') });
  await page.keyboard.press('Escape');
  await expect(dialog).toHaveCount(0);
  await expect(page.getByRole('button', { name: 'Manage databank views' })).toBeFocused();
});
test('nested chooser Escape uses existing shared modal lifecycle', async ({ page }) => {
  const dialog = await openViews(page);
  await dialog.getByPlaceholder('Clone name', { exact: true }).fill('Nested view');
  await dialog.getByRole('button', { name: 'Clone', exact: true }).click();
  await dialog.getByRole('button', { name: 'Add columns', exact: true }).click();
  await expect(page.getByRole('dialog')).toHaveCount(2);
  await page.keyboard.press('Escape');
  // Shared Modal attaches an Escape listener per instance; both close today.
  await expect(page.getByRole('dialog')).toHaveCount(0);
});
