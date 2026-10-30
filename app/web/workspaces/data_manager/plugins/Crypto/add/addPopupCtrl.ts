import { useEffect, useRef, useState } from 'react';
import type { CryptoExchangeId } from '../crypto';
import { useCrypto } from '../cryptoStore';
import { cryptoService } from '../DataSourceCryptoService';

export function useAddPopup(exchangeId: CryptoExchangeId, onClose: () => void, onStarted: () => void) {
  const exchange = cryptoService.exchange(exchangeId), store = useCrypto();
  const [query, setQuery] = useState(''), [selected, setSelected] = useState<string[]>([]), [timeframe, setTimeframe] = useState(exchange.timeframes[0]), [postfix, setPostfix] = useState(''), [agreed, setAgreed] = useState(false), [error, setError] = useState('');
  const allCheck = useRef<HTMLInputElement>(null);
  const rows = exchange.symbols.filter(row => row.symbol.toLowerCase().includes(query.trim().toLowerCase()));
  const all = rows.length > 0 && rows.every(row => selected.includes(row.symbol));
  useEffect(() => { if (allCheck.current) allCheck.current.indeterminate = selected.length > 0 && !all; }, [all, selected]);
  function save() {
    try {
      if (!selected.length) throw new Error('No symbols selected');
      if (!agreed) throw new Error('Please read and confirm Data Disclaimer for Free Data.');
      cryptoService.add(exchangeId, selected, timeframe, postfix); onStarted(); onClose();
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to add Crypto data.'); }
  }
  return { exchange, store, query, setQuery, selected, setSelected, timeframe, setTimeframe, postfix, setPostfix, agreed, setAgreed, error, setError, allCheck, rows, all, save };
}
