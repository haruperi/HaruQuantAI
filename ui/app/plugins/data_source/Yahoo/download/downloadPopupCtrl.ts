import { useState } from 'react';
import { presetRange, today, type Preset } from '../../Dukascopy/dukascopyDownload';
import { yahooStart, type YahooDefinition } from '../yahoo';
import { useYahoo } from '../yahooStore';
import { yahooService } from '../YahooService';
import type { YahooCallbacks } from '../add/addPopupCtrl';
export interface YahooDownloadProps extends YahooCallbacks { targets: YahooDefinition[] }
export function useYahooDownload({ targets, onClose, onStarted }: YahooDownloadProps) {
  const store = useYahoo(), minimum = targets.map(yahooStart).sort()[0], now = today();
  const initial = presetRange('sixMonths', targets[0].to || minimum, minimum, minimum, now);
  const [from, setFrom] = useState(initial.from), [to, setTo] = useState(initial.to), [preset, setPreset] = useState<Preset>('custom'), [overwrite, setOverwrite] = useState(false), [error, setError] = useState('');
  function choose(value: Preset) { const range = presetRange(value, targets[0].to || minimum, minimum, from, to); setFrom(range.from); setTo(range.to); setPreset(value); setError(''); }
  function start() { try { yahooService.importData({ targets, dateFrom: from, dateTo: to, dateType: preset, overwrite }); onStarted(); onClose(); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to start Yahoo download.'); } }
  return { store, minimum, now, from, setFrom, to, setTo, preset, setPreset, overwrite, setOverwrite, error, setError, choose, start };
}
