import { describe, expect, it, vi } from 'vitest';
import {
  buildDataLogWsUrl,
  cancelLogOperation,
  clearLogs,
  createLog,
  fetchLogs,
  formatDataLogLine,
  isErrorLogRecord,
  subscribeDataLogStream,
  summarizeLogProgress,
  type DataLogRecord,
  type WebSocketLike,
} from '../../../app/workspace/DataManager/dataManagerLogClient';

const okResponse = (data: unknown) =>
  new Response(JSON.stringify({ status: 'success', data }), { status: 200 });

describe('DataManagerLog client and real-time WebSocket stream', () => {
  it('formats log records with UTC timestamp, symbol, action, and message', () => {
    const rec: DataLogRecord = {
      id: 1,
      timestamp_utc: '2026-10-21T08:05:00Z',
      action: 'DOWNLOAD',
      symbol: 'EURUSD',
      message: 'Downloaded 2025 bars',
      details: '',
      status: 'running',
      progress: 50,
    };
    expect(formatDataLogLine(rec)).toBe('2026.10.21 08:05 [EURUSD] DOWNLOAD: Downloaded 2025 bars');

    const rawTimeRec: DataLogRecord = {
      ...rec,
      timestamp_utc: 'invalid-date',
      symbol: '',
    };
    expect(formatDataLogLine(rawTimeRec)).toBe('invalid-date DOWNLOAD: Downloaded 2025 bars');
  });

  it('detects error records and error log lines accurately', () => {
    const base: DataLogRecord = {
      id: 1,
      timestamp_utc: '2026-10-21T08:05:00Z',
      action: 'DOWNLOAD',
      symbol: 'EURUSD',
      message: 'All good',
      details: '',
      status: 'running',
      progress: 25,
      is_error: false,
    };
    expect(isErrorLogRecord(base)).toBe(false);
    expect(isErrorLogRecord({ ...base, is_error: true })).toBe(true);
    expect(isErrorLogRecord({ ...base, status: 'error' })).toBe(true);
    expect(isErrorLogRecord({ ...base, progress: -1 })).toBe(true);
    expect(isErrorLogRecord({ ...base, action: 'IMPORT_ERR' })).toBe(true);
    expect(isErrorLogRecord('2026.10.21 08:05 [EURUSD] DOWNLOAD: Operation failed')).toBe(true);
    expect(isErrorLogRecord('2026.10.21 08:05 [EURUSD] DOWNLOAD: Completed')).toBe(false);
  });

  it('summarizes operation progress, error counts, and cancellation state', () => {
    expect(summarizeLogProgress([])).toEqual({
      progress: 0,
      status: 'idle',
      label: 'No active operations',
      symbol: '',
      errorCount: 0,
      cancellable: false,
    });

    const records: DataLogRecord[] = [
      {
        id: 1,
        timestamp_utc: '2026-10-21T08:00:00Z',
        action: 'IMPORT_ERR',
        symbol: 'BTCUSDT',
        message: 'Bad row',
        details: '',
        status: 'error',
        progress: -1,
        is_error: true,
      },
      {
        id: 2,
        timestamp_utc: '2026-10-21T08:01:00Z',
        action: 'DOWNLOAD',
        symbol: 'EURUSD',
        message: 'Downloading EURUSD',
        details: '',
        status: 'running',
        progress: 65,
      },
    ];
    expect(summarizeLogProgress(records)).toEqual({
      progress: 65,
      status: 'running',
      label: 'Downloading EURUSD',
      symbol: 'EURUSD',
      errorCount: 1,
      cancellable: true,
    });
  });

  it('calls REST endpoints for fetchLogs, createLog, clearLogs, and cancelLogOperation', async () => {
    const sample: DataLogRecord = {
      id: 7,
      timestamp_utc: '2026-10-21T09:00:00Z',
      action: 'EXPORT',
      symbol: 'AAPL',
      message: 'Exported CSV',
      details: '',
      status: 'completed',
      progress: 100,
    };
    const fetchFn = vi
      .fn()
      .mockResolvedValueOnce(okResponse([sample]))
      .mockResolvedValueOnce(okResponse(sample))
      .mockResolvedValueOnce(okResponse({ cleared: 3, status: 'idle', progress: 0 }))
      .mockResolvedValueOnce(
        okResponse({ ...sample, action: 'CANCEL', status: 'cancelled', progress: 0 }),
      );

    const logs = await fetchLogs(50, { baseUrl: '/api/v1', fetchFn });
    expect(logs).toEqual([sample]);
    expect(fetchFn.mock.calls[0][0]).toBe('/api/v1/data/logs?limit=50');

    const created = await createLog(
      { action: 'EXPORT', symbol: 'AAPL', message: 'Exported CSV' },
      { baseUrl: '/api/v1', fetchFn },
    );
    expect(created.symbol).toBe('AAPL');
    expect(fetchFn.mock.calls[1][0]).toBe('/api/v1/data/logs');

    const cleared = await clearLogs({ baseUrl: '/api/v1', fetchFn });
    expect(cleared).toEqual({ cleared: 3, status: 'idle', progress: 0 });
    expect(fetchFn.mock.calls[2][0]).toBe('/api/v1/data/logs/clear');

    const cancelled = await cancelLogOperation('AAPL', 'CSV export', {
      baseUrl: '/api/v1',
      fetchFn,
    });
    expect(cancelled.status).toBe('cancelled');
    expect(JSON.parse(fetchFn.mock.calls[3][1].body)).toMatchObject({
      action: 'CANCEL',
      symbol: 'AAPL',
      status: 'cancelled',
      progress: 0,
    });
  });

  it('streams live log entries, snapshots, and clear events over WebSocket', () => {
    const url = buildDataLogWsUrl({
      baseUrl: 'http://127.0.0.1:8000/api/v1',
      authToken: 'tok-123',
      sinceCursor: 4,
    });
    expect(url).toBe('ws://127.0.0.1:8000/api/v1/ws?channels=logs%2Cjobs&token=tok-123&since_cursor=4');

    let socketInstance: WebSocketLike | null = null;
    const closeSpy = vi.fn();
    const entries: DataLogRecord[] = [];
    const snapshots: DataLogRecord[][] = [];
    const clearedEvents: number[] = [];
    const progressEvents: number[] = [];
    const errors: string[] = [];

    const unsubscribe = subscribeDataLogStream({
      baseUrl: 'http://127.0.0.1:8000/api/v1',
      webSocketFactory: () => {
        socketInstance = {
          onmessage: null,
          onerror: null,
          onclose: null,
          close: closeSpy,
        };
        return socketInstance;
      },
      onEntry: rec => entries.push(rec),
      onSnapshot: list => snapshots.push(list),
      onCleared: res => clearedEvents.push(res.cleared),
      onProgress: prog => progressEvents.push(prog.progress),
      onError: err => errors.push(err),
    });

    expect(socketInstance).not.toBeNull();

    socketInstance!.onmessage?.({
      data: JSON.stringify({
        channel: 'logs',
        event_type: 'datamgr.log.entry',
        timestamp: '2026-10-21T10:00:00Z',
        payload: {
          id: 10,
          action: 'DOWNLOAD',
          symbol: 'EURUSD',
          status: 'running',
          progress: 40,
          message: '40% complete',
        },
      }),
    });
    expect(entries).toHaveLength(1);
    expect(entries[0].progress).toBe(40);
    expect(progressEvents.at(-1)).toBe(40);

    socketInstance!.onmessage?.({
      data: JSON.stringify({
        channel: 'logs',
        event_type: 'datamgr.log.stream',
        timestamp: '2026-10-21T10:01:00Z',
        payload: {
          entries: [
            {
              id: 11,
              action: 'IMPORT',
              symbol: 'GBPUSD',
              status: 'completed',
              progress: 100,
              message: 'Import finished',
            },
          ],
        },
      }),
    });
    expect(snapshots).toHaveLength(1);
    expect(progressEvents.at(-1)).toBe(100);

    socketInstance!.onmessage?.({
      data: JSON.stringify({
        channel: 'logs',
        event_type: 'datamgr.log.cleared',
        timestamp: '2026-10-21T10:02:00Z',
        payload: { cleared: 5 },
      }),
    });
    expect(clearedEvents).toEqual([5]);
    expect(progressEvents.at(-1)).toBe(0);

    socketInstance!.onmessage?.({ data: '{malformed-json' });
    expect(errors).toContain('Malformed WebSocket log event');

    unsubscribe();
    expect(closeSpy).toHaveBeenCalledTimes(1);
  });
});
