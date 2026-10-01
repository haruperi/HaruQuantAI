import { create } from 'zustand';
import { darwinexCatalog, darwinexAdd, darwinexDownload, darwinexStatus, darwinexCancel, darwinexImport, type DarwinexSymbolInfo, type DarwinexRecord } from './backend';
import { darwinexDownloadRanges, type DarwinexDefinition, type DarwinexDownload } from './darwinex';

export const darwinexActive = (state?: string) => state === 'running';
export const darwinexKey = 'sqx-darwinex-data-v1';
export interface DarwinexJob {
  kind: 'add' | 'import' | 'download'; definitions: DarwinexDefinition[]; request?: DarwinexDownload;
  state: 'running' | 'completed' | 'cancelled' | 'failed'; progress: number;
  completed: number; error?: string; jobId?: string; canPause: false;
}
interface Store {
  catalog: DarwinexSymbolInfo[]; folder: string; postfix: string; definitions: DarwinexDefinition[]; ranges: Record<string, never[]>;
  job: DarwinexJob | null; storageError: string; backendAvailable: boolean;
  refresh: () => Promise<void>; poll: () => Promise<void>;
  start: (kind: 'add' | 'import', definitions: DarwinexDefinition[], external: boolean, folder?: string, postfix?: string, files?: File[]) => Promise<void>;
  download: (request: DarwinexDownload, full: boolean, external: boolean) => Promise<void>;
  advance: () => void; action: (action: 'pause' | 'resume' | 'stop') => void;
}
function fromBackend(row: DarwinexRecord): DarwinexDefinition {
  return { id: row.id, symbol: row.symbol, underlying: row.underlying, instrument: row.instrument,
    source: 'Darwinex', timeframe: row.timeframe, broker: row.broker, brokerName: row.broker === '-1' ? 'Default' : row.broker,
    timezone: 'UTC', category: 'Tick data', from: row.date_from.slice(0, 10), to: row.date_to.slice(0, 10), bars: row.bars,
    availableFrom: row.options.metadata.date_from };
}
function message(cause: unknown): string { return cause instanceof Error ? cause.message : 'Darwinex operation failed.'; }
export const useDarwinex = create<Store>((set, get) => {
  let importFiles: File[] = [];
  let polling = false;
  let stopRequested = false;
  async function startNext(job: DarwinexJob): Promise<void> {
    const target = job.definitions[job.completed];
    let started: { job_id: string };
    if (job.kind === 'import') {
      const added = await darwinexAdd(target);
      if (stopRequested) { set({ job: { ...job, state: 'cancelled' } }); return; }
      started = await darwinexImport(added.id, target.underlying, importFiles);
    } else {
      const range = darwinexDownloadRanges({ ...job.request!, targets: [target] })[target.id];
      started = await darwinexDownload(target.id, range.from, range.to, job.request!.overwrite);
    }
    set({ job: { ...job, jobId: started.job_id } });
    if (stopRequested) await darwinexCancel(started.job_id);
  }
  function guard(external: boolean) {
    if (!get().backendAvailable) throw new Error(get().storageError || 'Darwinex backend is unavailable.');
    if (external || darwinexActive(get().job?.state)) throw new Error('Finish or stop the active data operation first.');
  }
  return {
    catalog: [], folder: '', postfix: '', definitions: [], ranges: {}, job: null, storageError: '', backendAvailable: false,
    refresh: async () => {
      try {
        const catalog = await darwinexCatalog();
        if (!catalog.available) { set({ backendAvailable: false, storageError: catalog.reason }); return; }
        set({ catalog: catalog.symbols, definitions: catalog.datasets.map(fromBackend), backendAvailable: true, storageError: '' });
      } catch (cause) { set({ backendAvailable: false, storageError: message(cause) }); }
    },
    start: async (kind, definitions, external, folder = '', postfix = '', files = []) => {
      guard(external);
      if (definitions.some(row => row.timezone !== 'UTC' && row.timezone !== 'Etc/UTC')) throw new Error('Darwinex currently stores source data in UTC.');
      stopRequested = false;
      importFiles = files;
      set({ folder, postfix });
      const job: DarwinexJob = { kind, definitions, state: 'running', completed: 0, progress: 0, canPause: false };
      set({ job });
      try {
        if (kind === 'import') { if (!files.length) throw new Error('Choose actual Darwinex log files.'); await startNext(job); return; }
        for (const row of definitions) {
          const created = await darwinexAdd(row);
          job.completed += 1; job.jobId = created.id;
          set({ job: { ...job, progress: 100 * job.completed / definitions.length } });
        }
        await get().refresh();
        set({ job: { ...job, state: 'completed', progress: 100 } });
      } catch (cause) { set({ job: { ...job, state: 'failed', error: message(cause) } }); await get().refresh(); throw cause; }
    },
    download: async (request, _full, external) => {
      guard(external); darwinexDownloadRanges(request);
      stopRequested = false;
      const job: DarwinexJob = { kind: 'download', request, definitions: request.targets, state: 'running', completed: 0, progress: 0, canPause: false };
      set({ job });
      try { await startNext(job); }
      catch (cause) { set({ job: { ...job, state: 'failed', error: message(cause) } }); throw cause; }
    },
    poll: async () => {
      const job = get().job;
      if (polling || !job || !['download', 'import'].includes(job.kind) || job.state !== 'running' || !job.jobId) return;
      polling = true;
      try {
        const status = await darwinexStatus(job.jobId);
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
      if (action !== 'stop' || !job || !['download', 'import'].includes(job.kind) || job.state !== 'running') return;
      stopRequested = true;
      if (!job.jobId) return;
      void darwinexCancel(job.jobId).then(() => get().poll()).catch(cause => set({ storageError: message(cause) }));
    },
  };
});
export function reservedDarwinex() { return useDarwinex.getState().definitions; }
