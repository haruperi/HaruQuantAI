import { expect, test } from '@playwright/test';

test.beforeEach(async ({ page }) => {
  let revision = 0;
  const values: Record<string, Record<string, unknown>> = {};
  await page.addInitScript(() => {
    const original = window.fetch.bind(window);
    window.fetch = ((input: RequestInfo | URL, init?: RequestInit) => {
      if (String(input).includes('/api/v1/events?')) {
        return Promise.resolve(new Response(new ReadableStream<Uint8Array>({ start() { /* Remain connected. */ } }), {
          status: 200, headers: { 'Content-Type': 'text/event-stream' },
        }));
      }
      return original(input, init);
    }) as typeof fetch;
  });
  await page.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname;
    let data: unknown = {};
    let status = 200;
    if (path.endsWith('/auth/login')) data = { token: 'e2e-session' };
    if (path.endsWith('/status')) data = { cpu_count: 8 };
    if (path.endsWith('/settings')) {
      if (route.request().method() === 'PUT') {
        const body = route.request().postDataJSON() as { expected_revision: number; changes: Record<string, unknown> };
        if (body.expected_revision !== revision) status = 409;
        else {
          for (const [key, fields] of Object.entries(body.changes)) {
            values[key] = { ...values[key], ...(fields as Record<string, unknown>) };
          }
          revision += 1;
        }
      }
      data = { revision, values };
    }
    await route.fulfill({ status, contentType: 'application/json', body: JSON.stringify(status === 200 ? { status: 'success', data } : { status: 'error', error: { code: 'SETTINGS_CONFLICT', message: 'Stale settings' } }) });
  });
  await page.goto('/');
  await expect(page.getByText('Host online')).toBeVisible();
});

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
  await expect(page.getByText('Configured workers 4', { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByText('Configured workers 4', { exact: true })).toBeVisible();
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

test('all configuration tabs and non-secret SMTP fields survive a fresh reload', async ({ page }) => {
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Configuration...', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Configuration', exact: true });
  await dialog.getByRole('checkbox', { name: 'Turn off application sounds' }).check();
  await dialog.getByRole('tab', { name: 'CPU' }).click();
  await dialog.getByRole('radio', { name: 'Use custom number of cores' }).check();
  await dialog.getByLabel('Custom cores').fill('3');
  await dialog.getByRole('tab', { name: 'Performance' }).click();
  await dialog.getByRole('checkbox', { name: 'Compute metrics in pips' }).check();
  await dialog.getByRole('tab', { name: 'Memory' }).click();
  await dialog.getByLabel('Maximum memory (GB)').fill('12');
  await dialog.getByRole('tab', { name: 'Databanks' }).click();
  await dialog.getByLabel('Synchronize changes').selectOption('Immediately');
  await expect(dialog.getByRole('button', { name: 'Apply to all existing databanks' })).toBeDisabled();
  await dialog.getByRole('tab', { name: 'Optimizations' }).click();
  await dialog.getByRole('checkbox', { name: "Don't store 3D chart data" }).uncheck();
  await dialog.getByRole('tab', { name: 'Troubleshooting' }).click();
  await dialog.getByRole('checkbox', { name: 'Enable debug logging' }).check();
  await dialog.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(page.getByText('Configured workers 3', { exact: true })).toBeVisible();
  await expect(page.getByText('Configured memory 12 GB', { exact: true })).toBeVisible();

  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await page.getByRole('menuitem', { name: 'SMTP server...', exact: true }).click();
  const smtp = page.getByRole('dialog', { name: 'SMTP server' });
  await smtp.getByLabel('SMTP server').fill('mail.example.test');
  await smtp.getByLabel('Sender email').fill('sender@example.test');
  await smtp.getByLabel('Password').fill('ephemeral-only');
  await smtp.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(smtp).toHaveCount(0);
  await page.reload();
  await expect(page.getByText('Configured workers 3', { exact: true })).toBeVisible();
  await expect(page.getByText('Configured memory 12 GB', { exact: true })).toBeVisible();
  const persisted = await page.evaluate(() => JSON.parse(localStorage.getItem('sqx-recreation-v1') || '{}'));
  expect(persisted.state?.settings).toBeUndefined();
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await page.getByRole('menuitem', { name: 'SMTP server...', exact: true }).click();
  await expect(page.getByRole('dialog', { name: 'SMTP server' }).getByLabel('SMTP server')).toHaveValue('mail.example.test');
  await expect(page.getByRole('dialog', { name: 'SMTP server' }).getByLabel('Password')).toHaveValue('');
});

test('a rejected database write leaves the settings dialog open and reports failure', async ({ page }) => {
  await page.route('**/api/v1/settings', async route => {
    if (route.request().method() !== 'PUT') { await route.fallback(); return; }
    await route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ status: 'error', error: { code: 'UNAVAILABLE', message: 'Database unavailable' } }) });
  });
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Configuration...', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Configuration', exact: true });
  await dialog.getByRole('checkbox', { name: 'Turn off application sounds' }).check();
  await dialog.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(dialog.getByRole('alert')).toContainText('not saved');
  await expect(dialog).toBeVisible();
});

test('a lower host core count does not silently rewrite the saved CPU key', async ({ page }) => {
  await page.route('**/api/v1/status', route => route.fulfill({ contentType: 'application/json', body: JSON.stringify({ status: 'success', data: { cpu_count: 4 } }) }));
  await page.route('**/api/v1/settings', async route => {
    if (route.request().method() !== 'GET') { await route.fallback(); return; }
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ status: 'success', data: { revision: 0, values: { 'config.cpu': { core_usage: 'all', custom_cores: 8 } } } }) });
  });
  await page.reload();
  await expect(page.getByText('Host online')).toBeVisible();
  let changes: Record<string, unknown> | null = null;
  page.on('request', request => {
    if (request.url().endsWith('/api/v1/settings') && request.method() === 'PUT') {
      changes = (request.postDataJSON() as { changes: Record<string, unknown> }).changes;
    }
  });
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Configuration...', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Configuration', exact: true });
  await dialog.getByRole('checkbox', { name: 'Turn off application sounds' }).check();
  await dialog.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(dialog).toHaveCount(0);
  expect(changes).toEqual({ 'config.global': { sounds_off: true } });
});

test('a save renews an expired host session and commits the change', async ({ page }) => {
  let expired = false;
  await page.route('**/api/v1/settings', async route => {
    if (route.request().method() === 'PUT' && !expired) {
      expired = true;
      await route.fulfill({ status: 401, contentType: 'application/json', body: JSON.stringify({ status: 'error', error: { code: 'UNAUTHORIZED', message: 'Session expired' } }) });
      return;
    }
    await route.fallback();
  });
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Configuration...', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Configuration', exact: true });
  await dialog.getByRole('tab', { name: 'CPU' }).click();
  await dialog.getByRole('radio', { name: 'Use custom number of cores' }).check();
  await dialog.getByLabel('Custom cores').fill('4');
  await dialog.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(dialog).toHaveCount(0);
  await expect(page.getByText('Configured workers 4', { exact: true })).toBeVisible();
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
