import { expect, test } from '@playwright/test';
import { spawn, spawnSync } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync } from 'node:fs';
import { createServer } from 'node:net';
import { tmpdir } from 'node:os';
import path from 'node:path';

test('new settings persist through real HTTP/database, redact secrets, refresh, and rotate the isolated account', async ({ page }) => {
  test.setTimeout(180000);
  const repo = path.resolve('..');
  const temporary = mkdtempSync(path.join(tmpdir(), 'haru-settings-ui-'));
  const database = path.join(temporary, 'host.db');
  const python = path.join(repo, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
  const server = createServer();
  await new Promise<void>(resolve => server.listen(0, '127.0.0.1', resolve));
  const port = (server.address() as { port: number }).port;
  await new Promise<void>((resolve, reject) => server.close(error => error ? reject(error) : resolve()));
  const script = path.join(temporary, 'host.py');
  writeFileSync(script, `import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from app.host import persistence
persistence.DEFAULT_DATABASE_PATH = Path(sys.argv[2])
from app.host.settings import SettingsManager, settings_catalogue, _set_field
from app.host.session import hash_password
from app.host.bootstrap import create_host_app, HostRuntime
import uvicorn
target = SettingsManager(sys.argv[2], data_dir=Path(sys.argv[2]).parent / 'data')
seed = {}
for field in settings_catalogue(target.get_snapshot())['fields']:
    if field['group'] == 'connect_remote':
        _set_field(seed.setdefault('app_general', {}).setdefault('remote_access', {}), field['key'], field['value'])
    elif field['group'] not in ('runtime', 'user_access'):
        _set_field(seed.setdefault(field['group'], {}), field['key'], '' if field['secret'] else field['value'])
target.update({'application': seed, 'user_access': {'username': 'isolated', 'password_hash': hash_password('isolated-old-password')}})
runtime = HostRuntime(target)
(Path(sys.argv[2]).parent / 'issuer.txt').write_text(runtime.host_instance_id)
uvicorn.run(create_host_app(target, runtime=runtime, configuration=target), host='127.0.0.1', port=int(sys.argv[3]), log_level='warning')
`);
  const child = spawn(python, [script, repo, database, String(port)], { cwd: repo, windowsHide: true, stdio: 'ignore' });
  try {
    await expect.poll(async () => { try { return (await fetch(`http://127.0.0.1:${port}/api/v1/status`)).ok; } catch { return false; } }, { timeout: 30000 }).toBe(true);
    await page.route('**/api/v1/**', async route => {
      const incoming = new URL(route.request().url());
      const response = await route.fetch({ url: `http://127.0.0.1:${port}${incoming.pathname}${incoming.search}`, timeout: 10000 });
      await route.fulfill({ response });
    });
    // Isolate the long-lived SSE stream; all settings/login HTTP uses the real host.
    await page.addInitScript(() => {
      const original = window.fetch.bind(window);
      window.fetch = ((input: RequestInfo | URL, init?: RequestInit) => String(input).includes('/api/v1/events?')
        ? Promise.resolve(new Response(new ReadableStream<Uint8Array>({ start() { /* Keep the isolated stream connected. */ } }), { status: 200, headers: { 'Content-Type': 'text/event-stream' } }))
        : original(input, init)) as typeof fetch;
    });
    const login = async (password: string) => {
      const dialog = page.getByRole('dialog', { name: 'Connect to HaruQuantAI host' });
      await dialog.getByLabel('Host password', { exact: true }).fill(password);
      await dialog.getByRole('button', { name: 'Connect', exact: true }).click();
      await expect(page.getByText('Host online', { exact: true })).toBeVisible();
    };
    const open = async (entry: string, title: string) => {
      await page.getByRole('button', { name: 'Settings', exact: true }).click();
      await page.getByRole('menuitem', { name: entry, exact: true }).click();
      return page.getByRole('dialog', { name: title, exact: true });
    };
    const save = async (dialog: ReturnType<typeof page.getByRole>) => {
      await dialog.getByRole('button', { name: 'Save', exact: true }).click();
      await expect(dialog).toHaveCount(0);
    };
    await page.goto('/'); await login('isolated-old-password');
    let dialog = await open('Notifications...', 'Notifications');
    await dialog.getByLabel('Duration seconds', { exact: true }).fill('6');
    await dialog.getByRole('tab', { name: 'Email', exact: true }).click();
    await dialog.getByLabel('SMTP server', { exact: true }).fill('smtp.example.test');
    await dialog.getByLabel('Recipient addresses', { exact: true }).fill('["recipient@example.test"]');
    await dialog.getByLabel('Password', { exact: true }).fill('synthetic-mail-secret');
    await dialog.getByRole('tab', { name: 'Telegram', exact: true }).click();
    await dialog.getByLabel('Chat ID', { exact: true }).fill('synthetic-chat');
    await dialog.getByLabel('Bot token', { exact: true }).fill('synthetic-bot-secret');
    await save(dialog);
    dialog = await open('Credentials...', 'Credentials');
    await dialog.getByLabel('Account ID', { exact: true }).fill('42');
    await dialog.getByLabel('Password', { exact: true }).fill('synthetic-mt5-secret');
    await dialog.getByRole('tab', { name: 'cTrader', exact: true }).click();
    await dialog.getByLabel('Account ID', { exact: true }).fill('43');
    await dialog.getByLabel('Client secret', { exact: true }).fill('synthetic-ctrader-secret');
    await dialog.getByRole('tab', { name: 'AI agents', exact: true }).click();
    await dialog.getByLabel('Openai / model', { exact: true }).fill('synthetic-model');
    await dialog.getByLabel('Openai / api key', { exact: true }).fill('synthetic-ai-secret');
    await save(dialog);
    dialog = await open('Advanced settings...', 'Advanced settings');
    await dialog.getByLabel('Auto save interval s', { exact: true }).fill('150');
    await dialog.getByRole('tab', { name: 'Workspace', exact: true }).click();
    await dialog.getByLabel('Projects dir', { exact: true }).fill('temporary/projects');
    await dialog.getByRole('tab', { name: 'Backtest', exact: true }).click();
    await dialog.getByLabel('Max threads', { exact: true }).fill('3');
    await dialog.getByRole('tab', { name: 'Calibration', exact: true }).click();
    await dialog.getByLabel('Qqe / rsiperiod', { exact: true }).fill('[8,14]');
    await save(dialog);
    dialog = await open('MCP Server...', 'MCP Server');
    await dialog.getByLabel('Allowed tools', { exact: true }).fill('["settings.read"]');
    await dialog.getByLabel('Auth token', { exact: true }).fill('synthetic-mcp-secret');
    await save(dialog);
    const verify = spawnSync(python, ['-c', `import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from app.host.persistence import SettingsStore, DatabaseManager, HostSessionStore
store = HostSessionStore(DatabaseManager(sys.argv[2]))
peer = (Path(sys.argv[2]).parent / 'issuer.txt').read_text()
sessions = store.list_records(peer_id=peer)
assert len(sessions) == 1 and sessions[0].status == "ACTIVE"
assert len(sessions[0].token_hash) == 64
_, rows = SettingsStore(sys.argv[2]).read_all()
groups = {r.key:r.value for r in rows if r.scope == 'application'}
assert all(r.scope == 'application' for r in rows), 'A settings save created a mirror row'
assert 'connect_remote' not in groups
assert groups['notify_desktop']['duration_seconds'] == 6
assert groups['notify_email']['recipient_addresses'] == ['recipient@example.test']
assert groups['notify_email']['password'] == 'synthetic-mail-secret'
assert groups['notify_telegram']['bot_token'] == 'synthetic-bot-secret'
assert groups['config_metatrader5']['account_id'] == 42
assert groups['config_ctrader']['client_secret'] == 'synthetic-ctrader-secret'
assert groups['config_agents']['openai']['model'] == 'synthetic-model'
assert groups['config_agents']['openai']['api_key'] == 'synthetic-ai-secret'
assert groups['app_general']['auto_save_interval_s'] == 150
assert groups['workspace_paths']['projects_dir'] == 'temporary/projects'
assert groups['engine_backtest']['max_threads'] == 3
assert groups['calibration_indicators']['QQE.RSIPeriod'] == [8,14]
assert groups['connect_mcp']['auth_token'] == 'synthetic-mcp-secret'
`, repo, database], { cwd: repo, windowsHide: true, encoding: 'utf8' });
    expect(verify.status, 'independent SettingsStore read-back').toBe(0);
    await page.reload(); await expect(page.getByText('Host online', { exact: true })).toBeVisible();
    dialog = await open('Notifications...', 'Notifications');
    await expect(dialog.getByLabel('Duration seconds', { exact: true })).toHaveValue('6');
    await dialog.getByRole('tab', { name: 'Telegram', exact: true }).click();
    await expect(dialog.getByLabel('Bot token', { exact: true })).toHaveValue('');
    await expect(dialog.getByText('Configured', { exact: true })).toBeVisible();
    await dialog.getByLabel('Clear Bot token', { exact: true }).check(); await save(dialog);
    const rawResponses: string[] = [];
    page.on('response', response => { if (response.url().includes('/settings') && response.request().method() === 'GET') void response.text().then(text => rawResponses.push(text)); });
    dialog = await open('Credentials...', 'Credentials');
    await dialog.getByRole('tab', { name: 'AI agents', exact: true }).click();
    await expect(dialog.getByLabel('Openai / model', { exact: true })).toHaveValue('synthetic-model');
    await expect(dialog.getByLabel('Openai / api key', { exact: true })).toHaveValue('');
    await dialog.getByRole('button', { name: 'Close', exact: true }).last().click();
    const storage = await page.evaluate(() => JSON.stringify({ local: { ...localStorage }, session: { ...sessionStorage } }));
    expect(storage).not.toContain('synthetic-');
    expect(rawResponses.join('')).not.toContain('synthetic-ai-secret');
    dialog = await open('User access...', 'User access');
    await dialog.getByLabel('Username', { exact: true }).fill('replacement');
    await dialog.getByLabel('Current host password', { exact: true }).fill('isolated-old-password');
    await dialog.getByLabel('New host password', { exact: true }).fill('isolated-new-password');
    await dialog.getByLabel('Confirm new host password', { exact: true }).fill('isolated-new-password');
    await dialog.getByLabel('Session duration (minutes)', { exact: true }).fill('2880');
    await dialog.screenshot({ path: '../.agents/logs/20261008_220338_host-login-wiring/coverage-account-before.png' });
    await dialog.getByRole('button', { name: 'Save', exact: true }).click({ timeout: 10000 });
    await expect(dialog).toHaveCount(0); await login('isolated-new-password');
    await page.reload(); await expect(page.getByText('Host online', { exact: true })).toBeVisible();
  } finally {
    child.kill();
    await new Promise<void>(resolve => { if (child.exitCode !== null) resolve(); else child.once('exit', () => resolve()); });
    const resolved = path.resolve(temporary);
    if (path.dirname(resolved) !== path.resolve(tmpdir()) || !path.basename(resolved).startsWith('haru-settings-ui-')) throw new Error('Unexpected temporary cleanup target');
    rmSync(resolved, { recursive: true, force: true });
  }
});
