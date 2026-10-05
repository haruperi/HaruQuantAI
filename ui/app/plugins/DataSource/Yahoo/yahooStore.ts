import { create } from 'zustand';
import { yahooCatalog, yahooAdd, yahooDownload, yahooStatus, yahooCancel, type YahooRecord } from './backend';
import { yahooDownloadRanges, type YahooDefinition, type YahooDownload } from './yahoo';

export const yahooActive = (state?: string) => state === 'running';
export const yahooKey = 'sqx-yahoo-data-v1';
export interface YahooJob {
  kind: 'add' | 'download'; definitions: YahooDefinition[]; request?: YahooDownload;
  state: 'running' | 'completed' | 'cancelled' | 'failed'; progress: number;
  completed: number; error?: string; jobId?: string; canPause: false;
}
interface Store {
  definitions: YahooDefinition[]; ranges: Record<string, never[]>;
  job: YahooJob | null; storageError: string; backendAvailable: boolean;
  refresh: () => Promise<void>; poll: () => Promise<void>;
  startAdd: (definitions: YahooDefinition[], external: boolean) => Promise<void>;
  startDownload: (request: YahooDownload, external: boolean) => Promise<void>;
  advance: () => void; action: (action: 'pause' | 'resume' | 'stop') => void;
}
function fromBackend(row: YahooRecord): YahooDefinition {
  const meta = row.options.metadata;
  const category = ({ EQUITY: 'Stocks', ETF: 'ETF', INDEX: 'Index', CURRENCY: 'Forex', CRYPTOCURRENCY: 'Crypto' } as const)[meta.instrumentType as 'EQUITY'] ?? 'Unknown';
  return { id: row.id, symbol: row.symbol, underlying: row.underlying, instrument: row.instrument,
    name: meta.shortName || meta.longName || row.underlying, exchange: meta.exchangeName || '',
    source: 'Yahoo', timeframe: 'D1', broker: '-1', brokerName: '—', timezone: 'UTC', category,
    barType: 'start', from: row.date_from.slice(0, 10), to: row.date_to.slice(0, 10), bars: row.bars,
    availableFrom: meta.firstTradeDate ? new Date(meta.firstTradeDate * 1000).toISOString().slice(0, 10) : undefined };
}
function message(cause: unknown): string { return cause instanceof Error ? cause.message : 'Yahoo operation failed.'; }
export const useYahoo = create<Store>((set, get) => {
  let polling = false;
  let stopRequested = false;
  async function startNext(job: YahooJob): Promise<void> {
    const request = job.request!;
    const target = job.definitions[job.completed];
    const range = yahooDownloadRanges({ ...request, targets: [target] })[target.id];
    const started = await yahooDownload(target.id, range.from, range.to, request.overwrite);
    set({ job: { ...job, jobId: started.job_id } });
    if (stopRequested) await yahooCancel(started.job_id);
  }
  function guard(external: boolean) {
    if (!get().backendAvailable) throw new Error(get().storageError || 'Yahoo backend is unavailable.');
    if (external || yahooActive(get().job?.state)) throw new Error('Finish or stop the active data operation first.');
  }
  return {
    definitions: [], ranges: {}, job: null, storageError: '', backendAvailable: false,
    refresh: async () => {
      try {
        const catalog = await yahooCatalog();
        if (!catalog.available) { set({ backendAvailable: false, storageError: catalog.reason }); return; }
        set({ definitions: catalog.datasets.map(fromBackend), backendAvailable: true, storageError: '' });
      } catch (cause) { set({ backendAvailable: false, storageError: message(cause) }); }
    },
    startAdd: async (definitions, external) => {
      guard(external);
      const job: YahooJob = { kind: 'add', definitions, state: 'running', completed: 0, progress: 0, canPause: false };
      set({ job });
      try {
        for (const row of definitions) {
          const created = await yahooAdd(row.underlying, row.symbol.slice(row.underlying.length));
          job.completed += 1; job.jobId = created.id;
          set({ job: { ...job, progress: 100 * job.completed / definitions.length } });
        }
        await get().refresh();
        set({ job: { ...job, state: 'completed', progress: 100 } });
      } catch (cause) { set({ job: { ...job, state: 'failed', error: message(cause) } }); await get().refresh(); throw cause; }
    },
    startDownload: async (request, external) => {
      guard(external); yahooDownloadRanges(request);
      stopRequested = false;
      const job: YahooJob = { kind: 'download', request, definitions: request.targets, state: 'running', completed: 0, progress: 0, canPause: false };
      set({ job });
      try { await startNext(job); }
      catch (cause) { set({ job: { ...job, state: 'failed', error: message(cause) } }); throw cause; }
    },
    poll: async () => {
      const job = get().job;
      if (polling || job?.kind !== 'download' || job.state !== 'running' || !job.jobId) return;
      polling = true;
      try {
        const status = await yahooStatus(job.jobId);
        if (get().job?.jobId !== job.jobId) return;
        if (status.state === 'succeeded') {
          const completed = job.completed + 1;
          const next = { ...job, completed, progress: 100 * completed / job.definitions.length };
          await get().refresh();
          if (stopRequested) set({ job: { ...next, state: 'cancelled' } });
          else if (completed === job.definitions.length) set({ job: { ...next, state: 'completed' } });
          else { try { await startNext(next); } catch (cause) { set({ job: { ...next, state: 'failed', error: message(cause) } }); } }
        } else if (['failed', 'timed_out', 'cancelled'].includes(status.state)) {
          set({ job: { ...job, state: status.state === 'cancelled' ? 'cancelled' : 'failed', error: status.state === 'cancelled' ? undefined : 'The backend acquisition failed. Check the host log.' } });
          await get().refresh();
        } else {
          const fraction = status.total_chunks ? status.completed_chunks / status.total_chunks : 0;
          set({ job: { ...job, progress: Math.min(99, 100 * (job.completed + fraction) / job.definitions.length) } });
        }
      } catch (cause) { set({ storageError: message(cause) }); }
      finally { polling = false; }
    },
    advance: () => {},
    action: action => {
      const job = get().job;
      if (action !== 'stop' || job?.kind !== 'download' || job.state !== 'running') return;
      stopRequested = true;
      if (!job.jobId) return;
      void yahooCancel(job.jobId).then(() => get().poll()).catch(cause => set({ storageError: message(cause) }));
    },
  };
});
export function reservedYahoo() { return useYahoo.getState().definitions; }
