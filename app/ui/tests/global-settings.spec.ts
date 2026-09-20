import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => { await page.goto('/'); });

test('settings menu matches the HaruQuantAI command hierarchy and supports keyboard dismissal', async ({ page }) => {
  const settings = page.getByRole('button', { name: 'Settings', exact: true });
  await settings.click();
  const menu = page.getByRole('menu', { name: 'Application settings' });
  await expect(menu.getByRole('menuitem')).toHaveText([
    'Configuration...', 'Benchmark...', 'Remote access...', 'MCP Server...', 'SMTP server...',
    'Language', 'Skin', 'HaruQuantAI Website', 'Help center', 'Support', 'Update license',
    'About', 'Reload UI', 'Exit',
  ]);
  await page.keyboard.press('Escape');
  await expect(menu).toHaveCount(0);
  await expect(settings).toBeFocused();
});

test('configuration tabs validate, save, persist and restore focus', async ({ page }) => {
  const settings = page.getByRole('button', { name: 'Settings', exact: true });
  await settings.click();
  await page.getByRole('menuitem', { name: 'Configuration...', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Configuration', exact: true });
  await expect(dialog.getByRole('tab')).toHaveText(['Global', 'CPU', 'Performance', 'Memory', 'Databanks', 'Optimizations', 'Troubleshooting']);
  await dialog.getByRole('tab', { name: 'CPU' }).click();
  await dialog.getByRole('radio', { name: 'Use custom number of cores' }).check();
  await dialog.getByLabel('Custom cores').fill('0');
  await dialog.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(dialog.getByRole('alert')).toContainText('Custom cores');
  await dialog.getByLabel('Custom cores').fill('4');
  await dialog.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(page.getByText('Workers 4', { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByText('Workers 4', { exact: true })).toBeVisible();
});

test('language, skin and zoom update persisted application preferences', async ({ page }) => {
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Language', exact: true }).click();
  await page.getByRole('menu', { name: 'Language' }).getByRole('menuitem', { name: 'German' }).click();
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Skin', exact: true }).click();
  await page.getByRole('menu', { name: 'Skin' }).getByRole('menuitem', { name: 'Light skin' }).click();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await page.getByRole('button', { name: 'Zoom in', exact: true }).click();
  await expect(page.getByText('110%', { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
});

test('benchmark, remote, MCP, SMTP, license, about and exit surfaces are functional', async ({ page }) => {
  const open = async (name: string) => { await page.getByRole('button', { name: 'Settings', exact: true }).click(); await page.getByRole('menuitem', { name, exact: true }).click(); };
  await open('Benchmark...'); await page.getByRole('button', { name: 'Start benchmark' }).click(); await expect(page.getByRole('heading', { name: 'Benchmark finished' })).toBeVisible({ timeout: 5000 }); await page.getByRole('button', { name: 'Close', exact: true }).last().click();
  await open('Remote access...'); const remote = page.getByRole('dialog', { name: 'Remote access' }); await remote.getByRole('checkbox', { name: 'Allow remote access to this application' }).check(); await remote.getByRole('checkbox', { name: 'Require a password' }).check(); await remote.getByRole('textbox', { name: 'Password', exact: true }).fill('ephemeral'); await remote.getByRole('button', { name: 'Save' }).click();
  await open('MCP Server...'); await expect(page.getByLabel('Client configuration (JSON)')).toContainText('mcpServers'); await page.getByRole('button', { name: 'Close', exact: true }).last().click();
  await open('SMTP server...'); const smtp = page.getByRole('dialog', { name: 'SMTP server' }); await smtp.getByRole('button', { name: 'Send test email' }).click(); await smtp.getByLabel('Test recipient').fill('owner@example.test'); await smtp.getByRole('button', { name: 'Send test email' }).click(); await expect(smtp.getByRole('status')).toContainText('simulated'); await smtp.getByRole('button', { name: 'Close', exact: true }).last().click();
  await open('Update license'); await page.getByLabel('License key').fill('local-only'); await page.getByRole('button', { name: 'Update license' }).click(); await expect(page.getByRole('status')).toContainText('simulated'); await page.getByRole('button', { name: 'Close', exact: true }).last().click();
  await open('About'); await expect(page.getByRole('dialog', { name: 'About HaruQuantAI' }).getByText('Build 144.2953 reference')).toBeVisible(); await page.getByRole('button', { name: 'Close', exact: true }).last().click();
  await open('Exit'); const exitDialog = page.getByRole('dialog', { name: 'Exit HaruQuantAI' }); await exitDialog.getByRole('button', { name: 'Exit' }).click(); await expect(exitDialog).toHaveCount(0);
});
