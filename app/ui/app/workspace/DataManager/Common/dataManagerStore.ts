import { normalizeLegacyBranding } from '../../../host/branding';
import { create } from 'zustand';
import { datasets } from './fixtures';
import { normalizeBrokerName, validateBroker, type BrokerProfile, type BrokerUpdateJob } from '../Catalogs/BrokerProfiles/brokerProfiles';

export interface MockDefinition {
  id: string; source: string; symbol: string; underlying: string; instrument: string;
  timeframe: string; broker: string; brokerName: string; timezone: string;
  category: string; from: string; to: string; bars: number;
}
const storageKey = 'sqx-data-manager-v1';

export interface AddDataRequest {
  symbols: string[];
  dataType: 'TICK' | 'M1';
  broker: string;
  postfix: string;
  instruments: string[];
  source?: string;
  category?: string;
}

interface DataState {
  definitions: MockDefinition[];
  brokers: BrokerProfile[];
  brokerJob: BrokerUpdateJob | null;
  storageError: string;
  addData: (request: AddDataRequest, existingSymbols?: string[]) => void;
  saveBroker: (profile: BrokerProfile) => void;
  saveBrokerStocks: (id: string, stocks: string[]) => void;
  removeBrokers: (ids: string[]) => void;
  importBrokers: (profiles: Omit<BrokerProfile, 'id'>[], overwrite: string[]) => number;
  startBrokerUpdate: (ids: string[], existing: string[]) => void;
  advanceBrokerUpdate: () => void;
  brokerAction: (action: 'pause' | 'resume' | 'stop') => void;
}

function completeBroker(value: Partial<BrokerProfile> & Pick<BrokerProfile, 'id' | 'name' | 'postfix' | 'timezone' | 'mtUse'>): BrokerProfile {
  return { desc: '', stockPickerUse: false, system: false, stocks: [], instruments: [], ...value };
}

function readState(): Pick<DataState, 'definitions' | 'brokers' | 'brokerJob' | 'storageError'> {
  try {
    const raw = localStorage.getItem(storageKey);
    if (!raw) return { definitions: [], brokers: [], brokerJob: null, storageError: '' };
    const value = normalizeLegacyBranding(JSON.parse(raw));
    if (![1, 2].includes(value.version) || !Array.isArray(value.definitions) || value.definitions.length > 10000
      || !Array.isArray(value.brokers) || value.brokers.length > 100
      || value.definitions.some((row: MockDefinition) => !row || ['id', 'source', 'symbol', 'underlying', 'instrument', 'timeframe', 'broker', 'brokerName', 'timezone', 'category', 'from', 'to'].some(key => typeof (row as unknown as Record<string, unknown>)[key] !== 'string') || row.bars !== 0)
      || value.brokers.some((broker: BrokerProfile) => !broker || ['id', 'name', 'postfix', 'timezone'].some(key => typeof (broker as unknown as Record<string, unknown>)[key] !== 'string') || typeof broker.mtUse !== 'boolean' || !Array.isArray(broker.instruments) || broker.instruments.some(item => typeof item !== 'string')))
      throw new Error('Invalid saved definitions');
    const brokers = (value.brokers as BrokerProfile[]).map(completeBroker);
    const brokerJob = value.version === 2 && value.brokerJob ? value.brokerJob as BrokerUpdateJob : null;
    if (brokerJob) {
      if (!['running', 'paused', 'cancelled', 'completed', 'failed'].includes(brokerJob.state) || !Number.isFinite(brokerJob.progress) || !Array.isArray(brokerJob.targets)) throw new Error('Invalid broker job');
      if (brokerJob.state === 'running') brokerJob.state = 'paused';
    }
    return { definitions: value.definitions, brokers, brokerJob, storageError: '' };
  } catch {
    return { definitions: [], brokers: [], brokerJob: null, storageError: 'Saved mock data could not be read. Existing browser storage has been preserved.' };
  }
}

export const useDataManagerStore = create<DataState>((set, get) => ({
  ...readState(),
  saveBroker: profile => {
    const state = get();
    if (state.storageError) throw new Error(state.storageError);
    const clean = validateBroker(profile, state.brokers, profile.id || undefined);
    const found = state.brokers.findIndex(row => row.id === profile.id);
    const brokers = [...state.brokers];
    if (found >= 0) brokers[found] = structuredClone(clean);
    else brokers.push({ ...structuredClone(clean), id: `broker-${crypto.randomUUID()}` });
    persistData(state, brokers, state.definitions, state.brokerJob);
    set({ brokers });
  },
  saveBrokerStocks: (id, stocks) => {
    const state = get();
    const index = state.brokers.findIndex(row => row.id === id);
    if (index < 0) throw new Error("Broker doesn't exist.");
    if (state.brokers[index].system) throw new Error("This broker can't be edited.");
    const brokers = [...state.brokers];
    brokers[index] = { ...brokers[index], stocks: [...stocks] };
    persistData(state, brokers, state.definitions, state.brokerJob);
    set({ brokers });
  },
  removeBrokers: ids => {
    const state = get();
    const selected = new Set(ids);
    const brokers = state.brokers.filter(row => !selected.has(row.id));
    persistData(state, brokers, state.definitions, state.brokerJob);
    set({ brokers });
  },
  importBrokers: (profiles, overwrite) => {
    const state = get();
    const replace = new Set(overwrite.map(name => normalizeBrokerName(name).toLowerCase()));
    const brokers = [...state.brokers];
    let count = 0;
    for (const raw of profiles) {
      const name = normalizeBrokerName(raw.name);
      const index = brokers.findIndex(row => row.name.toLowerCase() === name.toLowerCase());
      if (index >= 0) {
        if (!replace.has(name.toLowerCase()) || brokers[index].system) continue;
        brokers[index] = validateBroker({ ...raw, id: brokers[index].id }, brokers, brokers[index].id);
        count++;
      } else {
        brokers.push(validateBroker({ ...raw, id: `broker-${crypto.randomUUID()}` }, brokers));
        count++;
      }
    }
    persistData(state, brokers, state.definitions, state.brokerJob);
    set({ brokers });
    return count;
  },
  startBrokerUpdate: (ids, existing) => {
    const state = get();
    if (state.brokerJob && ['running', 'paused'].includes(state.brokerJob.state)) throw new Error('Please wait couple of seconds and try again.');
    const rows = ids.map(id => state.brokers.find(row => row.id === id)).filter((row): row is BrokerProfile => Boolean(row));
    if (!rows.length) throw new Error('You have to select some broker.');
    const seen = new Set(existing);
    const targets = rows.flatMap(row => row.stocks.map(ticker => ({ brokerId: row.id, ticker, symbol: ticker + row.postfix }))).filter(target => {
      if (seen.has(target.symbol)) return false;
      seen.add(target.symbol);
      return true;
    });
    if (!rows.some(row => row.stocks.length)) throw new Error('Nothing to update. Broker is without any stocks.');
    const brokerJob: BrokerUpdateJob = { brokerIds: ids, state: 'running', progress: 0, targets };
    persistData(state, state.brokers, state.definitions, brokerJob);
    set({ brokerJob });
  },
  advanceBrokerUpdate: () => {
    const state = get();
    if (state.brokerJob?.state !== 'running') return;
    const progress = Math.min(100, state.brokerJob.progress + 10);
    let definitions = state.definitions;
    let brokerJob = { ...state.brokerJob, progress, state: progress === 100 ? 'completed' as const : 'running' as const };
    if (progress === 100) {
      const today = new Date().toISOString().slice(0, 10);
      const additions = state.brokerJob.targets.map(target => {
        const broker = state.brokers.find(row => row.id === target.brokerId)!;
        return { id: `broker-data:${target.brokerId}:${target.symbol}`, source: 'Equity', symbol: target.symbol, underlying: target.ticker, instrument: target.symbol, timeframe: 'D1', broker: broker.id, brokerName: broker.name, timezone: broker.timezone, category: 'Stock', from: today, to: today, bars: 1 };
      });
      definitions = [...definitions, ...additions];
    }
    try {
      persistData(state, state.brokers, definitions, brokerJob);
      set({ definitions, brokerJob });
    } catch {
      set({ brokerJob: { ...state.brokerJob, state: 'failed', error: 'Unable to persist broker update progress.' } });
    }
  },
  brokerAction: action => {
    const state = get();
    if (!state.brokerJob || !['running', 'paused'].includes(state.brokerJob.state)) return;
    const brokerJob = { ...state.brokerJob, state: action === 'pause' ? 'paused' as const : action === 'resume' ? 'running' as const : 'cancelled' as const };
    persistData(state, state.brokers, state.definitions, brokerJob);
    set({ brokerJob });
  },
  addData: (request, existingSymbols) => {
    const state = get();
    if (state.storageError) throw new Error(state.storageError);
    if (!request.symbols.length) throw new Error('No symbols selected');
    if (!['TICK', 'M1'].includes(request.dataType)) throw new Error('Invalid data type');
    const broker = state.brokers.find(item => item.id === request.broker && item.mtUse);
    if (request.broker !== '-1' && !broker) throw new Error('Choose a valid broker profile');
    const existingNames = new Set([...datasets, ...state.definitions, ...(existingSymbols ?? []).map(s => ({ symbol: s }))].map(row => row.symbol));
    const additions = request.symbols.map((symbol, index): MockDefinition => {
      const name = symbol + request.postfix;
      if (existingNames.has(name)) throw new Error(`Data symbol ${name} already exists. Choose a different postfix.`);
      existingNames.add(name);
      const mapping = request.instruments[index] ?? '-1';
      if (broker && mapping !== '-1' && !broker.instruments.includes(mapping)) throw new Error('Select proper instrument or skip the symbol');
      return {
        id: `${(request.source ?? 'dukas').toLowerCase()}:${name}`,
        source: request.source ?? 'Dukascopy',
        symbol: name,
        underlying: symbol,
        instrument: mapping === '-1' ? symbol : mapping,
        timeframe: request.dataType,
        broker: request.broker,
        brokerName: broker?.name ?? 'Default',
        timezone: broker?.timezone ?? 'UTC',
        category: request.category ?? '—',
        from: '',
        to: '',
        bars: 0,
      };
    });
    const definitions = [...state.definitions, ...additions];
    if (definitions.length > 10000) throw new Error('Mock dataset limit reached');
    try {
      persistData(state, state.brokers, definitions, state.brokerJob);
    } catch {
      throw new Error('Unable to save mock definitions in browser storage. No symbols were added.');
    }
    set({ definitions });
  },
}));

function persistData(state: Pick<DataState, 'storageError'>, brokers: BrokerProfile[], definitions: MockDefinition[], brokerJob: BrokerUpdateJob | null): void {
  if (state.storageError) throw new Error(state.storageError);
  localStorage.setItem(storageKey, JSON.stringify({ version: 2, definitions, brokers, brokerJob }));
}
