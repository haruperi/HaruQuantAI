import { describe, expect, it, vi } from 'vitest';
import { createCodeEditorClient } from '../../../workspaces/code_editor/codeEditorClient';

function mockResponse(data: unknown) {
  return () => Promise.resolve(new Response(JSON.stringify({ status: 'success', data })));
}

describe('ImportExportModal interactive conflict session and user listing contracts', () => {
  it('calls user-only list and interactive import session endpoints', async () => {
    const fetchFn = vi.fn().mockImplementation(mockResponse({}));
    const client = createCodeEditorClient({ fetchFn, baseUrl: '/api/v1' });

    await client.listExportableFiles('custom');
    expect(fetchFn).toHaveBeenLastCalledWith(
      '/api/v1/code-editor/import-export/list?filter_text=custom',
      expect.objectContaining({ method: 'GET' })
    );

    await client.startImportSession(['app/include/pack.sxp'], 60);
    expect(fetchFn).toHaveBeenLastCalledWith(
      '/api/v1/code-editor/import-export/session/start',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          archive_paths: ['app/include/pack.sxp'],
          timeout_seconds: 60,
        }),
      })
    );

    for (const action of [
      'overwrite',
      'overwrite_always',
      'skip',
      'skip_always',
      'cancel',
    ] as const) {
      await client.applyImportSessionAction('import-123', action);
      expect(fetchFn).toHaveBeenLastCalledWith(
        '/api/v1/code-editor/import-export/session/action',
        expect.objectContaining({
          method: 'POST',
          body: JSON.stringify({ session_id: 'import-123', action }),
        })
      );
    }

    await client.getImportSession('import-123');
    expect(fetchFn).toHaveBeenLastCalledWith(
      '/api/v1/code-editor/import-export/session?session_id=import-123',
      expect.objectContaining({ method: 'GET' })
    );
  });
});
