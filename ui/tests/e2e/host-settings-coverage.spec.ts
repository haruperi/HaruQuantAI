import { expect, test } from '@playwright/test';
import { spawn, spawnSync } from 'node:child_process';
import { mkdtempSync, rmSync, writeFileSync, readFileSync, existsSync } from 'node:fs';
import { tmpdir } from 'node:os';
import path from 'node:path';

test('new settings persist through real HTTP/database, redact secrets, refresh, and rotate the isolated account', async ({ page }) => {
  test.setTimeout(180000);
  const repo = path.resolve('..');
  const temporary = mkdtempSync(path.join(tmpdir(), 'haru-settings-ui-'));
  const database = path.join(temporary, 'host.db');
  const python = path.join(repo, '.venv', process.platform === 'win32' ? 'Scripts/python.exe' : 'bin/python');
  const port = 4180;
  const script = path.join(temporary, 'host.py');
  writeFileSync(script, `"""Run the isolated real host used by settings browser verification.

Description:
    Start AppHost against a test-owned temporary database and loopback port.
Purpose:
    FEAT-HOST-SETTINGS: Verify UI-to-database persistence through real HTTP/SSE.
Key Capabilities:
    - FR-HOST-SETTINGS-LOAD: Read test-owned settings through SettingsManager.
      Logging: host startup and settings persistence emit structured FR logs.
Python API Usage:
    Executed as a subprocess owned and stopped by the browser test.
CLI Usage:
    python host.py repository temporary_database loopback_port
"""
import sys
from pathlib import Path
import os
(Path(sys.argv[2]).parent / "pid.txt").write_text(str(os.getpid()))
sys.path.insert(0, sys.argv[1])
from app.host.persistence import HostPersistence
HostPersistence.DEFAULT_DB_PATH = Path(sys.argv[2])
from app.host.settings import SettingsManager
from app.host.session import hash_password
from app.host.bootstrap import AppHost
from app.main import create_app
import uvicorn
target = SettingsManager()
if not target.get_scope('user_access'):
    examples = {'app_general': {'theme': 'dark', 'zoom': 1.0, 'auto_save_interval_s': 120},
     'notify_desktop': {'duration_seconds': 5},
     'notify_email': {'smtp_server': '',
                      'smtp_port': 587,
                      'recipient_addresses': [],
                      'password': ''},
     'notify_telegram': {'chat_id': '', 'bot_token': ''},
     'config_metatrader5': {'account_id': 0, 'password': ''},
     'config_ctrader': {'account_id': '', 'client_secret': ''},
     'config_agents': {'openai': {'model': '', 'api_key': ''}},
     'workspace_paths': {'projects_dir': 'temporary/initial'},
     'engine_backtest': {'max_threads': 2},
     'calibration_indicators': {'QQE.RSIPeriod': [14]},
     'connect_mcp': {'allowed_tools': [], 'auth_token': ''},
     'user_access': {'username': 'isolated', 'session_timeout_mins': 1440}}
    examples["user_access"]["password_hash"] = hash_password("isolated-old-password")
    target.save_settings({"application": examples})
runtime = AppHost(data_dir=Path(sys.argv[2]).parent / 'data', require_auth=True, use_process_pool=False)
(Path(sys.argv[2]).parent / 'issuer.txt').write_text(runtime.host_instance_id)
uvicorn.run(create_app(config=runtime.config, runtime=runtime), host='127.0.0.1', port=int(sys.argv[3]), log_level='warning', timeout_graceful_shutdown=1)
`);
  const startHost = () => spawn(python, [script, repo, database, String(port)], { cwd: repo, windowsHide: true, stdio: 'ignore' });
  let child = startHost();
  const stopHost = async () => {
    if (child.exitCode !== null) return;
    const pidFile = path.join(temporary, 'pid.txt');
    if (existsSync(pidFile)) process.kill(Number(readFileSync(pidFile, 'utf8')));
    else child.kill();
    await new Promise<void>(resolve => { if (child.exitCode !== null) resolve(); else child.once('exit', () => resolve()); });
  };
  const ready = async () => {
    await expect.poll(async () => {
      if (child.exitCode !== null) throw new Error('Isolated host exited before readiness');
      try {
        const body = await (await fetch(`http://127.0.0.1:${port}/api/v1/status`)).json();
        return body.data?.host_instance_id === readFileSync(path.join(temporary, 'issuer.txt'), 'utf8');
      } catch { return false; }
    }, { timeout: 30000 }).toBe(true);
  };
  try {
    await ready();
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
    const peer = await page.context().newPage();
    await peer.goto('/'); await expect(peer.getByText('Host online', { exact: true })).toBeVisible();
    let dialog = await open('Configuration...', 'Configuration');
    await dialog.getByLabel('Window Header custom text', { exact: true }).fill('UI database test');
    await dialog.getByRole('tab', { name: 'CPU', exact: true }).click();
    await dialog.getByLabel('Custom number of cores', { exact: true }).check();
    await dialog.getByLabel('Custom cores', { exact: true }).fill('3');
    await dialog.getByRole('tab', { name: 'Performance', exact: true }).click();
    await dialog.getByLabel('Compute metrics in pips (Recommended turned off)', { exact: true }).check();
    await dialog.getByRole('tab', { name: 'Memory', exact: true }).click();
    await dialog.getByLabel('G1', { exact: true }).check();
    await dialog.getByRole('tab', { name: 'Databanks', exact: true }).click();
    await dialog.getByRole('combobox', { name: 'Default auto-sync interval', exact: true }).selectOption('Every hour');
    await dialog.getByRole('tab', { name: 'Optimizations', exact: true }).click();
    await dialog.getByRole('checkbox').first().uncheck();
    await dialog.getByRole('tab', { name: 'Troubleshooting', exact: true }).click();
    await dialog.getByLabel('Activate debug level', { exact: true }).check();
    await save(dialog);
    await expect(peer.getByText('Configured workers 3', { exact: false })).toBeVisible();
    await peer.close();
    dialog = await open('Configuration...', 'Configuration');
    await expect(dialog.getByLabel('Window Header custom text', { exact: true })).toHaveValue('UI database test');
    await dialog.getByLabel('Window Header custom text', { exact: true }).fill('Canceled text');
    await dialog.getByRole('button', { name: 'Close', exact: true }).last().click();
    await page.reload(); await expect(page.getByText('Host online', { exact: true })).toBeVisible();
    dialog = await open('Configuration...', 'Configuration');
    await expect(dialog.getByLabel('Window Header custom text', { exact: true })).toHaveValue('UI database test');
    await dialog.getByRole('button', { name: 'Close', exact: true }).last().click();
    await page.getByRole('button', { name: 'Settings', exact: true }).click();
    await page.getByRole('menuitem', { name: 'Skin', exact: true }).click();
    await page.getByRole('menuitem', { name: 'Light skin', exact: true }).click();
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
    await page.getByRole('button', { name: 'Settings', exact: true }).click();
    await page.getByRole('button', { name: 'Zoom in', exact: true }).click({ clickCount: 3 });
    await expect(page.getByRole('menu', { name: 'Application settings' }).getByText('130%', { exact: true })).toBeVisible();
    await page.getByRole('button', { name: 'Settings', exact: true }).click();
    dialog = await open('Notifications...', 'Notifications');
    await dialog.getByLabel('Duration seconds', { exact: true }).fill('6');
    await dialog.getByRole('tab', { name: 'Email', exact: true }).click();
    await dialog.getByLabel('SMTP server', { exact: true }).fill('smtp.example.test');
    await dialog.getByLabel('Recipient addresses', { exact: true }).fill('["recipient@example.test"]');
    await dialog.getByLabel('Password', { exact: true }).fill('synthetic-mail-secret');
    await dialog.getByRole('tab', { name: 'Telegram', exact: true }).click();
    await dialog.getByLabel('Chat ID', { exact: true }).fill('synthetic-chat');
    await dialog.getByLabel('Bot token', { exact: true }).fill('synthetic-bot-secret');
    await save(dialog);
    dialog = await open('Remote access...', 'Remote access');
    await dialog.getByLabel('Allow remote access to this application', { exact: true }).check();
    await save(dialog);
    dialog = await open('SMTP server...', 'SMTP server');
    await dialog.getByLabel('Port', { exact: true }).fill('2525');
    await save(dialog);
    dialog = await open('Credentials...', 'Credentials');
    await dialog.getByLabel('Account ID', { exact: true }).fill('42');
    await dialog.getByLabel('Password', { exact: true }).fill('synthetic-mt5-secret');
    await dialog.getByRole('tab', { name: 'cTrader', exact: true }).click();
    await dialog.getByLabel('Account ID', { exact: true }).fill('account-43');
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
    await dialog.getByRole('tab', { name: 'Runtime', exact: true }).click();
    await expect(dialog.getByText('No settings are stored for this category.')).toBeVisible();
    await expect(dialog.getByRole('button', { name: 'Save', exact: true })).toBeEnabled();
    await save(dialog);
    dialog = await open('MCP Server...', 'MCP Server');
    await dialog.getByLabel('Allowed tools', { exact: true }).fill('["settings.read"]');
    await dialog.getByLabel('Auth token', { exact: true }).fill('synthetic-mcp-secret');
    await save(dialog);
    const verify = spawnSync(python, ['-c', `import sys
from pathlib import Path
sys.path.insert(0, sys.argv[1])
from app.host.persistence import HostPersistence
import json
HostPersistence.DEFAULT_DB_PATH = Path(sys.argv[2])
rows = HostPersistence.read_records('host_settings')
groups = {r['key']:json.loads(r['value_json']) for r in rows if r['scope'] == 'application'}
assert all(r['scope'] == 'application' for r in rows), 'A settings save created a mirror row'
assert 'connect_remote' not in groups
assert groups['app_general']['header_custom_text'] == 'UI database test'
assert groups['app_general']['theme'] == 'light'
assert groups['app_general']['remote_access']['allow'] is True
assert groups['notify_email']['smtp_port'] == 2525
assert round(groups['app_general']['zoom'], 1) == 1.3
assert groups['config_cpu']['custom_cores'] == 3
assert groups['config_memory']['gc_type'] == 'G1GC'
assert groups['config_performance']['compute_pips_metrics'] is True
assert groups['config_databanks']['databank_sync_interval_mins'] == 60
assert groups['config_optimizations']['dont_store_op_3d_charts_data'] is False
assert groups['config_troubleshooting']['debug_level_active'] is True
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
    expect(verify.status, 'independent HostPersistence read-back').toBe(0);
    await page.reload(); await expect(page.getByText('Host online', { exact: true })).toBeVisible();
    dialog = await open('Notifications...', 'Notifications');
    await expect(dialog.getByLabel('Duration seconds', { exact: true })).toHaveValue('6');
    await dialog.getByRole('tab', { name: 'Telegram', exact: true }).click();
    await expect(dialog.getByLabel('Bot token', { exact: true })).toHaveValue('');
    await expect(dialog.getByText('Configured', { exact: true })).toBeVisible();
    await dialog.getByLabel('Clear Bot token', { exact: true }).check(); await save(dialog);
    const rawResponses: string[] = [];
    const bodies: Promise<void>[] = [];
    const capture = (response: import('@playwright/test').Response) => {
      if (new URL(response.url()).pathname.endsWith('/settings/catalogue')) bodies.push(response.text().then(text => { rawResponses.push(text); }));
    };
    page.on('response', capture);
    dialog = await open('Credentials...', 'Credentials');
    await dialog.getByRole('tab', { name: 'AI agents', exact: true }).click();
    await expect(dialog.getByLabel('Openai / model', { exact: true })).toHaveValue('synthetic-model');
    await expect(dialog.getByLabel('Openai / api key', { exact: true })).toHaveValue('');
    await dialog.getByRole('button', { name: 'Close', exact: true }).last().click();
    const storage = await page.evaluate(() => JSON.stringify({ local: { ...localStorage }, session: { ...sessionStorage } }));
    expect(storage).not.toContain('synthetic-');
    await Promise.all(bodies); page.off('response', capture);
    expect(rawResponses.length).toBeGreaterThan(0);
    expect(rawResponses.join('')).not.toContain('synthetic-ai-secret');
    dialog = await open('User access...', 'User access');
    await dialog.getByLabel('Username', { exact: true }).fill('replacement');
    await dialog.getByLabel('Current host password', { exact: true }).fill('isolated-old-password');
    await dialog.getByLabel('New host password', { exact: true }).fill('isolated-new-password');
    await dialog.getByLabel('Confirm new host password', { exact: true }).fill('isolated-new-password');
    await dialog.getByLabel('Session duration (minutes)', { exact: true }).fill('2880');
    await dialog.screenshot({ path: '../.agents/logs/20261020_141505_settings-database-verification/iteration3-account.png' });
    await dialog.getByRole('button', { name: 'Save', exact: true }).click({ timeout: 10000 });
    await expect(dialog).toHaveCount(0); await login('isolated-new-password');
    await page.reload(); await expect(page.getByText('Host online', { exact: true })).toBeVisible();
    // Restart only the child created by this test, preserving its temporary database.
    await stopHost();
    child = startHost();
    await ready();
    await page.evaluate(() => { for (const key of Object.keys(localStorage)) if (key.startsWith('haruquantai.host-session.v1:')) localStorage.removeItem(key); });
    await page.reload(); await login('isolated-new-password');
    await expect(page.locator('html')).toHaveAttribute('data-theme', 'light');
    dialog = await open('Advanced settings...', 'Advanced settings');
    await expect(dialog.getByLabel('Auto save interval s', { exact: true })).toHaveValue('150');
    await dialog.screenshot({ path: '../.agents/logs/20261020_141505_settings-database-verification/iteration3-restart.png' });
  } finally {
    await stopHost();
    const resolved = path.resolve(temporary);
    if (path.dirname(resolved) !== path.resolve(tmpdir()) || !path.basename(resolved).startsWith('haru-settings-ui-')) throw new Error('Unexpected temporary cleanup target');
    rmSync(resolved, { recursive: true, force: true, maxRetries: 10, retryDelay: 100 });
  }
});
