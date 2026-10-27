/** Backend authority for historical downloads from the remaining broker sources. */
import { create } from 'zustand';
import { ApiClientError, createDomainClient } from '../../../host/transport';

export const sourceClient = createDomainClient('/data');
export interface SourceRecord { id: string; source: string; symbol: string; timeframe: string; underlying?: string; from?: string; to?: string }
export interface SourceJob { job_id: string; targets?: string[]; status: string; progress: number; message: string; error_message?: string | null; kind?: string; result?: {artifacts?: string[]} }
interface State {
  job: SourceJob | null; error: string; pending: boolean;
  start: (records: SourceRecord[], from: string, to: string, overwrite: boolean, connectionId?: string) => Promise<void>;
  trackJob: (job: SourceJob) => void;
  poll: () => Promise<void>;
  action: (action: 'pause' | 'resume' | 'stop') => Promise<void>;
}
const key = 'haruquantai-historical-job-v1';
const states = ['QUEUED','RUNNING','PAUSED','COMPLETED','CANCELLED','FAILED','INTERRUPTED'];
function validJob(value: SourceJob | null): value is SourceJob {
  return !!value && typeof value.job_id === 'string' && states.includes(value.status) && Number.isFinite(value.progress) && value.progress >= 0 && value.progress <= 100 && (value.targets === undefined || Array.isArray(value.targets) && value.targets.every(id => typeof id === 'string'));
}
export const sourceActive = (status?: string) => ['QUEUED', 'RUNNING', 'PAUSED'].includes(status ?? '');
export async function refreshSourceCatalog() {
  const { useDataManagerStore } = await import('./dataManagerStore');
  await useDataManagerStore.getState().syncRemoteDatasets();
}
function savedJob(): SourceJob | null {
  try {
    const value = JSON.parse(localStorage.getItem(key) ?? 'null');
    return validJob(value) ? value : null;
  } catch { return null; }
}
export const useHistoricalSources = create<State>((set, get) => {
  let polling = false; const downloaded = new Set<string>();
  function apply(job: SourceJob) {
    if (!validJob(job)) throw new Error('Invalid backend job response.');
    set({ job, error: '' });
    try { localStorage.setItem(key, JSON.stringify(job)); } catch { set({ error: 'Job accepted; its recovery ID could not be saved in this browser.' }); }
  }
  return {
    trackJob: apply,
    job: savedJob(), error: '', pending: false,
    start: async (records, from, to, overwrite, connectionId) => {
      if (get().pending || sourceActive(get().job?.status)) throw new Error('Finish or stop the active historical download first.');
      if (!records.length) throw new Error('Select saved datasets first.');
      set({ pending: true, error: '' });
      try {
        apply({...await sourceClient.post<SourceJob>('/providers/download', { provider: 'market', targets: records.map(row => ({ id: row.id })), date_from: from, date_to: to, overwrite, connection_id:connectionId }), targets: records.map(row => row.id)});
        if (!sourceActive(get().job?.status)) await refreshSourceCatalog();
      } catch (error) { set({ error: error instanceof Error ? error.message : 'Unable to start download.' }); throw error; }
      finally { set({ pending: false }); }
    },
    poll: async () => {
      const current = get().job;
      if (polling || !current || (!sourceActive(current.status) && !(current.status === 'COMPLETED' && current.result?.artifacts))) return;
      polling = true;
      try {
        const result = await sourceClient.get<SourceJob>(`/download-jobs/${encodeURIComponent(current.job_id)}`);
        apply({...result, targets: current.targets});
        if (!sourceActive(result.status)) {
          await refreshSourceCatalog();
          if (result.kind?.startsWith('custom.')) {
            const {useExternalIndicators} = await import('../Indicators/externalIndicatorsStore');
            await useExternalIndicators.getState().syncRemote();
          }
        }
        if (result.status === 'COMPLETED' && result.result?.artifacts && !downloaded.has(result.job_id)) {
          const {downloadRemoteArtifacts} = await import('../Export/dataExportStore');
          await downloadRemoteArtifacts(result.job_id, result.result.artifacts);
          downloaded.add(result.job_id);
        }
      } catch (error) {
        if (error instanceof ApiClientError && error.status === 404) apply({ ...current, status: 'INTERRUPTED', error_message: 'Backend job no longer exists.' });
        else set({ error: error instanceof Error ? error.message : 'Unable to read download status.' });
      } finally { polling = false; }
    },
    action: async action => {
      const current = get().job; if (!current) return;
      try {
        apply({...await sourceClient.post<SourceJob>(`/download-jobs/${encodeURIComponent(current.job_id)}/${action}`, {}), targets: current.targets});
        if (!sourceActive(get().job?.status)) await refreshSourceCatalog();
      } catch (error) { set({ error: error instanceof Error ? error.message : 'Unable to control download.' }); }
    },
  };
});

export function normalizeSource(provider: string): string {
  const key = provider.toLowerCase().replaceAll('-', '_');
  return ({ binancecoinm: 'binance_coinm', binanceusdtm: 'binance_usdtm', equity: 'sq_equity', futures: 'sq_futures' } as Record<string, string>)[key] ?? key;
}
