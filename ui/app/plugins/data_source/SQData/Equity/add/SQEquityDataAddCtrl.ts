import { useCallback, useEffect, useRef, useState } from 'react';
import { useAppStore } from '../../../../../host/store';
import { sqAllowed, sqSubscription, type SQConfig, type SQProvider, type SQTicker } from '../../sqData';
import { useSQData } from '../../sqDataStore';
import { equityService } from '../SQEquityDataService';
export interface SQAddCallbacks { onClose: () => void; onStarted: () => void }
export function useSQDataAdd(provider: SQProvider, { onClose, onStarted }: SQAddCallbacks, service: typeof equityService) {
  const store = useSQData(); const profile = useAppStore(state => state.settings.profile); const notify = useAppStore(state => state.notify);
  const [config, setConfig] = useState<SQConfig>(() => ({ ...store.preferred[provider], symbols: '' }));
  const [results, setResults] = useState<SQTicker[]>([]); const [lookedUp, setLookedUp] = useState(false);
  const [selected, setSelected] = useState<string[]>([]); const [agreed, setAgreed] = useState(false);
  const [conditions, setConditions] = useState(false); const [busy, setBusy] = useState(false); const [error, setError] = useState('');
  const [sort, setSort] = useState<{ key: keyof SQTicker; descending: boolean }>({ key: 'ticker', descending: false });
  const timer = useRef<ReturnType<typeof setTimeout> | null>(null); const sequence = useRef(0); const container = useRef<HTMLDivElement>(null); const returnFocus = useRef(false);
  const subscription = sqSubscription(provider, profile);
  const cancelLookup = useCallback(() => { sequence.current++; if (timer.current) clearTimeout(timer.current); timer.current = null; }, []);
  useEffect(() => () => cancelLookup(), [cancelLookup]);
  useEffect(() => { cancelLookup(); setBusy(false); setSelected(current => current.filter(ticker => results.some(row => row.ticker === ticker && sqAllowed(row, profile)))); }, [profile, cancelLookup, results]);
  const close = useCallback(() => { if (conditions) { returnFocus.current = true; setConditions(false); } else { cancelLookup(); onClose(); } }, [conditions, cancelLookup, onClose]);
  useEffect(() => { if (!conditions && returnFocus.current) { returnFocus.current = false; const id = window.setTimeout(() => container.current?.querySelector<HTMLButtonElement>('[data-sq-conditions]')?.focus(), 0); return () => clearTimeout(id); } }, [conditions]);
  const patch = (values: Partial<SQConfig>) => setConfig(current => ({ ...current, ...values }));
  function lookup() {
    setError(''); cancelLookup();
    try {
      const found = service.lookup(config); const token = sequence.current; setBusy(true);
      timer.current = setTimeout(() => { if (sequence.current !== token) return; setResults(found); setSelected([]); setLookedUp(true); setBusy(false); }, 180);
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Lookup failed.'); }
  }
  function add() {
    try {
      service.start(config, selected, agreed);
      onStarted(); onClose();
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to add symbols.'); }
  }
  const eligible = results.filter(row => sqAllowed(row, profile)); const allSelected = eligible.length > 0 && eligible.every(row => selected.includes(row.ticker));
  const rows = [...results].sort((a, b) => String(a[sort.key]).localeCompare(String(b[sort.key])) * (sort.descending ? -1 : 1));
  const columns: { key: keyof SQTicker; label: string }[] = [{ key: 'ticker', label: 'Ticker' }, { key: 'name', label: 'Name' }, { key: 'exchange', label: 'Exchange' }, ...(provider === 'equity' ? [{ key: 'type' as const, label: 'Type' }] : []), { key: 'dataFrom', label: 'Data from' }];
  return { provider, store, profile, notify, config, results, lookedUp, selected, agreed, conditions, busy, error, sort, container, subscription, cancelLookup, close, patch, lookup, add, eligible, allSelected, rows, columns, setConditions, setAgreed, setSelected, setSort, setResults, setLookedUp, setError };
}
export function useSQEquityDataAdd(callbacks: SQAddCallbacks) { return useSQDataAdd('equity', callbacks, equityService); }
