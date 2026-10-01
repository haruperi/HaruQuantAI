/** Owner-local presentation/resource documents; no backend execution authority. */
import { createElement, useEffect, useState } from 'react';
import { ExternalIndicatorEditorDialog } from './ExternalIndicatorEditorDialog';
import { ExternalIndicatorImportDialog } from './ExternalIndicatorImportDialog';
import { ExternalIndicatorRecognizeDialog } from './ExternalIndicatorRecognizeDialog';
import { ExternalIndicatorViewDialog } from './ExternalIndicatorViewDialog';
import { ExternalIndicatorDeleteDialog } from './ExternalIndicatorDeleteDialog';
import { ExternalIndicatorTransferDialog } from './ExternalIndicatorTransferDialog';
import { useExternalIndicators, externalJobActive } from './externalIndicatorsStore';

export function parseDate(value: string, pattern: string): number {
  const tokens = pattern.match(/yyyy|MM|dd|HH|mm|ss|SSS|./g) ?? [];
  const names: string[] = [];
  const expression = tokens.map(token => {
    if (['yyyy', 'MM', 'dd', 'HH', 'mm', 'ss', 'SSS'].includes(token)) { names.push(token); return `(\\d{${token.length}})`; }
    if (/[a-zA-Z]/.test(token)) throw new Error(`Unsupported date pattern: ${pattern}`);
    return token.replace(/[.*+?^${}()|[\]\\]/g, '\\$&');
  }).join('');
  if (!['yyyy', 'MM', 'dd'].every(token => names.includes(token)) || new Set(names).size !== names.length) throw new Error('Date format must contain yyyy, MM and dd once.');
  const match = new RegExp(`^${expression}$`).exec(value);
  if (!match) throw new Error(`Date does not match ${pattern}`);
  const parts = Object.fromEntries(names.map((name, i) => [name, Number(match[i + 1])]));
  const stamp = Date.UTC(parts.yyyy, parts.MM - 1, parts.dd, parts.HH ?? 0, parts.mm ?? 0, parts.ss ?? 0, parts.SSS ?? 0);
  const d = new Date(stamp);
  if (parts.yyyy < 1900 || d.getUTCFullYear() !== parts.yyyy || d.getUTCMonth() !== parts.MM - 1 || d.getUTCDate() !== parts.dd || d.getUTCHours() !== (parts.HH ?? 0) || d.getUTCMinutes() !== (parts.mm ?? 0) || d.getUTCSeconds() !== (parts.ss ?? 0)) throw new Error('Invalid calendar date/time.');
  return stamp;
}

export function splitRows(text: string, separator: string): string[][] {
  if (![',', ';', '\t', '|', ' '].includes(separator)) throw new Error('Choose a supported separator.');
  const rows: string[][] = []; let row: string[] = [], cell = '', quoted = false, closed = false;
  const push = () => { row.push(cell.trim()); if (row.length > 100) throw new Error('Maximum 100 columns per file.'); if (row.some(value => value !== '')) rows.push(row); row = []; cell = ''; closed = false; if (rows.length > limits.rows + 1000) throw new Error('File exceeds the 100,000 data-row limit.'); };
  for (let i = 0; i < text.length; i++) {
    const c = text[i];
    if (quoted) { if (c === '"') { if (text[i + 1] === '"') { cell += '"'; i++; } else { quoted = false; closed = true; } } else cell += c; }
    else if (c === separator) { row.push(cell.trim()); cell = ''; closed = false; }
    else if (c === '\n' || c === '\r') { if (c === '\r' && text[i + 1] === '\n') i++; push(); }
    else if (c === '"' && !cell && !closed) quoted = true;
    else { if (closed && c.trim()) throw new Error('Unexpected character after a quoted field.'); cell += c; }
  }
  if (quoted) throw new Error('Unclosed quoted field.');
  if (cell || row.length) push();
  return rows;
}

export const limits = { file: 10 * 1024 * 1024, folder: 50 * 1024 * 1024, files: 500, rows: 100000, timestamps: 200000 };

export const pluginId = 'indicators';
export const pluginName = 'External Indicators';

export function Sync({ onSync }: { onSync: (id: string, state: any) => void }) {
  const state = useExternalIndicators();
  const [legacy, setLegacy] = useState(() => Boolean(localStorage.getItem('haru-external-indicators-v1')));
  const [transferError, setTransferError] = useState('');
  useEffect(() => { void useExternalIndicators.getState().refresh(); }, []);
  useEffect(() => {
    const active = externalJobActive(state.job?.state);
    onSync('indicators', {
      backendAvailable: state.backendAvailable,
      definitions: state.definitions,
      job: state.job,
      storageError: state.storageError,
      active,
    });
  }, [state, onSync]);
  if (!legacy) return null;
  return createElement('div', { role: 'status' }, 'Saved browser indicators are preserved. ', createElement('button', { disabled: !state.backendAvailable || externalJobActive(state.job?.state), onClick: () => { void state.importLegacy().then(() => setLegacy(false)).catch(cause => setTransferError(cause instanceof Error ? cause.message : 'Indicator transfer failed.')); } }, 'Import saved indicators into backend'), transferError ? createElement('p', { role: 'alert' }, transferError) : null);
}

export function Dialogs({ externalDialog, otherProviderActive, onClose, onStarted, onNotify, onSaved }: any) {
  if (!externalDialog) return null;
  const state = useExternalIndicators.getState();
  if (externalDialog.kind === 'editor') {
    return createElement(ExternalIndicatorEditorDialog, { mode: externalDialog.mode, source: externalDialog.source, onClose, onSaved: (msg: string) => onNotify ? onNotify(msg) : null });
  }
  if (externalDialog.kind === 'import') {
    return createElement(ExternalIndicatorImportDialog, { item: externalDialog.source, externalActive: otherProviderActive, onClose, onStarted: () => onStarted('external', 'Importing indicator data.') });
  }
  if (externalDialog.kind === 'recognize') {
    return createElement(ExternalIndicatorRecognizeDialog, { onClose, onSaved: (msg: string) => onNotify ? onNotify(msg) : null });
  }
  if (externalDialog.kind === 'view') {
    return createElement(ExternalIndicatorViewDialog, { item: externalDialog.source, onClose });
  }
  if (externalDialog.kind === 'delete') {
    return createElement(ExternalIndicatorDeleteDialog, { names: externalDialog.selected.map((item: any) => item.name), onClose, onSaved: (msg: string) => { if (onSaved) onSaved(); if (onNotify) onNotify(msg); } });
  }
  if (externalDialog.kind === 'transfer') {
    return createElement(ExternalIndicatorTransferDialog, { mode: externalDialog.mode, selected: externalDialog.selected, all: state.definitions, onClose, onSaved: (msg: string) => onNotify ? onNotify(msg) : null });
  }
  return null;
}

export function advance() {
  useExternalIndicators.getState().advance();
}

export function action(act: 'pause' | 'resume' | 'stop') {
  useExternalIndicators.getState().action(act);
}
