import { useEffect, useMemo, useRef, useState } from 'react';
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
  const [warning, setWarning] = useState(false);
  const [mapping, setMapping] = useState<Record<string, string> | null>(null);
  const { brokers, storageError, addData } = useDukascopyAddService();
  const activeBroker = brokers.find((item) => item.id === broker);
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
  const save = () => {
    setError('');
    if (!selected.length) {
      setError('No symbols selected');
      return;
    }
    if (!confirmed) {
      setError(disclaimer);
      return;
    }
    if (broker !== '-1' && !mapping) {
      setMapping(
        Object.fromEntries(
          selected.map((symbol) => [
            symbol,
            activeBroker?.instruments.find(
              (item) => !item.startsWith('[') && item.startsWith(symbol),
            ) ?? '-1001',
          ]),
        ),
      );
      return;
    }
    if (mapping && Object.values(mapping).includes('-1001')) {
      setError('Select proper instrument or skip the symbol');
      return;
    }
    const symbols = selected.filter((symbol) => mapping?.[symbol] !== '-1000');
    try {
      addData({
        symbols,
        dataType,
        broker,
        postfix,
        instruments: mapping ? symbols.map((symbol) => mapping[symbol]) : [],
      });
      onComplete(
        `${symbols.length} Dukascopy mock dataset definition${symbols.length === 1 ? '' : 's'} added`,
      );
    } catch (cause) {
      setError(cause instanceof Error ? cause.message : 'Unable to add symbols');
    }
  };
  return {
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
    storageError,
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
