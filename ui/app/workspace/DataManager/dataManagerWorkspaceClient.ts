/** Typed, browser-scoped Data Manager shell contracts. No generated history. */
import { ApiClientError, createDomainClient, type TransportConfig } from '../../host/transport';

export const workspaceTabIds = ['data', 'instruments', 'sessions', 'brokers', 'custom-data', 'chart', 'home', 'stock-groups', 'log'] as const;
export type WorkspaceTabId = typeof workspaceTabIds[number];
export interface WorkspaceTab { id: WorkspaceTabId; title: string; core: boolean }
export interface WorkspaceLayout {
  tabs: WorkspaceTab[];
  active_tab: WorkspaceTabId;
  layout: { core_group: string; chart_position: 'right' };
}
export interface RecordedBar { time: number; open: number; high: number; low: number; close: number; volume: number }
export interface WorkspaceSelection { id: string; symbol: string; timeframe: string; broker_name: string; timezone: string }
export interface WorkspacePreview { state: 'ready' | 'unavailable' | 'error'; reason: string; rows: RecordedBar[]; limit: number }
export interface WorkspaceSnapshot { active_tab: WorkspaceTabId; selection: WorkspaceSelection | null; preview: WorkspacePreview }

const invalid = () => new ApiClientError('MALFORMED_RESPONSE', 'Invalid Data Manager workspace response.');
const object = (value: unknown): value is Record<string, unknown> => typeof value === 'object' && value !== null && !Array.isArray(value);
const tabId = (value: unknown): value is WorkspaceTabId => workspaceTabIds.includes(value as WorkspaceTabId);

export async function fetchWorkspace(config: TransportConfig = {}): Promise<WorkspaceLayout> {
  let data: unknown;
  try {
    data = await createDomainClient('/data', config).get<unknown>('/workspace');
  } catch (cause) {
    if (cause instanceof ApiClientError && cause.status === 404) {
      throw new ApiClientError('WORKSPACE_UNAVAILABLE', 'Restart the host to load the updated Data Manager workspace.', [], 404);
    }
    throw cause;
  }
  if (!object(data) || !Array.isArray(data.tabs) || !tabId(data.active_tab) || !object(data.layout) || typeof data.layout.core_group !== 'string' || data.layout.chart_position !== 'right') throw invalid();
  if (data.tabs.length !== workspaceTabIds.length || data.tabs.some(item => !object(item) || !tabId(item.id) || typeof item.title !== 'string' || typeof item.core !== 'boolean')) throw invalid();
  const ids = new Set(data.tabs.map(item => item.id));
  if (ids.size !== workspaceTabIds.length || data.tabs.filter(item => item.core).map(item => item.id).sort().join() !== ['brokers', 'custom-data', 'data', 'instruments', 'sessions'].join()) throw invalid();
  return data as unknown as WorkspaceLayout;
}

function recordedBars(value: unknown): value is RecordedBar[] {
  if (!Array.isArray(value) || value.length > 500) return false;
  return value.every((bar, index) => object(bar) && ['time', 'open', 'high', 'low', 'close', 'volume'].every(key => typeof bar[key] === 'number' && Number.isFinite(bar[key])) &&
    Number.isSafeInteger(bar.time) && Number(bar.time) >= 0 && Number(bar.time) <= 8640000000000 && Number(bar.volume) >= 0 &&
    Number(bar.low) <= Math.min(Number(bar.open), Number(bar.close), Number(bar.high)) &&
    Number(bar.high) >= Math.max(Number(bar.open), Number(bar.close), Number(bar.low)) &&
    (index === 0 || value[index - 1].time < Number(bar.time)));
}

export async function openWorkspaceTab(id: WorkspaceTabId, datasetId: string | null, config: TransportConfig = {}): Promise<WorkspaceSnapshot> {
  const data = await createDomainClient('/data', config).post<unknown>(`/workspace/tabs/${id}`, { context: datasetId === null ? null : { dataset_id: datasetId } });
  if (!object(data) || data.active_tab !== id || !object(data.preview)) throw invalid();
  const selection = data.selection;
  if (datasetId === null ? selection !== null : !object(selection) || selection.id !== datasetId || ['id', 'symbol', 'timeframe', 'broker_name', 'timezone'].some(key => typeof selection[key] !== 'string')) throw invalid();
  const preview = data.preview;
  if (!['ready', 'unavailable', 'error'].includes(String(preview.state)) || typeof preview.reason !== 'string' || preview.limit !== 500 || !recordedBars(preview.rows)) throw invalid();
  if ((preview.state === 'ready') !== (preview.rows.length > 0) || (selection === null && preview.state === 'ready')) throw invalid();
  return data as unknown as WorkspaceSnapshot;
}
