import { useCallback, useRef, useState } from 'react';
import { useDataManagerStore } from '../../Common/dataManagerStore';
import { useDarwinex } from '../darwinexStore';
import { darwinexService } from '../DarwinexService';

export function useAddPopup(onClose: () => void, onStarted: () => void) {
  const data = useDataManagerStore(); const store = useDarwinex();
  const [query, setQuery] = useState(''), [selected, setSelected] = useState<string[]>([]), [brokerId, setBroker] = useState('-1'), [postfix, setPostfix] = useState(store.postfix), [agreed, setAgreed] = useState(false), [error, setError] = useState(''), [notice, setNotice] = useState('');
  const [mapping, setMapping] = useState(false), [mappings, setMappings] = useState<Record<string,string>>({});
  const [sort, setSort] = useState<'symbol' | 'dateFrom' | null>(null), [descending, setDescending] = useState(false); const warned = useRef(false);
  const broker = data.brokers.find(row => row.id === brokerId && row.mtUse);
  const rows = darwinexService.catalogue.filter(row => row.symbol.toLowerCase().includes(query.toLowerCase())).sort((a,b) => sort ? a[sort].localeCompare(b[sort]) * (descending ? -1 : 1) : 0);
  const close = useCallback(() => { if (mapping) { setMapping(false); setError(''); } else onClose(); }, [mapping, onClose]);
  function save() {
    try {
      if (!selected.length) throw new Error('No symbols selected');
      if (!agreed) throw new Error('Please confirm that you understand the free data disclaimer.');
      if (brokerId !== '-1' && !broker) throw new Error('Choose a valid broker profile.');
      if (broker && !mapping) { setMappings(Object.fromEntries(selected.map(symbol => [symbol, broker.instruments.find(item => !item.startsWith('[') && item.startsWith(symbol)) ?? '-1001']))); setMapping(true); setError(''); return; }
      const context = darwinexService.context(); const definitions = darwinexService.definitions(selected, postfix, context.existing, broker, mappings);
      if (!definitions.length) throw new Error('No symbols selected');
      darwinexService.start('add', definitions, context.active, undefined, postfix); onStarted(); onClose();
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to add data.'); }
  }
  function mass(value: string) { setMappings(current => Object.fromEntries(Object.entries(current).map(([symbol, mapping]) => [symbol, mapping === '-1001' ? value : mapping]))); }
  return { data, store, query, setQuery, selected, setSelected, brokerId, setBroker, postfix, setPostfix, agreed, setAgreed, error, setError, notice, setNotice, mapping, mappings, setMappings, sort, setSort, descending, setDescending, warned, broker, rows, close, save, mass };
}
