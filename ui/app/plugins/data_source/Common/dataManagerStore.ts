import { normalizeLegacyBranding } from '../../../host/branding';
import { reservedDarwinex, useDarwinex } from '../Darwinex/darwinexStore';
import { cryptoActive, reservedCrypto, useCrypto } from '../Crypto/cryptoStore';
import { reservedYahoo, useYahoo, yahooActive } from '../Yahoo/yahooStore';
import { reservedSQDefinitions, sqActive, useSQData } from '../SQData/sqDataStore';
import { mt5Active, reservedMt5, useMt5Import } from '../MetaTrader/mt5ImportStore';
import { activeImport, useFileImports } from '../FileImport/fileImportStore';
import { useFileSymbols } from '../FileImport/fileSymbolsStore';
import { validateTD, type TDJob, type TDRequest } from '../TickDownloader/tickDownloader';
import { emptyDownload, resolveDownloadModes, downloadStep, validateDownload, availableStart, mergeRanges, validDate, type DownloadState, type DownloadRequest, type Interval } from '../Dukascopy/dukascopyDownload';
import { create } from 'zustand';
import { datasets } from './fixtures';
import { catalogue, type AddDukasRequest } from '../Dukascopy/dukascopy';
import { normalizeBrokerName, validateBroker, type BrokerProfile, type BrokerUpdateJob } from '../Catalogs/BrokerProfiles/brokerProfiles';
import { createDomainClient } from '../../../host/transport';

const dataClient = createDomainClient('/data');

export async function fetchRemoteDatasets(): Promise<MockDefinition[]> {
  try {
    const list = await dataClient.get<Array<{
      id: string;
      symbol: string;
      timeframe: string;
      broker?: string;
      source?: string;
      timezone?: string;
      bars?: number;
      bar_count?: number;
      bars_count?: number;
      date_from?: string;
      date_to?: string;
      category?: string;
    }>>('/datasets');
    return list.map(item => ({
      id: item.id,
      source: item.source || 'Server',
      symbol: item.symbol,
      underlying: item.symbol,
      instrument: item.symbol,
      timeframe: item.timeframe,
      broker: item.broker || 'default',
      brokerName: item.broker || 'Default',
      timezone: item.timezone || 'UTC',
      category: item.category || 'Forex',
      from: item.date_from || '',
      to: item.date_to || '',
      bars: item.bars ?? item.bar_count ?? item.bars_count ?? 0,
    }));
  } catch {
    return [];
  }
}

export interface MockDefinition {
  id: string; source: string; symbol: string; underlying: string; instrument: string;
  timeframe: string; broker: string; brokerName: string; timezone: string;
  category: string; from: string; to: string; bars: number;
}
const storageKey = 'sqx-data-manager-v1';
interface DataState { definitions: MockDefinition[]; brokers: BrokerProfile[]; brokerJob:BrokerUpdateJob|null; storageError: string; addData: (request: AddDukasRequest) => void;
  saveBroker:(profile:BrokerProfile)=>void; saveBrokerStocks:(id:string,stocks:string[])=>void; removeBrokers:(ids:string[])=>void; importBrokers:(profiles:Omit<BrokerProfile,'id'>[],overwrite:string[])=>number;
  startBrokerUpdate:(ids:string[],existing:string[])=>void; advanceBrokerUpdate:()=>void; brokerAction:(action:'pause'|'resume'|'stop')=>void;
  syncRemoteDatasets: () => Promise<void>;
}
function completeBroker(value:Partial<BrokerProfile>&Pick<BrokerProfile,'id'|'name'|'postfix'|'timezone'|'mtUse'>):BrokerProfile{return {desc:'',stockPickerUse:false,system:false,stocks:[],instruments:[],...value};}
function readState(): Pick<DataState, 'definitions' | 'brokers' | 'brokerJob' | 'storageError'> {
  try {
    const raw = localStorage.getItem(storageKey);
    if (!raw) return { definitions: [], brokers: [], brokerJob:null, storageError: '' };
    const value = normalizeLegacyBranding(JSON.parse(raw));
    if (![1,2].includes(value.version) || !Array.isArray(value.definitions) || value.definitions.length > 10000
      || !Array.isArray(value.brokers) || value.brokers.length > 100
      || value.definitions.some((row: MockDefinition) => !row || ['id', 'source', 'symbol', 'underlying', 'instrument', 'timeframe', 'broker', 'brokerName', 'timezone', 'category', 'from', 'to'].some(key => typeof (row as unknown as Record<string, unknown>)[key] !== 'string') || row.bars !== 0)
      || value.brokers.some((broker: BrokerProfile) => !broker || ['id', 'name', 'postfix', 'timezone'].some(key => typeof (broker as unknown as Record<string, unknown>)[key] !== 'string') || typeof broker.mtUse !== 'boolean' || !Array.isArray(broker.instruments) || broker.instruments.some(item => typeof item !== 'string')))
      throw new Error('Invalid saved definitions');
    const brokers=(value.brokers as BrokerProfile[]).map(completeBroker);const brokerJob=value.version===2&&value.brokerJob?value.brokerJob as BrokerUpdateJob:null;if(brokerJob){if(!['running','paused','cancelled','completed','failed'].includes(brokerJob.state)||!Number.isFinite(brokerJob.progress)||!Array.isArray(brokerJob.targets))throw new Error('Invalid broker job');if(brokerJob.state==='running')brokerJob.state='paused';}
    return { definitions: value.definitions, brokers, brokerJob, storageError: '' };
  } catch { return { definitions: [], brokers: [], brokerJob:null, storageError: 'Saved mock data could not be read. Existing browser storage has been preserved.' }; }
}
export const useDataManagerStore = create<DataState>((set, get) => ({
  ...readState(),
  saveBroker: profile => {const state=get();if(state.storageError)throw new Error(state.storageError);const clean=validateBroker(profile,state.brokers,profile.id||undefined);const found=state.brokers.findIndex(row=>row.id===profile.id);const brokers=[...state.brokers];if(found>=0)brokers[found]=structuredClone(clean);else brokers.push({...structuredClone(clean),id:`broker-${crypto.randomUUID()}`});persistData(state,brokers,state.definitions,state.brokerJob);set({brokers});},
  saveBrokerStocks:(id,stocks)=>{const state=get();const index=state.brokers.findIndex(row=>row.id===id);if(index<0)throw new Error("Broker doesn't exist.");if(state.brokers[index].system)throw new Error("This broker can't be edited.");const brokers=[...state.brokers];brokers[index]={...brokers[index],stocks:[...stocks]};persistData(state,brokers,state.definitions,state.brokerJob);set({brokers});},
  removeBrokers:ids=>{const state=get();const selected=new Set(ids);const brokers=state.brokers.filter(row=>!selected.has(row.id));persistData(state,brokers,state.definitions,state.brokerJob);set({brokers});},
  importBrokers:(profiles,overwrite)=>{const state=get();const replace=new Set(overwrite.map(name=>normalizeBrokerName(name).toLowerCase()));const brokers=[...state.brokers];let count=0;for(const raw of profiles){const name=normalizeBrokerName(raw.name);const index=brokers.findIndex(row=>row.name.toLowerCase()===name.toLowerCase());if(index>=0){if(!replace.has(name.toLowerCase())||brokers[index].system)continue;brokers[index]=validateBroker({...raw,id:brokers[index].id},brokers,brokers[index].id);count++;}else{brokers.push(validateBroker({...raw,id:`broker-${crypto.randomUUID()}`},brokers));count++;}}persistData(state,brokers,state.definitions,state.brokerJob);set({brokers});return count;},
  startBrokerUpdate:(ids,existing)=>{const state=get();if(state.brokerJob&&['running','paused'].includes(state.brokerJob.state))throw new Error('Please wait couple of seconds and try again.');const rows=ids.map(id=>state.brokers.find(row=>row.id===id)).filter((row):row is BrokerProfile=>Boolean(row));if(!rows.length)throw new Error('You have to select some broker.');const seen=new Set(existing);const targets=rows.flatMap(row=>row.stocks.map(ticker=>({brokerId:row.id,ticker,symbol:ticker+row.postfix}))).filter(target=>{if(seen.has(target.symbol))return false;seen.add(target.symbol);return true;});if(!rows.some(row=>row.stocks.length))throw new Error('Nothing to update. Broker is without any stocks.');const brokerJob:BrokerUpdateJob={brokerIds:ids,state:'running',progress:0,targets};persistData(state,state.brokers,state.definitions,brokerJob);set({brokerJob});},
  advanceBrokerUpdate:()=>{const state=get();if(state.brokerJob?.state!=='running')return;const progress=Math.min(100,state.brokerJob.progress+10);let definitions=state.definitions;let brokerJob={...state.brokerJob,progress,state:progress===100?'completed' as const:'running' as const};if(progress===100){const today=new Date().toISOString().slice(0,10);const additions=state.brokerJob.targets.map(target=>{const broker=state.brokers.find(row=>row.id===target.brokerId)!;return {id:`broker-data:${target.brokerId}:${target.symbol}`,source:'Equity',symbol:target.symbol,underlying:target.ticker,instrument:target.symbol,timeframe:'D1',broker:broker.id,brokerName:broker.name,timezone:broker.timezone,category:'Stock',from:today,to:today,bars:1};});definitions=[...definitions,...additions];}try{persistData(state,state.brokers,definitions,brokerJob);set({definitions,brokerJob});}catch{set({brokerJob:{...state.brokerJob,state:'failed',error:'Unable to persist broker update progress.'}});}},
  brokerAction:action=>{const state=get();if(!state.brokerJob||!['running','paused'].includes(state.brokerJob.state))return;const brokerJob={...state.brokerJob,state:action==='pause'?'paused' as const:action==='resume'?'running' as const:'cancelled' as const};persistData(state,state.brokers,state.definitions,brokerJob);set({brokerJob});},
  addData: request => {
    const state = get();
    if (useFileSymbols.getState().storageError) throw new Error(useFileSymbols.getState().storageError);
      if (useFileImports.getState().storageError) throw new Error(useFileImports.getState().storageError);
    if (state.storageError) throw new Error(state.storageError);
    if (!request.symbols.length) throw new Error('No symbols selected');
    if (!['TICK', 'M1'].includes(request.dataType)) throw new Error('Invalid data type');
    const broker = state.brokers.find(item => item.id === request.broker && item.mtUse);
    if (request.broker !== '-1' && !broker) throw new Error('Choose a valid broker profile');
    const existingNames = new Set([...reservedYahoo(), ...reservedCrypto(), ...reservedDarwinex(), ...reservedSQDefinitions(), ...reservedMt5(), ...datasets, ...state.definitions, ...useTickDownloader.getState().definitions, ...useFileSymbols.getState().definitions, ...useFileImports.getState().records, ...(activeImport(useFileImports.getState().job?.state) ? useFileImports.getState().job?.tasks.map(task => task.record) ?? [] : [])].map(row => row.symbol));
    const additions = request.symbols.map((symbol, index): MockDefinition => {
      const item = catalogue.find(row => row.symbol === symbol);
      if (!item) throw new Error('Unknown catalogue symbol');
      const name = symbol + request.postfix;
      if (existingNames.has(name)) throw new Error(`Data symbol ${name} already exists. Choose a different postfix.`);
      existingNames.add(name);
      const mapping = request.instruments[index] ?? '-1';
      if (broker && mapping !== '-1' && !broker.instruments.includes(mapping)) throw new Error('Select proper instrument or skip the symbol');
      return { id: `dukas:${name}`, source: 'Dukascopy', symbol: name, underlying: symbol,
        instrument: mapping === '-1' ? symbol : mapping, timeframe: request.dataType,
        broker: request.broker, brokerName: broker?.name ?? 'Default', timezone: broker?.timezone ?? 'UTC',
        category: item.category, from: '', to: '', bars: 0 };
    });
    const definitions = [...state.definitions, ...additions];
    if (definitions.length > 10000) throw new Error('Mock dataset limit reached');
    try { persistData(state,state.brokers,definitions,state.brokerJob); }
    catch { throw new Error('Unable to save mock definitions in browser storage. No symbols were added.'); }
    set({ definitions });
  },
  syncRemoteDatasets: async () => {
    try {
      const remote = await fetchRemoteDatasets();
      if (!remote.length) return;
      const state = get();
      const existingIds = new Set(state.definitions.map(d => d.id));
      const newItems = remote.filter(d => !existingIds.has(d.id));
      if (newItems.length > 0) {
        const merged = [...state.definitions, ...newItems];
        try { persistData(state, state.brokers, merged, state.brokerJob); } catch { /* ignore */ }
        set({ definitions: merged });
      }
    } catch {
      // Non-blocking sync
    }
  },
}));

function persistData(state:Pick<DataState,'storageError'>,brokers:BrokerProfile[],definitions:MockDefinition[],brokerJob:BrokerUpdateJob|null):void {if(state.storageError)throw new Error(state.storageError);localStorage.setItem(storageKey,JSON.stringify({version:2,definitions,brokers,brokerJob}));}

// Separate versioned mock download metadata preserves existing add-data v1 storage.
const downloadKey = 'sqx-data-download-v1';
function readDownloads(): DownloadState {
  const raw = localStorage.getItem(downloadKey);
  if (!raw) return { ...emptyDownload, ranges: {} };
  const saved = normalizeLegacyBranding(JSON.parse(raw));
  if (saved.version !== 1 || !saved.ranges || typeof saved.ranges !== 'object' || Array.isArray(saved.ranges)
    || Object.keys(saved.ranges).length > 10000 || ![null, 'standard', 'cdn', 'cdn-cn'].includes(saved.preferred)) throw new Error('Invalid saved downloads');
  for (const ranges of Object.values(saved.ranges) as Interval[][]) {
    if (!Array.isArray(ranges) || ranges.length > 1000 || ranges.some(row => !validDate(row.from) || !validDate(row.to) || row.from > row.to)) throw new Error('Invalid saved ranges');
  }
  if (saved.job) {
    if (!['running', 'paused', 'cancelled', 'completed', 'failed'].includes(saved.job.state) || !Number.isFinite(saved.job.progress) || saved.job.progress < 0 || saved.job.progress > 100) throw new Error('Invalid saved job');
    validateDownload(saved.job.request);
    saved.job.resolvedModes = resolveDownloadModes(saved.job.request);
    if (saved.job.state === 'running') saved.job.state = 'paused';
  }
  return { job: saved.job ?? null, preferred: saved.preferred, ranges: saved.ranges };
}
interface DownloadStore extends DownloadState {
  storageError: string;
  start: (request: DownloadRequest) => void;
  advance: () => void;
  action: (action: 'pause' | 'resume' | 'stop') => void;
}
export const useDukascopyDownloads = create<DownloadStore>((set, get) => {
  let initial: DownloadState = { ...emptyDownload, ranges: {} };
  let storageError = '';
  try { initial = readDownloads(); } catch { storageError = 'Saved mock downloads could not be read. Existing storage is preserved.'; }
  function persist(next: DownloadState) {
    if (get().storageError) throw new Error(get().storageError);
    localStorage.setItem(downloadKey, JSON.stringify({ version: 1, ...next }));
    set(next);
  }
  function snapshot(): DownloadState { const { job, ranges, preferred } = get(); return { job, ranges, preferred }; }
  return {
    ...initial, storageError,
    start: request => {
      if (yahooActive(useYahoo.getState().job?.state)) throw new Error('Finish or stop the active Yahoo operation first.');
      if (cryptoActive(useCrypto.getState().job?.state)) throw new Error('Finish or stop the active Crypto operation first.');
      if (sqActive(useDarwinex.getState().job?.state)) throw new Error('Finish or stop the active Darwinex operation first.');
      if (sqActive(useSQData.getState().job?.state)) throw new Error('Finish or stop the active market data operation first.');
      if (mt5Active(useMt5Import.getState().job?.state)) throw new Error('Finish or stop the active MT5 import first.');
      if (activeImport(useFileImports.getState().job?.state)) throw new Error('Finish or stop the active file import first.');
      if (get().job && ['running', 'paused'].includes(get().job!.state)) throw new Error('Finish or stop the active mock download first.');
      if (['running', 'paused'].includes(useTickDownloader.getState().job?.state ?? '')) throw new Error('Finish or stop the active import first.');
      validateDownload(request);
      try { persist({ ...snapshot(), preferred: request.downloadType, job: { request: structuredClone(request), resolvedModes: resolveDownloadModes(request), state: 'running', progress: 0 } }); }
      catch (cause) { throw new Error(cause instanceof Error && get().storageError ? cause.message : 'Unable to save mock download. No job was started.'); }
    },
    advance: () => {
      const state = snapshot(); if (!state.job || state.job.state !== 'running') return;
      const job = { ...state.job, progress: Math.min(100, state.job.progress + downloadStep(state.job)) };
      const ranges = { ...state.ranges };
      if (job.progress === 100) {
        job.state = 'completed';
        for (const target of job.request.targets) {
          const from = [job.request.dateFrom, availableStart(target, true)].sort().at(-1)!;
          ranges[target.id] = mergeRanges(ranges[target.id] ?? [], { from, to: job.request.dateTo }, job.request.overwrite);
        }
      }
      try { persist({ ...state, ranges, job }); }
      catch { set({ job: { ...state.job, state: 'failed', error: 'Unable to persist mock download progress. Previous saved coverage is unchanged.' } }); }
    },
    action: action => {
      const state = snapshot(); if (!state.job || !['running', 'paused'].includes(state.job.state)) return;
      const job = { ...state.job, state: action === 'pause' ? 'paused' as const : action === 'resume' ? 'running' as const : 'cancelled' as const };
      try { persist({ ...state, job }); }
      catch { set({ job: { ...state.job, state: 'failed', error: 'Unable to persist mock download action.' } }); }
    },
  };
});

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
      const saved = normalizeLegacyBranding(JSON.parse(raw));
      if (saved.version !== 1 || !Array.isArray(saved.definitions) || saved.definitions.length > 10000 || typeof saved.folder !== 'string' || typeof saved.postfix !== 'string'
        || saved.definitions.some((row: MockDefinition) => !row || ['id','source','symbol','underlying','instrument','timeframe','broker','brokerName','timezone','category','from','to'].some(key => typeof (row as unknown as Record<string, unknown>)[key] !== 'string') || row.bars !== 0)) throw new Error('Invalid saved import');
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
      validateTD(request, available, [...reservedYahoo(), ...reservedCrypto(), ...reservedDarwinex(), ...reservedSQDefinitions(), ...reservedMt5(), ...datasets, ...useDataManagerStore.getState().definitions, ...get().definitions, ...useFileSymbols.getState().definitions, ...useFileImports.getState().records, ...(activeImport(useFileImports.getState().job?.state) ? useFileImports.getState().job?.tasks.map(task => task.record) ?? [] : [])].map(row => row.symbol));
      if (get().definitions.length + request.symbols.length > 10000) throw new Error('Mock dataset limit reached.');
      const additions: MockDefinition[] = request.symbols.map(symbol => ({ id: `td:${symbol + request.postfix}`, symbol: symbol + request.postfix, underlying: symbol, instrument: symbol, source: 'TickDownloader', timeframe: 'TICK', broker: '-1', brokerName: 'Default', timezone: 'UTC', category: catalogue.find(row => row.symbol === symbol)?.category ?? '—', from: '', to: '', bars: 0 }));
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
