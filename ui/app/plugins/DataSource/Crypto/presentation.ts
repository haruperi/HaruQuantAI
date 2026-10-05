/** Owner-local presentation/resource documents; no backend execution authority. */
import { createElement, useEffect } from 'react';
import { CryptoAddDialog } from './CryptoAddDialog';
import { CryptoDownloadDialog } from './CryptoDownloadDialog';
import { useCrypto, cryptoActive } from './cryptoStore';
import { cryptoTargets } from './crypto';

export function today(): string { const now = new Date(); return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`; }

export function validDate(value: string): boolean { return /^\d{4}-\d{2}-\d{2}$/.test(value) && Number.isFinite(Date.parse(value)) && new Date(value).toISOString().slice(0, 10) === value; }

export interface Interval { from: string; to: string }

export type Preset = 'sinceLast' | 'sixMonths' | 'year' | 'fiveYears' | 'tenYears' | 'allTime' | 'custom';

export function presetRange(preset: Preset, last: string, minimum: string, from: string, to: string, now = today()): Interval {
  if (preset === 'custom') return { from, to };
  if (preset === 'allTime') return { from: minimum, to: now };
  if (preset === 'sinceLast') return { from: last, to };
  const date = new Date(`${now}T12:00:00Z`);
  if (preset === 'sixMonths') date.setUTCMonth(date.getUTCMonth() - 6);
  else date.setUTCFullYear(date.getUTCFullYear() - ({ year: 1, fiveYears: 5, tenYears: 10 }[preset]));
  return { from: [minimum, date.toISOString().slice(0, 10)].sort().at(-1)!, to };
}

export const pluginId = 'crypto';
export const pluginName = 'Crypto';

export function Sync({ onSync }: { onSync: (id: string, state: any) => void }) {
  const state = useCrypto();
  useEffect(() => { void useCrypto.getState().refresh(); const timer = setInterval(() => void useCrypto.getState().poll(), 1000); return () => clearInterval(timer); }, []);
  useEffect(() => {
    const active = cryptoActive(state.job?.state);
    const definitions = state.definitions;
    onSync('crypto', {
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

export function Dialogs({ dialog, contextDocument, selectedDatasetIds, onClose, onStarted }: any) {
  if (dialog?.id === 'crypto-add' && dialog.exchange) {
    return createElement(CryptoAddDialog, { contextDocument, exchangeId: dialog.exchange, onClose, onStarted: () => onStarted('crypto', 'Crypto symbols are being added') });
  }
  if (dialog?.id === 'crypto-download') {
    const cryptoState = useCrypto.getState();
    const targets = cryptoTargets(cryptoState.definitions.filter(row => selectedDatasetIds.includes(row.id)));
    return createElement(CryptoDownloadDialog, { contextDocument, targets, onClose, onStarted: () => onStarted('crypto', 'Crypto download started') });
  }
  return null;
}

export function advance() {
  useCrypto.getState().advance();
}

export function action(act: 'pause' | 'resume' | 'stop') {
  useCrypto.getState().action(act);
}

export function onSelectCommand(command: any, context: any) {
  if (command.dialog === 'crypto-download') {
    try {
      const state = useCrypto.getState();
      const targets = cryptoTargets(state.definitions.filter(row => context.selectedDatasetIds.includes(row.id)));
      if (!targets.length) throw new Error('You must select at least one Crypto record.');
      context.setSelectionMessage('');
      context.setDialog({ id: 'crypto-download' });
    } catch (cause: any) {
      context.setSelectionMessage(cause?.message || 'Unable to select Crypto data.');
    }
    return true;
  }
  return false;
}
