import {createDownloadStore} from '../Dukascopy/downloadStore';
import { normalizeSymbolContract } from './symbolContract';
import { createSymbolDataClient } from './symbolContract';
import { normalizeLegacyBranding } from '../../../host/branding';
import { reservedDarwinex, useDarwinex } from '../Darwinex/darwinexStore';
import { cryptoActive, reservedCrypto, useCrypto } from '../Crypto/cryptoStore';
import { reservedYahoo, useYahoo, yahooActive } from '../Yahoo/yahooStore';
import { reservedSQDefinitions, sqActive, useSQData } from '../SQData/sqDataStore';
import { mt5Active, reservedMt5, useMt5Import } from '../MetaTrader/mt5ImportStore';
import { activeImport, useFileImports } from '../FileImport/fileImportStore';
import { useFileSymbols } from '../FileImport/fileSymbolsStore';
import { validateTD, type TDJob, type TDRequest } from '../TickDownloader/tickDownloader';
import { validDate } from '../Dukascopy/dukascopyDownload';
import { create } from 'zustand';
import { catalogue, type AddDukasRequest } from '../Dukascopy/dukascopy';
import { normalizeBrokerName, validateBroker, type BrokerProfile, type BrokerUpdateJob } from '../Catalogs/BrokerProfiles/brokerProfiles';
import {
  fetchBrokers,
  deleteBrokers,
  saveBroker as saveBrokerApi,
  saveBrokerStocks as saveBrokerStocksApi,
} from '../Catalogs/BrokerProfiles/brokerApiClient';
import {type DomainClient } from '../../../host/transport';

let dataClient = createSymbolDataClient('/data');
let catalogRequest = 0;
let brokerRequest = 0;
let registeringDukascopy = false;

async function registrationRequest<T>(operation: Promise<T>): Promise<T> {
  let timer: ReturnType<typeof setTimeout> | undefined;
  const deadline = new Promise<never>((_resolve, reject) => {
    timer = setTimeout(() => reject(new Error('Registration request timed out. Refresh before retrying; the last request may still complete.')), 30000);
  });
  try { return await Promise.race([operation, deadline]); }
  finally { clearTimeout(timer); }
}

export class DukascopyRegistrationError extends Error {
  constructor(message: string, public readonly confirmedSymbols: string[]) {
    super(message);
  }
}

export function setDataClient(client: DomainClient): void {
  dataClient = client;
}

export function normalizeRelativePath(path?: string): string {
  if (!path) return '';
  const trimmed = path.trim();
  const dataIdx = trimmed.search(/data[\\/]/i);
  if (dataIdx >= 0) {
    return trimmed.slice(dataIdx);
  }
  return trimmed;
}

export async function fetchRemoteDatasets(): Promise<MockDefinition[]> {
  const list = await dataClient.get<Array<{
    id: string;
    symbol: string;
    timeframe: string;
    broker?: string;
    broker_name?: string;
    source?: string;
    timezone?: string;
    bars?: number;
    bar_count?: number;
    bars_count?: number;
    total_records?: number;
    total_days?: number;
    date_from?: string;
    date_to?: string;
    category?: string;
    underlying?: string;
    symbolDefinition?: string;
    path?: string;
    bar_type?: string;
  }>>('/home/datasets');
  if (!Array.isArray(list) || list.some(item => !item ||
      typeof item.id !== 'string' || typeof item.symbol !== 'string' || typeof item.timeframe !== 'string' ||
      [item.total_days, item.total_records, item.bars, item.bar_count, item.bars_count]
        .some(value => value !== undefined && (typeof value !== 'number' || !Number.isFinite(value) || value < 0)))) {
    throw new Error('Invalid saved dataset catalog response.');
  }
  return list.map(item => {
    let bName = (item.broker_name || item.broker || 'Default').trim();
    if (bName === '-1') bName = 'Default';
    if (bName.startsWith('[[') && bName.endsWith(']]')) bName = bName.slice(2, -2).trim();
    return {
      id: item.id,
      source: item.source || 'Server',
      symbol: item.symbol,
      underlying: item.underlying || item.symbol,
      symbolDefinition: item.symbolDefinition || item.symbol,
      timeframe: item.timeframe,
      broker: item.broker || 'default',
      brokerName: bName,
      timezone: item.timezone || 'UTC',
      category: item.category || 'Forex',
      from: (item.date_from || '').split(/[T ]/)[0],
      to: (item.date_to || '').split(/[T ]/)[0],
      bars: item.total_records ?? item.bars ?? item.bar_count ?? item.bars_count ?? 0,
      totalDays: item.total_days ?? 0,
      path: normalizeRelativePath(item.path),
      barType: item.bar_type || 'Start of bar',
    };
  });
}

export interface MockDefinition {
  id: string; source: string; symbol: string; underlying: string; symbolDefinition: string;
  timeframe: string; broker: string; brokerName: string; timezone: string;
  category: string; from: string; to: string; bars: number;
  path?: string;
  barType?: string;
  totalDays?: number;
}
const storageKey = 'sqx-data-manager-v1';
interface DataState { definitions: MockDefinition[]; brokers: BrokerProfile[]; brokerJob:BrokerUpdateJob|null; storageError: string; addData: (request: AddDukasRequest) => Promise<void>;
  savedDatasets: MockDefinition[] | null;
  catalogLoading: boolean;
  catalogError: string;
  saveBroker:(profile:BrokerProfile)=>Promise<void>; saveBrokerStocks:(id:string,stocks:string[])=>Promise<void>; removeBrokers:(ids:string[])=>Promise<void>; importBrokers:(profiles:Omit<BrokerProfile,'id'>[],overwrite:string[])=>Promise<number>;
  startBrokerUpdate:(ids:string[],existing:string[])=>void; advanceBrokerUpdate:()=>void; brokerAction:(action:'pause'|'resume'|'stop')=>void;
  syncRemoteDatasets: () => Promise<void>;
  brokerLoading: boolean; brokerError: string;
  syncBrokers: () => Promise<void>;
  editDataset: (id: string, updates: Partial<MockDefinition>) => Promise<void>;
  clearDataset: (id: string) => Promise<void>;
  removeDataset: (id: string) => Promise<void>;
  fetchChartBars: (datasetId: string, limit?: number, offset?: number) => Promise<Array<{ datetime: string; open: number; high: number; low: number; close: number; volume: number }>>;
}
function completeBroker(value:Partial<BrokerProfile>&Pick<BrokerProfile,'id'|'name'|'postfix'|'timezone'|'mtUse'>):BrokerProfile{return {desc:'',stockPickerUse:false,system:false,stocks:[],symbols:[],...value};}
function readState(): Pick<DataState, 'definitions' | 'brokers' | 'brokerJob' | 'storageError'> {
  try {
    const raw = localStorage.getItem(storageKey);
    if (!raw) return { definitions: [], brokers: [], brokerJob:null, storageError: '' };
    const value = normalizeLegacyBranding(normalizeSymbolContract(JSON.parse(raw)));
    if (![1,2].includes(value.version) || !Array.isArray(value.definitions) || value.definitions.length > 10000
      || !Array.isArray(value.brokers) || value.brokers.length > 100
      || value.definitions.some((row: MockDefinition) => !row || ['id', 'source', 'symbol', 'underlying', 'symbolDefinition', 'timeframe', 'broker', 'brokerName', 'timezone', 'category', 'from', 'to'].some(key => typeof (row as unknown as Record<string, unknown>)[key] !== 'string') || typeof row.bars !== 'number')
      || value.brokers.some((broker: BrokerProfile) => !broker || ['id', 'name', 'postfix', 'timezone'].some(key => typeof (broker as unknown as Record<string, unknown>)[key] !== 'string') || typeof broker.mtUse !== 'boolean' || !Array.isArray(broker.symbols) || broker.symbols.some(item => typeof item !== 'string')))
      throw new Error('Invalid saved definitions');
    const brokers=(value.brokers as BrokerProfile[]).map(completeBroker);const brokerJob=value.version===2&&value.brokerJob?value.brokerJob as BrokerUpdateJob:null;if(brokerJob){if(!['running','paused','cancelled','completed','failed'].includes(brokerJob.state)||!Number.isFinite(brokerJob.progress)||!Array.isArray(brokerJob.targets))throw new Error('Invalid broker job');if(brokerJob.state==='running')brokerJob.state='paused';}
    const cleanDefinitions = (value.definitions as MockDefinition[]).filter(
      row => !row.id.startsWith('broker-data:')
    );
    return { definitions: cleanDefinitions, brokers, brokerJob, storageError: '' };
  } catch { return { definitions: [], brokers: [], brokerJob:null, storageError: 'Saved mock data could not be read. Existing browser storage has been preserved.' }; }
}
export const useDataManagerStore = create<DataState>((set, get) => ({
  ...readState(),
  brokers: [], brokerJob: null,
  savedDatasets: null,
  brokerLoading: false, brokerError: '',
  catalogLoading: false,
  catalogError: '',
  saveBroker: async profile => {
    const state = get();
    const clean = validateBroker(profile, state.brokers, profile.id || undefined);
    const saved = await saveBrokerApi(clean);
    ++brokerRequest;
    set(current => ({brokerLoading:false,brokers: current.brokers.some(row => row.id === saved.id)
      ? current.brokers.map(row => row.id === saved.id ? saved : row) : [...current.brokers,saved]}));
  },
  saveBrokerStocks: async (id, stocks) => {
    const state = get();
    const index = state.brokers.findIndex(row => row.id === id);
    if (index < 0) throw new Error("Broker doesn't exist.");
    if (state.brokers[index].system) throw new Error("This broker can't be edited.");
    const confirmed = await saveBrokerStocksApi(id, stocks);
    ++brokerRequest;
    set(current => ({brokerLoading:false,brokers: current.brokers.map(row => row.id === id ? {...row,stocks:confirmed} : row)}));
  },
  removeBrokers: async ids => {
    const selected = ids.map(id => get().brokers.find(row => row.id === id));
    if (selected.some(row => !row)) throw new Error('Choose saved broker profiles.');
    const deleted = await deleteBrokers(ids);
    ++brokerRequest;
    set(current => ({brokerLoading:false,brokerError:'',brokers:current.brokers.filter(row => !deleted.includes(row.id))}));
  },
  importBrokers: async (profiles, overwrite) => {
    const state = get();
    const replace = new Set(overwrite.map(name => normalizeBrokerName(name).toLowerCase()));
    let count = 0;
    try {
    for (const raw of profiles) {
      const name = normalizeBrokerName(raw.name);
      const existing = state.brokers.find(row => row.name.toLowerCase() === name.toLowerCase());
      if (existing) {
        if (!replace.has(name.toLowerCase()) || existing.system) continue;
        const updated = await saveBrokerApi({
          id: existing.id,
          name,
          desc: raw.desc,
          postfix: raw.postfix,
          timezone: raw.timezone,
          mtUse: raw.mtUse,
          stockPickerUse: raw.stockPickerUse,
          system: false,
          stocks: raw.stocks,
          symbols: [], spreadModel: raw.spreadModel, commissionModel: raw.commissionModel,
        });
        if (raw.stockPickerUse) {
          await saveBrokerStocksApi(updated.id, raw.stocks);
        }
        count++;
      } else {
        const created = await saveBrokerApi({
          id: '',
          name,
          desc: raw.desc,
          postfix: raw.postfix,
          timezone: raw.timezone,
          mtUse: raw.mtUse,
          stockPickerUse: raw.stockPickerUse,
          system: false,
          stocks: raw.stocks,
          symbols: [], spreadModel: raw.spreadModel, commissionModel: raw.commissionModel,
        });
        if (raw.stockPickerUse) {
          await saveBrokerStocksApi(created.id, raw.stocks);
        }
        count++;
      }
    }
    } catch (cause) {
      await get().syncBrokers();
      throw new Error(`${count} broker profiles fully saved; loading stopped. ${cause instanceof Error ? cause.message : 'Unable to save profile or stocks.'}`);
    }
    await get().syncBrokers();
    if (get().brokerError) throw new Error(`${count} profiles saved; refresh failed: ${get().brokerError}`);
    return count;
  },
  startBrokerUpdate: () => { throw new Error('Automatic broker data updates are not implemented.'); },
  advanceBrokerUpdate: () => {
    const state = get();
    if (state.brokerJob?.state !== 'running') return;
    const progress = Math.min(100, state.brokerJob.progress + 10);
    const brokerJob: BrokerUpdateJob = {
      ...state.brokerJob,
      progress,
      state: progress === 100 ? ('completed' as const) : ('running' as const),
    };
    try {
      persistData(state, state.brokers, state.definitions, brokerJob);
      set({ brokerJob });
      if (progress === 100) {
        get().syncRemoteDatasets().catch(() => {});
      }
    } catch {
      set({
        brokerJob: {
          ...state.brokerJob,
          state: 'failed',
          error: 'Unable to persist broker update progress.',
        },
      });
    }
  },
  brokerAction:action=>{const state=get();if(!state.brokerJob||!['running','paused'].includes(state.brokerJob.state))return;const brokerJob={...state.brokerJob,state:action==='pause'?'paused' as const:action==='resume'?'running' as const:'cancelled' as const};persistData(state,state.brokers,state.definitions,brokerJob);set({brokerJob});},
  addData: async request => {
    if (registeringDukascopy) throw new Error('A symbol registration is already running.');
    if (!request.symbols.length) throw new Error('No symbols selected');
    if (!['TICK', 'M1'].includes(request.dataType)) throw new Error('Invalid data type');
    const postfix = request.postfix.toUpperCase();
    if (!/^[A-Z0-9_.-]*$/.test(postfix)) throw new Error('Use a safe alphanumeric postfix.');
    const items = request.symbols.map(symbol => {
      const item = catalogue.find(row => row.symbol === symbol);
      if (!item) throw new Error('Unknown catalogue symbol');
      return item;
    });
    if (new Set(request.symbols).size !== items.length) throw new Error('Duplicate symbol selection.');
    registeringDukascopy = true;
    const confirmed = new Set<string>();
    const baseline = new Set<string>();
    let attempted = false;
    const reconcile = async () => {
      const remote = await registrationRequest(fetchRemoteDatasets());
      ++catalogRequest;
      set({ savedDatasets: remote, definitions: remote.map(row => ({ ...row })), catalogError: '', catalogLoading: false });
      return remote;
    };
    try {
      const before = await reconcile();
      before.forEach(row => baseline.add(row.id));
      for (const item of items) {
        const symbol = item.symbol + postfix;
        if (symbol.length > 100) throw new Error('Data symbol exceeds 100 characters.');
        const id = `dukascopy:${symbol}:${request.dataType}`;
        if (baseline.has(id)) throw new Error(`Data symbol ${symbol} already exists. Choose a different postfix.`);
      }
      for (const [index, item] of items.entries()) {
        attempted = true;
        const symbol = item.symbol + postfix;
        const id = `dukascopy:${symbol}:${request.dataType}`;
        const saved = await registrationRequest(dataClient.post<Record<string, unknown>>('/datasets', {
          source: 'dukascopy', symbol, underlying: item.symbol, timeframe: request.dataType,
          broker: request.broker, symbolDefinition: request.symbolDefinitions[index] ?? '-1',
        }));
        if (!saved || saved.id !== id || saved.symbol !== symbol || saved.underlying !== item.symbol ||
            saved.timeframe !== request.dataType || saved.source !== 'dukascopy' ||
            ['broker', 'timezone', 'symbolDefinition', 'path', 'category'].some(key => typeof saved[key] !== 'string') || saved.bars !== 0) {
          throw new Error('The host did not confirm the requested dataset. Refresh before retrying.');
        }
        confirmed.add(item.symbol);
      }
      const after = await reconcile();
      if (items.some(item => !after.some(row => row.id === `dukascopy:${item.symbol + postfix}:${request.dataType}` && row.underlying === item.symbol))) {
        throw new Error('Registered symbols are missing from the saved catalog. Refresh before retrying.');
      }
    } catch (cause) {
      let refreshFailed = false;
      if (attempted) {
        try {
          const remote = await reconcile();
          for (const item of items) {
            if (remote.some(row => row.id === `dukascopy:${item.symbol + postfix}:${request.dataType}` &&
                !baseline.has(row.id) && row.underlying === item.symbol && row.timeframe === request.dataType)) confirmed.add(item.symbol);
          }
        } catch {
          refreshFailed = true;
          set({ catalogError: 'Unable to reconcile registrations. Refresh the saved catalog before retrying.' });
        }
      }
      const detail = cause instanceof Error ? cause.message : 'Unable to register symbols.';
      throw new DukascopyRegistrationError(
        `${confirmed.size} of ${items.length} symbols confirmed. ${detail}${refreshFailed ? ' Refresh the catalog before retrying; the last request may have succeeded.' : ''}`,
        [...confirmed],
      );
    } finally {
      registeringDukascopy = false;
    }
  },
  syncRemoteDatasets: async () => {
    const request = ++catalogRequest;
    set({ catalogLoading: true, catalogError: '' });
    try {
      const remote = await fetchRemoteDatasets();
      if (request !== catalogRequest) return;
      set({ savedDatasets: remote, definitions: remote.map(row => ({ ...row })) });
    } catch (cause) {
      if (request !== catalogRequest) return;
      set({ catalogError: cause instanceof Error ? cause.message : 'Unable to load saved dataset catalog.' });
    } finally {
      if (request === catalogRequest) set({ catalogLoading: false });
    }
  },
  syncBrokers: async () => {
    const request = ++brokerRequest;
    set({brokerLoading:true,brokerError:''});
    try {
      const remote = await fetchBrokers();
      if (request === brokerRequest) set({brokers:remote});
    } catch (cause) {
      if (request === brokerRequest) set({brokers:[],brokerError:cause instanceof Error ? cause.message : 'Unable to load broker profiles.'});
    } finally { if (request === brokerRequest) set({brokerLoading:false}); }
  },
  editDataset: async (id: string, updates: Partial<MockDefinition>) => {
    const state = get();
    await dataClient.put(`/datasets/${encodeURIComponent(id)}`, {
      symbol: updates.symbol,
      broker: updates.broker,
      timezone: updates.timezone,
      category: updates.category,
      symbolDefinition: updates.symbolDefinition,
    });
    const definitions = state.definitions.map(d => (d.id === id ? { ...d, ...updates } : d));
    try { persistData(state, state.brokers, definitions, state.brokerJob); } catch { /* ignore */ }
    set({ definitions });
    await get().syncRemoteDatasets();
  },
  clearDataset: async (id: string) => {
    const state = get();
    await dataClient.post(`/datasets/${encodeURIComponent(id)}/clear`, {});
    const definitions = state.definitions.map(d => (d.id === id ? { ...d, bars: 0, from: '', to: '' } : d));
    try { persistData(state, state.brokers, definitions, state.brokerJob); } catch { /* ignore */ }
    set({ definitions });
    await get().syncRemoteDatasets();
  },
  removeDataset: async (id: string) => {
    const state = get();
    await dataClient.post(`/datasets/${encodeURIComponent(id)}/delete`, {});
    const definitions = state.definitions.filter(d => d.id !== id);
    try { persistData(state, state.brokers, definitions, state.brokerJob); } catch { /* ignore */ }
    set({ definitions });
    await get().syncRemoteDatasets();
  },
  fetchChartBars: async (datasetId: string, limit = 500, offset = 0) => {
    const resp = await dataClient.post<{ bars: Array<{ datetime: string; open: number; high: number; low: number; close: number; volume: number }> }>('/datasets/review-chart', {
      dataset_id: datasetId,
      limit,
      offset,
    });
    return resp?.bars ?? [];
  },
}));

function persistData(state:Pick<DataState,'storageError'>,brokers:BrokerProfile[],definitions:MockDefinition[],brokerJob:BrokerUpdateJob|null):void {if(state.storageError)throw new Error(state.storageError);localStorage.setItem(storageKey,JSON.stringify({version:2,definitions,brokers,brokerJob}));}

// Separate versioned mock download metadata preserves existing add-data v1 storage.
export const useDukascopyDownloads = createDownloadStore(() => useDataManagerStore.getState().syncRemoteDatasets());

interface TDState {
  definitions: MockDefinition[]; job: TDJob | null; folder: string; postfix: string; storageError: string;
  start: (request: TDRequest, available: string[]) => void;
  advance: () => void;
  action: (action: 'pause' | 'resume' | 'stop') => void;
}
const tdKey = 'sqx-tickdownloader-v1';
export const useTickDownloader = create<TDState>((set, get) => {
  let initial: Pick<TDState, 'definitions' | 'job' | 'folder' | 'postfix' | 'storageError'> = { definitions: [], job: null, folder: '', postfix: '', storageError: '' };
  try {
    const raw = localStorage.getItem(tdKey);
    if (raw) {
      const saved = normalizeLegacyBranding(normalizeSymbolContract(JSON.parse(raw)));
      if (saved.version !== 1 || !Array.isArray(saved.definitions) || saved.definitions.length > 10000 || typeof saved.folder !== 'string' || typeof saved.postfix !== 'string'
        || saved.definitions.some((row: MockDefinition) => !row || ['id','source','symbol','underlying','symbolDefinition','timeframe','broker','brokerName','timezone','category','from','to'].some(key => typeof (row as unknown as Record<string, unknown>)[key] !== 'string') || row.bars !== 0)) throw new Error('Invalid saved import');
      if (saved.job) {
        if (!['running','paused','completed','cancelled','failed'].includes(saved.job.state) || !Number.isFinite(saved.job.progress) || saved.job.progress < 0 || saved.job.progress > 100) throw new Error('Invalid import job');
        validateTD(saved.job.request, saved.job.request.symbols, []);
        if (saved.job.state === 'running') saved.job.state = 'paused';
      }
      initial = { definitions: saved.definitions, folder: saved.folder, postfix: saved.postfix, job: saved.job ?? null, storageError: '' };
    }
  } catch { initial.storageError = 'Saved TickDownloader mock state could not be read. Existing storage is preserved.'; }
  function persist(patch: Partial<TDState>) {
    const next = { ...get(), ...patch };
    if (next.storageError) throw new Error(next.storageError);
    localStorage.setItem(tdKey, JSON.stringify({ version: 1, definitions: next.definitions, job: next.job, folder: next.folder, postfix: next.postfix }));
    set(patch);
  }
  return { ...initial,
    start: (request, available) => {
      if (yahooActive(useYahoo.getState().job?.state)) throw new Error('Finish or stop the active Yahoo operation first.');
      if (cryptoActive(useCrypto.getState().job?.state)) throw new Error('Finish or stop the active Crypto operation first.');
      if (sqActive(useDarwinex.getState().job?.state)) throw new Error('Finish or stop the active Darwinex operation first.');
      if (sqActive(useSQData.getState().job?.state)) throw new Error('Finish or stop the active market data operation first.');
      if (mt5Active(useMt5Import.getState().job?.state)) throw new Error('Finish or stop the active MT5 import first.');
      if (activeImport(useFileImports.getState().job?.state)) throw new Error('Finish or stop the active file import first.');
      if ([get().job?.state, useDukascopyDownloads.getState().job?.state].some(state => state === 'running' || state === 'paused')) throw new Error('Finish or stop the active data operation first.');
      if (useFileSymbols.getState().storageError) throw new Error(useFileSymbols.getState().storageError);
      if (useFileImports.getState().storageError) throw new Error(useFileImports.getState().storageError);
      validateTD(request, available, [...reservedYahoo(), ...reservedCrypto(), ...reservedDarwinex(), ...reservedSQDefinitions(), ...reservedMt5(), ...useDataManagerStore.getState().definitions, ...get().definitions, ...useFileSymbols.getState().definitions, ...useFileImports.getState().records, ...(activeImport(useFileImports.getState().job?.state) ? useFileImports.getState().job?.tasks.map(task => task.record) ?? [] : [])].map(row => row.symbol));
      if (get().definitions.length + request.symbols.length > 10000) throw new Error('Mock dataset limit reached.');
      const additions: MockDefinition[] = request.symbols.map(symbol => ({ id: `td:${symbol + request.postfix}`, symbol: symbol + request.postfix, underlying: symbol, symbolDefinition: symbol, source: 'TickDownloader', timeframe: 'TICK', broker: '-1', brokerName: 'Default', timezone: 'UTC', category: catalogue.find(row => row.symbol === symbol)?.category ?? '—', from: '', to: '', bars: 0 }));
      try { persist({ folder: request.folder, postfix: request.postfix, definitions: [...get().definitions, ...additions], job: { request: structuredClone(request), state: 'running', progress: 0 } }); }
      catch { throw new Error(get().storageError || 'Unable to save mock import. No import was started.'); }
    },
    advance: () => {
      const job = get().job; if (!job || job.state !== 'running') return;
      const progress = Math.min(100, job.progress + 5);
      try { persist({ job: { ...job, progress, state: progress === 100 ? 'completed' : 'running' } }); }
      catch { set({ job: { ...job, state: 'failed', error: 'Unable to persist mock import progress.' } }); }
    },
    action: action => {
      const job = get().job; if (!job || !['running','paused'].includes(job.state)) return;
      try { persist({ job: { ...job, state: action === 'pause' ? 'paused' : action === 'resume' ? 'running' : 'cancelled' } }); }
      catch { set({ job: { ...job, state: 'failed', error: 'Unable to persist mock import action.' } }); }
    },
  };
});
