/**
 * REST API client for HaruQuantAI Data Manager Log.
 *
 * Communicates with backend endpoints (/data/logs, /data/logs/clear)
 * mirroring SQX DataManagerLog plugin.
 */

import { createDomainClient, type DomainClient } from '../../host/transport';

export interface RemoteLogEntry {
  timestamp_utc: string;
  action: string;
  message: string;
  symbol?: string | null;
  details?: Record<string, unknown>;
  key?: string | null;
  pct?: number | null;
  log_str?: string | null;
}

export interface ClearLogsResponse {
  cleared_count: number;
  symbol?: string | null;
}

let client: DomainClient = createDomainClient('/data');

export function setDataManagerLogClient(customClient: DomainClient): void {
  client = customClient;
}

export function formatSqxLogLine(entry: RemoteLogEntry): string {
  try {
    const dt = new Date(entry.timestamp_utc);
    const month = dt.getMonth() + 1;
    const hours = String(dt.getHours()).padStart(2, '0');
    const minutes = String(dt.getMinutes()).padStart(2, '0');
    const timeStr = `${dt.getFullYear()}.${month}.${dt.getDate()} ${hours}:${minutes}`;
    const targetKey = entry.key || entry.symbol || '';
    const content = entry.log_str || entry.message;
    return targetKey ? `${timeStr} ${targetKey} ${content}` : `${timeStr} ${content}`;
  } catch {
    return `${entry.timestamp_utc.slice(0, 16)} ${entry.log_str || entry.message}`;
  }
}

export async function fetchLogs(
  symbol?: string,
  action?: string,
  limit = 100
): Promise<RemoteLogEntry[]> {
  const params = new URLSearchParams();
  if (symbol) params.set('symbol', symbol);
  if (action) params.set('action', action);
  params.set('limit', String(limit));
  const query = params.toString() ? `?${params.toString()}` : '';
  return client.get<RemoteLogEntry[]>(`/logs${query}`);
}

export async function createLog(
  entry: Partial<RemoteLogEntry>
): Promise<RemoteLogEntry> {
  return client.post<RemoteLogEntry>('/logs', entry);
}

export async function clearLogs(symbol?: string): Promise<ClearLogsResponse> {
  const query = symbol ? `?symbol=${encodeURIComponent(symbol)}` : '';
  return client.post<ClearLogsResponse>(`/logs/clear${query}`, {});
}
