import { expect, test, type Page, type Route } from '@playwright/test';
import type { IndicatorTestResultDto } from '../../workspaces/code_editor/codeEditorClient';
import { TEMPLATE_METADATA } from '../../workspaces/code_editor/templateCatalog';
import { createHash } from 'node:crypto';

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
    if (endpoint === '/catalogue/symbols' || endpoint === '/catalogue/indicators') data = [];
    else if (endpoint === '/compilations') data = null;
    else if (endpoint === '/export-formats') data = [
      { format_id: 'python', name: 'Python source template', extension: '.py.tpl' },
      { format_id: 'pseudocode', name: 'Pseudocode template', extension: '.txt.tpl' },
    ];
    else if (endpoint === '/templates') data = TEMPLATE_METADATA.map(item => ({
      template_id: item.id, name: item.name, description: item.description,
      category: item.categoryName, default_filename: item.defaultName + '.py', target_subdir: item.targetDir,
    }));
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
  await page.route('**/code-editor/compilations', (route) =>
    route.fulfill({
      json: {
        status: 'success',
        data: {
          job_id: 'inline-job', status: 'COMPLETED', progress: 100, message: 'Compilation completed with diagnostics', cancellation_requested: false,
          results: [{ success: false, file: 'app/include/blocks/indicators/custom/example.py',
          errors: [{ line: 1, column: 10, severity: 'error', message: 'Unresolved symbol: missing_name' }] }],
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

type PackageResponseWindow = Window & { packageResponsesConsumed: number };

test('a missing indicator value and null reference difference render without crashing', async ({ page }) => {
  await mockEditor(page);
  const result = indicatorResult(123);
  result.indicator_plots = [{ time: result.table_rows[0].time }];
  result.table_rows[0].indicator_val = null;
  result.table_rows[0].reference_val = 1;
  result.table_rows[0].diff = null;
  result.discrepancies = [{
    bar: 0, time: result.table_rows[0].time, series: 'value',
    type: 'NonFiniteValue', message: 'Indicator returned NaN or infinity',
  }];
  const pageErrors: string[] = [];
  page.on('pageerror', (error) => pageErrors.push(error.message));
  await page.route('**/code-editor/indicator-test/run', (route) => route.fulfill({
    json: { status: 'success', data: result },
  }));
  await page.goto('/codeeditor');
  await page.getByRole('button', { name: 'Test Indicator', exact: true }).click();
  const row = testerModal(page).getByRole('row').filter({ has: page.getByRole('cell', { name: 'NaN', exact: true }) });
  await expect(row).toBeVisible();
  await expect(row.getByRole('cell', { name: '—', exact: true })).toBeVisible();
  await expect(testerModal(page).getByRole('button', { name: 'Run Test', exact: true })).toBeEnabled();
  expect(pageErrors).toEqual([]);
});

function packageModal(page: Page) {
  return page.locator('div.fixed.inset-0').filter({
    has: page.getByRole('heading', { name: 'Import / Export Extension Pack', exact: true }),
  });
}

async function pendingPackage(page: Page, files = [
  'app/include/blocks/indicators/custom/first.py',
  'app/include/blocks/indicators/custom/second.py',
]) {
  await mockEditor(page);
  await page.addInitScript(() => {
    const state = window as PackageResponseWindow;
    state.packageResponsesConsumed = 0;
    const originalFetch = window.fetch.bind(window);
    window.fetch = async (...args) => {
      const response = await originalFetch(...args);
      if (String(args[0]).includes('/import-export/')) {
        const originalJson = response.json.bind(response);
        response.json = async () => {
          try {
            return await originalJson();
          } finally {
            state.packageResponsesConsumed++;
          }
        };
      }
      return response;
    };
  });
  let navigatorRequests = 0;
  const inspections: Route[] = [];
  const imports: Route[] = [];
  const exports: Route[] = [];
  await page.route('**/code-editor/init', (route) => route.fulfill({ json: {
    status: 'success', data: {
      status: 'ready', active_file: files[0] ?? null, layout: {},
      open_tabs: files.map((path) => ({
        file_path: path, title: path.split('/').pop(), content: 'value = 1', is_dirty: false, mode: 'python',
      })),
    },
  } }));
  await page.route('**/code-editor/navigator', (route) => {
    navigatorRequests++;
    return route.fulfill({ json: { status: 'success', data: {
      id: 'app/include', name: 'snippets', type: 'directory',
      children: files.map((path) => ({ id: path, path, name: path.split('/').pop(), type: 'file' })),
    } } });
  });
  await page.route('**/code-editor/import-export/inspect', (route) => { inspections.push(route); });
  await page.route('**/code-editor/import-export/import', (route) => { imports.push(route); });
  await page.route('**/code-editor/import-export/export', (route) => { exports.push(route); });
  await page.goto('/codeeditor');
  const editor = page.getByRole('textbox', { name: 'Source code editor', exact: true });
  if (files.length) await expect(editor).toHaveText('value = 1');
  else await expect(editor).toBeVisible();
  return { files, inspections, imports, exports, get navigatorRequests() { return navigatorRequests; } };
}

async function consumePackageResponse(page: Page, route: Route, data: unknown, error = false) {
  const before = await page.evaluate(() => (window as PackageResponseWindow).packageResponsesConsumed);
  await route.fulfill({
    status: error ? 422 : 200,
    json: error
      ? { status: 'error', error: { code: 'validation', message: String(data) } }
      : { status: 'success', data },
  });
  await expect.poll(() => page.evaluate(() => (window as PackageResponseWindow).packageResponsesConsumed)).toBeGreaterThan(before);
}

const packagePreview = [
  { filename: 'app/include/blocks/indicators/custom/existing.py', file_size: 24, exists_locally: true },
  { filename: 'app/include/blocks/indicators/custom/new.py', file_size: 32, exists_locally: false },
];

test('package export without open files is disabled and sends no request', async ({ page }) => {
  const mock = await pendingPackage(page, []);
  await page.getByRole('button', { name: 'Export', exact: true }).click();
  const modal = packageModal(page);
  await expect(modal.getByRole('button', { name: 'Export Pack', exact: true })).toBeDisabled();
  await expect(modal.getByText('Open a Python snippet to export.', { exact: true })).toBeVisible();
  expect(mock.exports).toHaveLength(0);
});

test('package export sends exact open disk paths and supported metadata', async ({ page }) => {
  const mock = await pendingPackage(page);
  await page.getByRole('textbox', { name: 'Source code editor', exact: true }).fill('unsaved = 2');
  await page.getByRole('button', { name: 'Export', exact: true }).click();
  const modal = packageModal(page);
  await expect(modal.getByRole('checkbox')).toHaveCount(0);
  await expect(modal.getByLabel('Target Directory', { exact: true })).toHaveCount(0);
  await expect(modal.getByText(/Export uses saved files on disk/)).toBeVisible();
  await expect(modal.getByText(/Archive-relative paths determine import destinations/)).toBeVisible();
  await modal.getByLabel('Pack Name', { exact: true }).fill('Research Pack');
  await modal.getByLabel('Description', { exact: true }).fill('Two Python snippets');
  await modal.getByLabel('Output File', { exact: true }).fill('app/include/research.zip');
  await modal.getByRole('button', { name: 'Export Pack', exact: true }).click();
  await expect.poll(() => mock.exports.length).toBe(1);
  expect(mock.exports[0].request().postDataJSON()).toEqual({
    file_paths: mock.files, archive_path: 'app/include/research.zip',
    metadata: { name: 'Research Pack', description: 'Two Python snippets' },
  });
  await consumePackageResponse(page, mock.exports[0], {
    status: 'exported', file_count: 2, archive_path: 'app/include/research.zip', files: mock.files,
  });
  await expect(modal.getByText('Successfully exported 2 file(s) to app/include/research.zip', { exact: true })).toBeVisible();
});

for (const [option, rule] of [
  ['Merge with existing files (Keep existing files)', 'skip'],
  ['Overwrite existing files (Replace existing with pack contents)', 'overwrite'],
  ['Import with rename (Save duplicates with _imported suffix)', 'rename'],
] as const) {
  test(`package import maps ${rule} for every preview entry and refreshes on success`, async ({ page }) => {
    const mock = await pendingPackage(page);
    await page.getByRole('button', { name: 'Import', exact: true }).click();
    const modal = packageModal(page);
    await modal.getByLabel('Select Pack File', { exact: true }).fill('app/include/source.zip');
    await modal.getByRole('button', { name: 'Inspect', exact: true }).click();
    await expect.poll(() => mock.inspections.length).toBe(1);
    expect(mock.inspections[0].request().postDataJSON()).toEqual({ archive_path: 'app/include/source.zip' });
    await consumePackageResponse(page, mock.inspections[0], packagePreview);
    await expect(modal.getByText(packagePreview[0].filename, { exact: true })).toBeVisible();
    await modal.getByRole('radio', { name: option, exact: true }).check();
    const before = mock.navigatorRequests;
    await modal.getByRole('button', { name: 'Import Pack', exact: true }).click();
    await expect.poll(() => mock.imports.length).toBe(1);
    expect(mock.imports[0].request().postDataJSON()).toEqual({
      archive_path: 'app/include/source.zip',
      resolution_rules: Object.fromEntries(packagePreview.map((entry) => [entry.filename, rule])),
    });
    await consumePackageResponse(page, mock.imports[0], {
      status: 'completed', extracted_count: 1, skipped_count: 1, extracted: [packagePreview[1].filename], skipped: [packagePreview[0].filename],
    });
    await expect(modal.getByText('Import complete: 1 extracted, 1 skipped.', { exact: true })).toBeVisible();
    await expect.poll(() => mock.navigatorRequests).toBe(before + 1);
  });
}

test('package archive changes clear an existing preview and an empty reinspection cannot import', async ({ page }) => {
  const mock = await pendingPackage(page);
  await page.getByRole('button', { name: 'Import', exact: true }).click();
  const modal = packageModal(page);
  await modal.getByRole('button', { name: 'Inspect', exact: true }).click();
  await expect.poll(() => mock.inspections.length).toBe(1);
  await consumePackageResponse(page, mock.inspections[0], packagePreview);
  await expect(modal.getByRole('button', { name: 'Import Pack', exact: true })).toBeEnabled();
  await modal.getByLabel('Select Pack File', { exact: true }).fill('app/include/empty.zip');
  await expect(modal.getByText(packagePreview[0].filename, { exact: true })).toHaveCount(0);
  await expect(modal.getByRole('button', { name: 'Import Pack', exact: true })).toBeDisabled();
  await modal.getByRole('button', { name: 'Inspect', exact: true }).click();
  await expect.poll(() => mock.inspections.length).toBe(2);
  await consumePackageResponse(page, mock.inspections[1], []);
  await expect(modal.getByText('Archive is empty or does not contain snippets.', { exact: true })).toBeVisible();
  await expect(modal.getByRole('button', { name: 'Import Pack', exact: true })).toBeDisabled();
  expect(mock.imports).toHaveLength(0);
});

for (const outcome of ['success', 'failure'] as const) {
  test(`package inspection ignores stale ${outcome} after the archive changes`, async ({ page }) => {
    const mock = await pendingPackage(page);
    await page.getByRole('button', { name: 'Import', exact: true }).click();
    const modal = packageModal(page);
    await modal.getByRole('button', { name: 'Inspect', exact: true }).click();
    await expect.poll(() => mock.inspections.length).toBe(1);
    await modal.getByLabel('Select Pack File', { exact: true }).fill('app/include/current.zip');
    await modal.getByRole('button', { name: 'Inspect', exact: true }).click();
    await expect.poll(() => mock.inspections.length).toBe(2);
    const current = [{ filename: 'app/include/current.py', file_size: 12, exists_locally: false }];
    await consumePackageResponse(page, mock.inspections[1], current);
    await expect(modal.getByText(current[0].filename, { exact: true })).toBeVisible();
    await consumePackageResponse(page, mock.inspections[0], outcome === 'success' ? packagePreview : 'obsolete inspection', outcome === 'failure');
    await expect(modal.getByText(current[0].filename, { exact: true })).toBeVisible();
    await expect(modal.getByText(packagePreview[0].filename, { exact: true })).toHaveCount(0);
    await expect(modal.getByText('Error: obsolete inspection', { exact: true })).toHaveCount(0);
    await expect(modal.getByRole('button', { name: 'Import Pack', exact: true })).toBeEnabled();
  });
}

for (const operation of ['inspect', 'export', 'import'] as const) {
  test(`package ${operation} failures are visible and do not refresh the navigator`, async ({ page }) => {
    const mock = await pendingPackage(page);
    await page.getByRole('button', { name: 'Import', exact: true }).click();
    const modal = packageModal(page);
    if (operation === 'import') {
      await modal.getByRole('button', { name: 'Inspect', exact: true }).click();
      await expect.poll(() => mock.inspections.length).toBe(1);
      await consumePackageResponse(page, mock.inspections[0], packagePreview);
      await expect(modal.getByRole('button', { name: 'Import Pack', exact: true })).toBeEnabled();
    }
    const before = mock.navigatorRequests;
    const button = operation === 'inspect' ? 'Inspect' : operation === 'export' ? 'Export Pack' : 'Import Pack';
    await modal.getByRole('button', { name: button, exact: true }).click();
    const requests = operation === 'inspect' ? mock.inspections : operation === 'export' ? mock.exports : mock.imports;
    await expect.poll(() => requests.length).toBe(1);
    await consumePackageResponse(page, requests[0], `${operation} rejected`, true);
    await expect(modal.getByText(`Error: ${operation} rejected`, { exact: true })).toBeVisible();
    expect(mock.navigatorRequests).toBe(before);
    if (operation === 'inspect') {
      await expect(modal.getByRole('button', { name: 'Import Pack', exact: true })).toBeDisabled();
    }
  });
}

test('Save As serializes the current buffer, replaces its tab and preserves another dirty buffer', async ({ page }) => {
  const mock = await pendingPackage(page);
  const source = mock.files[0];
  const other = mock.files[1];
  const target = source.replace('first.py', 'renamed.py');
  const editor = page.getByRole('textbox', { name: 'Source code editor', exact: true });
  const savesAs: Route[] = [];
  const saves: Route[] = [];
  const closes: Route[] = [];
  await page.route('**/code-editor/file/save-as', (route) => { savesAs.push(route); });
  await page.route('**/code-editor/file/save', (route) => { saves.push(route); });
  await page.route('**/code-editor/tabs/close', (route) => { closes.push(route); });
  await page.getByRole('button', { name: 'Close second.py', exact: true }).locator('..').click();
  await editor.fill('other_dirty = 2');
  await page.getByRole('button', { name: 'Close first.py', exact: true }).locator('..').click();
  await editor.fill('source_dirty = 3');
  page.once('dialog', (dialog) => dialog.accept(target));
  await page.getByRole('button', { name: 'Save As', exact: true }).click();
  await expect.poll(() => savesAs.length).toBe(1);
  expect(savesAs[0].request().postDataJSON()).toEqual({
    source_path: source, target_path: target, content: 'source_dirty = 3',
  });
  await expect(editor).toHaveAttribute('contenteditable', 'false');
  await expect(page.getByRole('button', { name: 'Saving As...', exact: true })).toBeDisabled();
  await page.getByRole('button', { name: 'Close second.py', exact: true }).locator('..').click();
  await page.getByRole('button', { name: 'Close first.py', exact: true }).click();
  await page.getByRole('button', { name: 'Save All', exact: true }).click();
  await page.keyboard.press('Control+s');
  await expect(editor).toHaveText('source_dirty = 3');
  expect(saves).toHaveLength(0);
  expect(closes).toHaveLength(0);
  mock.files[0] = target;
  await savesAs[0].fulfill({ json: { status: 'success', data: {
    status: 'saved_as', source_path: source, file_path: target, active_file: target,
    bytes_written: 16, diagnostics: [],
    tab: { file_path: target, title: 'renamed.py', content: 'source_dirty = 3', is_dirty: false, mode: 'python' },
  } } });
  await expect(page.getByRole('button', { name: 'Close renamed.py', exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Close first.py', exact: true })).toHaveCount(0);
  await expect(editor).toHaveAttribute('contenteditable', 'true');
  const firstBox = await page.getByRole('button', { name: 'Close renamed.py', exact: true }).boundingBox();
  const otherBox = await page.getByRole('button', { name: 'Close second.py', exact: true }).boundingBox();
  expect(firstBox!.x).toBeLessThan(otherBox!.x);
  await page.getByRole('button', { name: 'Close second.py', exact: true }).locator('..').click();
  await expect(editor).toHaveText('other_dirty = 2');
  await page.getByRole('button', { name: 'Close renamed.py', exact: true }).locator('..').click();
  await expect(editor).toHaveText('source_dirty = 3');
  await editor.fill('follow_up = 4');
  await page.getByRole('button', { name: 'Save', exact: true }).click();
  await expect.poll(() => saves.length).toBe(1);
  expect(saves[0].request().postDataJSON()).toEqual({ file_path: target, content: 'follow_up = 4' });
  await saves[0].fulfill({ json: { status: 'success', data: {
    status: 'saved', file_path: target, bytes_written: 13, diagnostics: [],
  } } });
  await expect(page.getByRole('button', { name: 'Save', exact: true })).toBeDisabled();
  expect(other).not.toBe(target);
});

for (const [status, code, message] of [
  [409, 'conflict', 'Save As destination already exists or is open'],
  [422, 'validation', 'Protected snippet package path'],
  [503, 'unavailable', 'File created; workspace state could not be saved. Original session retained.'],
] as const) {
  test(`Save As ${code} retains the source buffer and displays the failure`, async ({ page }) => {
    await pendingPackage(page);
    const editor = page.getByRole('textbox', { name: 'Source code editor', exact: true });
    await editor.fill('keep_dirty = 5');
    await page.route('**/code-editor/file/save-as', (route) => route.fulfill({
      status, json: { status: 'error', error: { code, message } },
    }));
    page.once('dialog', (dialog) => dialog.accept('app/include/new.py'));
    await page.getByRole('button', { name: 'Save As', exact: true }).click();
    await expect(page.getByText(`Save As error: ApiClientError: ${message}`, { exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Close first.py', exact: true })).toBeVisible();
    await expect(page.getByRole('button', { name: 'Close new.py', exact: true })).toHaveCount(0);
    await expect(editor).toHaveText('keep_dirty = 5');
    await expect(editor).toHaveAttribute('contenteditable', 'true');
    await expect(page.getByRole('button', { name: 'Save', exact: true })).toBeEnabled();
  });
}

test('cancelling Save As leaves the current buffer editable and sends no request', async ({ page }) => {
  await pendingPackage(page);
  const requests: Route[] = [];
  await page.route('**/code-editor/file/save-as', (route) => { requests.push(route); });
  const editor = page.getByRole('textbox', { name: 'Source code editor', exact: true });
  await editor.fill('keep_dirty = 5');
  page.once('dialog', (dialog) => dialog.dismiss());
  await page.getByRole('button', { name: 'Save As', exact: true }).click();
  await expect(editor).toHaveAttribute('contenteditable', 'true');
  await expect(editor).toHaveText('keep_dirty = 5');
  expect(requests).toHaveLength(0);
});

test('Save As is disabled without an active document', async ({ page }) => {
  await pendingPackage(page, []);
  await expect(page.getByRole('button', { name: 'Save As', exact: true })).toBeDisabled();
});

test('Save As waits for the current buffer session to finish synchronizing', async ({ page }) => {
  const mock = await pendingPackage(page);
  const sessions: Route[] = [];
  const savesAs: Route[] = [];
  await page.route('**/code-editor/session', (route) => {
    const body = route.request().postDataJSON();
    if (body.tabs.some((tab: { content: string }) => tab.content === 'awaiting_sync = 1')) sessions.push(route);
    else return route.fallback();
  });
  await page.route('**/code-editor/file/save-as', (route) => { savesAs.push(route); });
  const editor = page.getByRole('textbox', { name: 'Source code editor', exact: true });
  await editor.fill('awaiting_sync = 1');
  await expect.poll(() => sessions.length).toBe(1);
  const source = mock.files[0];
  const target = source.replace('first.py', 'synced.py');
  page.once('dialog', (dialog) => dialog.accept(target));
  await page.getByRole('button', { name: 'Save As', exact: true }).click();
  await expect(editor).toHaveAttribute('contenteditable', 'false');
  expect(savesAs).toHaveLength(0);
  await sessions[0].fulfill({ json: { status: 'success', data: {} } });
  await expect.poll(() => savesAs.length).toBe(1);
  expect(savesAs[0].request().postDataJSON().content).toBe('awaiting_sync = 1');
  await savesAs[0].fulfill({ json: { status: 'success', data: {
    status: 'saved_as', source_path: source, file_path: target, active_file: target,
    bytes_written: 17, diagnostics: [],
    tab: { file_path: target, title: 'synced.py', content: 'awaiting_sync = 1', is_dirty: false, mode: 'python' },
  } } });
  await expect(page.getByRole('button', { name: 'Close synced.py', exact: true })).toBeVisible();
  await expect(editor).toHaveAttribute('contenteditable', 'true');
  // Finish the final snapshot queued after the command completed.
  await expect.poll(() => sessions.length).toBe(2);
  expect(sessions[1].request().postDataJSON().active_file).toBe(target);
  await sessions[1].fulfill({ json: { status: 'success', data: {} } });
});

test('disk reload confirms a dirty buffer and cancellation preserves it', async ({ page }) => {
  const mock = await mockEditor(page);
  const requests: unknown[] = [];
  await page.route('**/code-editor/file/reload', route => {
    requests.push(route.request().postDataJSON());
    const original = mock.snapshot().open_tabs[0];
    return route.fulfill({ json: { status: 'success', data: { active_file: original.file_path,
      tab: { ...original, content: 'external_disk = 9', is_dirty: false } } } });
  });
  await page.goto('/codeeditor');
  const editor = page.getByRole('textbox', { name: 'Source code editor', exact: true });
  await editor.fill('keep_dirty = 1');
  page.once('dialog', dialog => dialog.dismiss());
  await page.getByRole('button', { name: 'Reload from disk', exact: true }).click();
  expect(requests).toEqual([]);
  await expect(editor).toHaveText('keep_dirty = 1');
  page.once('dialog', dialog => dialog.accept());
  await page.getByRole('button', { name: 'Reload from disk', exact: true }).click();
  await expect(editor).toHaveText('external_disk = 9');
  expect(requests).toEqual([{ file_path: mock.snapshot().active_file, discard_dirty: true }]);
  await expect(page.getByRole('button', { name: 'Save', exact: true })).toBeDisabled();
});

test('complete search controls send flags and directory scope', async ({ page }) => {
  await mockEditor(page);
  const searches: unknown[] = [];
  await page.route('**/code-editor/search', route => {
    searches.push(route.request().postDataJSON());
    return route.fulfill({ json: { status: 'success', data: [] } });
  });
  await page.goto('/codeeditor');
  await page.getByRole('button', { name: 'Search', exact: true }).click();
  await page.getByPlaceholder('Find in snippets...').fill('Alpha');
  await page.getByLabel('Case sensitive', { exact: true }).check();
  await page.getByLabel('Regular expression', { exact: true }).check();
  await page.getByLabel('Whole word', { exact: true }).check();
  await page.getByRole('textbox', { name: 'Search directory' }).fill('app/include/user');
  await page.getByRole('button', { name: 'Find', exact: true }).click();
  await expect.poll(() => searches.length).toBe(1);
  expect(searches[0]).toEqual({ query: 'Alpha', case_sensitive: true, regex: true, whole_word: true, search_dir: 'app/include/user' });
});

test('import repair exposes ambiguity and applies an explicit selection', async ({ page }) => {
  await mockEditor(page, 'value = Shared()');
  const requests: Array<{ selections: Record<string, string> }> = [];
  await page.route('**/code-editor/imports/repair', route => {
    const body = route.request().postDataJSON();
    requests.push(body);
    return route.fulfill({ json: { status: 'success', data: Object.keys(body.selections).length ? {
      content: 'from app.include.user.first import Shared\nvalue = Shared()', added: ['from app.include.user.first import Shared'], unresolved: [],
    } : { content: body.content, added: [], unresolved: [{ symbol: 'Shared', candidates: ['app.include.user.first', 'app.include.user.second'] }] } } });
  });
  await page.goto('/codeeditor');
  await page.getByRole('button', { name: 'Fix imports', exact: true }).click();
  await page.getByRole('combobox', { name: 'Import Shared', exact: true }).selectOption('app.include.user.first');
  await page.getByRole('button', { name: 'Apply import selections', exact: true }).click();
  await expect(page.getByRole('textbox', { name: 'Source code editor', exact: true })).toContainText('from app.include.user.first import Shared');
  expect(requests[1].selections).toEqual({ Shared: 'app.include.user.first' });
});

test('import repair cannot replace a buffer changed while its response was pending', async ({ page }) => {
  await mockEditor(page, 'value = Missing()');
  const pending: Route[] = [];
  await page.route('**/code-editor/imports/repair', route => { pending.push(route); });
  await page.goto('/codeeditor');
  await page.getByRole('button', { name: 'Fix imports', exact: true }).click();
  await expect.poll(() => pending.length).toBe(1);
  const editor = page.getByRole('textbox', { name: 'Source code editor', exact: true });
  await editor.fill('newer_buffer = 1');
  await pending[0].fulfill({ json: { status: 'success', data: { content: 'old_repair = 2', added: [], unresolved: [] } } });
  await expect(page.getByRole('alert')).toHaveText('Buffer changed; run import repair again.');
  await expect(editor).toHaveText('newer_buffer = 1');
});

test('typed catalogue supplies symbol and member autocomplete', async ({ page }) => {
  await mockEditor(page);
  await page.route('**/code-editor/catalogue/symbols', route => route.fulfill({ json: { status: 'success', data: [
    { name: 'QuantumMarker', module: 'app.include.user.marker', file_path: 'app/include/user/marker.py', kind: 'class', members: ['member_value'] },
  ] } }));
  await page.goto('/codeeditor');
  const editor = page.getByRole('textbox', { name: 'Source code editor', exact: true });
  await expect(editor).toHaveText('value = 1\n');
  await editor.fill('QuantumMar');
  await editor.press('End');
  await editor.press('Control+Space');
  await expect(page.getByRole('option', { name: /QuantumMarker/ })).toBeVisible();
  await editor.press('Escape');
  await editor.fill('QuantumMarker.mem');
  await editor.press('Control+Space');
  await expect(page.getByRole('option', { name: /member_value/ })).toBeVisible();
  await editor.press('Tab');
  await expect(editor).toHaveText('QuantumMarker.member_value');
});

test('compilation shows progress and cancellation remains pending until terminal delivery', async ({ page }) => {
  await mockEditor(page);
  let state = { job_id: 'editor-cancel', status: 'RUNNING', progress: 25, message: 'Compiling Python source', results: [], cancellation_requested: false };
  const bodies: unknown[] = [];
  let submitted = false;
  await page.route('**/code-editor/compilations*', route => {
    if (route.request().method() === 'POST') { bodies.push(route.request().postDataJSON()); submitted = true; }
    return route.fulfill({ json: { status: 'success', data: submitted ? state : null } });
  });
  await page.route('**/code-editor/compilations/editor-cancel/cancel', route => {
    state = { ...state, cancellation_requested: true, message: 'Cancellation requested; waiting for current import to return' };
    return route.fulfill({ json: { status: 'success', data: state } });
  });
  await page.goto('/codeeditor');
  await page.getByRole('button', { name: 'Compile', exact: true }).click();
  await expect(page.getByRole('progressbar', { name: 'Compilation progress' })).toHaveAttribute('value', '25');
  await page.getByRole('button', { name: 'Cancel compilation', exact: true }).click();
  await expect(page.getByRole('region', { name: 'Editor commands' }).getByRole('status')).toContainText('waiting for current import');
  await expect(page.getByRole('button', { name: 'Cancel compilation', exact: true })).toBeDisabled();
  state = { ...state, status: 'CANCELLED', message: 'Cancelled' };
  await expect(page.getByRole('region', { name: 'Editor commands' }).getByRole('status')).toContainText('CANCELLED');
  expect(bodies[0]).toMatchObject({ scope: 'file', content: 'value = 1\n' });
});

test('compilation diagnostics restore after reconnect', async ({ page }) => {
  await mockEditor(page, 'broken = missing_name');
  await page.route('**/code-editor/compilations', route => route.fulfill({ json: { status: 'success', data: {
    job_id: 'editor-restored', status: 'COMPLETED', progress: 100, message: 'Restored diagnostics', cancellation_requested: false,
    results: [{ file: 'app/include/blocks/indicators/custom/example.py', success: false,
      errors: [{ line: 1, column: 10, severity: 'error', message: 'Restored unresolved symbol' }] }],
  } } }));
  await page.goto('/codeeditor');
  await expect(page.locator('.cm-lintRange-error')).toBeVisible();
  await page.reload();
  await expect(page.locator('.cm-lintRange-error')).toBeVisible();
  await expect(page.getByRole('status')).toContainText('editor-restored');
});

test('package compilation, compile all and extension reload use distinct scopes', async ({ page }) => {
  await mockEditor(page);
  const requests: Array<{ scope: string; file_path?: string }> = [];
  await page.route('**/code-editor/compilations', route => {
    if (route.request().method() === 'GET') return route.fulfill({ json: { status: 'success', data: null } });
    requests.push(route.request().postDataJSON());
    return route.fulfill({ json: { status: 'success', data: { job_id: `editor-${requests.length}`, status: 'COMPLETED', progress: 100, message: '', results: [], cancellation_requested: false } } });
  });
  await page.goto('/codeeditor');
  page.once('dialog', dialog => dialog.accept('app/include/user/package'));
  await page.getByRole('button', { name: 'Compile package/plugin', exact: true }).click();
  await expect.poll(() => requests.length).toBe(1);
  await page.getByRole('button', { name: 'Compile all', exact: true }).click();
  await expect.poll(() => requests.length).toBe(2);
  await page.getByRole('button', { name: 'Reload extensions', exact: true }).click();
  await expect.poll(() => requests.length).toBe(3);
  expect(requests.map(request => request.scope)).toEqual(['package', 'all', 'registered']);
  expect(requests[0].file_path).toBe('app/include/user/package');
});

test('builtin protection makes the buffer read only and ownership filtering reaches the service', async ({ page }) => {
  await mockEditor(page);
  const filters: string[] = [];
  await page.route('**/code-editor/navigator*', route => {
    filters.push(new URL(route.request().url()).searchParams.get('ownership') ?? 'all');
    return route.fulfill({ json: { status: 'success', data: {
      id: 'app/include', name: 'snippets', type: 'directory', children: [{
        id: 'app/include/blocks/indicators/custom/example.py', name: 'example.py', type: 'file', protected: true, ownership: 'builtin',
      }],
    } } });
  });
  await page.goto('/codeeditor');
  await expect(page.getByRole('textbox', { name: 'Source code editor', exact: true })).toHaveAttribute('contenteditable', 'false');
  await page.getByRole('combobox', { name: 'Navigator ownership', exact: true }).selectOption('builtin');
  await expect.poll(() => filters.includes('builtin')).toBe(true);
});

test('code export creation uses the selected supported format', async ({ page }) => {
  await mockEditor(page);
  const requests: unknown[] = [];
  await page.route('**/code-editor/export-templates', route => {
    requests.push(route.request().postDataJSON());
    return route.fulfill({ json: { status: 'success', data: { file_path: 'app/include/user/code_templates/pseudocode/new.txt.tpl', status: 'saved', bytes_written: 10, diagnostics: [] } } });
  });
  await page.goto('/codeeditor');
  await page.getByRole('combobox', { name: 'Export template format' }).selectOption('pseudocode');
  page.once('dialog', dialog => dialog.accept('app/include/user/code_templates/pseudocode/new.txt.tpl'));
  await page.getByRole('button', { name: 'Create export template', exact: true }).click();
  await expect.poll(() => requests.length).toBe(1);
  expect(requests[0]).toEqual({ source_paths: ['app/include/blocks/indicators/custom/example.py'], target_path: 'app/include/user/code_templates/pseudocode/new.txt.tpl', format_id: 'pseudocode' });
});

test('late reconnect diagnostics cannot overwrite a newly submitted compilation', async ({ page }) => {
  await mockEditor(page);
  const initial: Route[] = [];
  await page.route('**/code-editor/compilations', route => {
    if (route.request().method() === 'GET') { initial.push(route); return; }
    return route.fulfill({ json: { status: 'success', data: { job_id: 'editor-new', status: 'COMPLETED', progress: 100, message: 'New result', results: [], cancellation_requested: false } } });
  });
  await page.goto('/codeeditor');
  await expect.poll(() => initial.length).toBeGreaterThan(0);
  await page.getByRole('button', { name: 'Compile', exact: true }).click();
  const status = page.getByRole('region', { name: 'Editor commands' }).getByRole('status');
  await expect(status).toContainText('editor-new');
  for (const route of initial) await route.fulfill({ json: { status: 'success', data: { job_id: 'editor-old', status: 'COMPLETED', progress: 100, message: 'Old result', results: [], cancellation_requested: false } } });
  await expect(status).toContainText('editor-new');
});

test('missing-file recovery warning is visible and the retained buffer stays editable', async ({ page }) => {
  await mockEditor(page);
  await page.route('**/code-editor/init', route => route.fulfill({ json: { status: 'success', data: {
    status: 'ready', active_file: 'app/include/user/missing.py', layout: {},
    open_tabs: [{ file_path: 'app/include/user/missing.py', title: 'missing.py', content: 'recover_me = 1', is_dirty: true, mode: 'python' }],
    recovery_warnings: ['Missing file: app/include/user/missing.py; buffer retained for Save As'],
  } } }));
  await page.goto('/codeeditor');
  await expect(page.getByRole('textbox', { name: 'Source code editor', exact: true })).toHaveText('recover_me = 1');
  await expect(page.getByText('Missing file: app/include/user/missing.py; buffer retained for Save As', { exact: true })).toBeVisible();
  await expect(page.getByRole('button', { name: 'Save As', exact: true })).toBeEnabled();
});

test('corrupted-session recovery fails visibly without writing a replacement session', async ({ page }) => {
  await mockEditor(page);
  const writes: Route[] = [];
  await page.route('**/code-editor/init', route => route.fulfill({ status: 503, json: { status: 'error', error: { code: 'internal', message: 'Invalid editor stored state' } } }));
  await page.route('**/code-editor/session', route => { writes.push(route); });
  await page.goto('/codeeditor');
  await expect(page.getByText('Session error: ApiClientError: Invalid editor stored state', { exact: true })).toBeVisible();
  expect(writes).toHaveLength(0);
  await expect(page.getByRole('button', { name: 'Save As', exact: true })).toBeDisabled();
});

test('template UI includes order subtypes and indicator-derived signal mappings', async ({ page }) => {
  const mock = await mockEditor(page);
  await page.route('**/code-editor/catalogue/indicators', route => route.fulfill({ json: { status: 'success', data: [
    { identity: 'app/include/blocks/indicators/trend/sma.py', file_path: 'app/include/blocks/indicators/trend/sma.py', name: 'SMA', outputs: ['value'], parameters: { period: 14 }, protected: true },
  ] } }));
  const previews: Array<{ indicator?: string; order_action_type?: string }> = [];
  await page.route('**/code-editor/templates/render', route => {
    previews.push(route.request().postDataJSON());
    return route.fulfill({ json: { status: 'success', data: { content: 'class NewSnippet: pass', file_path: 'app/include/user/new_snippet.py' } } });
  });
  await page.goto('/codeeditor');
  await page.getByRole('button', { name: 'Create from Template', exact: true }).click();
  await page.getByRole('button', { name: /Blocks Order Order execution/ }).click();
  await page.getByRole('combobox', { name: 'Order action subtype' }).selectOption('Close');
  await expect.poll(() => previews.some(request => request.order_action_type === 'Close')).toBe(true);
  await page.getByRole('button', { name: /Blocks Signal Trading signals/ }).click();
  await page.getByRole('combobox', { name: 'Signal indicator' }).selectOption('app/include/blocks/indicators/trend/sma.py');
  await expect.poll(() => previews.some(request => request.indicator?.endsWith('/sma.py'))).toBe(true);
  await page.getByRole('button', { name: 'Create & Open', exact: true }).click();
  await expect.poll(() => mock.creates.length).toBe(1);
  expect(mock.creates[0]).toMatchObject({ template_type: 'BlocksSignal', indicator: 'app/include/blocks/indicators/trend/sma.py' });
});

test('restored diagnostics are only attached to the matching source version', async ({ page }) => {
  await mockEditor(page, 'newer_buffer = 1');
  const original = 'broken = missing_name';
  const path = 'app/include/blocks/indicators/custom/example.py';
  await page.route('**/code-editor/compilations', route => route.fulfill({ json: { status: 'success', data: {
    job_id: 'editor-versioned', status: 'COMPLETED', progress: 100, message: 'Restored result', cancellation_requested: false,
    source_hashes: { [path]: createHash('sha256').update(original).digest('hex') },
    results: [{ file: path, success: false, errors: [{ line: 1, column: 10, severity: 'error', message: 'Old unresolved symbol' }] }],
  } } }));
  await page.goto('/codeeditor');
  await expect(page.getByText('Diagnostics are from an earlier source version. Compile the current buffer to refresh them.', { exact: true })).toBeVisible();
  await expect(page.locator('.cm-lintRange-error')).toHaveCount(0);
  await page.getByRole('textbox', { name: 'Source code editor', exact: true }).fill(original);
  await expect(page.locator('.cm-lintRange-error')).toBeVisible();
});
