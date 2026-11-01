import { test, expect, type Page } from '@playwright/test';
import { spawn, type ChildProcess } from 'node:child_process';
import { mkdtempSync, writeFileSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

const repo = path.resolve(process.cwd(), '../..');
const root = mkdtempSync(path.join(tmpdir(), 'haru-home-acceptance-'));
writeFileSync(path.join(root, '.home-acceptance'), 'test-owned');
const log = path.join(root, 'server.log');
let server: ChildProcess;
let serverOutput = '';
const start = () => {
  const child = spawn(path.join(repo, '.venv', 'Scripts', 'python.exe'),
    ['-m', 'tests.support.home_acceptance_server', '--root', root, '--port', '4180'],
    { cwd: repo, windowsHide: true, stdio: ['ignore', 'pipe', 'pipe'] });
  child.stdout?.on('data', chunk => serverOutput += chunk.toString());
  child.stderr?.on('data', chunk => serverOutput += chunk.toString());
  return child;
};
async function stop() {
  if (!server || server.exitCode !== null) return;
  const exited = new Promise<void>(resolve => server.once('exit', () => resolve()));
  server.kill(); await exited;
}
async function ready() {
  await expect.poll(async () => {
    if (server.exitCode !== null) throw new Error(`Acceptance server exited; see ${log}`);
    try { return (await fetch('http://127.0.0.1:4180/health')).status; } catch { return 0; }
  }, { timeout: 30000 }).toBe(200);
}
async function api(page: Page, route: string, body?: unknown) {
  return page.evaluate(async ({ route, body }) => {
    const key = Object.keys(localStorage).find(key => key.startsWith('haruquantai.host-session.v1:'));
    const session = key ? JSON.parse(localStorage.getItem(key)!) : {};
    const response = await fetch('/api/v1/home' + route, { method: body === undefined ? 'GET' : 'POST',
      headers: { Authorization: `Bearer ${session.token ?? ''}`, 'Content-Type': 'application/json' },
      body: body === undefined ? undefined : JSON.stringify(body) });
    return { ...(await response.json()), httpStatus: response.status };
  }, { route, body });
}

test.beforeAll(async () => { server = start(); await ready(); });
test.afterAll(async () => { await stop(); });

test('saved configuration, actual execution, chart, conflict, restart and both themes', async ({ page }, info) => {
  test.setTimeout(180000);
  await page.goto('/');
  await page.getByLabel('Host password', { exact: true }).fill('password');
  await page.getByRole('button', { name: 'Connect', exact: true }).click();
  await expect(page.locator('.home-connection-online')).toBeVisible();
  await page.locator('.home-projects li').filter({ hasText: 'Acceptance retester' }).getByRole('button', { name: 'Open project' }).click();
  await expect(page.getByLabel('Saved project', { exact: true })).toHaveValue('acceptance-retester');
  await expect(page.getByLabel('Saved task', { exact: true })).toHaveValue('task');
  await page.getByRole('tab', { name: 'Full settings', exact: true }).click();
  await page.getByRole('tab', { name: 'Money management', exact: true }).click();
  await page.getByLabel('Initial capital', { exact: true }).fill('200');
  await page.getByRole('tab', { name: 'Progress', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Start', exact: true })).toBeDisabled();
  await page.getByRole('button', { name: 'Save settings', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Save settings', exact: true })).toBeDisabled();
  const saved = await api(page, '/project/acceptance-retester');
  expect(saved.data.tasks.task.settings.execution.model.initial_capital).toBe(200);
  await expect(page.getByRole('button', { name: 'Start', exact: true })).toBeEnabled();
  await page.getByRole('button', { name: 'Start', exact: true }).click();
  await expect(page.locator('.sqd-task-desc')).toContainText('complete', { timeout: 30000 });
  const status = await api(page, '/engine/acceptance-retester/status');
  expect(status.data.status).toBe('COMPLETED');
  const identity = status.data.result.result_ids[0];
  const actual = await api(page, `/project/acceptance-retester/result/${identity}`);
  expect(actual.data.trades.map((trade: { net_pnl: number }) => trade.net_pnl)).toEqual([2, -2]);
  expect(actual.data.metrics.net_profit).toBe(0);
  expect(actual.data.equity_curve).toHaveLength(4);
  expect(actual.data.parameters.execution.model.initial_capital).toBe(200);
  await page.getByRole('tab', { name: 'Results', exact: true }).click();
  await page.getByLabel('Stored result', { exact: true }).selectOption(identity);
  await page.getByRole('tab', { name: 'Equity chart', exact: true }).click();
  await expect(page.getByRole('img', { name: 'Stored equity', exact: true })).toBeVisible();
  await page.screenshot({ path: info.outputPath('actual-result-dark.png') });

  await page.getByRole('tab', { name: 'Full settings', exact: true }).click();
  await page.getByRole('tab', { name: 'Notes', exact: true }).click();
  const notes = page.getByRole('textbox', { name: 'Notes', exact: true });
  const unicode = 'Research 日本語 🌱\n<script>escaped, complete plain text</script>';
  await notes.fill(unicode);
  await page.getByRole('button', { name: 'Save notes', exact: true }).click();
  await expect(page.locator('.sqd-notes-saved')).toHaveText('Saved');
  const before = await api(page, '/project/acceptance-retester');
  expect(before.data.metadata.notes).toBe(unicode);
  await notes.fill('Preserve this conflicting draft');
  const concurrent = await api(page, '/project/acceptance-retester/notes', { notes: 'Remote saved notes', expected_revision: before.data.revision });
  expect(concurrent.httpStatus).toBe(200);
  await page.getByRole('button', { name: 'Save notes', exact: true }).click();
  await expect(page.locator('.sqd-notes-conflict')).toBeVisible();
  await expect(notes).toHaveValue('Preserve this conflicting draft');
  await page.reload();
  await page.getByRole('tab', { name: 'Full settings', exact: true }).click();
  await page.getByRole('tab', { name: 'Notes', exact: true }).click();
  await expect(page.getByRole('textbox', { name: 'Notes', exact: true })).toHaveValue('Remote saved notes');

  await page.getByRole('tab', { name: 'Results', exact: true }).click();
  await page.getByRole('button', { name: '+ New analysis', exact: true }).click();
  await page.getByLabel('Name of custom plugin tab', { exact: true }).fill('Persisted review');
  await page.getByRole('button', { name: 'Create', exact: true }).click();
  await expect(page.getByRole('tab', { name: 'Persisted review', exact: true })).toBeVisible();
  await stop(); server = start(); await ready();
  await page.reload();
  await expect(page.getByLabel('Saved project', { exact: true })).toHaveValue('acceptance-retester');
  await page.getByRole('tab', { name: 'Results', exact: true }).click();
  await expect(page.getByRole('tab', { name: 'Persisted review', exact: true })).toBeVisible();
  const restarted = await api(page, '/project/acceptance-retester');
  expect(restarted.data.metadata.notes).toBe('Remote saved notes');
  expect(restarted.data.tasks.task.settings.execution.model.initial_capital).toBe(200);

  for (const [skin, theme] of [['Light skin', 'light'], ['Dark skin', 'dark']]) {
    await page.getByRole('button', { name: 'Settings', exact: true }).click();
    await page.getByRole('menuitem', { name: 'Skin', exact: true }).click();
    await page.getByRole('menuitem', { name: skin, exact: true }).click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', theme);
    await page.reload();
    await expect(page.locator('html')).toHaveAttribute('data-theme', theme);
    await expect(page.getByLabel('Saved project', { exact: true })).toHaveValue('acceptance-retester');
    await page.screenshot({ path: info.outputPath(`saved-${theme}.png`) });
  }
  await info.attach('isolated-host-log', { body: Buffer.from(serverOutput), contentType: 'text/plain' });
});
