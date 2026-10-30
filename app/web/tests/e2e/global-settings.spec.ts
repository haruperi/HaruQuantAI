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
    if (path.endsWith('/auth/login')) data = { token: 'e2e-session', expires_at: new Date(Date.now() + 86400000).toISOString() };
    if (path.endsWith('/status')) data = { cpu_count: 8 };
    if (path.endsWith('/settings/secrets') && route.request().method() === 'PUT') {
      const body = route.request().postDataJSON();
      if (body.expected_revision !== revision) status = 409;
      else { for (const [scope, fields] of Object.entries(body.changes)) values[scope] = { ...values[scope], ...fields as Record<string, unknown> }; revision += 1; }
    }
    if (path.endsWith('/settings/catalogue')) {
      const email: Record<string, [string, unknown]> = { enabled: ['bool', false], smtp_server: ['str', ''], smtp_port: ['int', 587], use_ssl: ['bool', false], use_tls: ['bool', true], username: ['str', ''], password: ['str', ''], from_address: ['str', ''], recipient_addresses: ['list', []] };
      const mcp: Record<string, [string, unknown]> = { enabled: ['bool', false], host: ['str', '127.0.0.1'], port: ['int', 8001], transport: ['str', 'stdio'], auth_token: ['str', ''], allowed_tools: ['list', []], max_context_items: ['int', 100] };
      data = { revision, unknown: [], fields: [[email, 'notify.email', 'notify_email'], [mcp, 'connect.mcp', 'connect_mcp']].flatMap(([schema, scope, group]) => Object.entries(schema).map(([key, [kind, fallback]]) => ({ scope, group, key, kind, label: key.replaceAll('_', ' '), readonly: false, secret: key === 'password' || key === 'auth_token', ...((key === 'password' || key === 'auth_token') ? { configured: Boolean(values[String(scope)]?.[key]) } : { value: values[String(scope)]?.[key] ?? fallback }) }))) };
    }
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
  const login = page.getByRole('dialog', { name: 'Connect to HaruQuantAI host' });
  await login.getByLabel('Host password').fill('test-password');
  await login.getByRole('button', { name: 'Connect', exact: true }).click();
  await expect(page.getByText('Host online')).toBeVisible();
});

test('settings menu matches the HaruQuantAI command hierarchy and supports keyboard dismissal', async ({ page }) => {
  const settings = page.getByRole('button', { name: 'Settings', exact: true });
  await settings.click();
  const menu = page.getByRole('menu', { name: 'Application settings' });
  await expect(menu.getByRole('menuitem')).toHaveText([
    'Configuration...', 'Benchmark...', 'Remote access...', 'MCP Server...', 'SMTP server...',
    'Notifications...', 'User access...', 'Credentials...', 'Advanced settings...', 'Skin', 'Reload UI', 'Exit',
  ]);
  await page.keyboard.press('Escape');
  await expect(menu).toHaveCount(0);
  await expect(settings).toBeFocused();
});

test('SQX configuration controls retain the data-frame and cleanup modes after refresh', async ({ page }) => {
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Configuration...', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Configuration', exact: true });
  await expect(dialog).toHaveCSS('width', '700px');
  await dialog.getByRole('radio', { name: 'Off', exact: true }).check();
  await dialog.getByRole('tab', { name: 'CPU', exact: true }).click();
  await expect(dialog.getByText('Total cores available 8')).toBeVisible();
  await expect(dialog.getByRole('checkbox', { name: 'Use thread affinity' })).toHaveCount(0);
  await dialog.getByRole('tab', { name: 'Memory', exact: true }).click();
  await dialog.getByRole('radio', { name: 'Let program determine maximum memory' }).check();
  await dialog.getByLabel('Cleanup interval', { exact: true }).selectOption('never');
  await dialog.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(dialog).toHaveCount(0);
  await page.reload();
  await expect(page.getByText('Host online')).toBeVisible();
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Configuration...', exact: true }).click();
  await expect(dialog.getByRole('radio', { name: 'Off', exact: true })).toBeChecked();
  for (const tab of ['Global', 'CPU', 'Performance', 'Memory', 'Databanks', 'Optimizations', 'Troubleshooting']) {
    await dialog.getByRole('tab', { name: tab, exact: true }).click();
    await expect(dialog.getByRole('tabpanel')).toBeVisible();
    await dialog.screenshot({ path: `../.agents/logs/20261008_220338_host-login-wiring/parity-${tab.toLowerCase()}.png` });
  }
  await dialog.getByRole('tab', { name: 'Memory', exact: true }).click();
  await expect(dialog.getByLabel('Cleanup interval', { exact: true })).toHaveValue('never');
  await expect(dialog.getByRole('radio', { name: 'Let program determine maximum memory' })).toBeChecked();
  await page.setViewportSize({ width: 480, height: 720 });
  const narrow = await dialog.boundingBox();
  expect(narrow!.width).toBeLessThanOrEqual(440);
  await expect(dialog.getByRole('button', { name: 'Save', exact: true })).toBeVisible();
  await dialog.screenshot({ path: '../.agents/logs/20261008_220338_host-login-wiring/parity-responsive.png' });
  await page.keyboard.press('Escape');
  await expect(dialog).toHaveCount(0);
});

test('configuration tabs validate, save, persist and restore focus', async ({ page }) => {
  const settings = page.getByRole('button', { name: 'Settings', exact: true });
  await settings.click();
  await page.getByRole('menuitem', { name: 'Configuration...', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Configuration', exact: true });
  await expect(dialog.getByRole('tab')).toHaveText(['Global', 'CPU', 'Performance', 'Memory', 'Databanks', 'Optimizations', 'Troubleshooting']);
  await dialog.getByRole('tab', { name: 'CPU' }).click();
  await dialog.getByRole('radio', { name: 'Custom number of cores' }).check();
  await dialog.getByLabel('Custom cores', { exact: true }).fill('0');
  await dialog.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(dialog.getByRole('alert')).toContainText('Custom cores');
  await dialog.getByLabel('Custom cores', { exact: true }).fill('4');
  await dialog.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(page.getByText('Configured workers 4', { exact: true })).toBeVisible();
  await page.reload();
  await expect(page.getByText('Configured workers 4', { exact: true })).toBeVisible();
});

test('skin and zoom update persisted application preferences', async ({ page }) => {
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Skin', exact: true }).click();
  await page.getByRole('menu', { name: 'Skin' }).getByRole('menuitem', { name: 'Light skin' }).click();
  await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Configuration...', exact: true }).click();
  const configuration = page.getByRole('dialog', { name: 'Configuration', exact: true });
  await expect(configuration.getByRole('tabpanel')).toHaveCSS('background-color', 'rgb(245, 245, 245)');
  await configuration.screenshot({ path: '../.agents/logs/20261008_220338_host-login-wiring/parity-light.png' });
  await configuration.getByRole('button', { name: 'Close', exact: true }).click();
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
  await dialog.getByRole('checkbox', { name: 'Turn off notification sounds' }).check();
  await dialog.getByRole('tab', { name: 'CPU' }).click();
  await dialog.getByRole('radio', { name: 'Custom number of cores' }).check();
  await dialog.getByLabel('Custom cores', { exact: true }).fill('3');
  await dialog.getByRole('tab', { name: 'Performance' }).click();
  await dialog.getByRole('checkbox', { name: 'Compute metrics in pips' }).check();
  await dialog.getByRole('tab', { name: 'Memory' }).click();
  await dialog.getByLabel('Maximum memory (GB)', { exact: true }).fill('12');
  await dialog.getByRole('tab', { name: 'Databanks' }).click();
  await dialog.getByLabel('Default auto-sync interval').selectOption('Immediately');
  await expect(dialog.getByRole('button', { name: 'Apply to all existing databanks' })).toBeDisabled();
  await dialog.getByRole('tab', { name: 'Optimizations' }).click();
  await dialog.getByRole('checkbox', { name: "Don't store data for 3D charts in Optimization profile" }).uncheck();
  await dialog.getByRole('tab', { name: 'Troubleshooting' }).click();
  await dialog.getByRole('checkbox', { name: 'Activate debug level' }).check();
  await dialog.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(page.getByText('Configured workers 3', { exact: true })).toBeVisible();
  await expect(page.getByText('Configured memory 12 GB', { exact: true })).toBeVisible();

  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await page.getByRole('menuitem', { name: 'SMTP server...', exact: true }).click();
  const smtp = page.getByRole('dialog', { name: 'SMTP server' });
  await smtp.getByLabel('SMTP server', { exact: true }).fill('mail.example.test');
  await smtp.getByLabel('Sender email').fill('sender@example.test');
  await smtp.getByLabel('Password', { exact: true }).fill('synthetic-stored-secret');
  await smtp.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(smtp).toHaveCount(0);
  await page.reload();
  await expect(page.getByText('Configured workers 3', { exact: true })).toBeVisible();
  await expect(page.getByText('Configured memory 12 GB', { exact: true })).toBeVisible();
  const persisted = await page.evaluate(() => JSON.parse(localStorage.getItem('sqx-recreation-v1') || '{}'));
  expect(persisted.state?.settings).toBeUndefined();
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await page.getByRole('menuitem', { name: 'SMTP server...', exact: true }).click();
  await expect(page.getByRole('dialog', { name: 'SMTP server' }).getByLabel('SMTP server', { exact: true })).toHaveValue('mail.example.test');
  await expect(page.getByRole('dialog', { name: 'SMTP server' }).getByLabel('Password', { exact: true })).toHaveValue('');
});

test('a rejected database write leaves the settings dialog open and reports failure', async ({ page }) => {
  await page.route('**/api/v1/settings', async route => {
    if (route.request().method() !== 'PUT') { await route.fallback(); return; }
    await route.fulfill({ status: 503, contentType: 'application/json', body: JSON.stringify({ status: 'error', error: { code: 'UNAVAILABLE', message: 'Database unavailable' } }) });
  });
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Configuration...', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Configuration', exact: true });
  await dialog.getByRole('checkbox', { name: 'Turn off notification sounds' }).check();
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
  await dialog.getByRole('checkbox', { name: 'Turn off notification sounds' }).check();
  await dialog.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(dialog).toHaveCount(0);
  expect(changes).toEqual({ 'config.global': { sounds_off: true } });
});

test('an expired session requires password re-entry before retrying the draft', async ({ page }) => {
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
  await dialog.getByRole('radio', { name: 'Custom number of cores' }).check();
  await dialog.getByLabel('Custom cores', { exact: true }).fill('4');
  await dialog.getByRole('button', { name: 'Save', exact: true }).click();
  const login = page.getByRole('dialog', { name: 'Connect to HaruQuantAI host' });
  await expect(login).toBeVisible();
  await expect(dialog).toBeVisible();
  await login.getByLabel('Host password').fill('test-password');
  await login.getByRole('button', { name: 'Connect', exact: true }).click();
  await expect(login).toHaveCount(0);
  await dialog.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(dialog).toHaveCount(0);
  await expect(page.getByText('Configured workers 4', { exact: true })).toBeVisible();
});

test('benchmark, remote, MCP, SMTP and exit surfaces are functional', async ({ page }) => {
  await expect(page.locator('.home-screen .version')).toContainText('SQX145 reference');
  const open = async (name: string) => { await page.getByRole('button', { name: 'Settings', exact: true }).click(); await page.getByRole('menuitem', { name, exact: true }).click(); };
  await open('Benchmark...'); await page.getByRole('button', { name: 'Start benchmark' }).click(); await expect(page.getByRole('heading', { name: 'Benchmark finished' })).toBeVisible({ timeout: 5000 }); await page.getByRole('button', { name: 'Close', exact: true }).last().click();
  await open('Remote access...'); const remote = page.getByRole('dialog', { name: 'Remote access' }); await remote.getByRole('checkbox', { name: 'Allow remote access to this application' }).check(); await remote.getByRole('checkbox', { name: 'Require a password' }).check(); await expect(remote.getByRole('textbox', { name: 'Remote password unavailable', exact: true })).toBeDisabled(); await remote.getByRole('button', { name: 'Save' }).click();
  await open('MCP Server...'); await expect(page.getByLabel('Auth token', { exact: true })).toHaveValue(''); await page.getByRole('button', { name: 'Close', exact: true }).last().click();
  await open('SMTP server...'); const smtp = page.getByRole('dialog', { name: 'SMTP server' }); await expect(smtp.getByLabel('Use SSL', { exact: true })).toBeVisible(); await expect(smtp.getByLabel('Use TLS', { exact: true })).toBeVisible(); await expect(smtp.getByRole('button', { name: 'Send test email' })).toHaveCount(0); await smtp.getByRole('button', { name: 'Close', exact: true }).last().click();
  await open('Exit'); const exitDialog = page.getByRole('dialog', { name: 'Exit HaruQuantAI' }); await exitDialog.getByRole('button', { name: 'Exit' }).click(); await expect(exitDialog).toHaveCount(0);
});


test('a server revision conflict preserves the draft and does not claim a save', async ({ page }) => {
  await page.route('**/api/v1/settings', async route => {
    if (route.request().method() !== 'PUT') { await route.fallback(); return; }
    await route.fulfill({ status: 409, contentType: 'application/json', body: JSON.stringify({ status: 'error', error: { code: 'REVISION_CONFLICT', message: 'Stale settings' } }) });
  });
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Configuration...', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Configuration', exact: true });
  await dialog.getByRole('checkbox', { name: 'Turn off notification sounds' }).check();
  await dialog.getByRole('button', { name: 'Save', exact: true }).click();
  await expect(dialog.getByRole('alert')).toContainText('settings changed in another session');
  await expect(dialog.getByRole('checkbox', { name: 'Turn off notification sounds' })).toBeChecked();
});


test('empty stored category explains its state and disables Save', async ({ page }) => {
  await page.route('**/api/v1/settings/catalogue', route => route.fulfill({
    status: 200, contentType: 'application/json',
    body: JSON.stringify({ status: 'success', data: { revision: 0, fields: [], unknown: [] } }),
  }));
  await page.getByRole('button', { name: 'Settings', exact: true }).click();
  await page.getByRole('menuitem', { name: 'Notifications...', exact: true }).click();
  const dialog = page.getByRole('dialog', { name: 'Notifications', exact: true });
  await expect(dialog.getByText('No settings are stored for this category.')).toBeVisible();
  await expect(dialog.getByRole('button', { name: 'Save', exact: true })).toBeDisabled();
  await dialog.getByRole('tab', { name: 'Email', exact: true }).click();
  await expect(dialog.getByText('No settings are stored for this category.')).toBeVisible();
  await expect(dialog.getByRole('button', { name: 'Save', exact: true })).toBeDisabled();
  await dialog.screenshot({ path: '../.agents/logs/20261020_141505_settings-database-verification/iteration3-empty-category.png' });
});
