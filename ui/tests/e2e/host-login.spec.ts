import { expect, test } from '@playwright/test';

// These cases verify UI contracts with mocked HTTP. Real host/SSE smoke is separate.
test('password-only dialog rejects invalid credentials and submits no username', async ({ page }) => {
  const credentials: unknown[] = [];
  await page.route('**/api/v1/**', async route => {
    if (new URL(route.request().url()).pathname.endsWith('/auth/login')) {
      credentials.push(route.request().postDataJSON());
      await route.fulfill({ status: 401, contentType: 'application/json', body: JSON.stringify({ status: 'error', error: { code: 'INVALID_CREDENTIALS', message: 'Login failed' } }) });
      return;
    }
    await route.fulfill({ status: 401, contentType: 'application/json', body: '{}' });
  });
  await page.goto('/');
  const dialog = page.getByRole('dialog', { name: 'Connect to HaruQuantAI host' });
  await expect(dialog).toBeVisible();
  await expect(dialog.getByLabel('Username')).toHaveCount(0);
  await dialog.getByLabel('Host password').fill('incorrect');
  await dialog.getByRole('button', { name: 'Connect', exact: true }).click();
  await expect(dialog.getByRole('button', { name: 'Connect', exact: true })).toBeEnabled();
  await expect(dialog.getByLabel('Host password')).toHaveValue('');
  await expect.poll(() => credentials.at(-1)).toEqual({ password: 'incorrect' });
  const persisted = await page.evaluate(() => JSON.stringify({ local: { ...localStorage }, session: { ...sessionStorage } }));
  expect(persisted).not.toContain('incorrect');
});

test('pending login prevents duplicate submission, then uses its issued token', async ({ page }) => {
  let release: (() => void) | undefined;
  const pending = new Promise<void>(resolve => { release = resolve; });
  let settingsToken = '';
  await page.route('**/api/v1/**', async route => {
    const request = route.request();
    const path = new URL(request.url()).pathname;
    if (path.endsWith('/auth/login')) {
      const credentials = request.postDataJSON() as { password?: string };
      if (!credentials.password) {
        await route.fulfill({ status: 401, contentType: 'application/json', body: JSON.stringify({ status: 'error', error: { code: 'INVALID_CREDENTIALS', message: 'Login required' } }) });
        return;
      }
      await pending;
      await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ status: 'success', data: { token: 'test-session' } }) });
      return;
    }
    if (path.endsWith('/settings')) settingsToken = request.headers()['authorization'] ?? '';
    if (path.endsWith('/events')) {
      await route.fulfill({ contentType: 'text/event-stream', body: ': heartbeat\n\n' });
      return;
    }
    const data = path.endsWith('/settings') ? { revision: 1, values: {} } : path.endsWith('/status') ? { cpu_count: 4 } : {};
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ status: 'success', data }) });
  });
  await page.goto('/');
  const dialog = page.getByRole('dialog', { name: 'Connect to HaruQuantAI host' });
  await dialog.getByLabel('Host password').fill('test-password');
  await dialog.getByRole('button', { name: 'Connect', exact: true }).click();
  await expect(dialog.getByRole('button', { name: 'Connecting...', exact: true })).toBeDisabled();
  await expect(dialog.getByLabel('Host password')).toBeDisabled();
  release?.();
  await expect(dialog).toHaveCount(0);
  await expect.poll(() => settingsToken).toBe('Bearer test-session');
});


test('login survives repeated reloads and a reopened tab until the host revokes it', async ({ page, context }) => {
  let logins = 0;
  let validations = 0;
  let revoked = false;
  const expires_at = new Date(Date.now() + 86400000).toISOString();
  await context.addInitScript(() => {
    const original = window.fetch.bind(window);
    window.fetch = ((input: RequestInfo | URL, init?: RequestInit) => String(input).includes('/api/v1/events?') ? Promise.resolve(new Response(new ReadableStream<Uint8Array>({ start() {} }), { headers: { 'Content-Type': 'text/event-stream' } })) : original(input, init)) as typeof fetch;
  });
  await context.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname;
    if (path.endsWith('/auth/login')) {
      logins++;
      await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ status: 'success', data: { token: 'persistent-session', expires_at } }) });
      return;
    }
    if (path.endsWith('/sessions/me')) {
      validations++;
      expect(route.request().headers()['authorization']).toBe('Bearer persistent-session');
      if (revoked) {
        await route.fulfill({ status: 401, contentType: 'application/json', body: JSON.stringify({ status: 'error', error: { code: 'INVALID_SESSION', message: 'Revoked' } }) });
        return;
      }
    }
    const data = path.endsWith('/settings') ? { revision: 1, values: {} } : path.endsWith('/status') ? { cpu_count: 4 } : { expires_at };
    await route.fulfill({ contentType: 'application/json', body: JSON.stringify({ status: 'success', data }) });
  });
  await page.goto('/');
  const dialog = page.getByRole('dialog', { name: 'Connect to HaruQuantAI host' });
  await dialog.getByLabel('Host password').fill('test-password');
  await dialog.getByRole('button', { name: 'Connect', exact: true }).click();
  await expect(page.getByText('Host online', { exact: true })).toBeVisible();
  for (let i = 0; i < 2; i++) {
    await page.reload();
    await expect(page.getByText('Host online', { exact: true })).toBeVisible();
    await expect(dialog).toHaveCount(0);
  }
  const saved = await page.evaluate(() => Object.entries(localStorage).filter(([key]) => key.startsWith('haruquantai.host-session.v1:')));
  expect(saved).toHaveLength(1);
  expect(saved[0][1]).not.toContain('test-password');
  expect(JSON.parse(saved[0][1]).expires_at).toBe(expires_at);
  const reopened = await context.newPage();
  await page.close();
  await reopened.goto('/');
  await expect(reopened.getByText('Host online', { exact: true })).toBeVisible();
  expect(logins).toBe(1);
  expect(validations).toBeGreaterThanOrEqual(3);
  revoked = true;
  await reopened.reload();
  await expect(reopened.getByRole('dialog', { name: 'Connect to HaruQuantAI host' })).toBeVisible();
  expect(logins).toBe(1);
  expect(await reopened.evaluate(() => Object.keys(localStorage).filter(key => key.startsWith('haruquantai.host-session.v1:')))).toEqual([]);
});
