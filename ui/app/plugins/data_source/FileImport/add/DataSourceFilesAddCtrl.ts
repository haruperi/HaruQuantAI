import { useCallback, useEffect, useRef, useState, type ReactNode } from 'react';
import { datasets } from '../../Common/fixtures';
import { useDataManagerStore, useTickDownloader } from '../../Common/dataManagerStore';
import { useFileSymbols } from '../fileSymbolsStore';
import { effectiveInstruments, newInstrument, validateName, type FileInstrument } from '../fileSymbols';
import { filesService } from '../DataSourceFilesService';

export type AddPopupProps = { onClose: () => void; onSaved: () => void; mass?: { content: ReactNode; postfix: ReactNode; busy: boolean; onSave: (instrument: FileInstrument, barType: 'start' | 'end') => Promise<boolean> } };
export function useFilesAdd({ onClose, onSaved, mass }: AddPopupProps) {
  const file = useFileSymbols();
  const data = useDataManagerStore();
  const td = useTickDownloader();
  const all = effectiveInstruments(file.instruments, file.overrides, file.removed);
  const brokers = [{ id: '-1', name: 'Default', postfix: '' }, ...data.brokers.filter(row => row.mtUse)];
  const [page, setPage] = useState<'symbol' | 'instrument' | 'help'>('symbol');
  const [helpOrigin, setHelpOrigin] = useState<'symbol' | 'instrument'>('symbol');
  const [symbol, setSymbol] = useState('');
  const [barType, setBarType] = useState<'start' | 'end'>('start');
  const [broker, setBroker] = useState('');
  const [selected, setSelected] = useState(all.find(row => row.type === 'Forex')?.symbol ?? all[0]?.symbol ?? '');
  const [draft, setDraft] = useState(newInstrument());
  const [swapDraft, setSwapDraft] = useState(all.find(row => row.symbol === selected)?.swap ?? newInstrument().swap);
  const [error, setError] = useState('');
  const container = useRef<HTMLDivElement>(null);
  const focusTarget = useRef<string | null>(null);
  const item = all.find(row => row.symbol === selected);
  const choices = all.filter(row => !broker || row.broker === broker);
  const shown = page === 'instrument' ? draft : item;
  useEffect(() => {
    const selector = focusTarget.current ?? 'button';
    focusTarget.current = null;
    const timer = window.setTimeout(() => container.current?.querySelector<HTMLElement>(`[role=dialog] ${selector}`)?.focus(), 0);
    return () => window.clearTimeout(timer);
  }, [page]);
  const back = useCallback(() => {
    setError('');
    if (page === 'help') { focusTarget.current = '[data-swap-help] button'; setPage(helpOrigin); }
    else if (page === 'instrument') { focusTarget.current = '[data-add-instrument]'; setPage('symbol'); }
    else onClose();
  }, [page, helpOrigin, onClose]);
  function choose(name: string) { setSelected(name); setSwapDraft(structuredClone(all.find(row => row.symbol === name)?.swap ?? newInstrument().swap)); }
  function help() { setHelpOrigin(page === 'instrument' ? 'instrument' : 'symbol'); setPage('help'); }
  async function save() {
    try {
      if (data.storageError || td.storageError) throw new Error(data.storageError || td.storageError);
      if (page === 'instrument') {
        validateName(draft.symbol, [], 'Instrument');
        const profile = brokers.find(row => row.id === draft.broker);
        const value = { ...draft, symbol: draft.symbol + (profile?.postfix ?? ''), brokerName: profile?.name ?? '' };
        filesService.addInstrument(value, brokers.map(row => row.id));
        setBroker(''); setSelected(value.symbol); setSwapDraft(structuredClone(value.swap));
        focusTarget.current = '[data-add-instrument]'; setPage('symbol'); setError('');
      } else {
        if (!item) throw new Error('Choose an instrument.');
        if (mass) { if (!await mass.onSave(item, barType)) return; onSaved(); onClose(); return; }
        filesService.addSymbol(symbol, item, barType, [...datasets, ...data.definitions, ...td.definitions].map(row => row.symbol));
        onSaved(); onClose();
      }
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to save.'); }
  }
  return { file, all, brokers, page, setPage, symbol, setSymbol, barType, setBarType, broker, setBroker, selected, draft, setDraft, swapDraft, setSwapDraft, error, setError, container, shown, choices, back, choose, help, save };
}
