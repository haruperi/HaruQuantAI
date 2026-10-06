import { expect, test, type Page } from '@playwright/test';
async function expand(page: Page) {
  await page.goto('/builder');
  await page.getByRole('button', { name: 'Expand databanks', exact: true }).click();
  return page.locator('.sqn-databanks');
}
test('simulated load progresses and completes without changing fixtures', async ({ page }, info) => {
  const pane = await expand(page);
  await pane.getByRole('button', { name: 'Load', exact: true }).click();
  const dialog = page.getByRole('dialog');
  const progress = dialog.getByRole('progressbar');
  await expect(dialog).toContainText('Loading records');
  await expect.poll(async () => Number(await progress.getAttribute('aria-valuenow'))).toBeGreaterThan(0);
  const value = Number(await progress.getAttribute('aria-valuenow'));
  expect(value).toBeLessThanOrEqual(100);
  await page.screenshot({ path: info.outputPath('load-normal.png') });
  await expect(dialog).toHaveCount(0);
  await expect(pane.locator('.sqx-records-count')).toContainText('Records: 40');
  await page.getByRole('button', { name: 'Notifications', exact: true }).click();
  await expect(page.locator('.notifications')).toContainText('Databank reloaded');
});
test('early dismissal completes once, cleans timers and reopening starts fresh', async ({ page }, info) => {
  const pane = await expand(page);
  await page.clock.install();
  await page.clock.pauseAt(new Date());
  await pane.getByRole('button', { name: 'Load', exact: true }).click();
  const dialog = page.getByRole('dialog');
  await expect(dialog.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '0');
  await page.clock.runFor(240);
  await expect(dialog.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '20');
  await page.keyboard.press('Escape');
  await expect(dialog).toHaveCount(0);
  await page.clock.runFor(2500);
  await page.getByRole('button', { name: 'Notifications', exact: true }).click();
  await expect(page.locator('.notifications p')).toHaveCount(1);
  await expect(page.locator('.notifications')).toContainText('Databank reloaded');
  await page.getByRole('button', { name: 'Notifications', exact: true }).click();
  await pane.getByRole('button', { name: 'Load', exact: true }).click();
  await expect(dialog.getByRole('progressbar')).toHaveAttribute('aria-valuenow', '0');
  await page.setViewportSize({ width: 1000, height: 760 });
  await page.screenshot({ path: info.outputPath('load-narrow.png') });
  await dialog.getByRole('button', { name: 'Close', exact: true }).click();
  await page.clock.runFor(2500);
  await expect(pane.locator('.sqx-records-count')).toContainText('Records: 40');
});
test('backdrop dismissal retains existing completion notification', async ({ page }) => {
  const pane = await expand(page);
  await pane.getByRole('button', { name: 'Load', exact: true }).click();
  await page.locator('.modal-backdrop').click({ position: { x: 4, y: 4 } });
  await expect(page.getByRole('dialog')).toHaveCount(0);
  await expect(pane.locator('.sqx-records-count')).toContainText('Records: 40');
  await page.getByRole('button', { name: 'Notifications', exact: true }).click();
  await expect(page.locator('.notifications')).toContainText('Databank reloaded');
});
