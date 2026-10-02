import { create } from 'zustand';
import { mt5Catalog, mt5Add, mt5Download, mt5Status, mt5Cancel, mt5Connect, mt5Symbols, type MT5Record } from './backend';
import { mt5ImportRanges, type Mt5Definition, type Mt5ImportRequest, type Mt5Symbol } from './mt5Import';
import type { BrokerProfile } from './presentation';
import { ApiClientError } from '../../../host/transport';

export const mt5Active = (state?: string) => state === 'running';
export const mt5ImportKey = 'sqx-mt5-import-v1';
export interface Mt5Job {
  kind: 'download'; definitions: Mt5Definition[]; request?: Mt5ImportRequest;
  state: 'running' | 'completed' | 'cancelled' | 'failed'; progress: number;
  completed: number; error?: string; jobId?: string; canPause: false;
}
interface Store {
  symbols: Mt5Symbol[]; folder: string; postfix: string; definitions: Mt5Definition[]; ranges: Record<string, never[]>;
  brokers: BrokerProfile[];
  job: Mt5Job | null; storageError: string; backendAvailable: boolean;
  refresh: () => Promise<void>; poll: () => Promise<void>;
  connect: (path: string) => Promise<void>;
  start: (request: Mt5ImportRequest, definitions: Mt5Definition[], external: boolean) => Promise<void>;
  advance: () => void; action: (action: 'pause' | 'resume' | 'stop') => void;
}
function fromBackend(row: MT5Record): Mt5Definition {
  const options = row.options ?? { metadata: {} };
  const metadata = options.metadata ?? {};
  const dateFrom = row.date_from ?? row.from ?? '';
  const dateTo = row.date_to ?? row.to ?? '';
  return {
    id: row.id,
    symbol: row.symbol,
    underlying: row.underlying,
    instrument: row.instrument,
    source: 'MT5',
    timeframe: (row.timeframe === 'TICK' ? 'TICK' : 'M1') as 'M1',
    broker: row.broker,
    brokerName: row.broker === '-1' ? 'Default' : (row.brokerName || row.broker),
    timezone: 'UTC',
    category: metadata.category || '',
    barType: 'start',
    from: typeof dateFrom === 'string' ? dateFrom.slice(0, 10) : '',
    to: typeof dateTo === 'string' ? dateTo.slice(0, 10) : '',
    bars: row.bars || 0,
    path: metadata.path || '',
    description: metadata.description || '',
  };
}
function message(cause: unknown): string {
  if (cause instanceof ApiClientError) return `${cause.message} [${cause.code}${cause.requestId ? `; request_id=${cause.requestId}` : ''}]`;
  return cause instanceof Error ? cause.message : 'MT5 operation failed.';
}
export const useMt5Import = create<Store>((set, get) => {
  let polling = false;
  let stopRequested = false;
  async function startNext(job: Mt5Job): Promise<void> {
    const request = job.request!;
    const target = job.definitions[job.completed];
    const range = mt5ImportRanges(request, get().symbols)[target.underlying];
    const added = await mt5Add(target);
    if (stopRequested) { set({ job: { ...job, state: 'cancelled' } }); await get().refresh(); return; }
    const started = await mt5Download(added.id, range.from, range.to);
    set({ job: { ...job, jobId: started.job_id } });
    if (stopRequested) await mt5Cancel(started.job_id);
  }
  function guard(external: boolean) {
    if (!get().backendAvailable) throw new Error(get().storageError || 'MT5 backend is unavailable.');
    if (external || mt5Active(get().job?.state)) throw new Error('Finish or stop the active data operation first.');
  }
  return {
    symbols: [], folder: '', postfix: '', definitions: [], ranges: {}, brokers: [], job: null, storageError: '', backendAvailable: false,
    refresh: async () => {
      try {
        const catalog = await mt5Catalog();
        if (!catalog.available) { set({ backendAvailable: false, storageError: catalog.reason }); return; }
        set({ definitions: catalog.datasets.map(fromBackend), brokers: catalog.brokers || [], backendAvailable: true, storageError: '' });
      } catch (cause) { set({ backendAvailable: false, storageError: message(cause) }); }
    },
    connect: async path => {
      if (mt5Active(get().job?.state)) throw new Error('Finish or stop the active import first.');
      try {
        await mt5Connect(path);
        const result = await mt5Symbols();
        set({ symbols: result.symbols, folder: path });
        await get().refresh();
      } catch (cause) { throw new Error(message(cause)); }
    },
    start: async (request, definitions, external) => {
      guard(external);
      if (!definitions.length) throw new Error('Select terminal symbols.');
      mt5ImportRanges(request, get().symbols);
      stopRequested = false;
      const job: Mt5Job = { kind: 'download', request, definitions, state: 'running', completed: 0, progress: 0, canPause: false };
      set({ job, postfix: request.postfix });
      try { await startNext(job); }
      catch (cause) { const detail = message(cause); set({ job: { ...job, state: 'failed', error: detail } }); throw new Error(detail); }
    },
    poll: async () => {
      const job = get().job;
      if (polling || job?.kind !== 'download' || job.state !== 'running' || !job.jobId) return;
      polling = true;
      try {
        const status = await mt5Status(job.jobId);
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
      void mt5Cancel(job.jobId).then(() => get().poll()).catch(cause => set({ storageError: message(cause) }));
    },
  };
});
export function reservedMt5() { return useMt5Import.getState().definitions; }
