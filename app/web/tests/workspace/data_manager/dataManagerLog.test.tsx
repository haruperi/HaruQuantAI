import { describe, expect, it, vi } from 'vitest';
import {
  buildDataLogWsUrl,
  clearLogs,
  fetchLogs,
  fetchActiveLogs,
  formatDataLogLine,
  isErrorLogRecord,
  subscribeDataLogStream,
  summarizeLogProgress,
  type DataLogRecord,
  type WebSocketLike,
} from '../../../workspaces/data_manager/dataManagerLogClient';

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

  it('reads shared structured history and active tasks, and confirms clear', async () => {
    const entry = {id:'entry',timestamp:'2026-10-21T09:00:00Z',task_id:'job',message:'Downloaded',level:'info',progress:50};
    const fetchFn = vi.fn().mockResolvedValueOnce(okResponse({entries:[entry],total:1}))
      .mockResolvedValueOnce(okResponse([entry])).mockResolvedValueOnce(okResponse({cleared_count:1}));
    const config = {baseUrl:'/api/v1',fetchFn};
    expect(await fetchLogs(50,config)).toMatchObject([{id:'entry',symbol:'job',message:'Downloaded',timestamp_utc:entry.timestamp}]);
    expect(fetchFn.mock.calls[0][0]).toBe('/api/v1/data/logs?limit=50');
    expect(await fetchActiveLogs(config)).toMatchObject([{symbol:'job',progress:50}]);
    expect(await clearLogs(config)).toEqual({cleared:1,status:'idle',progress:0});
  });

  it('handles backend progress and clear without fabricating entries for host jobs', () => {
    let socket: WebSocketLike;
    const onEntry=vi.fn(),onProgress=vi.fn(),onCleared=vi.fn();
    const stop=subscribeDataLogStream({webSocketFactory:()=>socket={onmessage:null,onerror:null,onclose:null,close:vi.fn()},onEntry,onProgress,onCleared});
    const update={task_id:'job',timestamp:'2026-10-21T09:00:00Z',progress:25,message:'AAPL',level:'info'};
    const emit=(event_type:string,payload:unknown,channel='logs')=>socket.onmessage?.({data:JSON.stringify({channel,event_type,payload})});
    emit('datamanager.logs.progress',{workspace:'data-manager',update,entry:{id:'a',...update}});
    expect(onEntry).toHaveBeenCalledWith(expect.objectContaining({id:'a',symbol:'job',progress:25}));
    emit('datamanager.logs.progress',{workspace:'data-manager',update,entry:null});
    expect(onEntry).toHaveBeenCalledTimes(1);
    emit('job.updated',{message:'Unrelated'},'jobs');
    expect(onEntry).toHaveBeenCalledTimes(1);
    emit('datamanager.logs.cleared',{workspace:'data-manager',cleared_count:1});
    expect(onCleared).toHaveBeenCalledWith({cleared:1,status:'idle',progress:0});
    expect(onProgress).toHaveBeenCalledTimes(2);
    stop();
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
