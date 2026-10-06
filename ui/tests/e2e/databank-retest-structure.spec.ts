import { expect, test, type Page } from '@playwright/test';
async function expand(page: Page) {
  await page.goto('/builder');
  await page.getByRole('button', { name: 'Expand databanks', exact: true }).click();
  return page.locator('.sqn-databanks');
}
test('selection guard, unchecked config and cancellation preserve source fixtures', async ({ page }, info) => {
  const pane = await expand(page);
  await pane.getByRole('button', { name: 'Retest', exact: true }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await page.getByRole('button', { name: 'Notifications', exact: true }).click();
  await expect(page.locator('.notifications')).toContainText('You have to select at least one strategy');
  await page.getByRole('button', { name: 'Notifications', exact: true }).click();
  await pane.getByRole('checkbox', { name: /^Select Strategy / }).first().check();
  for (const cancel of ['Cancel', 'Escape', 'backdrop']) {
    await pane.getByRole('button', { name: 'Retest', exact: true }).click();
    const dialog = page.getByRole('dialog');
    await expect(dialog).toContainText('Do you want to copy seleted strategies to Retester?');
    await expect(dialog.getByRole('checkbox')).not.toBeChecked();
    await dialog.getByRole('checkbox').check();
    await expect(dialog.getByRole('checkbox')).toBeChecked();
    if (cancel === 'Cancel') {
      await page.screenshot({ path: info.outputPath('retest-normal.png') });
      await page.setViewportSize({ width: 1000, height: 760 });
      await page.screenshot({ path: info.outputPath('retest-narrow.png') });
      await dialog.getByRole('button', { name: 'Cancel', exact: true }).click();
    } else if (cancel === 'Escape') await page.keyboard.press('Escape');
    else await page.locator('.modal-backdrop').click({ position: { x: 4, y: 4 } });
    await expect(dialog).toHaveCount(0);
    await expect(pane.locator('.sqx-records-count')).toContainText('Records: 40');
  }
});
test('Copy emits demo notification and retains source selection without navigation', async ({ page }) => {
  const pane = await expand(page);
  const row = pane.getByRole('checkbox', { name: /^Select Strategy / }).first();
  await row.check();
  const sourceUrl = page.url();
  await pane.getByRole('button', { name: 'Retest', exact: true }).click();
  await page.getByRole('dialog').getByRole('button', { name: 'Copy (keep original)', exact: true }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(row).toBeChecked();
  await expect(pane.locator('.sqx-records-count')).toContainText('Records: 40');
  await expect(page).toHaveURL(sourceUrl);
  await page.getByRole('button', { name: 'Notifications', exact: true }).click();
  await expect(page.locator('.notifications')).toContainText('Copied 1 strategies to Retester (demo)');
});
test('Move removes source fixture through existing demo callback without navigation', async ({ page }) => {
  const pane = await expand(page);
  const row = pane.getByRole('checkbox', { name: /^Select Strategy / }).first();
  const name = (await row.getAttribute('aria-label'))!;
  await row.check();
  const sourceUrl = page.url();
  await pane.getByRole('button', { name: 'Retest', exact: true }).click();
  await page.getByRole('dialog').getByRole('checkbox').check();
  await page.getByRole('dialog').getByRole('button', { name: 'Move (remove from this databank)', exact: true }).click();
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(pane.getByRole('checkbox', { name, exact: true })).toHaveCount(0);
  await expect(pane.locator('.sqx-records-count')).toContainText('Records: 39');
  await expect(page).toHaveURL(sourceUrl);
  await page.getByRole('button', { name: 'Notifications', exact: true }).click();
  await expect(page.locator('.notifications')).toContainText('Moved 1 strategies to Retester (demo)');
});
