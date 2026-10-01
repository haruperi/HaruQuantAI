/** Owner-local presentation/resource documents; no backend execution authority. */
import { createElement, useEffect } from 'react';
import { FileImportDialog } from './FileImportDialog';
import { FileMassImportDialog } from './FileMassImportDialog';
import { useFileImports, activeImport } from './fileImportStore';
import { emptyFileRecord } from './fileImport';

export interface FileDefinition {
  id: string; symbol: string; instrument: string; underlying: string; source: string;
  timeframe: string; broker: string; brokerName: string; timezone: string; category: string;
  from: string; to: string; bars: number; barType: 'start' | 'end'; connection: 'History';
}

export interface FileInstrument {
  symbol: string; name: string; type: string; broker: string; brokerName: string;
  pointValue: number; tickSize: number; tickStep: number; spread: number; slippage: number;
  minDistance: number; multiplier: number; sizeStep: number; timezone: string;
  commission: Commission; swap: Swap;
}

export interface Commission { model: CommissionModel; value: number; unit: string; min: number; minUnit: string; max: number; maxUnit: string }

export type CommissionModel = typeof commissionModels[number];

export const commissionModels = ['None', 'Per trade', 'Size based', 'Percentage based', 'Stockpicker'] as const;

export interface Swap { use: boolean; type: 'money' | 'points' | 'percent'; long: number; short: number; tripleSwapOn: string; rolloutHour: string }

export function defaultCommission(model: CommissionModel = 'None'): Commission {
  return { model, value: model === 'Stockpicker' ? 0.0035 : 0, unit: 'share', min: 0.35, minUnit: 'money', max: 1, maxUnit: 'equity' };
}

export function newInstrument(type = 'Forex'): FileInstrument {
  return { symbol: 'EURUSD', name: 'EURUSD', type, broker: '-1', brokerName: 'Default', timezone: 'UTC',
    pointValue: type === 'Stock' || type === 'Futures' ? 1 : 100000,
    tickSize: type === 'Stock' ? 0.01 : type === 'Futures' ? 0.1 : 0.0001,
    tickStep: type === 'Stock' ? 0.01 : type === 'Futures' ? 0.1 : 0.00001,
    spread: type === 'Stock' || type === 'Futures' ? 0 : 1, slippage: 0, minDistance: 0, multiplier: 1, sizeStep: 1,
    commission: defaultCommission(), swap: { use: false, type: 'money', long: 0, short: 0, tripleSwapOn: 'WEDNESDAY', rolloutHour: '23:00' } };
}

export function validateName(name: string, existing: string[], label = 'Symbol'): void {
  if (!name || name.length > 128 || !/^[a-zA-Z0-9_@.:$]+$/.test(name)) throw new Error(`${label} name is required (maximum 128 characters); use letters, numbers, or _ @ . : $.`);
  if (existing.some(item => item.toLowerCase() === name.toLowerCase())) throw new Error(`${label} ${name} already exists.`);
}

export { emptyFileRecord };
export const pluginId = 'file-import';
export const pluginName = 'File Import';

export function Sync({ onSync }: { onSync: (id: string, state: any) => void }) {
  const state = useFileImports();
  useEffect(() => { void useFileImports.getState().refresh(); const timer = setInterval(() => void useFileImports.getState().poll(), 1000); return () => clearInterval(timer); }, []);
  useEffect(() => {
    const active = activeImport(state.job?.state);
    onSync('file-import', {
      backendAvailable: state.backendAvailable,
      definitions: state.records,
      records: state.records,
      job: state.job,
      storageError: state.storageError,
      active,
    });
  }, [state, onSync]);
  return null;
}

export function Dialogs({ dialog, contextDocument, selectedDatasetIds, toolRows, onClose, onStarted }: any) {
  if (dialog?.id === 'file-import') {
    const rows = (toolRows ?? []).filter((r: any) => selectedDatasetIds.includes(r.id) && r.source === 'File import');
    const row = rows[0];
    if (!row) return null;
    const instrument = (contextDocument?.instruments ?? []).find((item: any) => item.symbol === row.symbol) ?? newInstrument();
    const target = { ...emptyFileRecord(row.symbol, instrument, 'start'), ...row };
    return createElement(FileImportDialog, { target, contextDocument, onClose, onStarted: () => onStarted('file') });
  }
  if (dialog?.id === 'file-mass-import') {
    return createElement(FileMassImportDialog, { contextDocument, onClose, onStarted: () => onStarted('file') });
  }
  return null;
}

export function advance() {
  useFileImports.getState().advance();
}

export function action(act: 'pause' | 'resume' | 'stop') {
  useFileImports.getState().action(act);
}

export function onSelectCommand(command: any, context: any) {
  if (command.dialog === 'file-import') {
    const rows = (context.datasets ?? []).filter((r: any) => context.selectedDatasetIds.includes(r.id) && r.source === 'File import');
    const row = rows[0];
    if (!row) {
      context.setSelectionMessage('You must select at least one File record.');
      return true;
    }
    if ('cloned' in row && row.cloned) {
      context.setSelectionMessage('Cannot import into cloned data.');
      return true;
    }
    context.setSelectionMessage('');
    context.setDialog({ id: 'file-import' });
    return true;
  }
  return false;
}
