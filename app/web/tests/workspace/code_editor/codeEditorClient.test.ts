import { describe, expect, it, vi } from 'vitest';
import { createCodeEditorClient, type IndicatorConfigDto, type IndicatorTestResultDto } from '../../../workspaces/code_editor/codeEditorClient';

function mockResponse(data: unknown) {
  return () => Promise.resolve(new Response(JSON.stringify({ status: 'success', data })));
}

describe('codeEditorClient', () => {
  it('maps reload, import selection, job lifecycle and export authoring contracts', async () => {
    const fetchFn = vi.fn().mockImplementation(mockResponse({}));
    const client = createCodeEditorClient({ fetchFn, baseUrl: '/api/v1' });
    await client.reloadDisk('app/extend/user/a.py', true);
    expect(fetchFn).toHaveBeenLastCalledWith('/api/v1/code-editor/file/reload', expect.objectContaining({ body: JSON.stringify({ file_path: 'app/extend/user/a.py', discard_dirty: true }) }));
    await client.repairImports('app/extend/user/a.py', '', { Symbol: 'app.include.user.source' });
    expect(fetchFn).toHaveBeenLastCalledWith('/api/v1/code-editor/imports/repair', expect.objectContaining({ body: JSON.stringify({ file_path: 'app/extend/user/a.py', content: '', selections: { Symbol: 'app.include.user.source' } }) }));
    await client.startCompilation('package', 'app/extend/user/package');
    expect(fetchFn).toHaveBeenLastCalledWith('/api/v1/code-editor/compilations', expect.objectContaining({ body: JSON.stringify({ scope: 'package', file_path: 'app/extend/user/package' }) }));
    await client.cancelCompilation('editor-1');
    expect(fetchFn).toHaveBeenLastCalledWith('/api/v1/code-editor/compilations/editor-1/cancel', expect.objectContaining({ method: 'POST' }));
    await client.compilation('editor-1');
    expect(fetchFn).toHaveBeenLastCalledWith('/api/v1/code-editor/compilations?job_id=editor-1', expect.objectContaining({ method: 'GET' }));
    await client.createExportTemplate(['app/extend/user/a.py'], 'app/extend/user/new.py.tpl', 'python');
    expect(fetchFn).toHaveBeenLastCalledWith('/api/v1/code-editor/export-templates', expect.objectContaining({ body: JSON.stringify({ source_paths: ['app/extend/user/a.py'], target_path: 'app/extend/user/new.py.tpl', format_id: 'python' }) }));
  });
  it('sends the exact Save As source, destination and empty buffer', async () => {
    const result = {
      status: 'saved_as', source_path: 'app/extend/source.py', file_path: 'app/extend/new.py',
      active_file: 'app/extend/new.py', bytes_written: 0, diagnostics: [],
      tab: { file_path: 'app/extend/new.py', title: 'new.py', content: '', mode: 'python', is_dirty: false },
    };
    const fetchFn = vi.fn().mockImplementation(mockResponse(result));
    const client = createCodeEditorClient({ fetchFn, baseUrl: '/api/v1' });
    expect(await client.saveAsFile('app/extend/source.py', 'app/extend/new.py', '')).toEqual(result);
    expect(fetchFn).toHaveBeenCalledExactlyOnceWith('/api/v1/code-editor/file/save-as', expect.objectContaining({
      method: 'POST', body: JSON.stringify({ source_path: 'app/extend/source.py', target_path: 'app/extend/new.py', content: '' }),
    }));
  });
  it('retains typed diagnostic variants and nullable reference differences', async () => {
    const result: IndicatorTestResultDto = {
      test_id: 'diagnostics', status: 'success', symbol: 'EURUSD', timeframe: 'H1',
      bars_calculated: 1, candlesticks: [], indicator_plots: [{ time: 1 }],
      table_rows: [{ time: 1, open: 1, high: 2, low: 0, close: 1, indicator_val: null, diff: null }],
      discrepancies: [
        { bar: 0, time: 1, calc: 2, ref: 1, diff: 1 },
        { bar: 0, time: 1, series: 'value', type: 'NonFiniteValue', message: 'gap' },
        { bar: 0, type: 'CodeEditorError', message: 'execution failed' },
      ],
    };
    const fetchFn = vi.fn().mockImplementation(mockResponse(result));
    const client = createCodeEditorClient({ fetchFn, baseUrl: '/api/v1' });
    expect(await client.runIndicatorTest({ indicatorName: 'SMA' })).toEqual(result);
  });

  it('retains complete saved and loaded indicator configurations', async () => {
    const config: IndicatorConfigDto = {
      test_id: 'saved', indicator_name: 'MACD', symbol: 'EURUSD', timeframe: 'H1',
      params: { fast_period: 12, slow_period: 26 }, bars_to_reserve: 0,
      bar_count: 2, reference_values: null, saved_name: 'Review',
    };
    const saved = { status: 'saved' as const, config_id: config.test_id, config };
    const loaded = { status: 'loaded' as const, config };
    const fetchFn = vi.fn().mockImplementationOnce(mockResponse(saved)).mockImplementationOnce(mockResponse(loaded));
    const client = createCodeEditorClient({ fetchFn, baseUrl: '/api/v1' });
    expect(await client.saveTestConfig('saved', 'Review')).toEqual(saved);
    expect(await client.loadTestConfig('saved')).toEqual(loaded);
    expect(fetchFn).toHaveBeenLastCalledWith('/api/v1/code-editor/indicator-test/load?config_id=saved', expect.objectContaining({ method: 'GET' }));
  });

  it('calls initWorkspace with correct GET endpoint', async () => {
    const fetchFn = vi.fn().mockImplementation(
      mockResponse({
        status: 'initialized',
        active_file: 'app/extend/example.py',
        open_tabs: [],
        layout: { navigator_visible: true, split_mode: 'none', bottom_panel: 'problems' },
      }),
    );

    const client = createCodeEditorClient({ fetchFn, baseUrl: '/api/v1' });
    const res = await client.initWorkspace();

    expect(fetchFn).toHaveBeenCalledWith('/api/v1/code-editor/init', expect.objectContaining({ method: 'GET' }));
    expect(res.status).toBe('initialized');
    expect(res.active_file).toBe('app/extend/example.py');
  });

  it('calls fetchNavigator with optional rootDir query param', async () => {
    const fetchFn = vi
      .fn()
      .mockImplementation(mockResponse({ id: 'root', name: 'snippets', type: 'directory', children: [] }));

    const client = createCodeEditorClient({ fetchFn, baseUrl: '/api/v1' });
    const res = await client.fetchNavigator('app/extend');

    expect(fetchFn).toHaveBeenCalledWith(
      '/api/v1/code-editor/navigator?root_dir=app%2Fextend',
      expect.objectContaining({ method: 'GET' }),
    );
    expect(res.id).toBe('root');
  });

  it('calls openTab and closeTab with proper payloads', async () => {
    const fetchFn = vi.fn().mockImplementation(
      mockResponse({
        status: 'opened',
        tab: { file_path: 'test.py', title: 'test.py', is_dirty: false, content: '', mode: 'python' },
        active_file: 'test.py',
      }),
    );

    const client = createCodeEditorClient({ fetchFn, baseUrl: '/api/v1' });
    await client.openTab('test.py', 'python');

    expect(fetchFn).toHaveBeenCalledWith(
      '/api/v1/code-editor/tabs/open',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ file_path: 'test.py', mode: 'python' }),
      }),
    );

    await client.closeTab('test.py', true);
    expect(fetchFn).toHaveBeenCalledWith(
      '/api/v1/code-editor/tabs/close',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ file_path: 'test.py', force: true }),
      }),
    );
  });

  it('calls saveFile, newFile, and compileFile', async () => {
    const fetchFn = vi
      .fn()
      .mockImplementation(mockResponse({ status: 'saved', file_path: 'test.py', diagnostics: [] }));

    const client = createCodeEditorClient({ fetchFn, baseUrl: '/api/v1' });
    await client.saveFile('test.py', 'x = 1\n');

    expect(fetchFn).toHaveBeenCalledWith(
      '/api/v1/code-editor/file/save',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ file_path: 'test.py', content: 'x = 1\n' }),
      }),
    );

    await client.newFile('test2.py', '# new');
    expect(fetchFn).toHaveBeenCalledWith(
      '/api/v1/code-editor/file/new',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ file_path: 'test2.py', content: '# new' }),
      }),
    );

    await client.compileFile('test2.py', '# new');
    expect(fetchFn).toHaveBeenCalledWith(
      '/api/v1/code-editor/compile',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ file_path: 'test2.py', content: '# new' }),
      }),
    );
  });

  it('calls template listing and creation endpoints', async () => {
    const fetchFn = vi.fn().mockImplementation(
      mockResponse([
        {
          template_id: 'BlocksIndicators',
          name: 'Indicator Block',
          description: '',
          category: 'Blocks',
          default_filename: 'Indicator.py',
          target_subdir: 'indicators',
        },
      ]),
    );

    const client = createCodeEditorClient({ fetchFn, baseUrl: '/api/v1' });
    const list = await client.listTemplates();
    expect(list.length).toBe(1);

    await client.createFromTemplate('BlocksIndicators', 'CustomIndy', 'Blocks');
    expect(fetchFn).toHaveBeenCalledWith(
      '/api/v1/code-editor/templates/create',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ template_type: 'BlocksIndicators', name: 'CustomIndy', category: 'Blocks' }),
      }),
    );
  });

  it('calls import/export endpoints with resolution rules', async () => {
    const fetchFn = vi
      .fn()
      .mockImplementation(
        mockResponse({ status: 'success', archive_path: 'export.zip', file_count: 2, files: ['a.py', 'b.py'] }),
      );

    const client = createCodeEditorClient({ fetchFn, baseUrl: '/api/v1' });
    await client.exportPack(['a.py', 'b.py'], 'export.zip', { title: 'Pack' });
    expect(fetchFn).toHaveBeenCalledWith(
      '/api/v1/code-editor/import-export/export',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ file_paths: ['a.py', 'b.py'], archive_path: 'export.zip', metadata: { title: 'Pack' } }),
      }),
    );

    await client.inspectPack('export.zip');
    expect(fetchFn).toHaveBeenCalledWith(
      '/api/v1/code-editor/import-export/inspect',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ archive_path: 'export.zip' }),
      }),
    );

    await client.importPack('export.zip', { 'a.py': 'overwrite' });
    expect(fetchFn).toHaveBeenCalledWith(
      '/api/v1/code-editor/import-export/import',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ archive_path: 'export.zip', resolution_rules: { 'a.py': 'overwrite' } }),
      }),
    );
  });

  it('runs indicator tester with parameter configuration', async () => {
    const fetchFn = vi.fn().mockImplementation(
      mockResponse({
        test_id: 'test-123',
        status: 'success',
        symbol: 'EURUSD',
        timeframe: 'H1',
        bars_calculated: 100,
        candlesticks: [],
        indicator_plots: [],
        table_rows: [],
        discrepancies: [],
      }),
    );

    const client = createCodeEditorClient({ fetchFn, baseUrl: '/api/v1' });
    const res = await client.runIndicatorTest({
      indicatorName: 'SimpleMovingAverage',
      symbol: 'EURUSD',
      timeframe: 'H1',
      params: { period: 20 },
      barsToReserve: 50,
      barCount: 150,
    });

    expect(res.test_id).toBe('test-123');
    expect(fetchFn).toHaveBeenCalledWith(
      '/api/v1/code-editor/indicator-test/run',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          indicator_name: 'SimpleMovingAverage',
          symbol: 'EURUSD',
          timeframe: 'H1',
          params: { period: 20 },
          bars_to_reserve: 50,
          bar_count: 150,
        }),
      }),
    );
  });
  it.each([
    ['omitted', {}, null],
    ['null', { params: null }, null],
    ['empty', { params: {} }, {}],
    ['period', { params: { period: 20 } }, { period: 20 }],
    [
      'non-period',
      { params: { fast_period: 12, slow_period: 26 } },
      { fast_period: 12, slow_period: 26 },
    ],
  ] as const)('preserves %s indicator parameters and transport defaults', async (_label, input, expected) => {
    const fetchFn = vi.fn().mockImplementation(mockResponse({}));
    const client = createCodeEditorClient({ fetchFn, baseUrl: '/api/v1' });

    await client.runIndicatorTest({ indicatorName: 'MACD', ...input });

    expect(fetchFn).toHaveBeenCalledExactlyOnceWith(
      '/api/v1/code-editor/indicator-test/run',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          indicator_name: 'MACD',
          symbol: 'EURUSD',
          timeframe: 'H1',
          params: expected,
          bars_to_reserve: 50,
          bar_count: 150,
        }),
      }),
    );
  });

  it.each([{ references: [1.1, 1.2] }, { references: [] }])(
    'preserves explicit test settings and references $references',
    async ({ references }) => {
      const fetchFn = vi.fn().mockImplementation(mockResponse({}));
      const client = createCodeEditorClient({ fetchFn, baseUrl: '/api/v1' });

      await client.runIndicatorTest({
        indicatorName: 'RSI',
        symbol: 'GBPUSD',
        timeframe: 'M5',
        params: {},
        barsToReserve: 0,
        barCount: 2,
        referenceValues: references,
      });

      expect(fetchFn).toHaveBeenCalledExactlyOnceWith(
        '/api/v1/code-editor/indicator-test/run',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({
            indicator_name: 'RSI',
            symbol: 'GBPUSD',
            timeframe: 'M5',
            params: {},
            bars_to_reserve: 0,
            bar_count: 2,
            reference_values: references,
          }),
        }),
      );
    },
  );

  it('passes the indicator category to both preview and creation', async () => {
    const fetchFn = vi
      .fn()
      .mockImplementation(mockResponse({ file_path: 'app/include/blocks/indicators/research/research_ma.py', content: '' }));
    const client = createCodeEditorClient({ fetchFn, baseUrl: '/api/v1' });
    await client.renderTemplatePreview('BlocksIndicators', 'ResearchMA', 'research');
    expect(fetchFn).toHaveBeenLastCalledWith(
      '/api/v1/code-editor/templates/render',
      expect.objectContaining({
        body: JSON.stringify({ template_id: 'BlocksIndicators', name: 'ResearchMA', category: 'research' }),
      }),
    );
    await client.createFromTemplate('BlocksIndicators', 'ResearchMA', 'research');
    expect(fetchFn).toHaveBeenLastCalledWith(
      '/api/v1/code-editor/templates/create',
      expect.objectContaining({
        body: JSON.stringify({ template_type: 'BlocksIndicators', name: 'ResearchMA', category: 'research' }),
      }),
    );
  });
});
