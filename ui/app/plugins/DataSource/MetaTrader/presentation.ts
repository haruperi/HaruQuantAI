/** Owner-local presentation/resource documents; no backend execution authority. */
import { createElement, useEffect } from 'react';
import { Mt5ImportDialog } from './Mt5ImportDialog';
import { useMt5Import, mt5Active } from './mt5ImportStore';

export function today(): string { const now = new Date(); return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`; }

export type Preset = 'sinceLast' | 'sixMonths' | 'year' | 'fiveYears' | 'tenYears' | 'allTime' | 'custom';

export interface Interval { from: string; to: string }

export function validDate(value: string): boolean { return /^\d{4}-\d{2}-\d{2}$/.test(value) && Number.isFinite(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value; }

export function presetRange(preset: Preset, last: string, minimum: string, from: string, to: string, now = today()): Interval {
  if (preset === 'custom') return { from, to };
  if (preset === 'allTime') return { from: minimum, to: now };
  if (preset === 'sinceLast') return { from: last, to };
  const date = new Date(`${now}T12:00:00Z`);
  if (preset === 'sixMonths') date.setUTCMonth(date.getUTCMonth() - 6);
  else date.setUTCFullYear(date.getUTCFullYear() - ({ year: 1, fiveYears: 5, tenYears: 10 }[preset]));
  return { from: [minimum, date.toISOString().slice(0, 10)].sort().at(-1)!, to };
}

export interface DownloadTarget { id: string; symbol: string; source: string; underlying?: string; instrument?: string; timeframe: string; from: string; to: string; bars: number; sourceDataId?: string; fastDownloadAvailable?: boolean }

export interface BrokerProfile { id: string; name: string; postfix: string; timezone: string; mtUse: boolean; instruments: string[] }

export const pluginId = 'mt5';
export const pluginName = 'MT5';

export function Sync({ onSync }: { onSync: (id: string, state: any) => void }) {
  const state = useMt5Import();
  useEffect(() => { void useMt5Import.getState().refresh(); const timer = window.setInterval(() => { void useMt5Import.getState().poll(); }, 1000); return () => window.clearInterval(timer); }, []);
  useEffect(() => {
    const active = mt5Active(state.job?.state);
    const definitions = state.definitions;
    onSync('mt5', {
      definitions,
      backendAvailable: state.backendAvailable,
      job: state.job,
      ranges: state.ranges,
      storageError: state.storageError,
      active,
    });
  }, [state, onSync]);
  return null;
}

export function Dialogs({ dialog, contextDocument, onClose, onStarted }: any) {
  if (dialog?.id === 'mt5-import') {
    return createElement(Mt5ImportDialog, { contextDocument, onClose, onStarted: () => onStarted('mt5', 'MT5 import started') });
  }
  return null;
}

export function advance() {
  useMt5Import.getState().advance();
}

export function action(act: 'pause' | 'resume' | 'stop') {
  useMt5Import.getState().action(act);
}
