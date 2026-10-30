import { expect, test, type Page } from './frontendStructureFixtures';
async function expand(page: Page) {
  await page.goto('/builder');
  await page.getByRole('button', { name: 'Expand databanks', exact: true }).click();
  return page.locator('.sqn-databanks');
}
test('single rename preserves selection guard, autofocus, trim and blank fallback', async ({ page }, info) => {
  const pane = await expand(page);
  await pane.getByRole('button', { name: 'Rename', exact: true }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await page.getByRole('button', { name: 'Notifications', exact: true }).click();
  await expect(page.locator('.notifications')).toContainText('You have to select at least one strategy');
  await page.getByRole('button', { name: 'Notifications', exact: true }).click();
  const selected = pane.getByRole('checkbox', { name: /^Select Strategy / }).first();
  const original = (await selected.getAttribute('aria-label'))!.slice('Select '.length);
  await selected.check();
  await pane.getByRole('button', { name: 'Rename', exact: true }).click();
  const dialog = page.getByRole('dialog');
  await expect(dialog).toContainText('Rename selected strategies (1)');
  await expect(dialog.getByRole('textbox')).toBeFocused();
  await dialog.getByRole('textbox').fill('   ');
  await dialog.getByRole('button', { name: 'Rename', exact: true }).click();
  await expect(pane.getByRole('checkbox', { name: `Select ${original}`, exact: true })).toBeChecked();
  await pane.getByRole('button', { name: 'Rename', exact: true }).click();
  await dialog.getByRole('textbox').fill('  Reviewed rename  ');
  await page.screenshot({ path: info.outputPath('rename-single.png') });
  await dialog.getByRole('button', { name: 'Rename', exact: true }).click();
  await expect(pane.getByRole('checkbox', { name: 'Select Reviewed rename', exact: true })).toBeChecked();
});
test('multiple rename preserves affixes and unselected fixture names', async ({ page }, info) => {
  const pane = await expand(page);
  const rows = pane.getByRole('checkbox', { name: /^Select Strategy / });
  const originals = await Promise.all([0, 1, 2].map(i => rows.nth(i).getAttribute('aria-label')));
  await rows.nth(0).check();
  await rows.nth(1).check();
  await pane.getByRole('button', { name: 'Rename', exact: true }).click();
  const dialog = page.getByRole('dialog');
  await expect(dialog).toContainText('Rename selected strategies (2)');
  await expect(dialog.getByRole('textbox').first()).toBeFocused();
  await dialog.getByRole('textbox').nth(0).fill('  pre-  ');
  await dialog.getByRole('textbox').nth(1).fill('  -post  ');
  await page.setViewportSize({ width: 1000, height: 760 });
  await page.screenshot({ path: info.outputPath('rename-multiple-narrow.png') });
  await dialog.getByRole('button', { name: 'Rename', exact: true }).click();
  for (const original of originals.slice(0, 2)) await expect(pane.getByRole('checkbox', { name: `Select pre-${original!.slice(7)}-post`, exact: true })).toBeChecked();
  await expect(pane.getByRole('checkbox', { name: originals[2]!, exact: true })).not.toBeChecked();
});
test('Close, Escape and backdrop cancel without mutating the fixture', async ({ page }) => {
  const pane = await expand(page);
  const row = pane.getByRole('checkbox', { name: /^Select Strategy / }).first();
  const original = (await row.getAttribute('aria-label'))!;
  await row.check();
  for (const method of ['Close', 'Escape', 'backdrop']) {
    await pane.getByRole('button', { name: 'Rename', exact: true }).click();
    const dialog = page.getByRole('dialog');
    await dialog.getByRole('textbox').fill('Cancelled change');
    if (method === 'Close') await dialog.getByRole('button', { name: 'Close', exact: true }).last().click();
    else if (method === 'Escape') await page.keyboard.press('Escape');
    else await page.locator('.modal-backdrop').click({ position: { x: 4, y: 4 } });
    await expect(dialog).toHaveCount(0);
    await expect(pane.getByRole('checkbox', { name: original, exact: true })).toBeChecked();
  }
});
