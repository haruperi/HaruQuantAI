import { create } from 'zustand';
import { addDefinitions, cancelDownload, getCapability, startDownload, statusDownload, type BackendBroker, type BackendDataset } from './backend';
import { emptyDownload, validateDownload, type DownloadRequest, type DownloadState } from './dukascopyDownload';

/** Browser state mirrors the host and never persists market coverage. */
export interface DownloadStore extends DownloadState {
  storageError: string;
  available: boolean;
  definitionsAvailable: boolean;
  reason: string;
  definitions: BackendDataset[];
  brokers: BackendBroker[];
  brokerCatalogStatus: 'available' | 'unavailable';
  refresh: () => Promise<void>;
  addData: (request: { symbols: string[]; dataType: 'TICK' | 'M1'; broker: string; postfix: string; instruments: string[] }) => Promise<void>;
  start: (request: DownloadRequest, otherActive?: boolean) => Promise<void>;
  poll: () => Promise<void>;
  advance: () => void;
  action: (action: 'pause' | 'resume' | 'stop') => void;
}

export function dukascopyActive(state?: string): boolean {
  return state === 'running' || state === 'paused';
}

export const useDukascopyDownloads = create<DownloadStore>((set, get) => ({
  ...emptyDownload,
  ranges: {},
  storageError: '',
  available: false,
  definitionsAvailable: false,
  reason: 'market_catalog_migration_required',
  definitions: [],
  brokers: [],
  brokerCatalogStatus: 'unavailable',
  refresh: async () => {
    try {
      const catalog = await getCapability();
      const brokerCatalogStatus = catalog.broker_catalog_status === 'available'
        && Array.isArray(catalog.brokers) ? 'available' : 'unavailable';
      set({
        available: catalog.modes.standard === 'available',
        definitionsAvailable: catalog.definitions_available === true,
        reason: catalog.reason,
        definitions: catalog.datasets,
        brokers: brokerCatalogStatus === 'available' ? catalog.brokers : [],
        brokerCatalogStatus,
      });
    } catch {
      set({ available: false, definitionsAvailable: false, reason: 'backend_unavailable', definitions: [], brokers: [], brokerCatalogStatus: 'unavailable' });
    }
  },
  addData: async request => {
    if (!get().definitionsAvailable) throw new Error('Dataset storage is unavailable.');
    await addDefinitions(request);
    await get().refresh();
  },
  start: async (request, otherActive = false) => {
    if (!get().available) throw new Error('Dukascopy acquisition is unavailable.');
    if (otherActive || dukascopyActive(get().job?.state)) throw new Error('Finish or stop the active data operation first.');
    validateDownload(request);
    if (request.targets.length !== 1) throw new Error('Choose one Dukascopy dataset per download job.');
    const target = request.targets[0];
    if (!get().definitions.some(row => row.id === target.id)) throw new Error('Choose a registered Dukascopy dataset.');
    const started = await startDownload(target.id, request.dateFrom, request.dateTo, request.overwrite, request.downloadType);
    set({ job: { request, state: 'running', progress: 0, jobId: started.job_id, canPause: false }, preferred: request.downloadType });
  },
  poll: async () => {
    const job = get().job;
    if (!job?.jobId || !dukascopyActive(job.state)) return;
    try {
      const status = await statusDownload(job.jobId);
      const state = status.state === 'succeeded' ? 'completed'
        : status.state === 'cancelled' ? 'cancelled'
        : status.state === 'failed' || status.state === 'timed_out' ? 'failed' : 'running';
      set({ job: { ...job, state, progress: Math.round(status.progress * 100), error: status.error } });
      if (state === 'completed') await get().refresh();
    } catch {
      set({ job: { ...job, state: 'failed', error: 'Unable to read the host job status.' } });
    }
  },
  advance: () => {},
  action: action => {
    const job = get().job;
    if (action === 'stop' && job?.jobId && dukascopyActive(job.state)) {
      void cancelDownload(job.jobId).then(() => get().poll()).catch(() => {
        set({ job: { ...job, state: 'failed', error: 'Unable to cancel the host job.' } });
      });
    }
  },
}));
