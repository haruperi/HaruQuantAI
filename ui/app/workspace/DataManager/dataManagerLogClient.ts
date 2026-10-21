/**
 * Data Manager Log & Operation Tracking Client
 *
 * Streams live data download, import, and export logs over the host WebSocket
 * (/api/v1/ws?channels=logs,jobs) and communicates with the backend REST
 * endpoints (/api/v1/data/logs, /api/v1/data/logs/clear).
 */

import {
  createDomainClient,
  getAuthToken,
  hostBaseUrl,
  type TransportConfig,
} from '../../host/transport';

export type DataLogStatus =
  | 'idle'
  | 'info'
  | 'running'
  | 'paused'
  | 'completed'
  | 'cancelled'
  | 'error'
  | 'failed';

export interface DataLogRecord {
  id: number;
  timestamp_utc: string;
  action: string;
  message: string;
  symbol: string;
  details: string;
  status?: DataLogStatus;
  progress?: number;
  is_error?: boolean;
  cancellable?: boolean;
  created_at?: string;
}

export interface CreateLogPayload {
  action: string;
  message: string;
  symbol?: string;
  details?: string;
  status?: DataLogStatus;
  progress?: number;
  timestamp_utc?: string;
}

export interface ClearLogResult {
  cleared: number;
  status: 'idle';
  progress: number;
}

export interface DataOperationProgress {
  progress: number;
  status: DataLogStatus;
  label: string;
  symbol: string;
  errorCount: number;
  cancellable: boolean;
}

export interface WebSocketLike {
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onmessage: ((event: any) => unknown) | null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onerror: ((event: any) => unknown) | null;
  // eslint-disable-next-line @typescript-eslint/no-explicit-any
  onclose: ((event: any) => unknown) | null;
  close: () => void;
}

export interface DataLogStreamOptions {
  baseUrl?: string;
  authToken?: string | null;
  sinceCursor?: number;
  webSocketFactory?: (url: string) => WebSocketLike;
  onEntry?: (record: DataLogRecord) => void;
  onSnapshot?: (records: DataLogRecord[]) => void;
  onCleared?: (result: ClearLogResult) => void;
  onProgress?: (progress: DataOperationProgress) => void;
  onError?: (error: string) => void;
}

function client(config: TransportConfig = {}) {
  return createDomainClient('/data', config);
}

/**
 * Format a log record into the canonical Data Manager log line:
 * "YYYY.M.D HH:MM [SYMBOL] ACTION: message"
 */
export function formatDataLogLine(record: DataLogRecord): string {
  const d = new Date(record.timestamp_utc);
  let timeStr = record.timestamp_utc;
  if (!Number.isNaN(d.getTime())) {
    const year = d.getUTCFullYear();
    const month = d.getUTCMonth() + 1;
    const day = d.getUTCDate();
    const hours = String(d.getUTCHours()).padStart(2, '0');
    const mins = String(d.getUTCMinutes()).padStart(2, '0');
    timeStr = `${year}.${month}.${day} ${hours}:${mins}`;
  }
  const symPart = record.symbol ? `[${record.symbol}] ` : '';
  const actPart = record.action ? `${record.action}: ` : '';
  return `${timeStr} ${symPart}${actPart}${record.message}`;
}

/**
 * Determine whether a structured log record or formatted log string represents an error.
 */
export function isErrorLogRecord(entry: DataLogRecord | string): boolean {
  if (typeof entry === 'string') {
    return /\b(error|failed|exception)\b/i.test(entry);
  }
  if (entry.is_error === true) return true;
  const status = (entry.status ?? '').toLowerCase();
  if (status === 'error' || status === 'failed') return true;
  if (typeof entry.progress === 'number' && entry.progress < 0) return true;
  if (entry.action.toUpperCase().includes('ERR')) return true;
  return /\b(error|failed|exception)\b/i.test(entry.message);
}

/**
 * Summarize active operation progress, error count, and cancellation availability.
 */
export function summarizeLogProgress(
  records: readonly DataLogRecord[],
): DataOperationProgress {
  let errorCount = 0;
  for (const record of records) {
    if (isErrorLogRecord(record)) errorCount += 1;
  }
  const latest = records.at(-1);
  if (!latest) {
    return {
      progress: 0,
      status: 'idle',
      label: 'No active operations',
      symbol: '',
      errorCount: 0,
      cancellable: false,
    };
  }
  const rawStatus = (latest.status ?? (isErrorLogRecord(latest) ? 'error' : 'info')) as DataLogStatus;
  const rawProgress = typeof latest.progress === 'number' ? latest.progress : 0;
  const clampedProgress = rawProgress < 0 ? 0 : Math.min(100, rawProgress);
  const cancellable =
    latest.cancellable === true || rawStatus === 'running' || rawStatus === 'paused';
  return {
    progress: rawStatus === 'completed' ? 100 : clampedProgress,
    status: rawStatus,
    label: latest.message || latest.action || 'Data operation',
    symbol: latest.symbol || '',
    errorCount,
    cancellable,
  };
}

/**
 * Fetch the most recent Data Manager log entries.
 */
export async function fetchLogs(
  limit = 100,
  config: TransportConfig = {},
): Promise<DataLogRecord[]> {
  return client(config).get<DataLogRecord[]>(`/logs?limit=${limit}`);
}

/**
 * Append a new entry to the Data Manager log.
 */
export async function createLog(
  payload: CreateLogPayload,
  config: TransportConfig = {},
): Promise<DataLogRecord> {
  return client(config).post<DataLogRecord>('/logs', payload);
}

/**
 * Clear all Data Manager log entries and reset operation progress state.
 */
export async function clearLogs(
  config: TransportConfig = {},
): Promise<ClearLogResult> {
  return client(config).post<ClearLogResult>('/logs/clear', {});
}

/**
 * Record a cancellation request for an active Data Manager operation.
 */
export async function cancelLogOperation(
  symbol = '',
  label = 'Data operation',
  config: TransportConfig = {},
): Promise<DataLogRecord> {
  return createLog(
    {
      action: 'CANCEL',
      symbol,
      status: 'cancelled',
      progress: 0,
      message: `${label} cancelled`,
    },
    config,
  );
}

/**
 * Build the host WebSocket URL subscribed to the logs and jobs channels.
 */
export function buildDataLogWsUrl(
  options: Pick<DataLogStreamOptions, 'baseUrl' | 'authToken' | 'sinceCursor'> = {},
): string | null {
  const baseUrl = options.baseUrl ?? hostBaseUrl();
  const token = options.authToken === undefined ? getAuthToken() : options.authToken;
  const origin =
    typeof window !== 'undefined' && window.location?.origin
      ? window.location.origin
      : 'http://127.0.0.1:8000';
  const resolved = new URL(`${baseUrl.replace(/\/$/, '')}/ws`, origin);
  resolved.protocol = resolved.protocol === 'https:' ? 'wss:' : 'ws:';
  resolved.searchParams.set('channels', 'logs,jobs');
  if (token) resolved.searchParams.set('token', token);
  if (typeof options.sinceCursor === 'number' && options.sinceCursor >= 0) {
    resolved.searchParams.set('since_cursor', String(options.sinceCursor));
  }
  return resolved.toString();
}

function normalizeIncomingRecord(raw: Record<string, unknown>, fallbackTime: string): DataLogRecord {
  const action = String(raw.action ?? raw.operation ?? raw.level ?? 'INFO');
  const status = String(
    raw.status ?? (action.toUpperCase().includes('ERR') ? 'error' : 'info'),
  ).toLowerCase() as DataLogStatus;
  const rawPct = typeof raw.progress === 'number' ? raw.progress : status === 'error' ? -1 : 0;
  const isError =
    Boolean(raw.is_error) || status === 'error' || status === 'failed' || rawPct < 0;
  return {
    id: typeof raw.id === 'number' ? raw.id : Date.now(),
    timestamp_utc: String(raw.timestamp_utc ?? fallbackTime),
    action,
    message: String(raw.message ?? ''),
    symbol: String(raw.symbol ?? ''),
    details: String(raw.details ?? ''),
    status,
    progress: rawPct,
    is_error: isError,
    cancellable: Boolean(raw.cancellable) || status === 'running' || status === 'paused',
  };
}

/**
 * Subscribe to real-time Data Manager log and operation progress events via WebSocket.
 */
export function subscribeDataLogStream(options: DataLogStreamOptions = {}): () => void {
  const url = buildDataLogWsUrl(options);
  const factory =
    options.webSocketFactory ??
    (typeof WebSocket !== 'undefined'
      ? (target: string): WebSocketLike => new WebSocket(target) as unknown as WebSocketLike
      : null);
  if (!url || !factory) return () => {};

  let closed = false;
  let socket: WebSocketLike;
  try {
    socket = factory(url);
  } catch (err) {
    options.onError?.(err instanceof Error ? err.message : 'WebSocket connection failed');
    return () => {};
  }

  socket.onmessage = event => {
    if (closed || typeof event.data !== 'string') return;
    try {
      const frame = JSON.parse(event.data) as {
        channel?: string;
        event_type?: string;
        timestamp?: string;
        payload?: Record<string, unknown>;
      };
      const payload = frame.payload ?? {};
      const stamp = frame.timestamp ?? new Date().toISOString();
      if (frame.event_type === 'datamgr.log.cleared') {
        const result: ClearLogResult = {
          cleared: typeof payload.cleared === 'number' ? payload.cleared : 0,
          status: 'idle',
          progress: 0,
        };
        options.onCleared?.(result);
        options.onProgress?.({
          progress: 0,
          status: 'idle',
          label: 'No active operations',
          symbol: '',
          errorCount: 0,
          cancellable: false,
        });
        return;
      }
      if (frame.event_type === 'datamgr.log.stream' && Array.isArray(payload.entries)) {
        const records = payload.entries
          .filter((item): item is Record<string, unknown> => typeof item === 'object' && item !== null)
          .map(item => normalizeIncomingRecord(item, stamp));
        options.onSnapshot?.(records);
        options.onProgress?.(summarizeLogProgress(records));
        return;
      }
      if (frame.channel === 'logs' || frame.channel === 'jobs') {
        const record = normalizeIncomingRecord(payload, stamp);
        if (record.message || record.action) {
          options.onEntry?.(record);
          options.onProgress?.(summarizeLogProgress([record]));
        }
      }
    } catch {
      options.onError?.('Malformed WebSocket log event');
    }
  };

  socket.onerror = () => {
    if (!closed) options.onError?.('Data Manager log stream error');
  };

  return () => {
    closed = true;
    try {
      socket?.close();
    } catch {
      // ignore close errors on teardown
    }
  };
}
