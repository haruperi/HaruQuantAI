import { describe, expect, it, vi } from 'vitest';
import { createCodeEditorClient } from '../../../workspaces/code_editor/codeEditorClient';
import { IndicatorTestPresentation } from '../../../workspaces/code_editor/indicator_test_presentation';

function mockResponse(data: unknown) {
  return () => Promise.resolve(new Response(JSON.stringify({ status: 'success', data })));
}

describe('IndicatorTesterModal suite, distribution, and calibration contracts', () => {
  it('formats suite rows using IndicatorTestPresentation and roundtrips parameters/shift', () => {
    const label = IndicatorTestPresentation.format_parameters('MACD.Signal', '12,26,9', 2);
    expect(label).toBe('MACD(12,26,9)[2]');
    expect(IndicatorTestPresentation.raw_parameters(label)).toBe('12,26,9');
    expect(IndicatorTestPresentation.shift_text(label)).toBe('2');
    expect(IndicatorTestPresentation.row_class(true, 'Passed')).toBe('passed');
    expect(IndicatorTestPresentation.row_class(true, 'Failed - 3 differences')).toBe('failed');
    expect(IndicatorTestPresentation.row_class(true, 'Skipped - File not found.')).toBe('other');
    expect(IndicatorTestPresentation.row_class(false, '')).toBe('unchecked');
  });

  it('calls indicator suite, test distribution, and calibration endpoints with exact payloads', async () => {
    const fetchFn = vi.fn().mockImplementation(mockResponse({}));
    const client = createCodeEditorClient({ fetchFn, baseUrl: '/api/v1' });

    await client.suiteIndicators();
    expect(fetchFn).toHaveBeenLastCalledWith(
      '/api/v1/code-editor/indicator-suite/indicators',
      expect.objectContaining({ method: 'GET' })
    );

    await client.suiteCreateConfig(['ATR'], 'MetaTrader4', 300);
    expect(fetchFn).toHaveBeenLastCalledWith(
      '/api/v1/code-editor/indicator-suite/config/new',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          indicators: ['ATR'],
          engine: 'MetaTrader4',
          bars_to_reserve: 300,
        }),
      })
    );

    await client.suiteAddTests(['RSI'], false);
    expect(fetchFn).toHaveBeenLastCalledWith(
      '/api/v1/code-editor/indicator-suite/config/add-tests',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ indicators: ['RSI'], allow_duplicates: false }),
      })
    );

    await client.suiteStart({ selected_only: true });
    expect(fetchFn).toHaveBeenLastCalledWith(
      '/api/v1/code-editor/indicator-suite/start',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({ config: null, selected_only: true }),
      })
    );

    await client.suiteStop('indy-suite-1');
    expect(fetchFn).toHaveBeenLastCalledWith(
      '/api/v1/code-editor/indicator-suite/stop?job_id=indy-suite-1',
      expect.objectContaining({ method: 'POST' })
    );

    await client.downloadTests({
      archive_path: 'data/indicator_tests/bundle.zip',
      expected_sha256: 'a'.repeat(64),
    });
    expect(fetchFn).toHaveBeenLastCalledWith(
      '/api/v1/code-editor/indicator-suite/download-tests',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          archive_path: 'data/indicator_tests/bundle.zip',
          expected_sha256: 'a'.repeat(64),
        }),
      })
    );

    await client.calibrateIndicators({
      project_name: 'Proj1',
      symbols: ['EURUSD'],
      timeframes: ['H1'],
      engine: 'MetaTrader4',
      max_steps: 20,
      indicators: ['ATR'],
    });
    expect(fetchFn).toHaveBeenLastCalledWith(
      '/api/v1/code-editor/indicator-suite/calibrate',
      expect.objectContaining({
        method: 'POST',
        body: JSON.stringify({
          project_name: 'Proj1',
          symbols: ['EURUSD'],
          timeframes: ['H1'],
          engine: 'MetaTrader4',
          max_steps: 20,
          indicators: ['ATR'],
        }),
      })
    );
  });
});
