import { expect, test, type Page } from '@playwright/test';
import { tmpdir } from 'node:os';
import { join } from 'node:path';

const about = { application: 'HaruQuantAI', version: '1.0.0', build_timestamp: '2026-10-18T00:00:00Z', runtime: 'Test runtime', metadata_source: 'host-reported', license: { state: 'unavailable', reason: 'No license provider registered.' } };
const unavailable = { state: 'unavailable', reason: 'No release feed configured.', current_version: '1.0.0', latest_version: null, update_available: null, changelog: null, release_url: null, published_at: null, checked_at: '2026-10-21T00:00:00Z' };

async function connect(page: Page, options: { populated?: boolean; failure?: boolean; updates?: object; delayUpdate?: boolean } = {}) {
  const calls: string[] = [];
  await page.addInitScript(() => {
    const fetchOriginal = window.fetch.bind(window);
    window.fetch = ((input: RequestInfo | URL, init?: RequestInit) => String(input).includes('/api/v1/events?') ? Promise.resolve(new Response(new ReadableStream<Uint8Array>({ start() {} }), { headers: { 'Content-Type': 'text/event-stream' } })) : fetchOriginal(input, init)) as typeof fetch;
  });
  await page.route('**/api/v1/**', async route => {
    const path = new URL(route.request().url()).pathname;
    calls.push(path);
    if (path === '/api/v1/home' && options.failure) { await route.fulfill({ status: 500, json: { status: 'error', error: { code: 'UNAVAILABLE', message: 'Store unavailable.' } } }); return; }
    if (path === '/api/v1/home/updates' && options.delayUpdate) await new Promise(resolve => setTimeout(resolve, 1200));
    const data = path.endsWith('/auth/login') ? { token: 'isolated-test-session' }
      : path.endsWith('/settings') ? { revision: 1, values: {} }
      : path.endsWith('/status') ? { cpu_count: 4 }
      : path === '/api/v1/home/about' ? about
      : path === '/api/v1/home' ? { recent_projects: options.populated ? [{ id: 'p1', name: 'Host research project', workspace: 'projects', last_activity: '2026-10-21T00:00:00Z' }] : [] }
      : path === '/api/v1/home/updates' ? options.updates ?? unavailable
      : path === '/api/v1/home/diagnostics' ? { status: 'OK', database: { exists: true, path: 'data/database/test.db', error: null }, hardware: { ram_total_bytes: 8 * 1024 ** 3, ram_available_bytes: 4 * 1024 ** 3, ram_used_pct: 50 }, directories: { projects_dir: 'data/projects' } } : {};
    await route.fulfill({ json: { status: 'success', data } });
  });
  await page.goto('/');
  const dialog = page.getByRole('dialog', { name: 'Connect to HaruQuantAI host' });
  await dialog.getByLabel('Host password').fill('test-password');
  await dialog.getByRole('button', { name: 'Connect', exact: true }).click();
  await expect(dialog).toHaveCount(0);
  await expect(page.getByRole('main', { name: 'Home workspace' }).getByText('Host online', { exact: true })).toBeVisible();
  return calls;
}

test('default landing uses host data and explicit inspections', async ({ page }) => {
  const calls = await connect(page);
  await expect(page.getByRole('heading', { name: 'Your research starts here' })).toBeVisible();
  await expect(page.getByText('No recent projects yet')).toBeVisible();
  await expect(page.getByText('1.0.0', { exact: true })).toBeVisible();
  await page.screenshot({ path: join(tmpdir(), 'haru-home-desktop.png') });
  expect(calls).not.toContain('/api/v1/home/updates');
  expect(calls).not.toContain('/api/v1/home/diagnostics');
  await page.getByRole('button', { name: 'Check for updates' }).click();
  await expect(page.getByText('unavailable: No release feed configured.')).toBeVisible();
  await page.getByRole('button', { name: 'Inspect diagnostics' }).click();
  await expect(page.getByRole('heading', { name: 'System diagnostics' })).toBeVisible();
  await expect(page.getByText('4.00 GiB of 8.00 GiB')).toBeVisible();
  await expect(page.getByText('data/projects', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Prepare market data' }).click();
  await expect(page).toHaveURL(/\/datamanager/);
});

test('project shortcuts navigate without claiming a saved project was loaded', async ({ page }) => {
  await connect(page, { populated: true });
  const projects = page.getByRole('region', { name: 'Recent projects' });
  await expect(projects.getByText('Host research project')).toBeVisible();
  await projects.getByRole('button', { name: 'Open workspace' }).click();
  await expect(page).toHaveURL(/\/projects/);
});

test('failed host information preserves local guides and provides retry', async ({ page }) => {
  await connect(page, { failure: true });
  await expect(page.getByRole('button', { name: 'Retry host information' })).toBeVisible();
  await page.getByText('Read guide', { exact: true }).first().click();
  await expect(page.getByText(/Open Data Manager to inspect available datasets/)).toBeVisible();
});

test('local guides remain readable while locked on a narrow screen', async ({ page }) => {
  await page.setViewportSize({ width: 390, height: 844 });
  await page.goto('/');
  const dialog = page.getByRole('dialog', { name: 'Connect to HaruQuantAI host' });
  await dialog.getByRole('button', { name: /Close/i }).click();
  await expect(page.getByRole('button', { name: 'Check for updates' })).toBeDisabled();
  await page.getByText('Working offline', { exact: true }).click();
  await expect(page.getByText(/These text guides are bundled/)).toBeVisible();
  expect(await page.locator('.home-landing').evaluate(element => element.scrollWidth <= element.clientWidth)).toBe(true);
  await page.screenshot({ path: join(tmpdir(), 'haru-home-mobile.png') });
});

test('release text is escaped and pending work cancels on navigation', async ({ page }) => {
  await connect(page, { updates: { ...unavailable, state: 'available', latest_version: '1.1.0', update_available: true, changelog: '<script>unsafe()</script>' }, delayUpdate: true });
  await page.getByRole('button', { name: 'Check for updates' }).click();
  await expect(page.getByRole('button', { name: 'Checking…' })).toBeDisabled();
  await expect(page.getByText('Version 1.1.0 is available.')).toBeVisible();
  await expect(page.locator('.home-inspection pre')).toHaveText('<script>unsafe()</script>');
  await page.getByRole('button', { name: 'Check for updates' }).click();
  await page.getByRole('button', { name: 'Explore Builder' }).click();
  await expect(page).toHaveURL(/\/builder/);
  await expect(page.getByRole('heading', { name: 'Release information' })).toHaveCount(0);
});
