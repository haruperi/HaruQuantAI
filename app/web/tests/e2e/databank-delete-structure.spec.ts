import { expect, test, type Page } from './frontendStructureFixtures';
async function expand(page: Page) {
  await page.goto('/builder');
  await page.getByRole('button', { name: 'Expand databanks', exact: true }).click();
  return page.locator('.sqn-databanks');
}
test('empty selection retains existing error and no confirmation', async ({ page }) => {
  const pane = await expand(page);
  await pane.getByRole('button', { name: 'Delete', exact: true }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await page.getByRole('button', { name: 'Notifications', exact: true }).click();
  await expect(page.locator('.notifications')).toContainText('You have to select at least one strategy to delete');
  await expect(pane.locator('.sqx-records-count')).toContainText('Records: 40');
});
test('No, Close, Escape and backdrop preserve selected fixture', async ({ page }, info) => {
  const pane = await expand(page);
  const row = pane.getByRole('checkbox', { name: /^Select Strategy / }).first();
  const name = (await row.getAttribute('aria-label'))!;
  await row.check();
  for (const cancel of ['No', 'Close', 'Escape', 'backdrop']) {
    await pane.getByRole('button', { name: 'Delete', exact: true }).click();
    const dialog = page.getByRole('dialog');
    await expect(dialog).toContainText('Are you sure you want to remove selected reports (1)?');
    if (cancel === 'No') {
      await page.screenshot({ path: info.outputPath('delete-normal.png') });
      await page.setViewportSize({ width: 1000, height: 760 });
      await page.screenshot({ path: info.outputPath('delete-narrow.png') });
      await dialog.getByRole('button', { name: 'No', exact: true }).click();
    } else if (cancel === 'Close') await dialog.getByRole('button', { name: 'Close', exact: true }).click();
    else if (cancel === 'Escape') await page.keyboard.press('Escape');
    else await page.locator('.modal-backdrop').click({ position: { x: 4, y: 4 } });
    await expect(dialog).toHaveCount(0);
    await expect(pane.getByRole('checkbox', { name, exact: true })).toBeChecked();
    await expect(pane.locator('.sqx-records-count')).toContainText('Records: 40');
  }
});
test('confirmed multiple deletion removes selected IDs and clears selection', async ({ page }) => {
  const pane = await expand(page);
  const rows = pane.getByRole('checkbox', { name: /^Select Strategy / });
  const names = await Promise.all([0, 1, 2].map(i => rows.nth(i).getAttribute('aria-label')));
  await rows.nth(0).check();
  await rows.nth(1).check();
  await pane.getByRole('button', { name: 'Delete', exact: true }).click();
  const dialog = page.getByRole('dialog');
  await expect(dialog).toContainText('Are you sure you want to remove selected reports (2)?');
  await dialog.getByRole('button', { name: 'Yes', exact: true }).click();
  await expect(dialog).toHaveCount(0);
  for (const name of names.slice(0, 2)) await expect(pane.getByRole('checkbox', { name: name!, exact: true })).toHaveCount(0);
  await expect(pane.getByRole('checkbox', { name: names[2]!, exact: true })).not.toBeChecked();
  await expect(pane.locator('.sqx-records-count')).toContainText('Records: 38');
  await expect(pane.getByRole('checkbox', { name: /^Select Strategy / }).locator(':checked')).toHaveCount(0);
});
