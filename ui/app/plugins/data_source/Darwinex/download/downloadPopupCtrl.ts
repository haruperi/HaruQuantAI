import { useState } from 'react';
import { useAppStore } from '../../../../host/store';
import { darwinexStart, type DarwinexDefinition } from '../darwinex';
import { useDarwinex } from '../darwinexStore';
import { darwinexService } from '../DarwinexService';
import { today, presetRange, type Preset } from '../../Dukascopy/dukascopyDownload';

export function useDownloadPopup(targets: DarwinexDefinition[], onClose: () => void, onStarted: () => void) {
  const full = useAppStore(state => state.settings.profile) === 'Full'; const notify = useAppStore(state => state.notify); const store = useDarwinex();
  const minimum = darwinexStart(targets[0]), last = targets[0].to || minimum;
  const [from, setFrom] = useState(last), [to, setTo] = useState(today()), [preset, setPreset] = useState<Preset>('sinceLast'), [overwrite, setOverwrite] = useState(false), [error, setError] = useState('');
  function choose(value: Preset) { const range = presetRange(value, last, minimum, from, to); setFrom(range.from); setTo(range.to); setPreset(value); setError(''); }
  function start() { try { darwinexService.download({ targets, dateFrom: from, dateTo: to, dateType: preset, overwrite }); onStarted(); onClose(); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to start download.'); } }
  return { full, notify, store, minimum, from, setFrom, to, setTo, preset, setPreset, overwrite, setOverwrite, error, setError, choose, start };
}
