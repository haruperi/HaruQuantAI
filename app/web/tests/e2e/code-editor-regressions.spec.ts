import { expect, test, type Page, type Route } from '@playwright/test';
import type { IndicatorTestResultDto } from '../../workspaces/code_editor/codeEditorClient';

async function mockEditor(page: Page, source = 'value = 1\n') {
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
  let path = 'app/include/blocks/indicators/custom/example.py';
  let disk = source;
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
        file_path: `app/include/blocks/indicators/${snake(body.category)}/${snake(body.name)}.py`,
      };
    } else if (endpoint === '/templates/create') {
      creates.push(body);
      path = `app/include/blocks/indicators/${body.category}/my_indicator.py`;
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
  const editor = page.getByRole('textbox', { name: 'Source code editor', exact: true });
  await expect(editor).toHaveText('value = 1\n');
  await editor.fill('value = 2');
  page.once('dialog', (dialog) => dialog.dismiss());
  await page.getByRole('button', { name: 'Close example.py', exact: true }).click();
  await expect(editor).toHaveText('value = 2');
  expect(mock.closes).toEqual([]);
  page.once('dialog', (dialog) => dialog.accept());
  await page.getByRole('button', { name: 'Close example.py', exact: true }).click();
  await expect(page.getByRole('button', { name: 'Close example.py', exact: true })).toHaveCount(0);
  expect(mock.closes).toEqual([true]);
});

test('empty edits save correctly and reopening preserves unsaved text', async ({ page }) => {
  const mock = await mockEditor(page);
  await page.goto('/codeeditor');
  const editor = page.getByRole('textbox', { name: 'Source code editor', exact: true });
  await expect(editor).toHaveText('value = 1\n');
  await editor.fill('unsaved = 2');
  await page.locator('aside').filter({ hasText: 'Navigator' }).getByText('example.py', { exact: true }).click();
  await expect(editor).toHaveText('unsaved = 2');
  await editor.fill('');
  await page.getByRole('button', { name: 'Save', exact: true }).click();
  await expect.poll(() => mock.saves.length).toBe(1);
  expect(mock.saves[0].content).toBe('');
});

test('renaming an open dirty tab preserves content and saves to the new path', async ({ page }) => {
  const mock = await mockEditor(page);
  await page.goto('/codeeditor');
  const editor = page.getByRole('textbox', { name: 'Source code editor', exact: true });
  await expect(editor).toHaveText('value = 1\n');
  await editor.fill('value = 3');
  await page
    .locator('aside')
    .filter({ hasText: 'Navigator' })
    .getByText('example.py', { exact: true })
    .click({ button: 'right' });
  page.once('dialog', (dialog) => dialog.accept('app/include/renamed.py'));
  await page.getByRole('button', { name: /Rename/ }).click();
  await expect(page.getByRole('button', { name: 'Close renamed.py', exact: true })).toBeVisible();
  await expect(editor).toHaveText('value = 3');
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
  await expect(page.getByText('app/include/blocks/indicators/custom/my_indicator.py', { exact: true })).toBeVisible();
  await page.getByLabel('Category', { exact: true }).selectOption('trend');
  await expect(page.getByText('app/include/blocks/indicators/trend/my_indicator.py', { exact: true })).toBeVisible();
  await page.getByLabel('Category', { exact: true }).selectOption('__new__');
  await expect(page.getByRole('button', { name: 'Create & Open', exact: true })).toBeDisabled();
  await page.getByLabel('New indicator category').fill('research');
  await expect(page.getByText('app/include/blocks/indicators/research/my_indicator.py', { exact: true })).toBeVisible();
  await page.getByRole('button', { name: 'Create & Open', exact: true }).click();
  await expect.poll(() => mock.creates.length).toBe(1);
  expect(mock.creates[0]).toEqual({ template_type: 'BlocksIndicators', name: 'MyIndicator', category: 'research' });
});

test('navigator labels indicator domains', async ({ page }) => {
  await mockEditor(page);
  await page.goto('/codeeditor');
  await expect(page.getByTitle('Building block domain')).toContainText('custom');
});

test('Python tokens have distinct colors and builtins inside strings stay strings', async ({ page }, testInfo) => {
  await mockEditor(
    page,
    '# len is a builtin\nclass Example:\n    def calculate(self, bars):\n        text = "len"\n        return len(bars) + 42\n',
  );
  await page.setViewportSize({ width: 1271, height: 932 });
  await page.goto('/codeeditor');
  const editor = page.getByRole('textbox', { name: 'Source code editor', exact: true });
  await expect(editor.locator('span').filter({ hasText: /^class$/ })).toHaveCSS('color', 'rgb(199, 146, 234)');
  await expect(editor.locator('span').filter({ hasText: /^Example$/ })).toHaveCSS('color', 'rgb(78, 201, 176)');
  await expect(editor.locator('span').filter({ hasText: /^"len"$/ })).toHaveCSS('color', 'rgb(206, 145, 120)');
  await expect(editor.locator('.cm-python-builtin')).toHaveCount(1);
  await expect(editor.locator('.cm-python-builtin')).toHaveText('len');
  await expect(editor.locator('.cm-python-builtin')).toHaveCSS('color', 'rgb(79, 193, 255)');
  await page.screenshot({ path: testInfo.outputPath('python-editor.png') });
});

test('Python completion offers builtins and local names and accepts Tab or Enter', async ({ page }) => {
  await mockEditor(page);
  await page.goto('/codeeditor');
  const editor = page.getByRole('textbox', { name: 'Source code editor', exact: true });
  await expect(editor).toHaveText('value = 1');
  await editor.press('Control+a');
  await editor.press('Backspace');
  await editor.pressSequentially('pri');
  await expect(page.getByRole('option', { name: 'print', exact: true })).toBeVisible();
  await editor.press('Tab');
  await expect(editor).toHaveText('print');
  await editor.press('Control+a');
  await page.keyboard.insertText('custom_value = 1\ncust');
  await editor.press('Escape');
  await expect(page.getByRole('listbox')).toHaveCount(0);
  await editor.press('Control+Space');
  await expect(page.getByRole('option', { name: 'custom_value', exact: true })).toBeVisible();
  await editor.press('Enter');
  await expect.poll(() => editor.innerText()).toContain('custom_value = 1\ncustom_value');
});

test('Python brackets and four-space indentation work while typing', async ({ page }) => {
  await mockEditor(page);
  await page.goto('/codeeditor');
  const editor = page.getByRole('textbox', { name: 'Source code editor', exact: true });
  await editor.fill('class Example:');
  await editor.press('End');
  await editor.press('Enter');
  await editor.pressSequentially('def run(self):');
  await editor.press('Escape');
  await editor.press('Enter');
  await editor.pressSequentially('return len(');
  await expect.poll(() => editor.innerText()).toContain('class Example:\n    def run(self):\n        return len()');
});

test('each tab retains its own undo history', async ({ page }) => {
  await mockEditor(page);
  const first = 'app/include/blocks/indicators/custom/example.py';
  const second = 'app/include/blocks/indicators/custom/other.py';
  await page.route('**/code-editor/navigator', (route) =>
    route.fulfill({
      json: {
        status: 'success',
        data: {
          id: 'app/include',
          name: 'include',
          type: 'directory',
          children: [first, second].map((path) => ({ id: path, path, name: path.split('/').pop(), type: 'file' })),
        },
      },
    }),
  );
  await page.route('**/code-editor/tabs/open', (route) =>
    route.fulfill({
      json: {
        status: 'success',
        data: {
          status: 'opened',
          tab: { file_path: second, title: 'other.py', content: 'other = 10', is_dirty: false, mode: 'python' },
          active_file: second,
        },
      },
    }),
  );
  await page.goto('/codeeditor');
  const editor = page.getByRole('textbox', { name: 'Source code editor', exact: true });
  await expect(editor).toHaveText('value = 1');
  await editor.fill('value = 2');
  await page.locator('aside').filter({ hasText: 'Navigator' }).getByText('other.py', { exact: true }).click();
  await expect(editor).toHaveText('other = 10');
  await editor.fill('other = 99');
  await page.getByRole('button', { name: 'Close example.py' }).locator('..').click();
  await expect(editor).toHaveText('value = 2');
  await editor.press('Control+z');
  await expect(editor).toHaveText('value = 1');
  await page.getByRole('button', { name: 'Close other.py' }).locator('..').click();
  await expect(editor).toHaveText('other = 99');
  await editor.press('Control+z');
  await expect(editor).toHaveText('other = 10');
});

test('backend diagnostics appear inline in the editor', async ({ page }) => {
  await mockEditor(page, 'broken = missing_name');
  await page.route('**/code-editor/compile', (route) =>
    route.fulfill({
      json: {
        status: 'success',
        data: {
          success: false,
          file: 'example.py',
          errors: [{ line: 1, column: 10, severity: 'error', message: 'Unresolved symbol: missing_name' }],
        },
      },
    }),
  );
  await page.goto('/codeeditor');
  await page.getByRole('button', { name: 'Compile', exact: true }).click();
  await expect(page.locator('.cm-lintRange-error')).toBeVisible();
  await expect(page.getByText('Line 1:10 — Unresolved symbol: missing_name', { exact: true })).toBeVisible();
});

test('save shortcut writes the current CodeMirror buffer', async ({ page }) => {
  const mock = await mockEditor(page);
  await page.goto('/codeeditor');
  const editor = page.getByRole('textbox', { name: 'Source code editor', exact: true });
  await expect(editor).toHaveText('value = 1');
  await editor.fill('value = 8');
  await editor.press('Control+s');
  await expect.poll(() => mock.saves.length).toBe(1);
  expect(mock.saves[0].content).toBe('value = 8');
});

type TesterResponseWindow = Window & { testerResponsesConsumed: number };

function testerModal(page: Page) {
  return page.locator('div.fixed.inset-0').filter({
    has: page.getByRole('heading', { name: 'Indicator Test Studio', exact: true }),
  });
}

function indicatorResult(value: number): IndicatorTestResultDto {
  const candle = { time: 1735689600, open: 1, high: 2, low: 0.5, close: 1.5, volume: 100 };
  return {
    test_id: `result-${value}`,
    status: 'success',
    symbol: 'EURUSD',
    timeframe: 'H1',
    bars_calculated: 1,
    candlesticks: [candle],
    indicator_plots: [{ time: candle.time, value }],
    table_rows: [{ ...candle, indicator_val: value }],
    discrepancies: [],
  };
}

async function pendingTester(page: Page, holdDefaults = false) {
  await mockEditor(page);
  // Observe body consumption so negative assertions cannot race an unread response.
  await page.addInitScript(() => {
    const state = window as TesterResponseWindow;
    state.testerResponsesConsumed = 0;
    const originalFetch = window.fetch.bind(window);
    window.fetch = async (...args) => {
      const response = await originalFetch(...args);
      if (String(args[0]).includes('/indicator-test/')) {
        const originalJson = response.json.bind(response);
        response.json = async () => {
          try {
            return await originalJson();
          } finally {
            state.testerResponsesConsumed++;
          }
        };
      }
      return response;
    };
  });
  const runs: Route[] = [];
  const defaults: Route[] = [];
  await page.route('**/code-editor/indicator-test/run', (route) => { runs.push(route); });
  if (holdDefaults) {
    await page.route('**/code-editor/indicator-test/new', (route) => { defaults.push(route); });
  }
  await page.goto('/codeeditor');
  await expect(page.getByRole('textbox', { name: 'Source code editor', exact: true })).toBeVisible();
  await page.clock.install({ time: new Date('2026-10-30T12:00:00Z') });
  await page.clock.pauseAt(new Date('2026-10-30T12:00:01Z'));
  await page.getByRole('button', { name: 'Test Indicator', exact: true }).click();
  await expect(testerModal(page)).toBeVisible();
  if (holdDefaults) {
    // The development shell uses StrictMode: retire its discarded first effect.
    await expect.poll(() => defaults.length).toBe(2);
    await consumeTesterResponse(page, defaults.shift()!, { params: { period: 14 } });
  }
  return { runs, defaults };
}

async function consumeTesterResponse(page: Page, route: Route, data: unknown, error = false) {
  const before = await page.evaluate(() => (window as TesterResponseWindow).testerResponsesConsumed);
  await route.fulfill({
    status: error ? 422 : 200,
    json: error
      ? { status: 'error', error: { code: 'validation', message: String(data) } }
      : { status: 'success', data },
  });
  await expect.poll(() => page.evaluate(() => (window as TesterResponseWindow).testerResponsesConsumed)).toBeGreaterThan(before);
}

for (const outcome of ['success', 'failure'] as const) {
  test(`input change ignores an old ${outcome} inside the debounce window`, async ({ page }) => {
    const { runs } = await pendingTester(page);
    const modal = testerModal(page);
    await expect(modal.getByLabel('period', { exact: true })).toHaveValue('14');
    await page.clock.runFor(250);
    await expect.poll(() => runs.length).toBe(1);
    await modal.getByLabel('period', { exact: true }).fill('20');
    await consumeTesterResponse(page, runs[0], outcome === 'success' ? indicatorResult(777) : 'obsolete run', outcome === 'failure');
    expect(runs).toHaveLength(1);
    await expect(modal.getByRole('alert')).toHaveCount(0);
    await expect(modal.getByText('777.00000', { exact: true })).toHaveCount(0);
    await expect(modal.locator('canvas')).toHaveCount(0);
    await expect(modal.getByRole('button', { name: 'Execution Logs (0)', exact: true })).toBeVisible();
    await page.clock.runFor(250);
    await expect.poll(() => runs.length).toBe(2);
    expect(runs[1].request().postDataJSON().params).toEqual({ period: 20 });
    await consumeTesterResponse(page, runs[1], indicatorResult(123));
    await expect(modal.getByText('123.00000', { exact: true })).toBeVisible();
    await expect(modal.locator('canvas').first()).toBeVisible();
    await expect(modal.getByRole('button', { name: 'Run Test', exact: true })).toBeEnabled();
    await expect(modal.getByRole('button', { name: 'Execution Logs (1)', exact: true })).toBeVisible();
  });
}

test('an old failure cannot clear the running state or overwrite a newer run', async ({ page }) => {
  const { runs } = await pendingTester(page);
  const modal = testerModal(page);
  await expect(modal.getByLabel('period', { exact: true })).toBeVisible();
  await page.clock.runFor(250);
  await expect.poll(() => runs.length).toBe(1);
  await modal.getByRole('combobox').selectOption('M5');
  await modal.getByRole('textbox').fill('GBPUSD');
  await page.clock.runFor(250);
  await expect.poll(() => runs.length).toBe(2);
  expect(runs[1].request().postDataJSON()).toMatchObject({ symbol: 'GBPUSD', timeframe: 'M5' });
  await consumeTesterResponse(page, runs[0], 'obsolete failure', true);
  await expect(modal.getByRole('button', { name: 'Running...', exact: true })).toBeDisabled();
  await expect(modal.getByRole('alert')).toHaveCount(0);
  await expect(modal.getByRole('button', { name: 'Execution Logs (0)', exact: true })).toBeVisible();
  await consumeTesterResponse(page, runs[1], indicatorResult(456));
  await expect(modal.getByText('456.00000', { exact: true })).toBeVisible();
  await expect(modal.getByRole('button', { name: 'Run Test', exact: true })).toBeEnabled();
});

test('changing indicator through a saved configuration ignores obsolete defaults failure', async ({ page }) => {
  const { runs, defaults } = await pendingTester(page, true);
  const modal = testerModal(page);
  await expect.poll(() => defaults.length).toBe(1);
  await page.route('**/code-editor/indicator-test/load?*', (route) => route.fulfill({
    json: { status: 'success', data: { config: {
      indicator_name: 'RSI', symbol: 'GBPUSD', timeframe: 'M5', params: { period: 9 }, bars_to_reserve: 0, bar_count: 2,
    } } },
  }));
  page.once('dialog', (dialog) => dialog.accept('saved-rsi'));
  await modal.getByRole('button', { name: 'Load Test Configuration', exact: true }).click();
  await expect.poll(() => defaults.length).toBe(2);
  expect(defaults[1].request().postDataJSON().indicator_name).toBe('RSI');
  await consumeTesterResponse(page, defaults[1], { params: { period: 14 } });
  await expect(modal.getByLabel('period', { exact: true })).toHaveValue('9');
  await consumeTesterResponse(page, defaults[0], 'obsolete defaults', true);
  await expect(modal.getByRole('alert')).toHaveCount(0);
  await expect(modal.getByRole('button', { name: 'Execution Logs (0)', exact: true })).toBeVisible();
  await page.clock.runFor(250);
  await expect.poll(() => runs.length).toBe(1);
  expect(runs[0].request().postDataJSON()).toMatchObject({
    indicator_name: 'RSI', symbol: 'GBPUSD', timeframe: 'M5', params: { period: 9 }, bars_to_reserve: 0, bar_count: 2,
  });
  await consumeTesterResponse(page, runs[0], indicatorResult(321));
  await expect(modal.getByText('321.00000', { exact: true })).toBeVisible();
});

test('closing the tester with pending defaults and a run leaves a reopened tester clean', async ({ page }) => {
  const pageErrors: string[] = [];
  page.on('pageerror', (error) => pageErrors.push(error.message));
  const { runs, defaults } = await pendingTester(page, true);
  let modal = testerModal(page);
  await expect.poll(() => defaults.length).toBe(1);
  // Manual execution can precede the defaults response.
  await modal.getByRole('button', { name: 'Run Test', exact: true }).click();
  await expect.poll(() => runs.length).toBe(1);
  await modal.locator('button').filter({ has: page.locator('svg.lucide-x') }).click();
  await expect(testerModal(page)).toHaveCount(0);
  await page.clock.runFor(1000);
  expect(runs).toHaveLength(1);
  await page.getByRole('button', { name: 'Test Indicator', exact: true }).click();
  modal = testerModal(page);
  await expect.poll(() => defaults.length).toBe(3);
  await consumeTesterResponse(page, defaults[1], { params: { period: 14 } });
  await consumeTesterResponse(page, defaults[2], { params: { period: 21 } });
  await consumeTesterResponse(page, defaults[0], 'closed defaults', true);
  await consumeTesterResponse(page, runs[0], 'closed run', true);
  await expect(modal.getByLabel('period', { exact: true })).toHaveValue('21');
  await expect(modal.getByRole('alert')).toHaveCount(0);
  await expect(modal.getByRole('button', { name: 'Execution Logs (0)', exact: true })).toBeVisible();
  await page.clock.runFor(250);
  await expect.poll(() => runs.length).toBe(2);
  await consumeTesterResponse(page, runs[1], indicatorResult(654));
  await expect(modal.getByText('654.00000', { exact: true })).toBeVisible();
  expect(pageErrors).toEqual([]);
});
