import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => { await page.goto('/'); });

test('footer exposes the requested HaruQuantAI actions and skips Code Editor', async ({ page }) => {
  const actions = page.locator('.status-actions');
  await expect(actions.getByRole('button', { name: 'Theme', exact: true })).toHaveCount(0);
  await expect(actions.getByRole('button', { name: 'Help', exact: true })).toHaveCount(0);
  await expect(page.getByRole('button', { name: /Feature Profile/ })).toHaveCount(0);
  await expect(actions.getByRole('button', { name: 'Notifications', exact: true })).toBeVisible();
  await expect(actions.getByRole('button', { name: 'Debug Console', exact: true })).toBeVisible();
  await expect(actions.getByRole('button', { name: 'Grid Control', exact: true })).toBeVisible();
  await expect(actions.getByRole('button', { name: 'Volume & Market Profile Addon', exact: true })).toBeVisible();
  await expect(actions.getByRole('button', { name: 'Code Editor', exact: true })).toHaveCount(0);
});

test('Debug Console filters and clears the bounded mock log', async ({ page }) => {
  await page.getByRole('button', { name: 'Debug Console', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Debug Console', exact: true })).toBeVisible();
  const log = page.getByRole('log');
  await expect(log).toContainText('Frontend research workspace initialized.');
  await page.getByLabel('Category').selectOption('Engine');
  await expect(log).toContainText('Deterministic mock engine');
  await page.getByPlaceholder('Filter messages').fill('does-not-exist');
  await expect(log).toContainText('No log entries match');
  await page.getByPlaceholder('Filter messages').fill('');
  await page.getByRole('button', { name: 'Clear log', exact: true }).click();
  await expect(log).toContainText('No log entries match');
});

test('Grid Control refreshes and exposes finished-job error detail', async ({ page }) => {
  await page.getByRole('button', { name: 'Grid Control', exact: true }).click();
  await expect(page.getByRole('heading', { name: 'Grid engine overview' })).toBeVisible();
  await expect(page.getByText('Auto-refresh every 3 seconds')).toBeVisible();
  await expect(page.getByRole('combobox')).toHaveValue('Local grid');
  await expect(page.getByText('Records: 0')).toHaveCount(2);
  await page.getByRole('button', { name: 'Refresh data' }).click();
  await page.getByRole('button', { name: 'Error', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Errors' });
  await expect(dialog).toContainText('simulated worker stopped');
  await dialog.getByRole('button', { name: 'Close', exact: true }).last().click();
});

test('Volume Profile addon dialog matches the inactive HaruQuantAI branch', async ({ page }) => {
  await page.getByRole('button', { name: 'Volume & Market Profile Addon', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Volume & Market Profile Addon' });
  await expect(dialog).toContainText("You don't have this addon active.");
  await dialog.getByRole('button', { name: 'Learn more about Volume & Market Profile in HaruQuantAI' }).click();
  await expect(dialog).toBeVisible();
  await dialog.getByRole('button', { name: 'Upgrade to Ultimate' }).click();
  await expect(dialog.getByRole('link')).toHaveCount(0);
  await dialog.getByRole('button', { name: 'Close', exact: true }).last().click();
  await expect(dialog).toHaveCount(0);
});
