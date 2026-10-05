import { create } from 'zustand';
import { fileCatalog, fileStart, fileStatus, fileCancel, fileSaveFormat, fileDeleteFormat, filePublishGroup, formatFromBackend } from './backend';
import type { ImportFormat, ImportJob, ImportRecord, ImportTask } from './fileImport';
interface Store {
  predefinedFormats: ImportFormat[]; formats: ImportFormat[]; records: ImportRecord[]; groups: { name: string; symbols: string[] }[];
  timezone: string; job: ImportJob | null; storageError: string; backendAvailable: boolean;
  refresh: () => Promise<void>; poll: () => Promise<void>;
  saveFormat: (format: ImportFormat, replace?: boolean) => Promise<void>; deleteFormat: (name: string) => Promise<void>;
  start: (tasks: ImportTask[], timezone: string, group: string, skipped: number, external: boolean) => Promise<void>;
  advance: () => void; action: (action: 'pause' | 'resume' | 'stop') => void;
}
export const activeImport = (state?: string) => state === 'running';
const message = (cause: unknown) => cause instanceof Error ? cause.message : 'File import failed.';
export const useFileImports = create<Store>((set, get) => {
  let polling = false; let stopping = false;
  async function next(job: ImportJob) {
    const request = job.tasks[job.completed].request;
    if (!request) throw new Error('Choose file contents for backend import.');
    const started = await fileStart(request);
    set({ job: { ...job, jobId: started.job_id } });
    if (stopping) await fileCancel(started.job_id);
  }
  return {
    predefinedFormats: [], formats: [], records: [], groups: [], timezone: 'Etc/UCT', job: null, storageError: '', backendAvailable: false,
    refresh: async () => {
      try {
        const catalog = await fileCatalog();
        if (!catalog.available) { set({ backendAvailable: false, storageError: catalog.reason }); return; }
        set({ backendAvailable: true, storageError: '', predefinedFormats: catalog.formats.map(formatFromBackend), formats: catalog.custom_formats.map(formatFromBackend), records: catalog.datasets.map(row => ({
          ...row, source: 'File import', connection: 'History', broker: '-1', brokerName: '—', category: '—',
          from: row.date_from.slice(0, 10), to: row.date_to.slice(0, 10), barType: 'start', timestamps: [], unknownBars: row.bars,
        })) });
      } catch (cause) { set({ backendAvailable: false, storageError: message(cause) }); }
    },
    saveFormat: async (format, replace = false) => { await fileSaveFormat(format, replace); await get().refresh(); },
    deleteFormat: async name => { await fileDeleteFormat(name); await get().refresh(); },
    start: async (tasks, timezone, group, skipped, external) => {
      if (!get().backendAvailable) throw new Error(get().storageError || 'File import backend is unavailable.');
      if (external || activeImport(get().job?.state)) throw new Error('Finish or stop the active data operation first.');
      if (!tasks.length) throw new Error('Choose data to import.');
      if (tasks.some(task => task.record.barType === 'end')) throw new Error('The source parser preserves start-of-bar timestamps. End-of-bar conversion is unavailable.');
      if (!['UTC', 'Etc/UCT'].includes(timezone)) throw new Error('The source parser interprets timestamps as UTC. Choose UTC for this import.');
      stopping = false;
      const job: ImportJob = { tasks, state: 'running', progress: 0, completed: 0, skipped, group, canPause: false };
      set({ job, timezone });
      try { await next(job); }
      catch (cause) { set({ job: { ...job, state: 'failed', error: message(cause) } }); throw cause; }
    },
    poll: async () => {
      const job = get().job;
      if (polling || job?.state !== 'running' || !job.jobId) return;
      polling = true;
      try {
        const status = await fileStatus(job.jobId);
        if (get().job?.jobId !== job.jobId) return;
        if (status.state === 'succeeded') {
          const completed = job.completed + 1;
          const updated = { ...job, completed, progress: 100 * completed / job.tasks.length };
          await get().refresh();
          if (stopping) set({ job: { ...updated, state: 'cancelled' } });
          else if (completed === job.tasks.length) {
            try {
              if (job.group) await filePublishGroup(job.group, job.tasks.map(task => task.request!.symbol));
              set({ job: { ...updated, state: 'completed' } });
            } catch (cause) { set({ job: { ...updated, state: 'failed', error: message(cause) } }); }
          }
          else await next(updated);
        } else if (['failed', 'cancelled', 'timed_out'].includes(status.state)) {
          set({ job: { ...job, state: status.state === 'cancelled' ? 'cancelled' : 'failed', error: status.state === 'cancelled' ? undefined : 'Backend import failed; check the host log.' } });
          await get().refresh();
        } else {
          const fraction = status.total_partitions ? status.published_partitions / status.total_partitions : 0;
          set({ job: { ...job, progress: Math.min(99, 100 * (job.completed + fraction) / job.tasks.length) } });
        }
      } catch (cause) { set({ storageError: message(cause) }); }
      finally { polling = false; }
    },
    advance: () => { void get().poll(); },
    action: action => {
      const job = get().job;
      if (action !== 'stop' || job?.state !== 'running') return;
      stopping = true;
      if (job.jobId) void fileCancel(job.jobId).then(() => get().poll()).catch(cause => set({ storageError: message(cause) }));
    },
  };
});
