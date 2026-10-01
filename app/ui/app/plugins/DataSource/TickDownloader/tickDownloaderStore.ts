import { create } from 'zustand';
import { validateTD, type TDRequest } from './tickDownloader';
import { tdCatalog, tdInspect, tdImport, tdStatus, tdCancel, encodeBI5, type TDFileInfo } from './backend';
export const tdActive = (state?: string) => state === 'running';
export interface TDDefinition { id: string; source: string; symbol: string; underlying: string; instrument: string; timeframe: string; broker: string; brokerName: string; timezone: string; category: string; from: string; to: string; bars: number }
interface ImportJob { request: TDRequest; state: 'running' | 'completed' | 'failed' | 'cancelled'; progress: number; completed: number; total: number; canPause: false; jobId?: string; error?: string }
interface Store {
 definitions: TDDefinition[]; job: ImportJob | null; folder: string; postfix: string; backendAvailable: boolean; storageError: string;
 refresh: () => Promise<void>; poll: () => Promise<void>;
 start: (request: TDRequest, available: string[], existing?: string[], otherActive?: boolean, files?: File[]) => Promise<void>;
 advance: () => void; action: (action: 'pause' | 'resume' | 'stop') => void;
}
const message = (cause: unknown) => cause instanceof Error ? cause.message : 'Tick Downloader import failed.';
export const useTickDownloader = create<Store>((set, get) => {
 let stopping = false, polling = false;
 let pending: { file: File; info: TDFileInfo }[] = [];
 async function next(job: ImportJob) {
   const selected = pending[job.completed];
   const content_base64 = await encodeBI5(selected.file);
   if (stopping) { set({ job: { ...job, state: 'cancelled' } }); pending = []; return; }
   const result = await tdImport(selected.info.symbol, job.request.postfix, selected.info.decimals, [{ hour: selected.info.hour, content_base64 }]);
   set({ job: { ...job, jobId: result.job_id } });
   if (stopping) await tdCancel(result.job_id);
 }
 return {
  definitions: [], job: null, folder: '', postfix: '', backendAvailable: false, storageError: '',
  refresh: async () => {
   try {
    const catalog = await tdCatalog();
    if (!catalog.available) { set({ backendAvailable: false, storageError: catalog.reason }); return; }
    set({ backendAvailable: true, storageError: '', definitions: catalog.datasets.map(row => ({ id: row.id, symbol: row.symbol, underlying: row.underlying, instrument: row.instrument, source: 'TickDownloader', timeframe: row.timeframe, broker: '-1', brokerName: 'Default', timezone: 'UTC', category: 'Tick data', from: row.date_from.slice(0, 10), to: row.date_to.slice(0, 10), bars: row.bars })) });
   } catch (cause) { set({ backendAvailable: false, storageError: message(cause) }); }
  },
  start: async (request, available, existing = [], otherActive = false, files = []) => {
   if (!get().backendAvailable) throw new Error(get().storageError || 'Tick Downloader backend unavailable.');
   if (otherActive || tdActive(get().job?.state)) throw new Error('Finish or stop the active data operation first.');
   validateTD(request, available, existing);
   if (!files.length) throw new Error('Select the actual BI5 files.');
   const inspected = await tdInspect(files.map(file => file.webkitRelativePath));
   const byPath = new Map(files.map(file => [file.webkitRelativePath, file]));
   pending = inspected.files.filter(info => request.symbols.includes(info.symbol)).sort((a, b) => a.symbol.localeCompare(b.symbol) || a.hour.localeCompare(b.hour)).map(info => ({ info, file: byPath.get(info.path)! }));
   if (!pending.length) throw new Error('No BI5 hours found for selected symbols.');
   stopping = false;
   const job: ImportJob = { request, state: 'running', progress: 0, completed: 0, total: pending.length, canPause: false };
   set({ job, folder: request.folder, postfix: request.postfix });
   try { await next(job); } catch (cause) { pending = []; set({ job: { ...job, state: 'failed', error: message(cause) } }); throw cause; }
  },
  poll: async () => {
   const job = get().job;
   if (polling || job?.state !== 'running' || !job.jobId) return;
   polling = true;
   try {
    const status = await tdStatus(job.jobId);
    if (get().job?.jobId !== job.jobId) return;
    if (status.state === 'succeeded') {
      const nextJob = { ...job, completed: job.completed + 1, progress: 100 * (job.completed + 1) / job.total };
      await get().refresh();
      if (stopping || nextJob.completed === job.total) { pending = []; set({ job: { ...nextJob, state: stopping ? 'cancelled' : 'completed' } }); }
      else { try { await next(nextJob); } catch (cause) { pending = []; set({ job: { ...nextJob, state: 'failed', error: message(cause) } }); } }
    } else if (['failed', 'timed_out', 'cancelled'].includes(status.state)) {
      pending = []; set({ job: { ...job, state: status.state === 'cancelled' ? 'cancelled' : 'failed', error: status.state === 'cancelled' ? undefined : 'BI5 import failed. Check the host log.' } }); await get().refresh();
    }
   } catch (cause) { set({ storageError: message(cause) }); } finally { polling = false; }
  },
  advance: () => {},
  action: action => {
   const job = get().job;
   if (action !== 'stop' || job?.state !== 'running') return;
   stopping = true;
   if (job.jobId) void tdCancel(job.jobId).then(() => get().poll()).catch(cause => set({ storageError: message(cause) }));
  },
 };
});
