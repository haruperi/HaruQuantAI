import { useEffect, useRef, useState, type ChangeEvent } from 'react';
import { useAppStore } from '../../../../host/store';
import { useDataManagerStore } from '../../Common/dataManagerStore';
import { useMt5Import } from '../mt5ImportStore';
import { mt5Preset, type Mt5Folder } from '../mt5Import';
import { today, type Preset } from '../../Dukascopy/dukascopyDownload';
import { mt5Api } from '../DataSourceMt5Api';

function initialFrom(): string {
  const date = new Date(`${today()}T12:00:00Z`);
  date.setUTCFullYear(date.getUTCFullYear() - 1);
  return date.toISOString().slice(0, 10);
}

export function useMt5ApiImport(onClose: () => void, onStarted: () => void) {
  const store = useMt5Import();
  const data = useDataManagerStore();
  const notify = useAppStore(state => state.notify);
  const picker = useRef<HTMLInputElement>(null);
  const timer = useRef<number | null>(null);
  const initialDate = initialFrom();
  const [folder, setFolder] = useState<Mt5Folder | null>(null);
  const [fetched, setFetched] = useState(false);
  const [loading, setLoading] = useState(false);
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('');
  const [selected, setSelected] = useState<string[]>([]);
  const [from, setFrom] = useState(initialDate);
  const [to, setTo] = useState(today());
  const [preset, setPreset] = useState<Preset>('sinceLast');
  const [broker, setBroker] = useState('-1');
  const [postfix, setPostfix] = useState(store.postfix);
  const [error, setError] = useState('');
  useEffect(() => () => { if (timer.current !== null) window.clearTimeout(timer.current); }, []);

  const brokers = [{ id: '-1', name: 'Default', postfix: '', timezone: 'UTC' },
    ...data.brokers.filter(item => item.mtUse)];
  const visible = fetched ? mt5Api.filter(query, category) : [];
  const categories = [...new Set(mt5Api.symbols.map(row => row.path))];
  const allVisible = visible.length > 0 && visible.every(row => selected.includes(row.name));
  const grouped = [...new Set(visible.map(row => row.path))].map(path => ({ path, rows: visible.filter(row => row.path === path) }));

  function clearResults(): void { setFetched(false); setLoading(false); setQuery(''); setCategory(''); setSelected([]); }
  function fetchSymbols(): void {
    if (!folder) { setError('Select an MT5 installation folder before fetching symbols.'); return; }
    setError(''); setLoading(true); setFetched(false); setSelected([]);
    timer.current = window.setTimeout(() => { setLoading(false); setFetched(true); timer.current = null; }, 180);
  }
  function choose(value: Preset): void {
    const range = value === 'sinceLast' ? { from: initialDate, to } : mt5Preset(value, from, to);
    setFrom(range.from); setTo(range.to); setPreset(value); setError('');
  }
  function start(): void {
    try {
      if (!folder || !fetched) throw new Error('Select an MT5 installation folder and fetch its symbols.');
      const profile = brokers.find(item => item.id === broker);
      if (!profile) throw new Error('Choose a valid broker profile.');
      const request = { folder: folder.folder, symbols: selected, dateFrom: from, dateTo: to, dateType: preset,
        broker: profile.id, brokerName: profile.name, timezone: profile.timezone, postfix };
      mt5Api.start(request);
      onStarted(); onClose();
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to start MT5 import.'); }
  }
  function chooseFolder(event: ChangeEvent<HTMLInputElement>): void {
          if (!event.target.files?.length) return;
          try { const next = mt5Api.discover(Array.from(event.target.files, file => file.webkitRelativePath)); setFolder(next); clearResults(); setError(''); }
          catch (cause) { setFolder(null); clearResults(); setError(cause instanceof Error ? cause.message : 'Unable to select MT5 folder.'); }
          event.target.value = '';
  }
  return { store, notify, picker, folder, fetched, loading, query, setQuery, category, setCategory, selected, setSelected, from, setFrom, to, setTo, preset, setPreset, broker, setBroker, postfix, setPostfix, error, setError, brokers, visible, categories, allVisible, grouped, fetchSymbols, choose, start, chooseFolder };
}
