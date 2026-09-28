/** Generic harness survives removal of every application contribution. */
import { expect, test } from '@playwright/test';

declare const process: { env: Record<string, string | undefined> };

test('surviving UI and backend read resources without their producer', async ({ page, request }) => {
  if (!process.env.HARU_TEST_URL) throw new Error('Removal harness requires an isolated real host');
  const login = await request.post('/api/v1/auth/login', { data: {} });
  expect(login.ok()).toBeTruthy();
  const token = (await login.json()).data.token;
  const headers = { Authorization: `Bearer ${token}` };
  const capabilities = await request.get('/api/v1/contributions', { headers });
  expect(capabilities.ok()).toBeTruthy();
  const installed = (await capabilities.json()).data;
  expect(installed.issues).toEqual([]);
  const expectedBackends = installed.packages.filter((item: { backend_entry: string | null }) => item.backend_entry).map((item: { id: string }) => item.id).sort();
  expect(Object.keys(installed.active).sort()).toEqual(expectedBackends);
  const unavailable = await request.post('/api/v1/contributions/removed.producer/missing', { headers, data: {} });
  expect(unavailable.status()).toBe(503);
  expect((await unavailable.json()).error.code).toBe('MISSING_CAPABILITY');
  const resources = await request.get('/api/v1/resources/', { headers });
  expect(resources.ok()).toBeTruthy();
  const list = (await resources.json()).data;
  expect(list.length).toBeGreaterThan(0);
  const result = await request.post('/api/v1/resources/read', { headers, data: list[0] });
  expect(result.ok()).toBeTruthy();
  expect((await result.json()).data.schema).toBe('{"type":"string"}');
  const errors: string[] = [];
  page.on('pageerror', error => errors.push(error.message));
  await page.goto('/');
  await expect(page.locator('.app-shell')).toBeVisible();
  await expect(page.getByText('Host online')).toBeVisible({ timeout: 30000 });
  const continueBtn = page.getByRole('button', { name: 'Continue' });
  if (await continueBtn.isVisible()) {
    await continueBtn.click();
    await expect(continueBtn).toHaveCount(0);
  }
  const buttons = page.locator('aside[aria-label="Applications"] button');
  const labels = await buttons.evaluateAll(nodes => nodes.map(node => node.getAttribute('aria-label')));
  for (const label of labels) {
    await page.getByRole('button', { name: label!, exact: true }).first().click();
    await expect(page.locator('.module-area').first()).toBeVisible();
    await expect(page.getByText('This contribution is unavailable. Stored data is retained.', { exact: true })).toHaveCount(0);
  }
  if (!installed.packages.some((item: { kind: string }) => item.kind === 'workspace')) {
    await expect(page.getByText('No workspace is installed. The host is ready.')).toBeVisible();
  }
  expect(errors).toEqual([]);
});
