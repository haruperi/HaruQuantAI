import { useEffect, useMemo, useRef, useState } from 'react';
import { DukascopyRegistrationError } from '../../Common/dataManagerStore';
import { filterCatalogue } from '../dukascopy';
import { useDukascopyAddService } from '../DukascopyService';

export interface AddPopupProps {
  open: boolean;
  onClose: () => void;
  onComplete: (message: string) => void;
}
export const disclaimer =
  'I confirm that I understand the following: Data are provided for free by Dukascopy. HaruQuantAI Data Manager is only a tool to download the data directly to the program. HaruQuantAI is not responsible for quality or availability of the data.';

export function useAddPopupController({ open, onComplete }: AddPopupProps) {
  const [query, setQuery] = useState('');
  const [category, setCategory] = useState('');
  const [selected, setSelected] = useState<string[]>([]);
  const [dataType, setDataType] = useState<'TICK' | 'M1'>('TICK');
  const [broker, setBroker] = useState('-1');
  const [postfix, setPostfix] = useState('');
  const [confirmed, setConfirmed] = useState(false);
  const [error, setError] = useState('');
  const [saving, setSaving] = useState(false);
  const saveLock = useRef(false);
  const [warning, setWarning] = useState(false);
  const [mapping, setMapping] = useState<Record<string, string> | null>(null);
  const { brokers, brokerLoading, brokerError, reloadBrokers, addData } = useDukascopyAddService();
  const activeBroker = brokers.find((item) => item.id === broker);
  const brokerInvalid = broker !== '-1' && !activeBroker?.mtUse;
  useEffect(() => {
    if (open) void reloadBrokers();
  }, [open, reloadBrokers]);
  const rows = useMemo(() => filterCatalogue(query, category), [query, category]);
  const groups = useMemo(
    () =>
      Array.from(new Set(rows.map((row) => row.fullCategory))).map((name) => ({
        name,
        rows: rows.filter((row) => row.fullCategory === name),
      })),
    [rows],
  );
  const root = useRef<HTMLDivElement>(null);
  const headerCheck = useRef<HTMLInputElement>(null);
  const all = rows.length > 0 && rows.every((row) => selected.includes(row.symbol));
  useEffect(() => {
    if (headerCheck.current) headerCheck.current.indeterminate = !all && selected.length > 0;
  }, [all, selected]);
  useEffect(() => {
    if (!open) return;
    setSelected([]);
    setConfirmed(false);
    setError('');
    setMapping(null);
    setWarning(false);
    const previous = document.activeElement as HTMLElement | null;
    root.current?.querySelector<HTMLButtonElement>('button')?.focus();
    return () => previous?.focus();
  }, [open]);
  const changeFilter = (text: string, type: string) => {
    setQuery(text);
    setCategory(type);
    setSelected([]);
  };
  const toggle = (symbols: string[]) =>
    setSelected((current) =>
      symbols.every((symbol) => current.includes(symbol))
        ? current.filter((symbol) => !symbols.includes(symbol))
        : [...new Set([...current, ...symbols])],
    );
  const save = async () => {
    if (saveLock.current) return;
    setError('');
    if (brokerLoading || brokerError || brokerInvalid) {
      setError(brokerError || (brokerLoading ? 'Wait for broker profiles to load.' : 'Choose an available broker profile.'));
      return;
    }
    if (!selected.length) {
      setError('No symbols selected');
      return;
    }
    if (!confirmed) {
      setError(disclaimer);
      return;
    }
    const resolvedInstruments = selected.map((symbol) => {
      if (activeBroker) {
        const found = activeBroker.instruments.find(
          (item) => item === symbol || (!item.startsWith('[') && item.startsWith(symbol)),
        );
        if (found) return found;
      }
      return '-1';
    });
    saveLock.current = true;
    setSaving(true);
    try {
      await addData({
        symbols: selected,
        dataType,
        broker,
        postfix,
        instruments: resolvedInstruments,
      });
      onComplete(
        `${selected.length} Dukascopy dataset definition${selected.length === 1 ? '' : 's'} added`,
      );
    } catch (cause) {
      if (cause instanceof DukascopyRegistrationError) {
        setSelected(current => current.filter(symbol => !cause.confirmedSymbols.includes(symbol)));
      }
      setError(cause instanceof Error ? cause.message : 'Unable to add symbols');
    } finally {
      saveLock.current = false;
      setSaving(false);
    }
  };
  return {
    saving,
    brokerLoading,
    brokerError,
    brokerInvalid,
    reloadBrokers,
    query,
    category,
    selected,
    dataType,
    broker,
    postfix,
    confirmed,
    error,
    warning,
    mapping,
    brokers,
    activeBroker,
    rows,
    groups,
    root,
    headerCheck,
    all,
    changeFilter,
    toggle,
    save,
    setMapping,
    setError,
    setConfirmed,
    setDataType,
    setBroker,
    setPostfix,
    setWarning,
  };
}
export type AddPopupController = ReturnType<typeof useAddPopupController>;
