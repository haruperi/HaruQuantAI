import './dataManager.css';
import { useCallback, useEffect, useRef, useState, type ComponentType } from 'react';
import {
  Bitcoin, ChartCandlestick, ChevronDown, ChevronRight, CircleDollarSign,
  CirclePlus, Clock, Cloud, CloudDownload, Coins, Database, DollarSign, Download,
  FileInput, FileUp, Files, FileSpreadsheet, FolderInput, FolderOpen, Landmark, ListPlus,
  MonitorDown, Network, Plus, RefreshCw, Save, Search, Server,
  Settings2, Trash2, Globe2, Info, CopyPlus, CalendarPlus, FileSearch,
} from 'lucide-react';

import { useAppStore } from './localState';
import { Button, Checkbox, Field, Modal, ProgressBar, Section, Select, TextInput } from '../../components/ui';
import { instruments } from './Common/fixtures';
import {
  dataSourceContextActions, dataSourceProviders, type DataSourceCommand,
  type DataSourceCommandIcon, type DataSourceDialogId, type DataSourceProvider,
  type DirectDataSourceAction,
} from './Common/dataSourceRibbon';
import { useAttachments } from '../../host/composition';
import { effectiveInstruments, seedInstruments, type FileDefinition, type FileInstrument, type InstrumentBroker } from './Catalogs/Instruments/fileSymbols';
import { FileSymbolDialog } from './Catalogs/Instruments/FileSymbolDialog';
import { useFileSymbols } from './Catalogs/Instruments/fileSymbolsStore';
import { InstrumentEditorDialog } from './Catalogs/Instruments/InstrumentEditorDialog';
import { CloneInstrumentDialog } from './Catalogs/Instruments/CloneInstrumentDialog';
import { InstrumentTransferDialog } from './Catalogs/Instruments/InstrumentTransferDialog';
import { SessionTemplateDialog } from './Catalogs/Sessions/SessionTemplateDialog';
import { CloneSessionDialog } from './Catalogs/Sessions/CloneSessionDialog';
import { SessionTransferDialog } from './Catalogs/Sessions/SessionTransferDialog';
import { effectiveSessions, type SessionBroker, type SessionDefinition } from './Catalogs/Sessions/sessions';
import { useSessions } from './Catalogs/Sessions/sessionStore';
import { StockGroupEditorDialog } from './Catalogs/StockGroups/StockGroupEditorDialog';
import { StockGroupStocksDialog } from './Catalogs/StockGroups/StockGroupStocksDialog';
import { StockGroupTransferDialog } from './Catalogs/StockGroups/StockGroupTransferDialog';
import { serializeStockGroupsJson, summarizeGroup, type StockGroupDefinition } from './Catalogs/StockGroups/stockGroups';
import { stockGroupJobActive, useStockGroups } from './Catalogs/StockGroups/stockGroupsStore';
import { BrokerProfileEditorDialog } from './Catalogs/BrokerProfiles/BrokerProfileEditorDialog';
import { BrokerStocksDialog } from './Catalogs/BrokerProfiles/BrokerStocksDialog';
import { BrokerRecordImportDialog } from './Catalogs/BrokerProfiles/BrokerRecordImportDialog';
import { BrokerTransferDialog } from './Catalogs/BrokerProfiles/BrokerTransferDialog';
import { brokerCounts, serializeBrokersJson, type BrokerProfile } from './Catalogs/BrokerProfiles/brokerProfiles';
import { useDataManagerStore } from './Common/dataManagerStore';
import { actionsClient, type DatasetRow } from './Actions/actionsClient';
import { CsvExportDialog } from './Actions/CsvExportDialog';
import { Mt4ExportDialog } from './Actions/Mt4ExportDialog';
import { Mt5ExportDialog } from './Actions/Mt5ExportDialog';
import { CloneTimezoneDialog } from './Actions/CloneTimezoneDialog';
import { ViewAnalyzeDialog } from './Actions/ViewAnalyzeDialog';
import { SaveDefinitionsDialog } from './Actions/SaveDefinitionsDialog';
import { LoadDefinitionsDialog } from './Actions/LoadDefinitionsDialog';
import { MassDeleteDialog } from './Actions/MassDeleteDialog';

export interface DataSourcePluginPort {
  pluginId: string;
  pluginName?: string;
  Sync: ComponentType<{ onSync: (id: string, state: any) => void }>;
  Dialogs: ComponentType<any>;
  advance?: () => void;
  action?: (act: 'pause' | 'resume' | 'stop') => void;
  onSelectCommand?: (command: DataSourceCommand, context: any) => boolean;
}

export type ExportKind = 'csv' | 'mt4' | 'mt5';
export interface ExportTarget {
  id: string;
  symbol: string;
  source: string;
  underlying?: string;
  instrument?: string;
  timeframe: string;
  from: string;
  to: string;
  bars: number;
  sourceDataId?: string;
}

export interface ToolTarget {
  id: string;
  symbol: string;
  instrument: string;
  source: string;
  timeframe: string;
  timezone: string;
  from: string;
  to: string;
  bars: number;
  category: string;
  sourceDataId?: string;
}

export const externalIndicatorTypes = [
  { value: 1, label: 'Indicator value - price' },
  { value: 2, label: 'Indicator value - number' },
  { value: 3, label: 'Indicator value - price range' },
  { value: 10, label: 'Signal - 0 means false, anything else means true' },
] as const;

export interface ExternalIndicatorDefinition {
  id?: string;
  name: string;
  type: 1 | 2 | 3 | 10;
  values: Array<{ name: string; mt4: string; mt5: string; el: string }>;
  timeframe: string;
  dateFrom: string;
  dateTo: string;
  totalDays: number;
  records: Array<{ timestamp: number; values: number[] }>;
}

function externalTypeLabel(value: number): string {
  return externalIndicatorTypes.find(item => item.value === value)?.label ?? '';
}

function activeExternalLines(item: { values: Array<{ name: string }> }) {
  return item.values.filter(line => line.name.trim());
}

function simulationSummary(target: { from?: string; to?: string; bars?: number }, ranges: { from: string; to: string }[]) {
  const from = target.from ?? '';
  const to = target.to ?? '';
  const bars = target.bars ?? 0;
  if (!ranges || !ranges.length) return { from, to, bars };
  const samples = ranges.reduce((sum, row) => sum + (Date.parse(row.to) - Date.parse(row.from)) / 86400000 + 1, 0);
  return {
    from: [from, ...ranges.map(row => row.from)].filter(Boolean).sort()[0],
    to: [to, ...ranges.map(row => row.to)].filter(Boolean).sort().at(-1)!,
    bars: bars + samples,
  };
}

function isOperationActive(state?: string): boolean {
  return state === 'running' || state === 'paused';
}

function downloadExportArtifacts(artifacts: Array<{ name: string; mime: string; content: string }>): void {
  for (const artifact of artifacts) {
    const url = URL.createObjectURL(new Blob([artifact.content], { type: artifact.mime }));
    const anchor = document.createElement('a');
    anchor.href = url;
    anchor.download = artifact.name;
    anchor.hidden = true;
    document.body.append(anchor);
    anchor.click();
    anchor.remove();
    window.setTimeout(() => URL.revokeObjectURL(url), 1000);
  }
}

function selectExportTargets(rows: ExportTarget[], ids: string[], mode: ExportKind): ExportTarget[] {
  const selected = rows.filter(row => ids.includes(row.id));
  if (mode === 'csv') {
    const eligible = selected.filter(row => row.bars > 0 && row.from && row.to);
    if (!eligible.length) throw new Error('You must select at least one data record with data to export.');
    return eligible;
  }
  if (selected.length !== 1) throw new Error('You must select exactly one data record.');
  const row = selected[0];
  if (!row.bars || !row.from || !row.to) throw new Error('There is no data to export.');
  const frames = row.timeframe.toUpperCase();
  if (mode === 'mt4' && !frames.includes('TICK')) throw new Error('MT4 FXT/HST export requires Tick data.');
  if (mode === 'mt5' && !(frames.startsWith('TICK') || frames.startsWith('M1'))) throw new Error('MT5 export requires Tick or M1 source data.');
  return [row];
}

function selectCloneTargets(rows: ToolTarget[], ids: string[]): ToolTarget[] {
  const selected = rows.filter(row => ids.includes(row.id));
  if (!selected.length) throw new Error('You have to select some symbol.');
  const cloned = selected.find(row => row.sourceDataId);
  if (cloned) throw new Error(`'${cloned.symbol}' is cloned data. You cannot clone it again.`);
  return selected;
}

function selectReviewTarget(rows: ToolTarget[], ids: string[]): ToolTarget {
  const selected = rows.filter(row => ids.includes(row.id));
  if (!selected.length) throw new Error('You have to select a symbol.');
  const target = selected[0];
  if (!target.bars) throw new Error(`Symbol '${target.symbol}' doesn't contain any data`);
  return target;
}

const tabs = ['Data sources', 'Export', 'Tools', 'Instruments', 'Sessions', 'External indicators', 'Stock groups', 'Broker profiles', 'Log'];
type OperationState = 'idle' | 'running' | 'paused' | 'completed' | 'cancelled';
interface DialogState { id: DataSourceDialogId; exchange?: string }
type InstrumentDialogState =
  | { kind: 'editor'; mode: 'add' | 'edit' | 'mass'; selected: FileInstrument[] }
  | { kind: 'clone'; source: FileInstrument }
  | { kind: 'delete'; selected: FileInstrument[] }
  | { kind: 'transfer'; mode: 'save' | 'load'; selected: FileInstrument[] };
type SessionDialogState =
  | { kind:'editor'; mode:'add'|'edit'; source?:SessionDefinition }
  | { kind:'clone'; source:SessionDefinition }
  | { kind:'delete'; selected:SessionDefinition[] }
  | { kind:'transfer'; mode:'save'|'load'; selected:SessionDefinition[] };
type ExternalIndicatorDialogState =
  | { kind: 'editor'; mode: 'add' | 'edit'; source?: ExternalIndicatorDefinition }
  | { kind: 'import'; source: ExternalIndicatorDefinition }
  | { kind: 'recognize' }
  | { kind: 'view'; source: ExternalIndicatorDefinition }
  | { kind: 'delete'; selected: ExternalIndicatorDefinition[] }
  | { kind: 'transfer'; mode: 'save' | 'load'; selected: ExternalIndicatorDefinition[] };
type StockGroupDialogState =
  | { kind: 'editor'; mode: 'add'|'edit'; source?: StockGroupDefinition }
  | { kind: 'stocks'; source: StockGroupDefinition }
  | { kind: 'delete'; selected: StockGroupDefinition[] }
  | { kind: 'load' };
type BrokerDialogState =
  | {kind:'editor';mode:'add'|'edit';source?:BrokerProfile}
  | {kind:'stocks';source:BrokerProfile}
  | {kind:'import';recordType:'instrument'|'session'}
  | {kind:'delete';selected:BrokerProfile[]}
  | {kind:'load'};

const yahooIconUrl = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAABmJLR0QA/wD/AP+gvaeTAAAACXBIWXMAAC4jAAAuIwF4pT92AAAAB3RJTUUH4woCBzE7zqTrtQAABIdJREFUWMPtl9tvVFUUxn/7nDP3mc4MpYBFaGnVWq5iEyURCiQYH/oPmPhC4p/ko/4HJMYnfDKFioBgAin03uJIL3TKdKadc2bOnMve24cho6U3RJDEsF9Pzv6+9a31rbW2uCxGNW/wGLzh85aA9Tov36q4xH9BQAiI5A2y3SZmtAmppMYtKWrzChXq10vASgv6P09y7qs86XwTomEr7l2tcvfKOrWibilhvQ7Z27pMBoba6D+bIZY2QMPqos+t7yVBXW9IwysvQisqOPBhjN5PUiSyJqYlUFJTnPNYmGoQOPrFakDrzXl9PlS9RXGlu0yOnU+T7Yi0/qmtSR4O25RnQ1AbK3ETASsl2HPMIrHHQBgCFWrsBcn6rET5TUjDEmSOmGS7TYyIQCuNW1ZUJkP29UXoP5cmnmmKK0NNad5n+tc67rLaZAPr+agyXSaXLrfTfyFNLGngu4qxYYcfvylRmQgBSB0yuPB1noGhLPGMgVdXTFx3uPZdhb4zKdo7o5hWE8mtSiZGHFbnArTebEPjeZM2Sori7x7prEXH4Rid7yc4Ophm33sRDLOZij1HLI5fzHCwL07H4RjpnMVKwSeRMzg2mCGZNZ9ZDyrLAeM3HWqLahP4lkXoPlXM3K2zUvCQgUYY0LYvQt+nKZKdJvG9Br0fJ2l/N4phNVNUeuxTuOdy+FSc/T0xzEgTquFIpm/WKE76rfTtSkBrKD8KGbtuU69KAJJtJv3n0uR7LHI9FkcHM6SeRVm3JRM/OwR1Tf9gmkTGREmNDDVrxYAHwzZ2QbJl+FsVoQDqS5Kp2zUGhrKkciZWVLC/J0bvR0m8muTQ8TiRhIFSsFYMmLjtEISK0NPMj9VBgAygcN9lftQjcPV2+FvbUAVQnAqYvOHQfihGKmeSzFqc/qINryZJ5yyEgEZVMnOrTmkmwIwK7v6wjgDs1RDHltRXFXZBbgu+fR8QYBckD687nLjURjJrEksafPBZChnoVnezyyHjIw75zgjnL+fpPp1EhpqxYZufvi2zPhNuPZFepBGFnmZpwufRb3Xy70SJpw0SGbNpJQG+q/hj1KXyOODMlzlOXGwjvbd5XSxu8GTK485ClUZJsZME27ZiAdiPQ8ZGbJzKX5H8vbuNj9j4nqKjO0o8YyBE83siY5LtsLDiYjcBdp4FflVTGG0w/9DFd9UGdZbnGszdd6mWJEtTDZyyRIaawNOsrwQ8mfPw1tXmFv6P9gEF649CJm/U6B1IEU02+darkvFrDuXZEHdZcfvKGqYp6DqZoOEoHgxXmbnhEtR233d3Hcdag5a6NZyU0lSe+EzeqlFfkmgJi3d8rhZLJNoNpK9xFiWNFbVrAe5OQED2iEXf2VRruDRsxfTNGk9nA9Sz/iI9zdp0yNoOq9dLEYhmBV2n4nSdTBJNGGjV9PjYLza1hY3+Fi+7P+y02cRyBh0Ho9QqEiU9goZm+o7D4phP6L6a94zY6WVkxATZXpPUARPDAhVCbUVSnZXIxqshsGMKlKcpj4esjgctocW/kPulXCBasG+fZv9TAn8CXIAhGt3hCvQAAAAASUVORK5CYII=';
const mt5IconUrl = 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACAAAAAgCAYAAABzenr0AAAEsWlUWHRYTUw6Y29tLmFkb2JlLnhtcAAAAAAAPD94cGFja2V0IGJlZ2luPSLvu78iIGlkPSJXNU0wTXBDZWhpSHpyZVN6TlRjemtjOWQiPz4KPHg6eG1wbWV0YSB4bWxuczp4PSJhZG9iZTpuczptZXRhLyIgeDp4bXB0az0iWE1QIENvcmUgNS41LjAiPgogPHJkZjpSREYgeG1sbnM6cmRmPSJodHRwOi8vd3d3LnczLm9yZy8xOTk5LzAyLzIyLXJkZi1zeW50YXgtbnMjIj4KICA8cmRmOkRlc2NyaXB0aW9uIHJkZjphYm91dD0iIgogICAgeG1sbnM6dGlmZj0iaHR0cDovL25zLmFkb2JlLmNvbS90aWZmLzEuMC8iCiAgICB4bWxuczpleGlmPSJodHRwOi8vbnMuYWRvYmUuY29tL2V4aWYvMS4wLyIKICAgIHhtbG5zOnBob3Rvc2hvcD0iaHR0cDovL25zLmFkb2JlLmNvbS9waG90b3Nob3AvMS4wLyIKICAgIHhtbG5zOnhtcD0iaHR0cDovL25zLmFkb2JlLmNvbS94YXAvMS4wLyIKICAgIHhtbG5zOnhtcE1NPSJodHRwOi8vbnMuYWRvYmUuY29tL3hhcC8xLjAvbW0vIgogICAgeG1sbnM6c3RFdnQ9Imh0dHA6Ly9ucy5hZG9iZS5jb20veGFwLzEuMC9zVHlwZS9SZXNvdXJjZUV2ZW50IyIKICAgdGlmZjpJbWFnZUxlbmd0aD0iMzIiCiAgIHRpZmY6SW1hZ2VXaWR0aD0iMzIiCiAgIHRpZmY6UmVzb2x1dGlvblVuaXQ9IjIiCiAgIHRpZmY6WFJlc29sdXRpb249IjcyLzEiCiAgIHRpZmY6WVJlc29sdXRpb249IjcyLzEiCiAgIGV4aWY6UGl4ZWxYRGltZW5zaW9uPSIzMiIKICAgZXhpZjpQaXhlbFlEaW1lbnNpb249IjMyIgogICBleGlmOkNvbG9yU3BhY2U9IjEiCiAgIHBob3Rvc2hvcDpDb2xvck1vZGU9IjMiCiAgIHBob3Rvc2hvcDpJQ0NQcm9maWxlPSJzUkdCIElFQzYxOTY2LTIuMSIKICAgeG1wOk1vZGlmeURhdGU9IjIwMjYtMDMt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';

function YahooProviderIcon({ size = 27 }: { size?: number }) {
  return <img aria-hidden="true" className="provider-image-icon" src={yahooIconUrl} width={size} height={size}/>;
}
function Mt5ProviderIcon({ size = 27 }: { size?: number }) {
  return <img aria-hidden="true" className="provider-image-icon" src={mt5IconUrl} width={size} height={size}/>;
}

const providerIcons: Record<string, ComponentType<{ size?: number }>> = {
  dukascopy: Plus, tickdownloader: Download, 'file-import': FileUp,
  'sq-equity': Database, 'sq-futures': Server, darwinex: Cloud, crypto: Bitcoin,
  yahoo: YahooProviderIcon, mt5: Mt5ProviderIcon,
};
const contextIcons: Record<string, ComponentType<{ size?: number }>> = {
  'update-all': RefreshCw, 'update-selected': RefreshCw, 'mass-delete': Trash2,
  'save-definitions': Save, 'load-definitions': FolderOpen,
};
const commandIcons: Record<DataSourceCommandIcon, ComponentType<{ className?: string; size?: number }>> = {
  add: CirclePlus, binance: Bitcoin,
  bitfinex: ChartCandlestick, coinbase: Landmark, 'coin-m': CircleDollarSign,
  crypto: Coins, download: CloudDownload, 'file-import': FileInput,
  'folder-import': FolderInput, information: Info, 'mass-import': Files,
  poloniex: Network, refresh: RefreshCw, search: Search, 'symbol-list': ListPlus,
  'terminal-import': MonitorDown, 'usdt-m': DollarSign,
};

function CommandIcon({ icon, size = 15 }: { icon: DataSourceCommandIcon; size?: number }) {
  const Icon = commandIcons[icon];
  return <Icon className="command-icon" size={size}/>;
}

function ProviderMenu({ provider, isOpen, nestedOpen, onToggle, onToggleNested, onSelect }: {
  provider: DataSourceProvider; isOpen: boolean; nestedOpen: boolean; onToggle: () => void;
  onToggleNested: () => void; onSelect: (command: DataSourceCommand) => void;
}) {
  const Icon = providerIcons[provider.id] ?? Database;
  return <div className={`data-source-menu ${isOpen ? 'open' : ''}`}>
    <button className="data-source-button" data-control-id={provider.id} aria-haspopup="menu" aria-expanded={isOpen} aria-controls={`data-source-menu-${provider.id}`} onClick={onToggle}>
      <Icon size={27}/><span>{provider.label}</span><ChevronDown className="menu-chevron" size={12}/>
    </button>
    {isOpen && <div className="data-source-dropdown" id={`data-source-menu-${provider.id}`} role="menu" aria-label={`${provider.label} actions`}>
      {provider.commands.map(command => command.children ? <div className="nested-menu" key={command.id}>
        <button role="menuitem" data-command-icon={command.icon} aria-haspopup="menu" aria-expanded={nestedOpen} onClick={onToggleNested}><CommandIcon icon={command.icon}/><span>{command.label}</span><ChevronRight size={13}/></button>
        {nestedOpen && <div className="nested-dropdown" role="menu" aria-label={`${command.label} exchanges`}>
          {command.children.map(child => <button role="menuitem" data-command-icon={child.icon} key={child.id} onClick={() => onSelect(child)}><CommandIcon icon={child.icon} size={14}/><span>{child.label}</span></button>)}
        </div>}
      </div> : <button role="menuitem" data-command-icon={command.icon} key={command.id} onClick={() => onSelect(command)}>
        <CommandIcon icon={command.icon}/><span>{command.label}</span>
      </button>)}
    </div>}
  </div>;
}

function DateRangeFields() {
  return <div className="form-grid two"><Field label="Date from"><TextInput type="date" defaultValue="2018-01-01"/></Field><Field label="Date to"><TextInput type="date" defaultValue="2026-08-31"/></Field></div>;
}
function ExistingDataPolicy() {
  return <Field label="When existing data overlap"><Select value="replace" onChange={() => {}}><option value="replace">Replace overlapping data</option><option value="append">Keep existing data and append new history</option></Select></Field>;
}
function MockBoundaryNote() {
  return <p className="dialog-note">This research-workstation control is simulated. It does not contact a provider, transmit credentials, or modify native application data.</p>;
}
function downloadTextFile(filename: string, text: string, type = 'application/json;charset=utf-8') { const url = URL.createObjectURL(new Blob([text], { type })); const anchor = document.createElement('a'); anchor.href = url; anchor.download = filename; anchor.click(); URL.revokeObjectURL(url); }

function DataSourceDialog({ state, selectedCount, onClose, onSecondary, onComplete }: {
  state: DialogState; selectedCount: number; onClose: () => void;
  onSecondary: (id: DataSourceDialogId) => void; onComplete: (message: string) => void;
}) {
  const titles: Record<DataSourceDialogId, string> = {
    'new-instrument': 'Add instrument',
    'dukascopy-add': 'Add Dukascopy data', 'dukascopy-download': 'Download Dukascopy data',
    'dukascopy-information': 'Dukascopy data disclaimer', 'tickdownloader-import': 'Import data from TickDownloader',
    'file-add': 'Add symbol', 'file-import': 'Import one data file', 'file-mass-import': 'Import multiple data files',
    'sq-equity-find': 'Find and add Equity data',
    'sq-futures-find': 'Find and add Futures data', 'darwinex-add': 'Add Darwinex Tick Data',
    'darwinex-import': 'Import data from a Darwinex folder', 'darwinex-download': 'Download Darwinex data',
    'crypto-add': `Add ${state.exchange ?? 'crypto'} symbols`, 'crypto-download': 'Download Crypto data',
    'yahoo-add': 'Add Yahoo data', 'yahoo-download': 'Download Yahoo data', 'mt5-import': 'Import data from MT5',
    'mass-delete': 'Remove or clear selected datasets', 'save-definitions': 'Save selected dataset definitions',
    'load-definitions': 'Load dataset definitions', 'instrument-identification': 'Identify instruments for imported symbols',
    'data-format-name': 'Save data format', 'data-usage-conditions': 'Data usage conditions',
    'dependency-warning': 'Dependent dataset warning',
  };

  let content;
  switch (state.id) {
    case 'new-instrument':
      content = <div className="form-grid two"><Field label="Instrument symbol"><TextInput placeholder="EURUSD"/></Field><Field label="Instrument type"><Select value="forex" onChange={() => {}}><option value="forex">Forex</option><option value="futures">Futures</option><option value="stocks">Stocks</option><option value="crypto">Crypto</option></Select></Field><Field label="Base currency"><TextInput placeholder="EUR"/></Field><Field label="Quote currency"><TextInput placeholder="USD"/></Field></div>;
      break;
    case 'dukascopy-information':
      content = <section aria-label="Dukascopy disclaimer" style={{ lineHeight: 1.6, display: 'flex', flexDirection: 'column', gap: 12 }}><h1 style={{ textAlign: 'center', fontSize: 24 }}>Disclaimer</h1>
        <p>The Dukascopy Trading Tools include different financial information. Such data are a result of original and unique methods and technology of information gathering, compilation, analysis and statistical evaluation developed by Dukascopy Bank SA. Therefore, such data reflect the current fair value of the respective financial instruments as independently assessed by Dukascopy Bank SA and NOT the actual values at a given point in time. If you are looking to obtain actual quotes please contact the respective entities that provide this information.</p>
        <p>The Dukascopy Trading Tools data and/or any other data available as free product from Dukascopy Bank's website shall not constitute a forecast of the market value of any instruments at any future point either, and is not an investment advice or recommendation in any form.</p>
        <p>Anyone using and/or putting free web products including all or parts of the information taken from the Dukascopy Trading Tools and/or any other data available as free product from Dukascopy Bank's website shall put a clear note to the public that such data are not meant to indicate the actual value at any given point in time but represent a discretionary assessment by Dukascopy Bank SA only.</p>
        <p>The market data assessment system is in constant development and is provided "AS IS", "AS AVAILABLE", "WITH ALL ITS FAULTS" and is offered without any covenants or any express, implied or statutory warranties including (without limitation and qualification) any warranties as to accuracy, functionality, performance, merchantability, quiet enjoyment, system integration, data accuracy or fitness for any particular purpose and any warranties arising from trade usage, course of dealing or course of performance.</p>
      </section>;
      break;
    case 'crypto-download':
    case 'yahoo-download':
      content = <><DateRangeFields/><ExistingDataPolicy/><MockBoundaryNote/></>;
      break;
    case 'crypto-add':
      content = <><Field label="Exchange"><TextInput value={state.exchange ?? 'Selected exchange'} readOnly/></Field><div className="form-grid two"><Field label="Search symbols"><TextInput placeholder="BTCUSDT"/></Field><Field label="Data precision"><Select value="M1" onChange={() => {}}><option>M1</option><option>TICK</option></Select></Field><Field label="Data-name postfix"><TextInput placeholder="Optional"/></Field></div><div className="mock-symbol-list"><strong>Available symbols</strong><span>Symbol · Name · Available data range</span></div><MockBoundaryNote/></>;
      break;
    case 'yahoo-add':
      content = <><Field label="Yahoo symbols"><textarea className="text-area" placeholder={'AAPL\nMSFT\nEURUSD=X'}/></Field><Field label="Data-name postfix"><TextInput placeholder="Optional"/></Field><MockBoundaryNote/></>;
      break;
    case 'mass-delete':
      content = <><p><strong>{selectedCount}</strong> selected dataset{selectedCount === 1 ? '' : 's'} will be affected.</p><Field label="Requested operation"><Select value="remove" onChange={() => {}}><option value="remove">Remove dataset definitions and their mock data</option><option value="clear">Keep definitions and clear their mock data</option></Select></Field><p className="callout">A dependency check is required before this destructive operation can continue.</p></>;
      break;
    case 'save-definitions':
      content = <><p>Export definitions for <strong>{selectedCount}</strong> selected dataset{selectedCount === 1 ? '' : 's'}.</p><Field label="Suggested file name"><TextInput defaultValue="Data.json"/></Field><MockBoundaryNote/></>;
      break;
    case 'load-definitions':
      content = <><Field label="Dataset definition file"><input className="file-input compact" type="file" accept=".json,application/json"/></Field><p className="callout">The JSON file will be validated for supported schema, contained values, and conflicting identities before any mock definitions are applied.</p><MockBoundaryNote/></>;
      break;
    case 'instrument-identification':
      content = <><p>Map each provider symbol to an existing instrument or skip it. Automatic guessing is never silently accepted.</p><div className="form-grid two"><Field label="Provider symbol"><TextInput value="EURUSD" readOnly/></Field><Field label="Target instrument"><Select value="EURUSD" onChange={() => {}}><option>EURUSD</option><option>Default instrument</option><option>Skip this symbol</option></Select></Field></div></>;
      break;
    case 'data-format-name':
      content = <Field label="Format name"><TextInput placeholder="My broker OHLCV format"/></Field>;
      break;
    case 'data-usage-conditions':
      content = <><p>Market-data availability and permitted usage depend on the applicable data-provider terms. This application does not grant redistribution rights or guarantee continued access.</p><MockBoundaryNote/></>;
      break;
    case 'dependency-warning':
      content = <p className="callout">One or more selected datasets may be used as a source for derived data. Removing or clearing the source can prevent future derived-data updates. Continue only after reviewing those dependencies.</p>;
      break;
  }

  return <Modal title={titles[state.id]} width={560} onClose={onClose} footer={<>
    {state.id === 'dukascopy-information' ? <>
      <Button className="secondary" onClick={() => onSecondary('data-usage-conditions')}>Usage conditions</Button>
      <Button className="primary" onClick={onClose}>Understood</Button>
    </> : <>
      <Button className="secondary" onClick={onClose}>Close</Button>
      <Button className="primary" onClick={() => onComplete(`${titles[state.id]} completed using simulated data`)}>Save</Button>
    </>}
  </>}>{content}</Modal>;
}

function InstrumentTable({ selected, onSelect, onEdit, onDelete }: {
  selected: string[]; onSelect: (ids: string[]) => void;
  onEdit: (item: FileInstrument) => void; onDelete: (item: FileInstrument) => void;
}) {
  const instruments = useFileSymbols(state => state.instruments);
  const overrides = useFileSymbols(state => state.overrides);
  const removed = useFileSymbols(state => state.removed);
  const [descending, setDescending] = useState(false);
  const [query, setQuery] = useState('');
  const [type, setType] = useState('');
  const [broker, setBroker] = useState('');
  const effective = effectiveInstruments(instruments, overrides, removed);
  const rows = effective.filter(item => (!type || item.type === type)
    && (!broker || item.broker === broker)
    && (item.symbol + ' ' + item.name).toLowerCase().includes(query.toLowerCase()))
    .sort((a, b) => a.symbol.localeCompare(b.symbol) * (descending ? -1 : 1));
  const allSelected = rows.length > 0 && rows.every(item => selected.includes(item.symbol));
  const columns = ['Description', 'Broker profile', 'Point value', 'Pip/Tick size', 'Pip/Tick step',
    'Default spread', 'Default slippage', 'Commissions', 'Swap', 'Data type', 'Order size mult.', 'Order size step'];
  return <main className="full dataset-workspace" aria-label="Instruments">
    <div className="dataset-filters">
      <input className="text-input" aria-label="Filter instruments" placeholder="Filter items" value={query} onChange={event => setQuery(event.target.value)}/>
      <select className="text-input" aria-label="Instrument data type" value={type} onChange={event => setType(event.target.value)}>
        <option value="">All data types</option>{[...new Set(instruments.map(item => item.type))].map(type => <option key={type}>{type}</option>)}
      </select>
      <select className="text-input" aria-label="Instrument broker profile" value={broker} onChange={event => setBroker(event.target.value)}><option value="">All broker profiles</option>{[...new Map(instruments.map(item => [item.broker, item.brokerName])).entries()].map(([id, name]) => <option value={id} key={id}>{name}</option>)}</select>
    </div>
    <div className="dataset-grid"><table className="plain-table instrument-table" aria-label="Instruments">
      <thead><tr>
        <th><input type="checkbox" aria-label="Select all visible instruments" checked={allSelected} disabled={!rows.length} onChange={() => onSelect(allSelected ? selected.filter(symbol => !rows.some(item => item.symbol === symbol)) : [...new Set([...selected, ...rows.map(item => item.symbol)])])}/></th>
        <th aria-sort={descending ? 'descending' : 'ascending'}><button className="dataset-sort" onClick={() => setDescending(value => !value)}>Instrument <span aria-hidden="true">{descending ? '▾' : '▴'}</span></button></th>
        {columns.map(column => <th key={column}>{column}</th>)}<th aria-label="Row actions"/>
      </tr></thead>
      <tbody>{rows.map(item => <tr key={item.symbol} className={selected.includes(item.symbol) ? 'selected' : ''} onDoubleClick={() => onEdit(item)}>
        <td><input type="checkbox" aria-label={`Select instrument ${item.symbol}`} checked={selected.includes(item.symbol)} onChange={() => onSelect(selected.includes(item.symbol) ? selected.filter(symbol => symbol !== item.symbol) : [...selected, item.symbol])}/></td>
        <td><strong>{item.symbol}</strong></td><td title={item.name}>{item.name}</td><td>{item.brokerName}</td>
        <td>{item.pointValue.toLocaleString()}</td><td>{item.tickSize}</td><td>{item.tickStep}</td><td>{item.spread}</td>
        <td>{item.slippage}</td><td>{item.commission.model}</td><td>{item.swap.use ? item.swap.type : "None"}</td><td>{item.type}</td><td>{item.multiplier}</td><td>{item.sizeStep}</td>
        <td><button className="instrument-remove" aria-label={`Delete instrument ${item.symbol}`} title="Delete instrument" onClick={event => { event.stopPropagation(); onDelete(item); }}>×</button></td>
      </tr>)}{!rows.length && <tr><td colSpan={15} className="dataset-empty">No matching instruments.</td></tr>}</tbody>
    </table></div>
  </main>;
}

function ExternalIndicatorsTable({ rows: allRows, selected, job, onSelect, onEdit, onDelete }: { rows: ExternalIndicatorDefinition[]; selected: string[]; job?: { indicator?: string; state?: string; progress?: number }; onSelect: (names: string[]) => void; onEdit: (item: ExternalIndicatorDefinition) => void; onDelete: (item: ExternalIndicatorDefinition) => void }) {
  const [query, setQuery] = useState(''); const [dataType, setDataType] = useState('');
  const rows = allRows.filter(item => (!dataType || String(item.type) === dataType) && item.name.toLowerCase().includes(query.toLowerCase())).sort((a, b) => a.name.localeCompare(b.name));
  const allSelected = rows.length > 0 && rows.every(item => selected.includes(item.name));
  return <main className="full dataset-workspace" aria-label="External indicators">
    <div className="dataset-filters">
      <input className="text-input" aria-label="Filter external indicators" placeholder="Filter items" value={query} onChange={event => setQuery(event.target.value)}/>
      <select className="text-input" aria-label="External indicator data type" value={dataType} onChange={event => setDataType(event.target.value)}><option value="">All data types</option>{externalIndicatorTypes.map(item => <option key={item.value} value={item.value}>{item.label}</option>)}</select>
      <span role="status">Records: {rows.length}</span>
    </div>
    <div className="dataset-grid external-indicators-grid"><table className="plain-table" aria-label="External indicators">
      <colgroup><col style={{ width:26 }}/><col style={{ width:145 }}/><col style={{ width:100 }}/><col style={{ width:225 }}/><col style={{ width:90 }}/><col style={{ width:108 }}/><col style={{ width:108 }}/><col style={{ width:90 }}/><col style={{ width:108 }}/><col/><col style={{ width:26 }}/></colgroup>
      <thead><tr><th><input type="checkbox" aria-label="Select all external indicators" checked={allSelected} disabled={!rows.length} onChange={() => onSelect(allSelected ? selected.filter(name => !rows.some(item => item.name === name)) : [...new Set([...selected, ...rows.map(item => item.name)])])}/></th>
        {['Name', 'Values', 'Data type', 'Timeframe', 'Date from', 'Date to', 'Total Days', 'Total Records'].map(column => <th key={column}>{column}</th>)}<th aria-label="Status"/><th aria-label="Row actions"/>
      </tr></thead>
      <tbody>{rows.map(item => <tr key={item.name} className={selected.includes(item.name) ? 'selected' : ''} onDoubleClick={() => onEdit(item)}><td><input type="checkbox" aria-label={`Select indicator ${item.name}`} checked={selected.includes(item.name)} onChange={() => onSelect(selected.includes(item.name) ? selected.filter(name => name !== item.name) : [...selected, item.name])}/></td><td>{item.name}</td><td>{activeExternalLines(item).length}</td><td>{externalTypeLabel(item.type)}</td><td>{item.timeframe || '—'}</td><td>{item.dateFrom || '—'}</td><td>{item.dateTo || '—'}</td><td>{item.totalDays}</td><td>{item.records.length.toLocaleString()}</td><td className="indicator-status" aria-label={`Status for ${item.name}`}>{job?.indicator === item.name ? job.state === 'completed' ? 'Completed' : `${job.state} ${job.progress}%` : ''}</td><td><button className="instrument-remove" aria-label={`Delete indicator ${item.name}`} onClick={() => onDelete(item)}>×</button></td></tr>)}{!rows.length && <tr><td colSpan={11} className="dataset-empty">No External indicators defined.</td></tr>}</tbody>
    </table></div>
  </main>;
}

function SessionTable({ rows:allRows, selected, onSelect, onEdit, onDelete, brokers }:{rows:SessionDefinition[];selected:string[];onSelect:(names:string[])=>void;onEdit:(item:SessionDefinition)=>void;onDelete:(item:SessionDefinition)=>void;brokers:SessionBroker[]}) {
  const [query, setQuery] = useState('');
  const [broker,setBroker]=useState('');
  const rows=allRows.filter(item=>(!broker||item.broker===broker)&&(item.name+' '+item.brokerName).toLowerCase().includes(query.toLowerCase())).sort((a,b)=>a.name.localeCompare(b.name));
  const allSelected = rows.length > 0 && rows.every(item => selected.includes(item.name));
  return <main className="full dataset-workspace" aria-label="Sessions">
    <div className="dataset-filters">
      <input className="text-input" aria-label="Filter sessions" placeholder="Filter items" value={query} onChange={event => setQuery(event.target.value)}/>
      <select className="text-input" aria-label="Session broker profile" value={broker} onChange={event=>setBroker(event.target.value)}><option value="">All broker profiles</option>{brokers.map(item=><option value={item.id} key={item.id}>{item.name}</option>)}</select>
    </div>
    <div className="dataset-grid session-grid"><table className="plain-table session-table" aria-label="Sessions">
      <colgroup><col style={{ width: 26 }}/><col style={{ width: 500 }}/><col style={{ width: 150 }}/><col/><col style={{ width: 26 }}/></colgroup>
      <thead><tr>
        <th><input type="checkbox" aria-label="Select all visible sessions" checked={allSelected} disabled={!rows.length} onChange={() => onSelect(allSelected ? selected.filter(name => !rows.some(item=>item.name===name)) : [...new Set([...selected, ...rows.map(item=>item.name)])])}/></th>
        <th>Session Name</th><th>Broker profile</th><th aria-label="Unused space"/><th aria-label="Row actions"/>
      </tr></thead>
      <tbody>{rows.map(item => <tr key={item.name} className={selected.includes(item.name) ? 'selected' : ''} onDoubleClick={()=>onEdit(item)}>
        <td><input type="checkbox" aria-label={`Select session ${item.name}`} checked={selected.includes(item.name)} onChange={() => onSelect(selected.includes(item.name) ? selected.filter(name => name !== item.name) : [...selected, item.name])}/></td>
        <td><strong>{item.name}</strong></td><td>{item.brokerName}</td><td/>
        <td><button className="instrument-remove" aria-label={`Delete session ${item.name}`} onClick={event=>{event.stopPropagation();onDelete(item);}}>×</button></td>
      </tr>)}{!rows.length && <tr><td colSpan={5} className="dataset-empty">No matching sessions.</td></tr>}</tbody>
    </table></div>
  </main>;
}

function StockGroupsTable({ groups: allGroups, selected, datasets, onSelect, onEdit, onUpdate }: {
  groups: StockGroupDefinition[]; selected: string[]; datasets: ToolTarget[];
  onSelect: (ids: string[]) => void; onEdit: (group: StockGroupDefinition) => void;
  onUpdate: (group: StockGroupDefinition) => void;
}) {
  const [descending, setDescending] = useState(false);
  const [query, setQuery] = useState('');
  const rows = allGroups.filter(item => item.name.toLowerCase().includes(query.toLowerCase())).sort((a, b) => a.name.localeCompare(b.name) * (descending ? -1 : 1));
  const allSelected = rows.length > 0 && rows.every(item => selected.includes(item.id));
  return <main className="full dataset-workspace" aria-label="Stock groups">
    <div className="dataset-filters">
      <input className="text-input" aria-label="Filter stock groups" placeholder="Filter items" value={query} onChange={event => setQuery(event.target.value)}/>
    </div>
    <div className="dataset-grid stock-groups-grid"><table className="plain-table" aria-label="Stock groups">
      <thead><tr>
        <th><input type="checkbox" aria-label="Select all stock groups" checked={allSelected} disabled={!rows.length} onChange={() => onSelect(allSelected ? selected.filter(id => !rows.some(item => item.id === id)) : [...new Set([...selected, ...rows.map(item => item.id)])])}/></th>
        <th aria-sort={descending ? 'descending' : 'ascending'}><button className="dataset-sort" onClick={() => setDescending(value => !value)}>Name <span aria-hidden="true">{descending ? '▾' : '▴'}</span></button></th>
        <th>Count</th><th>Description</th><th>Number of symbols</th><th>Downloaded</th><th>Ready to use?</th><th>Data from</th><th>Data to</th>
      </tr></thead>
      <tbody>{rows.map(item => {
        const summary = summarizeGroup(item, datasets);
        return <tr key={item.id} className={selected.includes(item.id) ? 'selected' : ''} onDoubleClick={() => onEdit(item)}>
          <td><input type="checkbox" aria-label={`Select group ${item.name}`} checked={selected.includes(item.id)} onChange={() => onSelect(selected.includes(item.id) ? selected.filter(id => id !== item.id) : [...selected, item.id])}/></td>
          <td><strong>{item.name}</strong></td><td>{item.members.length}</td><td title={item.description}>{item.description}</td>
          <td>{summary.numberOfSymbols}</td><td>{summary.downloaded}</td><td>{summary.ready ? 'Yes' : 'No'}</td><td>{summary.from || '—'}</td><td>{summary.to || '—'}</td>
        </tr>;
      })}{!rows.length && <tr><td colSpan={9} className="dataset-empty">No groups of stocks are defined.</td></tr>}</tbody>
    </table></div>
  </main>;
}

function BrokerProfilesTable({ profiles: allProfiles, selected, instruments, sessions, onSelect, onEdit }: {
  profiles: BrokerProfile[]; selected: string[]; instruments: FileInstrument[]; sessions: SessionDefinition[];
  onSelect: (ids: string[]) => void; onEdit: (profile: BrokerProfile) => void;
}) {
  const [descending, setDescending] = useState(false);
  const [query, setQuery] = useState('');
  const rows = allProfiles.filter(item => item.name.toLowerCase().includes(query.toLowerCase())).sort((a, b) => a.name.localeCompare(b.name) * (descending ? -1 : 1));
  const allSelected = rows.length > 0 && rows.every(item => selected.includes(item.id));
  return <main className="full dataset-workspace" aria-label="Broker profiles">
    <div className="dataset-filters">
      <input className="text-input" aria-label="Filter broker profiles" placeholder="Filter items" value={query} onChange={event => setQuery(event.target.value)}/>
    </div>
    <div className="dataset-grid broker-profiles-grid"><table className="plain-table" aria-label="Broker profiles">
      <thead><tr>
        <th><input type="checkbox" aria-label="Select all broker profiles" checked={allSelected} disabled={!rows.length} onChange={() => onSelect(allSelected ? selected.filter(id => !rows.some(item => item.id === id)) : [...new Set([...selected, ...rows.map(item => item.id)])])}/></th>
        <th aria-sort={descending ? 'descending' : 'ascending'}><button className="dataset-sort" onClick={() => setDescending(value => !value)}>Name <span aria-hidden="true">{descending ? '▾' : '▴'}</span></button></th>
        <th>Description</th><th>Postfix</th><th>Timezone</th><th>Customized stocks</th><th>Customized instruments</th><th>Customized sessions</th>
      </tr></thead>
      <tbody>{rows.map(item => {
        const counts = brokerCounts(item, instruments, sessions);
        return <tr key={item.id} className={selected.includes(item.id) ? 'selected' : ''} onDoubleClick={() => onEdit(item)}>
          <td><input type="checkbox" aria-label={`Select broker ${item.name}`} checked={selected.includes(item.id)} onChange={() => onSelect(selected.includes(item.id) ? selected.filter(id => id !== item.id) : [...selected, item.id])}/></td>
          <td><strong>{item.name}</strong></td><td title={item.desc}>{item.desc}</td><td>{item.postfix}</td><td>{item.timezone}</td>
          <td>{counts.stocks}</td><td>{counts.instruments}</td><td>{counts.sessions}</td>
        </tr>;
      })}{!rows.length && <tr><td colSpan={8} className="dataset-empty">No brokers are defined.</td></tr>}</tbody>
    </table></div>
  </main>;
}

function DatasetTable({ selectedIds, onToggle, onSelect, pluginStates, dbDatasets, dbDatasetsLoaded }: {
  selectedIds: string[]; onToggle: (id: string) => void; onSelect: (ids: string[]) => void;
  pluginStates: Record<string, any>;
  dbDatasets: DatasetRow[];
  dbDatasetsLoaded: boolean;
}) {
  const definitions = useDataManagerStore(state => state.definitions);
  const fileDefinitions = useFileSymbols(state => state.definitions);
  const stockGroups = useStockGroups();
  const [stockGroup, setStockGroup] = useState('');

  const dukasRanges = pluginStates['dukascopy']?.ranges ?? {};
  const backendDukascopy = pluginStates['dukascopy']?.backendAvailable === true;
  const baseDatasets = (dbDatasets.length > 0
    ? dbDatasets.map(row => ({
        ...row,
        underlying: row.underlying || row.symbol,
        instrument: row.instrument || row.symbol,
        brokerName: row.brokerName || '—',
        timezone: row.timezone || '—',
        category: row.category || '—',
        ...simulationSummary(row, dukasRanges[row.id] ?? []),
      }))
    : [...definitions.filter(row => !(dbDatasetsLoaded || backendDukascopy) || row.source !== 'Dukascopy'), ...(pluginStates['td']?.definitions ?? []), ...fileDefinitions].map(row => ({ ...row, ...simulationSummary(row, dukasRanges[row.id] ?? []) }))
  );

  const pluginRows: any[] = Object.entries(pluginStates).flatMap(([id, state]) =>
    dbDatasetsLoaded && id === 'dukascopy' ? [] : state?.definitions ?? state?.records ?? []);
  const fileRecords = pluginStates['file-import']?.records ?? [];
  const committed = [
    ...stockGroups.generated,
    ...baseDatasets.filter(row => !fileRecords.some((record: any) => record.id === row.id)),
    ...pluginRows.filter(row => !baseDatasets.some((b: any) => b.id === row.id)),
  ];

  const fileJob = pluginStates['file-import']?.job;
  const pendingTasks = (isOperationActive(fileJob?.state) ? fileJob?.tasks : [])?.filter((task: any) => !committed.some(row => row.id === task.record.id)).map((task: any) => ({ ...task.record, from: '', to: '', bars: 0 })) ?? [];
  const allDatasets = [...committed, ...pendingTasks];

  const [query, setQuery] = useState('');
  const [source, setSource] = useState('');
  const [dataType, setDataType] = useState('');
  const [brokerFilter,setBrokerFilter]=useState('');
  const [hiddenIds, setHiddenIds] = useState<string[]>([]);
  const [descending, setDescending] = useState(false);
  const rows = allDatasets.filter(row => (!source || row.source === source)
    && (!stockGroup || stockGroups.groups.find(group => group.id === stockGroup)?.members.some(member => member.ticker === row.symbol))
    && (!dataType || row.category === dataType)
    && (!brokerFilter || row.brokerName === brokerFilter)
    && (row.symbol + ' ' + row.source).toLowerCase().includes(query.toLowerCase()))
    .sort((a, b) => a.symbol.localeCompare(b.symbol) * (descending ? -1 : 1));
  const allSelected = rows.length > 0 && rows.every(row => selectedIds.includes(row.id));
  const columns = ['Instrument', 'Broker profile', 'Underlying Symbol', 'Timeframe', 'Timezone',
    'Date from', 'Date to', 'Total Days', 'Total Records', 'Source', 'Bar type', 'Data type', 'Hide'];
  return <main className="full dataset-workspace" aria-label="Historical data">
    <div className="dataset-filters">
      <input className="text-input" aria-label="Filter items" placeholder="Filter items" value={query} onChange={event => setQuery(event.target.value)}/>
      <select className="text-input" aria-label="Data source" value={source} onChange={event => setSource(event.target.value)}>
        <option value="">All data sources</option>{[...new Set(allDatasets.map(row => row.source))].map(value => <option key={value}>{value}</option>)}
      </select>
      <select className="text-input" aria-label="Data type" value={dataType} onChange={event => setDataType(event.target.value)}>
        <option value="">All data types</option>{[...new Set(allDatasets.map(item => item.category))].map(value => <option key={value}>{value}</option>)}
      </select>
      <select className="text-input" aria-label="Stock group" value={stockGroup} onChange={event => setStockGroup(event.target.value)}><option value="">By stock group - none</option>{stockGroups.groups.map(group => <option value={group.id} key={group.id}>{group.name}</option>)}</select>
      <select className="text-input" aria-label="Broker profile" value={brokerFilter} onChange={event=>setBrokerFilter(event.target.value)}><option value="">All broker profiles</option>{[...new Set(allDatasets.map(row=>row.brokerName).filter(name=>name&&name!=='—'))].map(name=><option key={name}>{name}</option>)}</select>
      <span role="status">Records: {rows.length}</span>
    </div>
    <div className="dataset-grid"><table className="plain-table" aria-label="Historical data">
      <thead><tr>
        <th><input type="checkbox" aria-label="Select all visible datasets" checked={allSelected} disabled={!rows.length} onChange={() => onSelect(allSelected ? selectedIds.filter(id => !rows.some(row => row.id === id)) : [...new Set([...selectedIds, ...rows.map(row => row.id)])])}/></th>
        <th aria-sort={descending ? 'descending' : 'ascending'}><button className="dataset-sort" onClick={() => setDescending(value => !value)}>Symbol Name <span aria-hidden="true">{descending ? '▾' : '▴'}</span></button></th>
        {columns.map(column => <th key={column}>{column}</th>)}<th aria-label="Status" style={{ minWidth: 120 }}/>
      </tr></thead>
      <tbody>{rows.map(row => {
        const days = row.from && row.to ? Math.floor((Date.parse(row.to) - Date.parse(row.from)) / 86400000) + 1 : 0;

        let rowStatus = '';
        let rowTooltip = '';

        for (const [, s] of Object.entries(pluginStates)) {
          if (!s) continue;
          const job = s.job;
          if (!job) continue;
          if (job.definitions && Array.isArray(job.definitions)) {
            const idx = job.definitions.findIndex((item: any) => item.id === row.id);
            if (idx >= 0) {
              rowStatus = idx < (job.completed ?? 0) ? 'Completed' : `${job.state} ${job.progress}%`;
              rowTooltip = job.error || '';
              break;
            }
          }
          if (job.tasks && Array.isArray(job.tasks)) {
            const idx = job.tasks.findIndex((t: any) => t.record?.id === row.id || t.source?.id === row.id || t.definition?.id === row.id);
            if (idx >= 0) {
              rowStatus = (idx < (job.completed ?? 0) || job.state === 'completed') ? 'Completed' : `${job.state.charAt(0).toUpperCase()}${job.state.slice(1)} ${job.progress}%`;
              rowTooltip = job.error || '';
              break;
            }
          }
          if (job.targetIds && Array.isArray(job.targetIds)) {
            if (job.targetIds.includes(row.id)) {
              rowStatus = job.state === 'completed' ? 'Completed' : `${job.state.charAt(0).toUpperCase()}${job.state.slice(1)} ${job.progress}%`;
              rowTooltip = job.error || '';
              break;
            }
          }
          if (row.id.startsWith('td:') && job.request?.symbols?.some((sym: string) => `td:${sym + (job.request.postfix ?? '')}` === row.id)) {
            rowStatus = job.state === 'completed' ? 'Completed' : `${job.state.charAt(0).toUpperCase()}${job.state.slice(1)} ${job.progress}%`;
            rowTooltip = job.error || '';
            break;
          }
          if (job.request?.targets?.some((t: any) => t.id === row.id)) {
            rowStatus = job.state === 'completed' ? 'Completed' : `${job.state.charAt(0).toUpperCase()}${job.state.slice(1)} ${job.progress}%`;
            rowTooltip = job.error || '';
            break;
          }
        }

        if (!rowStatus) {
          if (fileRecords.some((record: any) => record.id === row.id) || stockGroups.generated.some(record => record.id === row.id) || pluginRows.some(item => item.id === row.id)) {
            rowStatus = 'Completed';
          }
        }

        return <tr key={row.id} className={selectedIds.includes(row.id) ? 'selected' : ''}>
          <td><input type="checkbox" aria-label={`Select ${row.symbol}`} checked={selectedIds.includes(row.id)} onChange={() => onToggle(row.id)}/></td>
          <td><strong>{row.symbol}</strong></td><td>{row.instrument}</td><td>{row.brokerName}</td><td>{row.underlying}</td>
          <td>{row.timeframe}</td><td>{row.timezone}</td><td>{row.from || '—'}</td><td>{row.to || '—'}</td><td>{days.toLocaleString()}</td>
          <td>{row.bars.toLocaleString()}</td><td>{row.source}</td><td>{"barType" in row ? row.barType === "start" ? "Start of bar" : "End of bar" : "—"}</td><td>{row.category}</td>
          <td><input type="checkbox" aria-label={`Hide ${row.symbol}`} checked={hiddenIds.includes(row.id)} onChange={() => setHiddenIds(current => current.includes(row.id) ? current.filter(id => id !== row.id) : [...current, row.id])}/></td>
          <td aria-label={`Status for ${row.symbol}`} title={rowTooltip}>{rowStatus}</td>
        </tr>;
      })}{!rows.length && <tr><td colSpan={16} className="dataset-empty">{allDatasets.length ? 'No matching data.' : 'No data defined.'}</td></tr>}</tbody>
    </table></div>
  </main>;
}

function getProviderJobLabel(owner: string, states: Record<string, any>): string {
  if (owner === 'broker') return 'Broker data update';
  if (owner === 'stock-groups') return 'Stock group data update';
  if (owner === 'external' || owner === 'indicators') return `Custom data import for '${states['indicators']?.job?.indicator ?? ''}'`;
  if (owner === 'tools') return 'Clone to timezone';
  if (owner === 'export') return states['export']?.job?.label ?? 'Export';
  if (owner === 'mt5') return 'MT5 mock import';
  if (owner === 'yahoo') return `Yahoo mock ${states['yahoo']?.job?.kind ?? 'download'}`;
  if (owner === 'crypto') return `Crypto mock ${states['crypto']?.job?.kind ?? 'download'}`;
  if (owner === 'darwinex') return `Darwinex mock ${states['darwinex']?.job?.kind ?? 'download'}`;
  if (owner === 'sq') return states['sq']?.job?.provider === 'futures' ? 'Futures data mock update' : 'Equity data mock update';
  if (owner === 'file') return 'File import';
  if (owner === 'td') return 'TickDownloader mock import';
  return 'Dukascopy download unavailable';
}

export function DataManager() {
  const plugins = useAttachments<DataSourcePluginPort>('data_source.presentation');
  const [pluginStates, setPluginStates] = useState<Record<string, any>>({});
  const handlePluginSync = useCallback((id: string, state: any) => {
    setPluginStates(prev => ({ ...prev, [id]: state }));
  }, []);

  const workspaceStorageError = useDataManagerStore(state => state.storageError);
  const instrumentStorageError = useFileSymbols(state => state.storageError);
  const definitions = useDataManagerStore(state => state.definitions);
  const brokerProfiles = useDataManagerStore(state => state.brokers);
  const brokerJob = useDataManagerStore(state => state.brokerJob);

  const [dbDatasets, setDbDatasets] = useState<DatasetRow[]>([]);
  const [dbDatasetsLoaded, setDbDatasetsLoaded] = useState(false);
  const loadDatabaseDatasets = useCallback(() => {
    actionsClient
      .listDatasets()
      .then(rows => {
        if (Array.isArray(rows)) {
          setDbDatasets(rows);
          setDbDatasetsLoaded(true);
        }
      })
      .catch(() => {});
  }, []);

  useEffect(() => {
    loadDatabaseDatasets();
  }, [loadDatabaseDatasets]);

  const fileDefinitions = useFileSymbols(state => state.definitions);
  const fileInstruments = useFileSymbols(state => state.instruments);
  const instrumentOverrides = useFileSymbols(state => state.overrides);
  const removedInstruments = useFileSymbols(state => state.removed);
  const customSessions = useSessions(state => state.sessions);
  const sessionOverrides = useSessions(state => state.overrides);
  const removedSessions = useSessions(state => state.removed);
  const stockGroups = useStockGroups();

  const fileImports = pluginStates['file-import'];
  useEffect(() => { try { if (fileImports?.groups) useStockGroups.getState().syncImports(fileImports.groups); } catch {} }, [fileImports?.groups]);
  useEffect(() => { if (stockGroups.job?.state !== 'running') return; const timer = window.setInterval(() => useStockGroups.getState().advance(), 220); return () => window.clearInterval(timer); }, [stockGroups.job?.state]);
  useEffect(() => { if (brokerJob?.state !== 'running') return; const timer = window.setInterval(() => useDataManagerStore.getState().advanceBrokerUpdate(), 220); return () => window.clearInterval(timer); }, [brokerJob?.state]);

  useEffect(() => {
    const timer = window.setInterval(() => {
      for (const plugin of plugins) {
        plugin.advance?.();
      }
    }, 220);
    return () => window.clearInterval(timer);
  }, [plugins]);

  const [progressOwner, setProgressOwner] = useState<string>('download');
  const activePlugin = plugins.find(p => p.pluginId === progressOwner);
  const pluginJob = pluginStates[progressOwner]?.job ?? null;
  const providerJob = progressOwner === 'broker' ? brokerJob : progressOwner === 'stock-groups' ? stockGroups.job : pluginJob;
  const providerAction = (act: 'pause' | 'resume' | 'stop') => {
    if (progressOwner === 'broker') {
      useDataManagerStore.getState().brokerAction(act);
    } else if (progressOwner === 'stock-groups') {
      stockGroups.action(act);
    } else {
      activePlugin?.action?.(act);
    }
  };

  const [tab, setTab] = useState('Data sources');
  const [dialog, setDialog] = useState<DialogState | null>(null);
  const [instrumentDialog, setInstrumentDialog] = useState<InstrumentDialogState | null>(null);
  const [selectedInstrumentIds, setSelectedInstrumentIds] = useState<string[]>([]);
  const [instrumentError, setInstrumentError] = useState('');
  const [sessionDialog,setSessionDialog]=useState<SessionDialogState|null>(null);
  const [selectedSessionIds,setSelectedSessionIds]=useState<string[]>([]);
  const [sessionError,setSessionError]=useState('');
  const [externalDialog, setExternalDialog] = useState<ExternalIndicatorDialogState | null>(null);
  const [selectedExternalNames, setSelectedExternalNames] = useState<string[]>([]);
  const [stockGroupDialog, setStockGroupDialog] = useState<StockGroupDialogState | null>(null);
  const [selectedStockGroupIds, setSelectedStockGroupIds] = useState<string[]>([]);
  const [stockGroupError, setStockGroupError] = useState('');
  const [brokerDialog,setBrokerDialog]=useState<BrokerDialogState|null>(null);
  const [selectedBrokerIds,setSelectedBrokerIds]=useState<string[]>([]);
  const [brokerError,setBrokerError]=useState('');
  const [exportDialog, setExportDialog] = useState<{ kind: ExportKind; targets: ExportTarget[] } | null>(null);
  const [cloneTargets, setCloneTargets] = useState<ToolTarget[] | null>(null);
  const [reviewTarget, setReviewTarget] = useState<ToolTarget | null>(null);
  const [openMenu, setOpenMenu] = useState<string | null>(null);
  const [nestedOpen, setNestedOpen] = useState(false);
  const [selectedDatasetIds, setSelectedDatasetIds] = useState<string[]>([]);
  const [progress, setProgress] = useState(0);
  const [operationState, setOperationState] = useState<OperationState>('idle');
  const [operationLabel, setOperationLabel] = useState('No active operations');
  const [selectionMessage, setSelectionMessage] = useState('');
  useEffect(() => { if (selectedDatasetIds.length > 0) setSelectionMessage(''); }, [selectedDatasetIds]);
  const [logEntries, setLogEntries] = useState<string[]>([]);
  const lastLoggedTransition = useRef('');
  const lastStockGroupTransition = useRef('');
  const lastBrokerTransition=useRef('');
  useEffect(()=>{if(!brokerJob)return;const transition=`${brokerJob.state}:${brokerJob.progress}`;if(lastBrokerTransition.current===transition)return;lastBrokerTransition.current=transition;if(brokerJob.progress%25!==0&&!['paused','failed','cancelled','completed'].includes(brokerJob.state))return;setLogEntries(current=>[...current,`${new Date().toLocaleString()} Broker data update — ${brokerJob.state} ${brokerJob.progress}% (simulation)`].slice(-500));},[brokerJob]);
  useEffect(() => {
    if (!stockGroups.job) return;
    const transition = `${stockGroups.job.state}:${stockGroups.job.progress}`;
    if (lastStockGroupTransition.current === transition) return;
    lastStockGroupTransition.current = transition;
    if (stockGroups.job.progress % 25 !== 0 && !['paused','failed','cancelled','completed'].includes(stockGroups.job.state)) return;
    const timestamp = new Date().toLocaleString();
    setLogEntries(current => [...current, `${timestamp} Stock group data update — ${stockGroups.job!.state} ${stockGroups.job!.progress}% (simulation)`].slice(-500));
  }, [stockGroups.job]);
  useEffect(() => {
    if (operationState === 'idle') return;
    const transition = operationLabel + ':' + operationState;
    if (lastLoggedTransition.current === transition) return;
    lastLoggedTransition.current = transition;
    const timestamp = new Date().toLocaleString();
    setLogEntries(current => [...current, timestamp + ' ' + operationLabel + ' — ' + operationState + ' (simulation)'].slice(-500));
  }, [operationLabel, operationState]);
  const [lastControlId, setLastControlId] = useState<string | null>(null);
  const ribbonRef = useRef<HTMLDivElement>(null);
  const notify = useAppStore(state => state.notify);

  const exportJob = pluginStates['export']?.job;
  const downloadedExport = useRef(exportJob?.state === 'completed' ? exportJob.id : '');
  useEffect(() => {
    if (exportJob?.state !== 'completed' || downloadedExport.current === exportJob.id) return;
    downloadedExport.current = exportJob.id;
    if (exportJob.artifacts) downloadExportArtifacts(exportJob.artifacts);
    notify(`${exportJob.label} completed — ${exportJob.artifacts.length} file${exportJob.artifacts.length === 1 ? '' : 's'} downloaded`);
  }, [exportJob, notify]);

  useEffect(() => {
    if (operationState !== 'running') return;
    const timer = window.setInterval(() => setProgress(current => {
      const next = Math.min(100, current + 8);
      if (next === 100) window.setTimeout(() => { setOperationState('completed'); notify(`${operationLabel} completed using simulated data`); }, 0);
      return next;
    }), 180);
    return () => window.clearInterval(timer);
  }, [notify, operationLabel, operationState]);

  useEffect(() => {
    const closeMenus = (event: MouseEvent) => { if (!ribbonRef.current?.contains(event.target as Node)) { setOpenMenu(null); setNestedOpen(false); } };
    const closeOnEscape = (event: KeyboardEvent) => { if (event.key === 'Escape') { setOpenMenu(null); setNestedOpen(false); } };
    document.addEventListener('mousedown', closeMenus);
    document.addEventListener('keydown', closeOnEscape);
    return () => { document.removeEventListener('mousedown', closeMenus); document.removeEventListener('keydown', closeOnEscape); };
  }, []);

  const anyPluginActive = Object.values(pluginStates).some(s => s?.active);
  const anyOperationActive = [brokerJob?.state].includes('running') || anyPluginActive || stockGroupJobActive(stockGroups.job?.state);

  const startOperation = (label: string) => {
    if (anyOperationActive || isOperationActive(operationState)) {
      setSelectionMessage('Finish or stop the active data operation first.');
      return;
    }
    setSelectionMessage('');
    setOpenMenu(null);
    setNestedOpen(false);
    setOperationLabel(label);
    setProgress(4);
    setOperationState('running');
    notify(`${label} queued as a simulation`);
  };

  const runDirectAction = (action: DirectDataSourceAction) => {
    if (action === 'update-all') {
      notify('Starting update for all datasets…');
      actionsClient
        .updateAll()
        .then(res => {
          const msg = `Update all completed: ${res.queued} dataset(s) processed.`;
          notify(msg);
          setLogEntries(c => [...c, `${new Date().toLocaleString()} ${msg}`]);
          loadDatabaseDatasets();
        })
        .catch(err => {
          notify(err?.message || 'Update all failed');
        });
      return;
    }
    if (action === 'update-selected') {
      const symbols = selectedDatasetIds.map(id => toolRows.find(r => r.id === id)?.symbol || id);
      notify(`Starting update for ${symbols.length} selected dataset(s)…`);
      actionsClient
        .updateSelected({ symbols })
        .then(res => {
          const msg = `Update selected completed: ${res.queued} dataset(s) processed.`;
          notify(msg);
          setLogEntries(c => [...c, `${new Date().toLocaleString()} ${msg}`]);
          loadDatabaseDatasets();
        })
        .catch(err => {
          notify(err?.message || 'Update selected failed');
        });
      return;
    }
    const labels: Record<DirectDataSourceAction, string> = {
      'sq-equity-update': 'Equity dataset update',
      'sq-futures-update': 'Futures dataset update',
      'update-all': 'All eligible dataset updates',
      'update-selected': `${selectedDatasetIds.length} selected dataset update${selectedDatasetIds.length === 1 ? '' : 's'}`,
    };
    startOperation(labels[action]);
  };

  const closeDialog = useCallback(() => {
    setDialog(null);
    setOpenMenu(null);
    setNestedOpen(false);
    if (lastControlId) window.setTimeout(() => document.querySelector<HTMLButtonElement>(`[data-control-id="${lastControlId}"]`)?.focus(), 0);
  }, [lastControlId]);

  const toggleDataset = (id: string) => setSelectedDatasetIds(current => current.includes(id) ? current.filter(item => item !== id) : [...current, id]);

  const dukasRanges = pluginStates['dukascopy']?.ranges ?? {};
  const backendDukascopy = pluginStates['dukascopy']?.backendAvailable === true;
  const toolRows: ToolTarget[] = [
    ...stockGroups.generated,
    ...(dbDatasets.length > 0
      ? dbDatasets.map(row => ({
          ...row,
          instrument: row.instrument || row.symbol,
          timezone: row.timezone || '—',
          category: row.category || '—',
          ...simulationSummary(row, dukasRanges[row.id] ?? []),
        }))
      : [
          ...definitions.filter(row => !(dbDatasetsLoaded || backendDukascopy) || row.source !== 'Dukascopy').map(row => ({ ...row, ...simulationSummary(row, dukasRanges[row.id] ?? []) })),
          ...fileDefinitions,
          ...Object.entries(pluginStates).flatMap(([id, state]) =>
            dbDatasetsLoaded && id === 'dukascopy' ? [] : state?.definitions ?? state?.records ?? []),
        ]),
  ].map(row => ({
    id: row.id,
    symbol: row.symbol,
    instrument: row.instrument || row.symbol,
    source: row.source,
    timeframe: row.timeframe,
    timezone: row.timezone || '—',
    from: row.from,
    to: row.to,
    bars: row.bars,
    category: row.category || '—',
    sourceDataId: 'sourceDataId' in row && typeof row.sourceDataId === 'string' ? row.sourceDataId : undefined,
  }));

  const selectCommand = (command: DataSourceCommand) => {
    if (['mt5-import', 'yahoo-add', 'yahoo-download', 'crypto-add', 'crypto-download', 'darwinex-add', 'darwinex-import', 'darwinex-download', 'sq-equity-find', 'sq-futures-find', 'tickdownloader-import', 'dukascopy-add', 'dukascopy-download', 'file-import', 'file-mass-import'].includes(command.dialog ?? '') && (isOperationActive(operationState) || anyOperationActive)) {
      setSelectionMessage('Finish or stop the active data operation first.');
      setOpenMenu(null);
      return;
    }

    const context = {
      selectedDatasetIds,
      setSelectionMessage,
      setDialog: (d: any) => { setOpenMenu(null); setNestedOpen(false); setDialog(d); },
      datasets: toolRows,
    };

    for (const plugin of plugins) {
      if (plugin.onSelectCommand?.(command, context)) {
        setOpenMenu(null);
        setNestedOpen(false);
        return;
      }
    }

    setOpenMenu(null);
    setNestedOpen(false);
    if (command.action) runDirectAction(command.action);
    if (command.dialog) setDialog({ id: command.dialog, exchange: command.exchange });
  };

  const contextNames = Object.freeze(
    (dbDatasets.length > 0
      ? dbDatasets
      : [
          ...definitions.filter(row => !backendDukascopy || row.source !== 'Dukascopy'),
          ...fileDefinitions,
          ...Object.values(pluginStates).flatMap(s => s?.definitions ?? s?.records ?? []),
        ]
    ).map(row => row.symbol)
  );
  const contextError = workspaceStorageError || instrumentStorageError || Object.values(pluginStates).map(s => s?.storageError).find(Boolean) || '';
  const commonContextActive = anyOperationActive || isOperationActive(operationState);
  const instrumentRows = effectiveInstruments(fileInstruments, instrumentOverrides, removedInstruments);
  const contextDocument = Object.freeze({
    existing: contextNames,
    error: contextError,
    active: commonContextActive,
    instruments: instrumentRows,
    brokers: brokerProfiles,
  });

  const exportRows: ExportTarget[] = toolRows;
  const instrumentBrokers: InstrumentBroker[] = [
    { id: '-1', name: 'Default', postfix: '', timezone: 'UTC' },
    ...brokerProfiles.filter(profile => profile.mtUse).map(profile => ({ id: profile.id, name: profile.name, postfix: profile.postfix, timezone: profile.timezone })),
  ];
  const sessionBrokers:SessionBroker[]=[{id:'-1',name:'Default',postfix:''},...brokerProfiles.filter(profile=>profile.mtUse).map(profile=>({id:profile.id,name:profile.name,postfix:profile.postfix}))];
  const sessionRows=effectiveSessions(customSessions,sessionOverrides,removedSessions);
  const selectedBrokers=brokerProfiles.filter(item=>selectedBrokerIds.includes(item.id));
  const requireBrokers = (): BrokerProfile[] | null => {
    if (selectedBrokers.length) {
      setSelectionMessage('');
      return selectedBrokers;
    }
    setSelectionMessage('You have to select some broker.');
    return null;
  };
  const openBrokerEdit = (profile: BrokerProfile) => {
    setSelectedBrokerIds([profile.id]);
    if (profile.system) {
      setSelectionMessage("This broker can't be edited.");
      return;
    }
    setBrokerDialog({ kind: 'editor', mode: 'edit', source: profile });
  };
  const updateBrokers = (items: BrokerProfile[]) => {
    try {
      if (anyDataActive) throw new Error('Finish or stop the active data operation first.');
      if (!items[0].stockPickerUse) throw new Error('This function is for stockpicking broker profile only.');
      useDataManagerStore.getState().startBrokerUpdate(items.map(row => row.id), toolRows.map(row => row.symbol));
      actionsClient.brokerDataUpdate().then(res => {
        const msg = `Broker profile update completed for ${res.updatedDatasets} dataset(s).`;
        setLogEntries(c => [...c, `${new Date().toLocaleString()} ${msg}`]);
        loadDatabaseDatasets();
      }).catch(() => {});
      setProgressOwner('broker');
      setOperationState('idle');
      setSelectionMessage('');
      notify('Data update started, please check Log tab for more information.');
    } catch (cause) {
      setSelectionMessage(cause instanceof Error ? cause.message : 'Unable to update broker data.');
    }
  };
  const selectedSessions=sessionRows.filter(item=>selectedSessionIds.includes(item.name));
  const requireSessions=():SessionDefinition[]|null=>{if(selectedSessions.length){setSelectionMessage('');return selectedSessions;}setSelectionMessage('You have to select some session.');return null;};
  const openSessionEdit=(item:SessionDefinition)=>{setSelectedSessionIds([item.name]);setSessionError('');setSessionDialog({kind:'editor',mode:'edit',source:item});};
  const openSessionDelete=(items:SessionDefinition[])=>{setSelectedSessionIds(items.map(item=>item.name));setSessionError('');setSessionDialog({kind:'delete',selected:items});};
  const removeSelectedSessions=()=>{if(sessionDialog?.kind!=='delete')return;try{const names=sessionDialog.selected.map(item=>item.name);useSessions.getState().remove(names,instruments.map(item=>item.session));setSelectedSessionIds(current=>current.filter(name=>!names.includes(name)));notify(`${names.length} session${names.length===1?'':'s'} removed.`);setSessionDialog(null);setSessionError('');}catch(cause){setSessionError(cause instanceof Error?cause.message:'Unable to remove sessions.');}};

  const indicatorDefinitions: ExternalIndicatorDefinition[] = pluginStates['indicators']?.definitions ?? [];
  const selectedExternal = indicatorDefinitions.filter(item => selectedExternalNames.includes(item.name));
  const requireExternal = (): ExternalIndicatorDefinition[] | null => { if (selectedExternal.length) { setSelectionMessage(''); return selectedExternal; } setSelectionMessage('You have to select at least one indicator.'); return null; };
  const openExternalEdit = (item: ExternalIndicatorDefinition) => { setSelectedExternalNames([item.name]); setSelectionMessage(''); setExternalDialog({ kind: 'editor', mode: 'edit', source: item }); };
  const openExternalDelete = (items: ExternalIndicatorDefinition[]) => { setSelectedExternalNames(items.map(item => item.name)); setSelectionMessage(''); setExternalDialog({ kind: 'delete', selected: items }); };

  const selectedStockGroups = stockGroups.groups.filter(item => selectedStockGroupIds.includes(item.id));
  const requireStockGroups = (): StockGroupDefinition[] | null => { if (selectedStockGroups.length) { setSelectionMessage(''); return selectedStockGroups; } setSelectionMessage('You have to select some group.'); return null; };
  const openStockGroupEdit = (group: StockGroupDefinition) => { setSelectedStockGroupIds([group.id]); if (group.system) { setSelectionMessage("This group can't be edited."); return; } setStockGroupDialog({ kind: 'editor', mode: 'edit', source: group }); };
  const updateStockGroups = (items: StockGroupDefinition[]) => { try { useStockGroups.getState().start(items.map(item => item.id), toolRows.map(row => row.symbol), anyDataActive); setProgressOwner('stock-groups'); setOperationState('idle'); setSelectionMessage(''); notify('Data update started, please check Log tab for more information.'); } catch (cause) { setSelectionMessage(cause instanceof Error ? cause.message : 'Unable to update stock group.'); } };
  const selectedInstruments = instrumentRows.filter(item => selectedInstrumentIds.includes(item.symbol));
  const requireInstruments = (): FileInstrument[] | null => {
    if (selectedInstruments.length) { setSelectionMessage(''); return selectedInstruments; }
    setSelectionMessage('You have to select some record.');
    return null;
  };
  const openInstrumentEdit = (item: FileInstrument) => {
    setSelectedInstrumentIds([item.symbol]); setInstrumentError('');
    setInstrumentDialog({ kind: 'editor', mode: 'edit', selected: [item] });
  };
  const openInstrumentDelete = (items: FileInstrument[]) => {
    setSelectedInstrumentIds(items.map(item => item.symbol)); setInstrumentError('');
    setInstrumentDialog({ kind: 'delete', selected: items });
  };
  const removeSelectedInstruments = () => {
    if (instrumentDialog?.kind !== 'delete') return;
    try {
      const names = instrumentDialog.selected.map(item => item.symbol);
      useFileSymbols.getState().removeInstruments(names, toolRows.map(row => row.instrument));
      setSelectedInstrumentIds(current => current.filter(name => !names.includes(name)));
      notify(`${names.length} instrument${names.length === 1 ? '' : 's'} removed.`);
      setInstrumentDialog(null); setInstrumentError('');
    } catch (cause) { setInstrumentError(cause instanceof Error ? cause.message : 'Unable to remove instruments.'); }
  };

  const otherProviderActive = isOperationActive(operationState) || anyOperationActive;
  const externalActive = otherProviderActive || isOperationActive(pluginStates['indicators']?.job?.state);
  const otherDataActive = externalActive || isOperationActive(pluginStates['export']?.job?.state);
  const anyDataActive = otherDataActive || isOperationActive(pluginStates['tools']?.job?.state);

  const openExport = (kind: ExportKind) => { try { if (anyDataActive) throw new Error('Finish or stop the active data operation first.'); const targets = selectExportTargets(exportRows, selectedDatasetIds, kind); setExportDialog({ kind, targets }); setSelectionMessage(''); } catch (cause) { setSelectionMessage(cause instanceof Error ? cause.message : 'Unable to select data for export.'); } };
  const openClone = () => { try { if (anyDataActive) throw new Error('Finish or stop the active data operation first.'); const targets = selectCloneTargets(toolRows, selectedDatasetIds); setCloneTargets(targets); setSelectionMessage(''); } catch (cause) { setSelectionMessage(cause instanceof Error ? cause.message : 'Unable to select data to clone.'); } };
  const openReview = () => { try { if (anyDataActive) throw new Error('Cannot view data while an operation is in progress.'); const target = selectReviewTarget(toolRows, selectedDatasetIds); setReviewTarget(target); setSelectionMessage(''); } catch (cause) { setSelectionMessage(cause instanceof Error ? cause.message : 'Unable to view data.'); } };

  let extraDetails = '';
  if ((progressOwner === 'external' || progressOwner === 'indicators') && pluginStates['indicators']?.job?.state === 'completed' && pluginStates['indicators']?.job?.ignored) {
    extraDetails = ` — ${pluginStates['indicators'].job.ignored} invalid rows ignored`;
  } else if (progressOwner === 'file' && pluginStates['file-import']?.job?.state === 'completed') {
    const fJob = pluginStates['file-import'].job;
    extraDetails = ` — ${fJob.completed} imported, ${fJob.skipped} skipped, ${(fJob.tasks ?? []).reduce((n: number, t: any) => n + (t.ignored ?? 0), 0)} invalid rows ignored`;
  }

  const progressText = selectionMessage || (
    operationState === 'idle'
      ? (providerJob
          ? `${getProviderJobLabel(progressOwner, pluginStates)} ${providerJob.state} ${providerJob.progress}%${providerJob.error ? `: ${providerJob.error}` : extraDetails}`
          : 'No active operations')
      : operationState === 'paused'
        ? `${operationLabel} paused at ${progress}%`
        : operationState === 'cancelled'
          ? `${operationLabel} cancelled`
          : operationState === 'completed'
            ? `${operationLabel} complete`
            : `${operationLabel}… ${progress}%`
  );

  return <div className={`data-manager ${tab === 'Log' ? 'show-log' : ''}`}><div className="dm-title">Data Manager</div><div className="ribbon-tabs">{tabs.map(item => <button key={item} className={tab === item ? 'active' : ''} onClick={() => setTab(item)}>{item}</button>)}</div><div className="ribbon" ref={ribbonRef}>
    {tab === 'Data sources' && <div className="data-source-ribbon" aria-label="Data source operations"><div className="provider-actions">{dataSourceProviders.map(provider => <ProviderMenu key={provider.id} provider={provider} isOpen={openMenu === provider.id} nestedOpen={nestedOpen && openMenu === provider.id} onToggle={() => { setOpenMenu(current => current === provider.id ? null : provider.id); setNestedOpen(false); }} onToggleNested={() => setNestedOpen(current => !current)} onSelect={command => { setLastControlId(provider.id); selectCommand(command); }}/>)}</div><div className="context-actions">{dataSourceContextActions.map(action => { const Icon = contextIcons[action.id] ?? Database; return <button className={`data-source-button ${action.id === 'mass-delete' ? 'destructive' : ''}`} data-control-id={action.id} key={action.id} title={action.label} onClick={() => { setLastControlId(action.id); if (action.requiresSelection && selectedDatasetIds.length === 0) { setSelectionMessage('Select at least one dataset first'); return; } if (action.action) runDirectAction(action.action); if (action.dialog) setDialog({ id: action.dialog }); }}><Icon size={27}/><span>{action.label}</span></button>; })}</div></div>}
    {tab === 'Export' && <div className="export-actions" aria-label="Data export operations"><Button data-control-id="export-csv" className="export-csv" onClick={() => { setLastControlId('export-csv'); openExport('csv'); }}><FileSpreadsheet size={24} aria-hidden="true"/>Export to CSV</Button><Button data-control-id="export-mt4" className="export-mt4" title="Export to MetaTrader 4 (FXT & HST)" onClick={() => { setLastControlId('export-mt4'); openExport('mt4'); }}><MonitorDown size={24} aria-hidden="true"/>Export MT4 (FXT &amp; HST)</Button><Button data-control-id="export-mt5" className="export-mt5" title="Export to MetaTrader 5 data (99% test)" onClick={() => { setLastControlId('export-mt5'); openExport('mt5'); }}><ChartCandlestick size={24} aria-hidden="true"/>Export to MT5 data (99% test)</Button></div>}
    {tab === 'Tools' && <div className="data-tool-actions" aria-label="Data tools"><Button data-control-id="tool-timezone" className="tool-timezone" onClick={() => { setLastControlId('tool-timezone'); openClone(); }}><span className="timezone-tool-icon" aria-hidden="true"><Globe2 size={26}/><Clock size={13}/></span>Clone to timezone</Button><Button data-control-id="tool-analyze" className="tool-analyze" onClick={() => { setLastControlId('tool-analyze'); openReview(); }}><ChartCandlestick size={26} aria-hidden="true"/>View &amp; Analyze</Button></div>}
    {tab === 'Instruments' && <div className="management-actions" aria-label="Instrument operations">
      <Button className="action-add" onClick={() => { setInstrumentError(''); setInstrumentDialog({ kind: 'editor', mode: 'add', selected: [] }); }}><CirclePlus size={26} aria-hidden="true"/>Add Instrument</Button>
      <Button className="action-clone" onClick={() => { const rows = requireInstruments(); if (rows) setInstrumentDialog({ kind: 'clone', source: rows[0] }); }}><CopyPlus size={26} aria-hidden="true"/>Clone Instrument</Button>
      <Button className="action-edit" onClick={() => { const rows = requireInstruments(); if (rows) setInstrumentDialog({ kind: 'editor', mode: rows.length === 1 ? 'edit' : 'mass', selected: rows }); }}><Settings2 size={26} aria-hidden="true"/>Mass Edit Instrument</Button>
      <Button className="action-delete" onClick={() => { const rows = requireInstruments(); if (rows) openInstrumentDelete(rows); }}><Trash2 size={26} aria-hidden="true"/>Mass Delete</Button>
      <Button className="action-save" onClick={() => { const rows = requireInstruments(); if (rows) setInstrumentDialog({ kind: 'transfer', mode: 'save', selected: rows }); }}><Save size={26} aria-hidden="true"/>Save</Button>
      <Button className="action-load" onClick={() => setInstrumentDialog({ kind: 'transfer', mode: 'load', selected: [] })}><FolderOpen size={26} aria-hidden="true"/>Load</Button>
    </div>}
    {tab === 'Sessions' && <div className="management-actions" aria-label="Session operations">
      <Button className="action-add" onClick={()=>{setSessionError('');setSessionDialog({kind:'editor',mode:'add'});}}><CalendarPlus size={26} aria-hidden="true"/>Add Session</Button>
      <Button className="action-clone" onClick={()=>{const rows=requireSessions();if(rows)setSessionDialog({kind:'clone',source:rows[0]});}}><CopyPlus size={26} aria-hidden="true"/>Clone Session</Button>
      <Button className="action-delete" onClick={()=>{const rows=requireSessions();if(rows)openSessionDelete(rows);}}><Trash2 size={26} aria-hidden="true"/>Mass Delete</Button>
      <Button className="action-save" onClick={()=>{const rows=requireSessions();if(rows)setSessionDialog({kind:'transfer',mode:'save',selected:rows});}}><Save size={26} aria-hidden="true"/>Save</Button>
      <Button className="action-load" onClick={()=>setSessionDialog({kind:'transfer',mode:'load',selected:[]})}><FolderOpen size={26} aria-hidden="true"/>Load</Button>
    </div>}
    {tab === 'External indicators' && <div className="management-actions" aria-label="External indicator operations">
      <Button className="action-add" onClick={() => setExternalDialog({ kind: 'editor', mode: 'add' })}><CirclePlus size={26} aria-hidden="true"/>Add new</Button>
      <Button className="action-clone" onClick={() => { const rows = requireExternal(); if (rows) setExternalDialog({ kind: 'import', source: rows[0] }); }}><FileInput size={26} aria-hidden="true"/>Import indicator data</Button>
      <Button className="action-edit" onClick={() => setExternalDialog({ kind: 'recognize' })}><FileSearch size={26} aria-hidden="true"/>Recognize from file</Button>
      <Button className="action-edit" onClick={() => { const rows = requireExternal(); if (!rows) return; if (!rows[0].records.length) { setSelectionMessage(`Custom indicator '${rows[0].name}' doesn't contain any data`); return; } setExternalDialog({ kind: 'view', source: rows[0] }); }}><ChartCandlestick size={26} aria-hidden="true"/>View &amp; Analyze</Button>
      <Button className="action-delete" onClick={() => { const rows = requireExternal(); if (rows) openExternalDelete(rows); }}><Trash2 size={26} aria-hidden="true"/>Mass delete</Button>
      <Button className="action-save" onClick={() => { const rows = requireExternal(); if (rows) setExternalDialog({ kind: 'transfer', mode: 'save', selected: rows }); }}><Save size={26} aria-hidden="true"/>Save</Button>
      <Button className="action-load" onClick={() => setExternalDialog({ kind: 'transfer', mode: 'load', selected: [] })}><FolderOpen size={26} aria-hidden="true"/>Load</Button>
    </div>}
    {tab === 'Stock groups' && <div className="management-actions" aria-label="Stock group operations">
      <Button className="action-add" onClick={() => setStockGroupDialog({ kind:'editor', mode:'add' })}><CirclePlus size={26} aria-hidden="true"/>Add new</Button>
      <Button className="action-clone" onClick={() => { const rows=requireStockGroups(); if(rows) updateStockGroups(rows); }}><RefreshCw size={26} aria-hidden="true"/>Update data in group (automatic)</Button>
      <Button className="action-edit" onClick={() => { const rows=requireStockGroups(); if(!rows)return; if(rows[0].system){setSelectionMessage("This group can't be edited.");return;} setStockGroupDialog({kind:'stocks',source:rows[0]}); }}><ListPlus size={26} aria-hidden="true"/>Edit stocks</Button>
      <Button className="action-delete" onClick={() => { const rows=requireStockGroups(); if(rows){const deletable=rows.filter(row=>!row.system);if(!deletable.length){setSelectionMessage('You have to select some non default group.');return;}setStockGroupDialog({kind:'delete',selected:deletable});} }}><Trash2 size={26} aria-hidden="true"/>Mass delete</Button>
      <Button className="action-save" onClick={() => { const rows=requireStockGroups(); if(rows){downloadTextFile('Groups.json',serializeStockGroupsJson(rows));notify('Groups saved.');} }}><Save size={26} aria-hidden="true"/>Save</Button>
      <Button className="action-load" onClick={() => setStockGroupDialog({kind:'load'})}><FolderOpen size={26} aria-hidden="true"/>Load</Button>
    </div>}
    {tab === 'Broker profiles' && <div className="management-actions broker-actions" aria-label="Broker profile operations">
      <Button className="action-add" onClick={()=>setBrokerDialog({kind:'editor',mode:'add'})}><CirclePlus size={26} aria-hidden="true"/>Add new</Button>
      <Button className="action-clone" onClick={()=>{const rows=requireBrokers();if(rows)updateBrokers(rows);}}><RefreshCw size={26} aria-hidden="true"/>Update data for broker (automatic)</Button>
      <Button className="action-edit" onClick={()=>setBrokerDialog({kind:'import',recordType:'instrument'})}><FileInput size={26} aria-hidden="true"/>Import broker instruments from JSON</Button>
      <Button className="action-load" onClick={()=>setBrokerDialog({kind:'import',recordType:'session'})}><CalendarPlus size={26} aria-hidden="true"/>Import broker sessions from JSON</Button>
      <Button className="action-edit" onClick={()=>{const rows=requireBrokers();if(!rows)return;const row=rows[0];if(!row.stockPickerUse){setSelectionMessage("This broker profile can't hold any stocks.");return;}if(row.system){setSelectionMessage("This broker can't be edited.");return;}setBrokerDialog({kind:'stocks',source:row});}}><ListPlus size={26} aria-hidden="true"/>Edit stocks</Button>
      <Button className="action-delete" onClick={()=>{const rows=requireBrokers();if(!rows)return;if(rows.some(row=>instrumentRows.some(item=>item.broker===row.id)||sessionRows.some(item=>item.broker===row.id))){setSelectionMessage('You have to select broker which is not used by any instrument or session.');return;}const deletable=rows.filter(row=>!row.system);if(!deletable.length){setSelectionMessage('You have to select some non default broker.');return;}setBrokerDialog({kind:'delete',selected:deletable});}}><Trash2 size={26} aria-hidden="true"/>Mass delete</Button>
      <Button className="action-save" onClick={()=>{const rows=requireBrokers();if(rows){downloadTextFile('Brokers.json',serializeBrokersJson(rows));notify('Brokers saved.');}}}><Save size={26} aria-hidden="true"/>Save</Button>
      <Button className="action-load" onClick={()=>setBrokerDialog({kind:'load'})}><FolderOpen size={26} aria-hidden="true"/>Load</Button>
    </div>}
  </div><div className="dm-progress" role="status" aria-label="Data Manager progress"><strong>Progress</strong><ProgressBar value={operationState === 'idle' && providerJob ? providerJob.progress : progress} label={progressText}/><Button disabled={providerJob?.canPause === false || (operationState !== 'running' && operationState !== 'paused' && !['running', 'paused'].includes(providerJob?.state ?? ''))} onClick={() => { setSelectionMessage(''); if (['running', 'paused'].includes(providerJob?.state ?? '')) providerAction(providerJob?.state === 'paused' ? 'resume' : 'pause'); else setOperationState(current => current === 'paused' ? 'running' : 'paused'); }}>{operationState === 'paused' || providerJob?.state === 'paused' ? 'Resume all' : 'Pause all'}</Button><Button disabled={operationState !== 'running' && operationState !== 'paused' && !['running', 'paused'].includes(providerJob?.state ?? '')} onClick={() => { setSelectionMessage(''); if (providerJob && ['running', 'paused'].includes(providerJob.state)) { providerAction('stop'); return; } setOperationState('cancelled'); notify(`${operationLabel} cancelled`); }}>Stop all</Button></div>
  <div className="dm-body">{tab === 'Log' ? <main className="dm-log"><header><strong>Log</strong><button className="clear-log" onClick={() => setLogEntries([])}>Clear log</button></header><div className="dm-log-output" role="log" aria-label="Data Manager log">{logEntries.map((entry, index) => <div key={index}>{entry}</div>)}</div></main> : ['Data sources', 'Export', 'Tools'].includes(tab) ? <DatasetTable selectedIds={selectedDatasetIds} onToggle={toggleDataset} onSelect={setSelectedDatasetIds} pluginStates={pluginStates} dbDatasets={dbDatasets} dbDatasetsLoaded={dbDatasetsLoaded}/> : tab === 'Broker profiles' ? <BrokerProfilesTable profiles={brokerProfiles} selected={selectedBrokerIds} instruments={instrumentRows} sessions={sessionRows} onSelect={setSelectedBrokerIds} onEdit={openBrokerEdit}/> : tab === 'Stock groups' ? <StockGroupsTable groups={stockGroups.groups} selected={selectedStockGroupIds} datasets={toolRows} onSelect={setSelectedStockGroupIds} onEdit={openStockGroupEdit} onUpdate={group=>updateStockGroups([group])}/> : tab === 'External indicators' ? <ExternalIndicatorsTable rows={indicatorDefinitions} selected={selectedExternalNames} job={pluginStates['indicators']?.job} onSelect={setSelectedExternalNames} onEdit={openExternalEdit} onDelete={item => openExternalDelete([item])}/> : tab === 'Instruments' ? <InstrumentTable selected={selectedInstrumentIds} onSelect={setSelectedInstrumentIds} onEdit={openInstrumentEdit} onDelete={item => openInstrumentDelete([item])}/> : tab === 'Sessions' ? <SessionTable rows={sessionRows} selected={selectedSessionIds} onSelect={setSelectedSessionIds} onEdit={openSessionEdit} onDelete={item=>openSessionDelete([item])} brokers={sessionBrokers}/> : <div className="dm-config"><Section title={tab}><div className="cards-list">{Array.from({ length: 6 }, (_, index) => <button key={index}><Database size={22}/><strong>{tab.replace(/s$/, '')} {index + 1}</strong><span>{index % 2 ? 'Configured · mock adapter' : 'Ready for configuration'}</span></button>)}</div></Section></div>}</div>

  {plugins.map(p => (
    <p.Sync key={p.pluginId} onSync={handlePluginSync} />
  ))}

  {plugins.map(p => (
    <p.Dialogs
      key={p.pluginId}
      dialog={dialog}
      exportDialog={exportDialog}
      cloneTargets={cloneTargets}
      reviewTarget={reviewTarget}
      externalDialog={externalDialog}
      contextDocument={contextDocument}
      selectedDatasetIds={selectedDatasetIds}
      toolRows={toolRows}
      externalActive={externalActive}
      otherDataActive={otherDataActive}
      otherProviderActive={otherProviderActive}
      onClose={closeDialog}
      onCloneClose={() => setCloneTargets(null)}
      onReviewClose={() => setReviewTarget(null)}
      onStarted={(owner: string, msg?: string) => {
        setProgressOwner(owner);
        setOperationState('idle');
        setSelectionMessage('');
        if (msg) notify(msg);
        closeDialog();
      }}
      onComplete={(msg: string) => {
        notify(msg);
        closeDialog();
      }}
      onNotify={(msg: string) => notify(msg)}
      onSaved={() => setSelectedExternalNames([])}
      onAddData={(req: any) => useDataManagerStore.getState().addData(req, [...contextNames])}
    />
  ))}

  {dialog?.id === 'file-add' && <FileSymbolDialog onClose={closeDialog} onSaved={() => notify('File symbol added')}/>}
  {instrumentDialog?.kind === 'editor' && (
    <InstrumentEditorDialog mode={instrumentDialog.mode} selected={instrumentDialog.selected} brokers={instrumentBrokers} onClose={() => setInstrumentDialog(null)} onSaved={message => notify(message)}/>
  )}
  {instrumentDialog?.kind === 'clone' && (
    <CloneInstrumentDialog source={instrumentDialog.source} brokers={instrumentBrokers} onClose={() => setInstrumentDialog(null)} onSaved={message => notify(message)}/>
  )}
  {instrumentDialog?.kind === 'transfer' && (
    <InstrumentTransferDialog mode={instrumentDialog.mode} selected={instrumentDialog.selected} all={instrumentRows} brokers={instrumentBrokers} onClose={() => setInstrumentDialog(null)} onSaved={message => notify(message)}/>
  )}
  {instrumentDialog?.kind === 'delete' && <div className="instruments-flow"><Modal title={instrumentDialog.selected.length === 1 ? 'Remove instrument' : 'Remove instruments'} width={520} onClose={() => { setInstrumentDialog(null); setInstrumentError(''); }} footer={<><Button onClick={() => { setInstrumentDialog(null); setInstrumentError(''); }}>No</Button><Button className="primary" onClick={removeSelectedInstruments}>Yes</Button></>}>
    {instrumentError && <p role="alert" className="instrument-error">{instrumentError}</p>}
    <p>{instrumentDialog.selected.length === 1 ? `Do you really want to delete instrument '${instrumentDialog.selected[0].symbol}'?` : `Do you really want to delete ${instrumentDialog.selected.length} selected instruments?`}</p>
  </Modal></div>}
  {sessionDialog?.kind==='editor'&&<SessionTemplateDialog mode={sessionDialog.mode} source={sessionDialog.source} brokers={sessionBrokers} onClose={()=>setSessionDialog(null)} onSaved={message=>notify(message)}/>}
  {sessionDialog?.kind==='clone'&&<CloneSessionDialog source={sessionDialog.source} brokers={sessionBrokers} onClose={()=>setSessionDialog(null)} onSaved={message=>notify(message)}/>}
  {sessionDialog?.kind==='transfer'&&<SessionTransferDialog mode={sessionDialog.mode} selected={sessionDialog.selected} all={sessionRows} brokers={sessionBrokers} onClose={()=>setSessionDialog(null)} onSaved={message=>notify(message)}/>}
  {sessionDialog?.kind==='delete'&&<div className="sessions-flow"><Modal title="Removing sessions" width={520} onClose={()=>{setSessionDialog(null);setSessionError('');}} footer={<><Button onClick={()=>{setSessionDialog(null);setSessionError('');}}>No</Button><Button className="primary" onClick={removeSelectedSessions}>Yes</Button></>}>{sessionError&&<p role="alert" className="session-error">{sessionError}</p>}<p>Are you sure you want to remove selected sessions ({sessionDialog.selected.length})?</p></Modal></div>}
  {stockGroupDialog?.kind === 'editor' && <StockGroupEditorDialog mode={stockGroupDialog.mode} source={stockGroupDialog.source} onClose={() => setStockGroupDialog(null)} onSaved={(message,item) => { setSelectedStockGroupIds([item.id]); notify(message); }}/>}
  {stockGroupDialog?.kind === 'stocks' && <StockGroupStocksDialog group={stockGroupDialog.source} onClose={() => setStockGroupDialog(null)} onSaved={message => notify(message)}/>}
  {stockGroupDialog?.kind === 'load' && <StockGroupTransferDialog onClose={() => setStockGroupDialog(null)} onSaved={message => notify(message)}/>}
  {stockGroupDialog?.kind === 'delete' && <div className="stock-groups-flow"><Modal title={stockGroupDialog.selected.length === 1 ? 'Remove group' : 'Remove groups'} width={520} onClose={() => { setStockGroupDialog(null); setStockGroupError(''); }} footer={<><Button onClick={() => { setStockGroupDialog(null); setStockGroupError(''); }}>No</Button><Button className="primary" onClick={() => { try { const ids=stockGroupDialog.selected.map(item=>item.id);useStockGroups.getState().remove(ids);setSelectedStockGroupIds(current=>current.filter(id=>!ids.includes(id)));notify(ids.length===1?'Group removed':'Groups removed');setStockGroupDialog(null);setStockGroupError(''); } catch(cause){setStockGroupError(cause instanceof Error?cause.message:'Unable to remove groups.');} }}>Yes</Button></>}>{stockGroupError&&<p role="alert" className="stock-group-error">{stockGroupError}</p>}<p>Are you sure you want to remove selected groups ({stockGroupDialog.selected.length})?</p></Modal></div>}
  {brokerDialog?.kind==='editor'&&<BrokerProfileEditorDialog mode={brokerDialog.mode} source={brokerDialog.source} canSetStockPicker={!brokerDialog.source?.stocks.length} canSetMt={!brokerDialog.source||(!instrumentRows.some(row=>row.broker===brokerDialog.source!.id)&&!sessionRows.some(row=>row.broker===brokerDialog.source!.id))} canSetTimezone={!brokerDialog.source||(!definitions.some(row=>row.broker===brokerDialog.source!.id)&&!fileDefinitions.some(row=>row.broker===brokerDialog.source!.id))} onClose={()=>setBrokerDialog(null)} onSaved={message=>notify(message)}/>}
  {brokerDialog?.kind==='stocks'&&<BrokerStocksDialog profile={brokerDialog.source} onClose={()=>setBrokerDialog(null)} onSaved={message=>notify(message)}/>}
  {brokerDialog?.kind==='import'&&<BrokerRecordImportDialog kind={brokerDialog.recordType} brokers={brokerProfiles} onClose={()=>setBrokerDialog(null)} onSaved={message=>notify(message)}/>}
  {brokerDialog?.kind==='load'&&<BrokerTransferDialog onClose={()=>setBrokerDialog(null)} onSaved={message=>notify(message)}/>}
  {exportDialog?.kind === 'csv' && (
    <CsvExportDialog
      targets={exportDialog.targets}
      onClose={() => setExportDialog(null)}
      onComplete={msg => {
        notify(msg);
        setLogEntries(c => [...c, `${new Date().toLocaleString()} ${msg}`]);
      }}
    />
  )}
  {exportDialog?.kind === 'mt4' && (
    <Mt4ExportDialog
      target={exportDialog.targets[0]}
      onClose={() => setExportDialog(null)}
      onComplete={msg => {
        notify(msg);
        setLogEntries(c => [...c, `${new Date().toLocaleString()} ${msg}`]);
      }}
    />
  )}
  {exportDialog?.kind === 'mt5' && (
    <Mt5ExportDialog
      target={exportDialog.targets[0]}
      onClose={() => setExportDialog(null)}
      onComplete={msg => {
        notify(msg);
        setLogEntries(c => [...c, `${new Date().toLocaleString()} ${msg}`]);
      }}
    />
  )}
  {cloneTargets && (
    <CloneTimezoneDialog
      targets={cloneTargets}
      onClose={() => setCloneTargets(null)}
      onComplete={msg => {
        notify(msg);
        setLogEntries(c => [...c, `${new Date().toLocaleString()} ${msg}`]);
        loadDatabaseDatasets();
      }}
    />
  )}
  {reviewTarget && (
    <ViewAnalyzeDialog
      target={reviewTarget}
      onClose={() => setReviewTarget(null)}
    />
  )}
  {dialog?.id === 'mass-delete' && (
    <MassDeleteDialog
      selectedSymbols={selectedDatasetIds.map(id => toolRows.find(r => r.id === id)?.symbol || id)}
      onClose={closeDialog}
      onComplete={msg => {
        notify(msg);
        setLogEntries(c => [...c, `${new Date().toLocaleString()} ${msg}`]);
        setSelectedDatasetIds([]);
        loadDatabaseDatasets();
      }}
    />
  )}
  {dialog?.id === 'save-definitions' && (
    <SaveDefinitionsDialog
      selectedSymbols={selectedDatasetIds.map(id => toolRows.find(r => r.id === id)?.symbol || id)}
      onClose={closeDialog}
      onComplete={msg => {
        notify(msg);
        setLogEntries(c => [...c, `${new Date().toLocaleString()} ${msg}`]);
        loadDatabaseDatasets();
      }}
    />
  )}
  {dialog?.id === 'load-definitions' && (
    <LoadDefinitionsDialog
      onClose={closeDialog}
      onComplete={msg => {
        notify(msg);
        setLogEntries(c => [...c, `${new Date().toLocaleString()} ${msg}`]);
        loadDatabaseDatasets();
      }}
    />
  )}
  {dialog && !['mt5-import', 'yahoo-add', 'yahoo-download', 'crypto-add', 'crypto-download', 'darwinex-add', 'darwinex-import', 'darwinex-download', 'mass-delete', 'save-definitions', 'load-definitions'].includes(dialog.id) && dialog.id !== 'sq-equity-find' && dialog.id !== 'sq-futures-find' && dialog.id !== 'file-import' && dialog.id !== 'file-mass-import' && dialog.id !== 'file-add' && dialog.id !== 'tickdownloader-import' && dialog.id !== 'dukascopy-add' && dialog.id !== 'dukascopy-download' && dialog.id !== 'dukascopy-information' && <DataSourceDialog state={dialog} selectedCount={selectedDatasetIds.length} onClose={closeDialog} onSecondary={id => setDialog({ id })} onComplete={message => { notify(message); closeDialog(); }}/>}</div>;
}
