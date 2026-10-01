import { create } from 'zustand';
import { cryptoCatalog, cryptoAdd, cryptoDownload, cryptoStatus, cryptoCancel, type CryptoRecord, exchangeId } from './backend';
import { cryptoDownloadRanges, type CryptoDefinition, type CryptoDownload } from './crypto';

export const cryptoActive = (state?: string) => state === 'running';
export const cryptoKey = 'sqx-crypto-data-v1';
export interface CryptoJob {
  kind: 'add' | 'download'; definitions: CryptoDefinition[]; request?: CryptoDownload;
  state: 'running' | 'completed' | 'cancelled' | 'failed'; progress: number;
  completed: number; error?: string; jobId?: string; canPause: false;
}
interface Store {
  exchanges: { name: string; timeframes: string[] }[]; definitions: CryptoDefinition[]; ranges: Record<string, never[]>;
  job: CryptoJob | null; storageError: string; backendAvailable: boolean;
  refresh: () => Promise<void>; poll: () => Promise<void>;
  startAdd: (definitions: CryptoDefinition[], external: boolean) => Promise<void>;
  startDownload: (request: CryptoDownload, external: boolean) => Promise<void>;
  advance: () => void; action: (action: 'pause' | 'resume' | 'stop') => void;
}
function fromBackend(row: CryptoRecord): CryptoDefinition {
  const inception = row.options.metadata.date_from;
  return { id: row.id, symbol: row.symbol, underlying: row.underlying, instrument: row.instrument,
    exchange: exchangeId(row.options.parameters.exchange), source: 'Crypto', timeframe: row.timeframe,
    broker: '-1', brokerName: '—', timezone: 'UTC', category: 'Crypto', barType: 'start',
    from: row.date_from.slice(0, 10), to: row.date_to.slice(0, 10), bars: row.bars,
    availableFrom: inception ? new Date(inception).toISOString().slice(0, 10) : undefined };
}
function message(cause: unknown): string { return cause instanceof Error ? cause.message : 'Crypto operation failed.'; }
export const useCrypto = create<Store>((set, get) => {
  let polling = false;
  let stopRequested = false;
  async function startNext(job: CryptoJob): Promise<void> {
    const request = job.request!;
    const target = job.definitions[job.completed];
    const range = cryptoDownloadRanges({ ...request, targets: [target] })[target.id];
    const started = await cryptoDownload(target.id, range.from, range.to, request.overwrite);
    set({ job: { ...job, jobId: started.job_id } });
    if (stopRequested) await cryptoCancel(started.job_id);
  }
  function guard(external: boolean) {
    if (!get().backendAvailable) throw new Error(get().storageError || 'Crypto backend is unavailable.');
    if (external || cryptoActive(get().job?.state)) throw new Error('Finish or stop the active data operation first.');
  }
  return {
    exchanges: [], definitions: [], ranges: {}, job: null, storageError: '', backendAvailable: false,
    refresh: async () => {
      try {
        const catalog = await cryptoCatalog();
        if (!catalog.available) { set({ backendAvailable: false, storageError: catalog.reason }); return; }
        set({ exchanges: catalog.exchanges, definitions: catalog.datasets.map(fromBackend), backendAvailable: true, storageError: '' });
      } catch (cause) { set({ backendAvailable: false, storageError: message(cause) }); }
    },
    startAdd: async (definitions, external) => {
      guard(external);
      const job: CryptoJob = { kind: 'add', definitions, state: 'running', completed: 0, progress: 0, canPause: false };
      set({ job });
      try {
        for (const row of definitions) {
          const created = await cryptoAdd(row.underlying, row.symbol.slice(row.underlying.length), row.exchange, row.timeframe);
          job.completed += 1; job.jobId = created.id;
          set({ job: { ...job, progress: 100 * job.completed / definitions.length } });
        }
        await get().refresh();
        set({ job: { ...job, state: 'completed', progress: 100 } });
      } catch (cause) { set({ job: { ...job, state: 'failed', error: message(cause) } }); await get().refresh(); throw cause; }
    },
    startDownload: async (request, external) => {
      guard(external); cryptoDownloadRanges(request);
      stopRequested = false;
      const job: CryptoJob = { kind: 'download', request, definitions: request.targets, state: 'running', completed: 0, progress: 0, canPause: false };
      set({ job });
      try { await startNext(job); }
      catch (cause) { set({ job: { ...job, state: 'failed', error: message(cause) } }); throw cause; }
    },
    poll: async () => {
      const job = get().job;
      if (polling || job?.kind !== 'download' || job.state !== 'running' || !job.jobId) return;
      polling = true;
      try {
        const status = await cryptoStatus(job.jobId);
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
          const fraction = status.progress || 0;
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
      void cryptoCancel(job.jobId).then(() => get().poll()).catch(cause => set({ storageError: message(cause) }));
    },
  };
});
export function reservedCrypto() { return useCrypto.getState().definitions; }
