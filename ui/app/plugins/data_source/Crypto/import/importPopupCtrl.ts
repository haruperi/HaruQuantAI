import { useState } from 'react';
import { cryptoStart, type CryptoDefinition } from '../crypto';
import { useCrypto } from '../cryptoStore';
import { cryptoService } from '../DataSourceCryptoService';
import { presetRange, today, type Preset } from '../../Dukascopy/dukascopyDownload';

export function useImportPopup(targets: CryptoDefinition[], onClose: () => void, onStarted: () => void) {
  const store = useCrypto(), minimum = cryptoStart(targets[0]), last = targets[0].to || minimum;
  const [from, setFrom] = useState(last), [to, setTo] = useState(today()), [preset, setPreset] = useState<Preset>('sinceLast'), [overwrite, setOverwrite] = useState(false), [error, setError] = useState('');
  function choose(value: Preset) { const range = presetRange(value, last, minimum, from, to); setFrom(range.from); setTo(range.to); setPreset(value); setError(''); }
  function start() { try { cryptoService.download({ targets, dateFrom: from, dateTo: to, dateType: preset, overwrite }); onStarted(); onClose(); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to start Crypto download.'); } }
  return { store, minimum, from, setFrom, to, setTo, preset, setPreset, overwrite, setOverwrite, error, setError, choose, start };
}
