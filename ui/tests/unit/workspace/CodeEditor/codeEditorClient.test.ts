import { describe, expect, it, vi } from 'vitest';
import { createCodeEditorClient } from '../../../../app/workspace/CodeEditor/codeEditorClient';

function mockResponse(data: unknown) {
  return () => Promise.resolve(new Response(JSON.stringify({ status: 'success', data })));
}

describe('codeEditorClient', () => {
  it('calls initWorkspace with correct GET endpoint', async () => {
    const fetchFn = vi.fn().mockImplementation(
      mockResponse({
        status: 'initialized',
        active_file: 'app/include/snippets/example.py',
        open_tabs: [],
        layout: { navigator_visible: true, split_mode: 'none', bottom_panel: 'problems' },
      })
    );

    const client = createCodeEditorClient({ fetchFn, baseUrl: '/api/v1' });
    const res = await client.initWorkspace();

    expect(fetchFn).toHaveBeenCalledWith(
      '/api/v1/code-editor/init',
      expect.objectContaining({ method: 'GET' })
    );
    expect(res.status).toBe('initialized');
    expect(res.active_file).toBe('app/include/snippets/example.py');
  });

  it('calls fetchNavigator with optional rootDir query param', async () => {
    const fetchFn = vi.fn().mockImplementation(
      mockResponse({ id: 'root', name: 'snippets', type: 'directory', children: [] })
    );

    const client = createCodeEditorClient({ fetchFn, baseUrl: '/api/v1' });
    const res = await client.fetchNavigator('app/include/snippets');

    expect(fetchFn).toHaveBeenCalledWith(
      '/api/v1/code-editor/navigator?root_dir=app%2Finclude%2Fsnippets',
      expect.objectContaining({ method: 'GET' })
    );
    expect(res.id).toBe('root');
  });

  it('calls openTab and closeTab with proper payloads', async () => {
    const fetchFn = vi.fn().mockImplementation(
      mockResponse({
        status: 'opened',
        tab: { file_path: 'test.py', title: 'test.py', is_dirty: false, content: '', mode: 'python' },
        active_file: 'test.py',
      })
    );

    const client = createCodeEditorClient({ fetchFn, baseUrl: '/api/v1' });
    await client.openTab('test.py', 'python');

    expect(fetchFn).toHaveBeenCalledWith(
      '/api/v1/code-editor/tabs/open',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ file_path: 'test.py', mode: 'python' }),
      })
    );

    await client.closeTab('test.py', true);
    expect(fetchFn).toHaveBeenCalledWith(
      '/api/v1/code-editor/tabs/close',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ file_path: 'test.py', force: true }),
      })
    );
  });

  it('calls saveFile, newFile, and compileFile', async () => {
    const fetchFn = vi.fn().mockImplementation(
      mockResponse({ status: 'saved', file_path: 'test.py', diagnostics: [] })
    );

    const client = createCodeEditorClient({ fetchFn, baseUrl: '/api/v1' });
    await client.saveFile('test.py', 'x = 1\n');

    expect(fetchFn).toHaveBeenCalledWith(
      '/api/v1/code-editor/file/save',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ file_path: 'test.py', content: 'x = 1\n' }),
      })
    );

    await client.newFile('test2.py', '# new');
    expect(fetchFn).toHaveBeenCalledWith(
      '/api/v1/code-editor/file/new',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ file_path: 'test2.py', content: '# new' }),
      })
    );

    await client.compileFile('test2.py', '# new');
    expect(fetchFn).toHaveBeenCalledWith(
      '/api/v1/code-editor/compile',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ file_path: 'test2.py', content: '# new' }),
      })
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
      ])
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
      })
    );
  });

  it('calls import/export endpoints with resolution rules', async () => {
    const fetchFn = vi.fn().mockImplementation(
      mockResponse({ status: 'success', archive_path: 'export.zip', file_count: 2, files: ['a.py', 'b.py'] })
    );

    const client = createCodeEditorClient({ fetchFn, baseUrl: '/api/v1' });
    await client.exportPack(['a.py', 'b.py'], 'export.zip', { title: 'Pack' });
    expect(fetchFn).toHaveBeenCalledWith(
      '/api/v1/code-editor/import-export/export',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ file_paths: ['a.py', 'b.py'], archive_path: 'export.zip', metadata: { title: 'Pack' } }),
      })
    );

    await client.inspectPack('export.zip');
    expect(fetchFn).toHaveBeenCalledWith(
      '/api/v1/code-editor/import-export/inspect',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ archive_path: 'export.zip' }),
      })
    );

    await client.importPack('export.zip', { 'a.py': 'overwrite' });
    expect(fetchFn).toHaveBeenCalledWith(
      '/api/v1/code-editor/import-export/import',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ archive_path: 'export.zip', resolution_rules: { 'a.py': 'overwrite' } }),
      })
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
      })
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
      })
    );
  });
});
