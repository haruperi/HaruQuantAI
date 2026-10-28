import { expect, test, type Page } from '@playwright/test';

async function mockEditor(page: Page) {
  await page.addInitScript(() => {
    localStorage.setItem(
      `haruquantai.host-session.v1:${location.origin}/api/v1`,
      JSON.stringify({
        version: 1,
        token: 'editor-browser-test',
        expires_at: new Date(Date.now() + 3600000).toISOString(),
      }),
    );
  });
  let path = 'app/include/indicators/custom/example.py';
  let disk = 'value = 1\n';
  let tabs = [{ file_path: path, title: 'example.py', content: disk, is_dirty: false, mode: 'python' }];
  let active: string | null = path;
  const closes: boolean[] = [];
  const creates: Array<{ template_type: string; name: string; category: string }> = [];
  const saves: Array<{ file_path: string; content: string }> = [];
  const state = () => ({ status: 'ready', open_tabs: tabs, active_file: active, layout: {} });
  await page.route('**/api/v1/**', async (route) => {
    const url = new URL(route.request().url());
    if (!url.pathname.includes('/code-editor/')) {
      const data = url.pathname.endsWith('/auth/login')
        ? { token: 'editor-test' }
        : url.pathname.endsWith('/settings')
          ? { revision: 0, values: {} }
          : {};
      await route.fulfill({ json: { status: 'success', data } });
      return;
    }
    const endpoint = url.pathname.split('/code-editor')[1];
    const body = route.request().method() === 'POST' ? route.request().postDataJSON() : {};
    let data: unknown = {};
    if (endpoint === '/init') data = state();
    else if (endpoint === '/navigator')
      data = {
        id: 'app/include',
        name: 'snippets',
        type: 'directory',
        children: [{ id: path, path, name: path.split('/').pop(), type: 'file' }],
      };
    else if (endpoint === '/session') {
      tabs = body.tabs;
      active = body.active_file;
      data = state();
    } else if (endpoint === '/tabs/close') {
      closes.push(body.force);
      tabs = [];
      active = null;
      data = { status: 'closed', active_file: null };
    } else if (endpoint === '/tabs/open') {
      tabs = [{ file_path: path, title: path.split('/').pop()!, content: disk, is_dirty: false, mode: 'python' }];
      data = { status: 'opened', tab: tabs[0], active_file: path };
    } else if (endpoint === '/file/save') {
      saves.push(body);
      disk = body.content;
      data = { status: 'saved', diagnostics: [] };
    } else if (endpoint === '/file/rename') {
      path = body.new_path;
      data = { status: 'renamed' };
    } else if (endpoint === '/templates/render') {
      if (!body.category) {
        await route.fulfill({
          status: 422,
          json: { status: 'error', error: { code: 'validation', message: 'Enter a category' } },
        });
        return;
      }
      const snake = (value: string) => value.replace(/([a-z0-9])([A-Z])/g, '$1_$2').toLowerCase();
      data = {
        content: `class ${body.name}: pass`,
        file_path: `app/include/indicators/${snake(body.category)}/${snake(body.name)}.py`,
      };
    } else if (endpoint === '/templates/create') {
      creates.push(body);
      path = `app/include/indicators/${body.category}/my_indicator.py`;
      data = {
        status: 'created',
        file_path: path,
        tab: { file_path: path, title: 'my_indicator.py', content: '', is_dirty: false, mode: 'python' },
      };
    } else if (endpoint === '/indicator-test/new') data = { params: { period: 14 } };
    else if (endpoint === '/indicator-test/run')
      data = {
        status: 'failed',
        test_id: 'missing',
        error: 'No stored history. Import history in Data Manager first.',
        symbol: 'EURUSD',
        timeframe: 'H1',
        bars_calculated: 0,
        candlesticks: [],
        indicator_plots: [],
        table_rows: [],
        discrepancies: [],
      };
    await route.fulfill({ json: { status: 'success', data } });
  });
  return { closes, saves, creates, snapshot: state };
}

test('dirty close prompts and cancellation retains the buffer', async ({ page }) => {
  const mock = await mockEditor(page);
  await page.goto('/codeeditor');
  const editor = page.locator('textarea');
  await expect(editor).toHaveValue('value = 1\n');
  await editor.fill('value = 2');
  page.once('dialog', (dialog) => dialog.dismiss());
  await page.getByRole('button', { name: 'Close example.py', exact: true }).click();
  await expect(editor).toHaveValue('value = 2');
  expect(mock.closes).toEqual([]);
  page.once('dialog', (dialog) => dialog.accept());
  await page.getByRole('button', { name: 'Close example.py', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Close example.py', exact: true })).toHaveCount(0);
  expect(mock.closes).toEqual([true]);
});

test('empty edits save correctly and reopening preserves unsaved text', async ({ page }) => {
  const mock = await mockEditor(page);
  await page.goto('/codeeditor');
  const editor = page.locator('textarea');
  await expect(editor).toHaveValue('value = 1\n');
  await editor.fill('unsaved = 2');
  await page.locator('aside').filter({ hasText: 'Navigator' }).getByText('example.py', { exact: true }).click();
  await expect(editor).toHaveValue('unsaved = 2');
  await editor.fill('');
  await page.getByRole('button', { name: 'Save', exact: true }).click();
  await expect.poll(() => mock.saves.length).toBe(1);
  expect(mock.saves[0].content).toBe('');
});

test('renaming an open dirty tab preserves content and saves to the new path', async ({ page }) => {
  const mock = await mockEditor(page);
  await page.goto('/codeeditor');
  const editor = page.locator('textarea');
  await expect(editor).toHaveValue('value = 1\n');
  await editor.fill('value = 3');
  await page
    .locator('aside')
    .filter({ hasText: 'Navigator' })
    .getByText('example.py', { exact: true })
    .click({ button: 'right' });
  page.once('dialog', (dialog) => dialog.accept('app/include/renamed.py'));
  await page.getByRole('button', { name: /Rename/ }).click();
  await expect(page.getByRole('button', { name: 'Close renamed.py', exact: true })).toBeVisible();
  await expect(editor).toHaveValue('value = 3');
  await page.getByRole('button', { name: 'Save', exact: true }).click();
  await expect.poll(() => mock.saves.length).toBe(1);
  expect(mock.saves[0]).toEqual({ file_path: 'app/include/renamed.py', content: 'value = 3' });
});

test('missing historical data is shown as an actionable error', async ({ page }) => {
  await mockEditor(page);
  await page.goto('/codeeditor');
  await page.getByRole('button', { name: 'Test Indicator', exact: true }).click();
  await expect(page.getByRole('alert')).toContainText('Import history in Data Manager first');
  await expect(page.getByText('Multi-Parameter Verification Sweep')).toHaveCount(0);
});

test('indicator creation supports presets, a custom category and the full target path', async ({ page }) => {
  const mock = await mockEditor(page);
  await page.goto('/codeeditor');
  await page.getByRole('button', { name: 'Create from Template', exact: true }).click();
  await expect(page.getByText('app/include/indicators/custom/my_indicator.py', { exact: true })).toBeVisible();
  await page.getByLabel('Category', { exact: true }).selectOption('trend');
  await expect(page.getByText('app/include/indicators/trend/my_indicator.py', { exact: true })).toBeVisible();
  await page.getByLabel('Category', { exact: true }).selectOption('__new__');
  await expect(page.getByRole('button', { name: 'Create & Open', exact: true })).toBeDisabled();
  await page.getByLabel('New indicator category').fill('research');
  await expect(page.getByText('app/include/indicators/research/my_indicator.py', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Create & Open', exact: true }).click();
  await expect.poll(() => mock.creates.length).toBe(1);
  expect(mock.creates[0]).toEqual({ template_type: 'BlocksIndicators', name: 'MyIndicator', category: 'research' });
});

test('navigator labels indicator domains', async ({ page }) => {
  await mockEditor(page);
  await page.goto('/codeeditor');
  await expect(page.getByTitle('Building block domain')).toContainText('custom');
});
