import { useState } from 'react';
import { useYahoo } from '../yahooStore';
import { yahooService } from '../YahooService';
export interface YahooCallbacks { onClose: () => void; onStarted: () => void }
export function useYahooAdd({ onClose, onStarted }: YahooCallbacks) {
  const store = useYahoo(); const [symbols, setSymbols] = useState(''), [postfix, setPostfix] = useState(''), [error, setError] = useState('');
  function save() { try { yahooService.add(symbols, postfix); onStarted(); onClose(); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to add Yahoo data.'); } }
  return { store, symbols, setSymbols, postfix, setPostfix, error, setError, save };
}
