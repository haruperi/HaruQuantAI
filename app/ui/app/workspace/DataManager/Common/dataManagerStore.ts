import { normalizeLegacyBranding } from '../../../host/branding';
import { create } from 'zustand';
import { normalizeBrokerName, validateBroker, type BrokerProfile } from '../Catalogs/BrokerProfiles/brokerProfiles';

const storageKey = 'sqx-data-manager-v1';

interface DataState {
  brokers: BrokerProfile[];
  storageError: string;
  saveBroker: (profile: BrokerProfile) => void;
  saveBrokerStocks: (id: string, stocks: string[]) => void;
  removeBrokers: (ids: string[]) => void;
  importBrokers: (profiles: Omit<BrokerProfile, 'id'>[], overwrite: string[]) => number;
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
    persistData(state, brokers);
    set({ brokers });
  },
  saveBrokerStocks: (id, stocks) => {
    const state = get();
    const index = state.brokers.findIndex(row => row.id === id);
    if (index < 0) throw new Error("Broker doesn't exist.");
    if (state.brokers[index].system) throw new Error("This broker can't be edited.");
    const brokers = [...state.brokers];
    brokers[index] = { ...brokers[index], stocks: [...stocks] };
    persistData(state, brokers);
    set({ brokers });
  },
  removeBrokers: ids => {
    const state = get();
    const selected = new Set(ids);
    const brokers = state.brokers.filter(row => !selected.has(row.id));
    persistData(state, brokers);
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
    persistData(state, brokers);
    set({ brokers });
    return count;
  },
}));

function persistData(state: Pick<DataState, 'storageError'>, brokers: BrokerProfile[]): void {
  if (state.storageError) throw new Error(state.storageError);
  // Preserve legacy data bytes as fields when editing unrelated local configuration.
  const raw = localStorage.getItem(storageKey);
  const saved = raw ? JSON.parse(raw) : {};
  localStorage.setItem(storageKey, JSON.stringify({ ...saved, version: 2, brokers }));
}
