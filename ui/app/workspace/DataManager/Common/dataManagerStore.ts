import { catalogPort } from './catalogClient';
import { normalizeLegacyBranding } from '../../../host/branding';
import { create } from 'zustand';
import { normalizeBrokerName, validateBroker, type BrokerProfile } from '../Catalogs/BrokerProfiles/brokerProfiles';

const storageKey = 'sqx-data-manager-v1';

interface DataState {
  brokers: BrokerProfile[];
  storageError: string; refresh:()=>Promise<void>; importLegacy:()=>Promise<void>;
  saveBroker: (profile: BrokerProfile) => Promise<void>;
  saveBrokerStocks: (id: string, stocks: string[]) => Promise<void>;
  removeBrokers: (ids: string[]) => Promise<void>;
  importBrokers: (profiles: Omit<BrokerProfile, 'id'>[], overwrite: string[]) => Promise<number>;
}

function completeBroker(value: Partial<BrokerProfile> & Pick<BrokerProfile, 'id' | 'name' | 'postfix' | 'timezone' | 'mtUse'>): BrokerProfile {
  return { desc: '', stockPickerUse: false, system: false, stocks: [], instruments: [], ...value };
}

function readState(): Pick<DataState, 'brokers' | 'storageError'> {
  try {
    const raw = localStorage.getItem(storageKey);
    if (!raw) return { brokers: [], storageError: '' };
    const value = normalizeLegacyBranding(JSON.parse(raw));
    if (![1, 2].includes(value.version) || !Array.isArray(value.brokers) || value.brokers.length > 100)
      throw new Error('Invalid saved brokers');
    const brokers = value.brokers.map((broker: BrokerProfile) => {
      if (!broker || ['id', 'name', 'postfix', 'timezone'].some(key => typeof (broker as unknown as Record<string, unknown>)[key] !== 'string') || typeof broker.mtUse !== 'boolean' || !Array.isArray(broker.instruments) || broker.instruments.some(item => typeof item !== 'string'))
        throw new Error('Invalid saved broker');
      return completeBroker(broker);
    });
    return { brokers, storageError: '' };
  } catch {
    return { brokers: [], storageError: 'Saved broker configuration could not be read. Existing browser storage has been preserved.' };
  }
}

const brokerPort = catalogPort<{ brokers: BrokerProfile[] }>('brokers');
export const useDataManagerStore = create<DataState>((set, get) => ({
  brokers: [], storageError: '',
  refresh: async () => { try { set({ ...await brokerPort.read(), storageError: '' }); } catch (cause) { set({ storageError: cause instanceof Error ? cause.message : 'Broker catalog unavailable.' }); } },
  importLegacy: async () => { const value = readState(); if (value.storageError) throw new Error(value.storageError); const saved = await brokerPort.write({ brokers: value.brokers }); set(saved); },
  saveBroker: async profile => {
    const state = get();
    if (state.storageError) throw new Error(state.storageError);
    const clean = validateBroker(profile, state.brokers, profile.id || undefined);
    const found = state.brokers.findIndex(row => row.id === profile.id);
    const brokers = [...state.brokers];
    if (found >= 0) brokers[found] = structuredClone(clean);
    else brokers.push({ ...structuredClone(clean), id: `broker-${crypto.randomUUID()}` });
    await persistData(state, brokers);
    set({ brokers });
  },
  saveBrokerStocks: async (id, stocks) => {
    const state = get();
    const index = state.brokers.findIndex(row => row.id === id);
    if (index < 0) throw new Error("Broker doesn't exist.");
    if (state.brokers[index].system) throw new Error("This broker can't be edited.");
    const brokers = [...state.brokers];
    brokers[index] = { ...brokers[index], stocks: [...stocks] };
    await persistData(state, brokers);
    set({ brokers });
  },
  removeBrokers: async ids => {
    const state = get();
    const selected = new Set(ids);
    const brokers = state.brokers.filter(row => !selected.has(row.id));
    await persistData(state, brokers);
    set({ brokers });
  },
  importBrokers: async (profiles, overwrite) => {
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
    await persistData(state, brokers);
    set({ brokers });
    return count;
  },
}));

async function persistData(state: Pick<DataState, 'storageError'>, brokers: BrokerProfile[]): Promise<void> {
  if (state.storageError) throw new Error(state.storageError);
  await brokerPort.write({ brokers });
}
