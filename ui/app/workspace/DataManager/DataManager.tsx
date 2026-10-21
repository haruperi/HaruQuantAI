import { useHostConnection } from '../../host/HostConnection';
import { DataManagerDock, type WorkspaceArrangeRequest, type WorkspaceArrangement } from './DataManagerDock';
import { DataManagerChart } from './DataManagerChart';
import { fetchWorkspace, openWorkspaceTab, type WorkspaceLayout, type WorkspaceSnapshot, type WorkspaceTabId } from './dataManagerWorkspaceClient';
import { BrokerProfilesTable, StockGroupsTable, ExternalIndicatorsTable, SessionTable, InstrumentTable, DatasetTable, getBrokerDisplayName } from './DataManagerPanels';
import { AddPopup as DarwinexAddDialog } from '../../plugins/data_source/Darwinex/add/module';
import { ImportPopup as DarwinexImportDialog } from '../../plugins/data_source/Darwinex/import/module';
import { DownloadPopup as DarwinexDownloadDialog } from '../../plugins/data_source/Darwinex/download/module';
import { useDarwinex, darwinexActive } from '../../plugins/data_source/Darwinex/darwinexStore';
import { darwinexTargets, type DarwinexDefinition } from '../../plugins/data_source/Darwinex/darwinex';
import { AddPopup as CryptoAddDialog } from '../../plugins/data_source/Crypto/add/module';
import { ImportPopup as CryptoDownloadDialog } from '../../plugins/data_source/Crypto/import/module';
import { cryptoActive, useCrypto } from '../../plugins/data_source/Crypto/cryptoStore';
import { cryptoTargets, type CryptoDefinition, type CryptoExchangeId } from '../../plugins/data_source/Crypto/crypto';
import { YahooAddDialog } from '../../plugins/data_source/Yahoo/add/module';
import { YahooDownloadDialog } from '../../plugins/data_source/Yahoo/download/module';
import { useYahoo, yahooActive } from '../../plugins/data_source/Yahoo/yahooStore';
import { yahooTargets, type YahooDefinition } from '../../plugins/data_source/Yahoo/yahoo';
import { ImportPopup as Mt5ImportDialog } from '../../plugins/data_source/MetaTrader/import/module';
import { mt5Active, useMt5Import } from '../../plugins/data_source/MetaTrader/mt5ImportStore';
import { mt5Summary } from '../../plugins/data_source/MetaTrader/mt5Import';
import { SQEquityAddPopup, runEquityUpdate } from '../../plugins/data_source/SQData/Equity/module';
import { SQFuturesAddPopup, runFuturesUpdate } from '../../plugins/data_source/SQData/Futures/module';
import { sqActive, useSQData } from '../../plugins/data_source/SQData/sqDataStore';
import { providerLabel } from '../../plugins/data_source/SQData/sqData';
import { ImportPopup as FileImportDialog } from '../../plugins/data_source/FileImport/import/module';
import { MassImportPopup as FileMassImportDialog } from '../../plugins/data_source/FileImport/massImport/module';
import { activeImport, useFileImports } from '../../plugins/data_source/FileImport/fileImportStore';
import { emptyFileRecord } from '../../plugins/data_source/FileImport/fileImport';
import { seedInstruments, type FileDefinition, type InstrumentBroker } from '../../plugins/data_source/FileImport/fileSymbols';
import { AddPopup as FileSymbolDialog } from '../../plugins/data_source/FileImport/add/module';
import { useFileSymbols } from '../../plugins/data_source/FileImport/fileSymbolsStore';
import { useInstruments } from '../../plugins/data_source/Catalogs/Instruments/instrumentsStore';
import { InstrumentsModal } from '../../plugins/data_source/Catalogs/Instruments/InstrumentsModal';
import type { CatalogInstrument } from '../../plugins/data_source/Catalogs/Instruments/instrumentsApiClient';
import { InstrumentTransferDialog } from '../../plugins/data_source/Catalogs/Instruments/InstrumentTransferDialog';
import { SessionTemplateDialog } from '../../plugins/data_source/Catalogs/Sessions/SessionTemplateDialog';
import { CloneSessionDialog } from '../../plugins/data_source/Catalogs/Sessions/CloneSessionDialog';
import { SessionTransferDialog } from '../../plugins/data_source/Catalogs/Sessions/SessionTransferDialog';
import { SessionNtImportDialog } from '../../plugins/data_source/Catalogs/Sessions/SessionNtImportDialog';
import { effectiveSessions, type SessionBroker, type SessionDefinition } from '../../plugins/data_source/Catalogs/Sessions/sessions';
import { useSessions } from '../../plugins/data_source/Catalogs/Sessions/sessionStore';
import { ExternalIndicatorEditorDialog } from '../../plugins/data_source/Indicators/ExternalIndicatorEditorDialog';
import { ExternalIndicatorImportDialog } from '../../plugins/data_source/Indicators/ExternalIndicatorImportDialog';
import { ExternalIndicatorRecognizeDialog } from '../../plugins/data_source/Indicators/ExternalIndicatorRecognizeDialog';
import { ExternalIndicatorViewDialog } from '../../plugins/data_source/Indicators/ExternalIndicatorViewDialog';
import { ExternalIndicatorDeleteDialog } from '../../plugins/data_source/Indicators/ExternalIndicatorDeleteDialog';
import { ExternalIndicatorTransferDialog } from '../../plugins/data_source/Indicators/ExternalIndicatorTransferDialog';
import { activeExternalLines, externalIndicatorTypes, externalTypeLabel, type ExternalIndicatorDefinition } from '../../plugins/data_source/Indicators/externalIndicators';
import { externalJobActive, useExternalIndicators } from '../../plugins/data_source/Indicators/externalIndicatorsStore';
import { StockGroupEditorDialog } from '../../plugins/data_source/Catalogs/StockGroups/StockGroupEditorDialog';
import { StockGroupStocksDialog } from '../../plugins/data_source/Catalogs/StockGroups/StockGroupStocksDialog';
import { StockGroupTransferDialog } from '../../plugins/data_source/Catalogs/StockGroups/StockGroupTransferDialog';
import { serializeStockGroupsJson, serializeStockGroupsXml, summarizeGroup, type StockGroupDefinition } from '../../plugins/data_source/Catalogs/StockGroups/stockGroups';
import { stockGroupJobActive, useStockGroups } from '../../plugins/data_source/Catalogs/StockGroups/stockGroupsStore';
import { BrokerProfileEditorDialog } from '../../plugins/data_source/Catalogs/BrokerProfiles/BrokerProfileEditorDialog';
import { BrokerStocksDialog } from '../../plugins/data_source/Catalogs/BrokerProfiles/BrokerStocksDialog';
import { BrokerRecordImportDialog } from '../../plugins/data_source/Catalogs/BrokerProfiles/BrokerRecordImportDialog';
import { BrokerTransferDialog } from '../../plugins/data_source/Catalogs/BrokerProfiles/BrokerTransferDialog';
import { brokerCounts, serializeBrokersJson, type BrokerProfile } from '../../plugins/data_source/Catalogs/BrokerProfiles/brokerProfiles';
import { fetchBrokerStocks } from '../../plugins/data_source/Catalogs/BrokerProfiles/brokerApiClient';
import { TickDownloaderImportDialog } from '../../plugins/data_source/TickDownloader/module';
import { ImportPopup } from '../../plugins/data_source/Dukascopy/import/module';
import { DisclaimerPopup } from '../../plugins/data_source/Dukascopy/disclaimer/module';
import { eligibleTargets, simulationSummary, type DownloadTarget } from '../../plugins/data_source/Dukascopy/dukascopyDownload';
import { AddPopup } from '../../plugins/data_source/Dukascopy/add/module';
import {
  normalizeRelativePath,
  useDataManagerStore,
  useDukascopyDownloads,
  useTickDownloader,
} from '../../plugins/data_source/Common/dataManagerStore';
import { CsvExportDialog } from '../../plugins/data_source/Export/CsvExportDialog';
import { Mt4ExportDialog } from '../../plugins/data_source/Export/Mt4ExportDialog';
import { Mt5ExportDialog } from '../../plugins/data_source/Export/Mt5ExportDialog';
import { downloadExportArtifacts, selectExportTargets, type ExportKind, type ExportTarget } from '../../plugins/data_source/Export/dataExport';
import { exportActive, useDataExports } from '../../plugins/data_source/Export/dataExportStore';
import { CloneTimezoneDialog } from '../../plugins/data_source/Tools/CloneTimezoneDialog';
import { ViewAnalyzeDialog } from '../../plugins/data_source/Tools/ViewAnalyzeDialog';
import { selectCloneTargets, selectReviewTarget, type ToolTarget } from '../../plugins/data_source/Tools/dataTools';
import { toolsActive, useDataTools } from '../../plugins/data_source/Tools/dataToolsStore';
import { cancelLogOperation, clearLogs, fetchLogs, formatDataLogLine, isErrorLogRecord, subscribeDataLogStream } from './dataManagerLogClient';
import { useCallback, useEffect, useRef, useState, type ComponentType } from 'react';
import {
  Bitcoin, ChartCandlestick, ChevronDown, ChevronRight, CircleDollarSign,
  CirclePlus, Clock, Cloud, CloudDownload, Coins, Database, DollarSign, Download,
  FileInput, FileUp, Files, FileSpreadsheet, FolderInput, FolderOpen, Landmark, ListPlus,
  MonitorDown, Network, Plus, RefreshCw, Save, Search, Server,
  Settings2, Trash2, Globe2, Info, CopyPlus, CalendarPlus, FileSearch,
} from 'lucide-react';

import { useAppStore } from '../../host/store';
import { createDomainClient } from '../../host/transport';
import { HelpTooltip, type HelpGuidePayload, type HelpTutorialItem } from '../../components/HelpTooltip';
import { Button, Checkbox, Field, Modal, ProgressBar, Section, Select, TextInput } from '../../components/ui';
import { DataManagerHome } from './DataManagerHome';
import {
  dataSourceContextActions, dataSourceProviders, type DataSourceCommand,
  type DataSourceCommandIcon, type DataSourceDialogId, type DataSourceProvider,
  type DirectDataSourceAction,
} from '../../plugins/data_source/Common/dataSourceRibbon';
import yahooIconUrl from '../../assets/dm-yahoo.png';
import mt5IconUrl from '../../assets/metatrader5.png';

export const helpTopicForTab: Record<string, string> = { Home: 'overview', 'Data sources': 'data', Export: 'export', Tools: 'data', Instruments: 'instruments', Sessions: 'sessions', 'External indicators': 'custom-data', 'Stock groups': 'stock-groups', 'Broker profiles': 'brokers', Log: 'log', Chart: 'chart' };
export const DEFAULT_DM_TUTORIALS: HelpTutorialItem[] = [
  { id: 'tick-precision-testing', test_id: 'dm-help-openlink-btn', title: 'Test strategies with tick precision', summary: 'Configure tick-level datasets and verify instrument spread rules.', steps: ['Select a tick or M1 dataset in Data sources.', 'Verify point value, tick size, and decimals in Instruments.', 'Export or link the dataset for high-precision evaluation.'] },
  { id: 'platform-data-export', test_id: 'dm-help-openlink-btn-2', title: 'Export data from Data Manager to external trading platforms', summary: 'Generate formatted bar and tick archives for external terminals.', steps: ['Select one or more saved datasets in the Data table.', 'Open the Export ribbon tab and select the target format.', 'Confirm date boundaries and download the exported artifacts.'] },
  { id: 'historical-data-import', test_id: 'dm-help-openlink-btn-3', title: 'Import historical bar and tick data from files', summary: 'Create a file symbol record and parse custom OHLCV CSV files.', steps: ['Add a symbol definition mapped to an existing Instrument.', 'Choose Import data file and verify column and date formatting.', 'Inspect the imported record count and preview bars in Chart.'] },
];
export const fetchDataManagerHelp = async (
  requestedTopic = 'overview',
  options?: Parameters<typeof createDomainClient>[1],
): Promise<HelpGuidePayload> => {
  const client = createDomainClient('/data', options);
  return client.get<HelpGuidePayload>(`/help?topic=${encodeURIComponent(requestedTopic)}`);
};

const tabs = ['Home', 'Data sources', 'Export', 'Tools', 'Instruments', 'Sessions', 'External indicators', 'Stock groups', 'Broker profiles', 'Log', 'Chart'];
const panelForTab: Record<string, WorkspaceTabId> = { Home: 'home', 'Data sources': 'data', Export: 'data', Tools: 'data', Instruments: 'instruments', Sessions: 'sessions', 'External indicators': 'custom-data', 'Stock groups': 'stock-groups', 'Broker profiles': 'brokers', Log: 'log', Chart: 'chart' };
const labelForPanel: Record<WorkspaceTabId, string> = { home: 'Home', data: 'Data sources', instruments: 'Instruments', sessions: 'Sessions', 'custom-data': 'External indicators', 'stock-groups': 'Stock groups', brokers: 'Broker profiles', log: 'Log', chart: 'Chart' };
type OperationState = 'idle' | 'running' | 'paused' | 'completed' | 'cancelled';
interface DialogState { id: DataSourceDialogId; exchange?: string; targetIds?: string[] }
type InstrumentDialogState =
  | { kind: 'editor'; mode: 'add' | 'edit' | 'mass'; selected: CatalogInstrument[] }
  | { kind: 'clone'; source: CatalogInstrument }
  | { kind: 'transfer'; mode: 'save' | 'load'; selected: CatalogInstrument[] };
type SessionDialogState =
  | { kind:'editor'; mode:'add'|'edit'; source?:SessionDefinition }
  | { kind:'clone'; source:SessionDefinition }
  | { kind:'delete'; selected:SessionDefinition[] }
  | { kind:'transfer'; mode:'save'|'load'; selected:SessionDefinition[] }
  | { kind:'import-nt' };
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
  return <p className="dialog-note">Data operations directly update the backend partitioned Parquet storage and catalog database.</p>;
}
function downloadTextFile(filename: string, text: string, type = 'application/json;charset=utf-8') { const url = URL.createObjectURL(new Blob([text], { type })); const anchor = document.createElement('a'); anchor.href = url; anchor.download = filename; anchor.click(); URL.revokeObjectURL(url); }

function DataSourceDialog({ state, selectedCount, selectedIds, onClose, onSecondary, onComplete }: {
  state: DialogState; selectedCount: number; selectedIds?: string[]; onClose: () => void;
  onSecondary: (id: DataSourceDialogId) => void; onComplete: (message: string) => void;
}) {
  const [agreed, setAgreed] = useState(false);
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
    'mass-delete': 'Delete data', 'save-definitions': 'Save selected dataset definitions',
    'load-definitions': 'Load dataset definitions', 'instrument-identification': 'Identify instruments for imported symbols',
    'data-format-name': 'Save data format', 'data-usage-conditions': 'Data usage conditions',
    'dependency-warning': 'Dependent dataset warning',
  };

  if (state.id === 'mass-delete') {
    const ids = state.targetIds ?? selectedIds ?? [];
    const count = state.targetIds ? state.targetIds.length : selectedCount;
    const handleClearData = async () => {
      const store = useDataManagerStore.getState();
      for (const id of ids) {
        try { await store.clearDataset(id); } catch { /* ignore */ }
      }
      onComplete(`Cleared stored data for ${ids.length} dataset(s)`);
    };
    const handleDelete = async () => {
      const store = useDataManagerStore.getState();
      for (const id of ids) {
        try { await store.removeDataset(id); } catch { /* ignore */ }
      }
      onComplete(`Removed ${ids.length} dataset(s)`);
    };
    return (
      <Modal
        title="Delete data"
        onClose={onClose}
        width={520}
        className="sqx-delete-data-modal"
        footer={
          <>
            <button className="sqx-delete-close-btn" onClick={onClose}>Close</button>
            <button className="sqx-delete-action-btn" onClick={handleClearData}>Clear data</button>
            <button className="sqx-delete-action-btn" onClick={handleDelete}>Delete</button>
          </>
        }
      >
        <p className="sqx-delete-prompt">
          Do you want to remove selected symbols ({count}) or only clear their data ?
        </p>
      </Modal>
    );
  }

  let content;
  switch (state.id) {
    case 'new-instrument':
      content = <div className="form-grid two"><Field label="Instrument symbol"><TextInput placeholder="EURUSD"/></Field><Field label="Instrument type"><Select value="forex" onChange={() => {}}><option value="forex">Forex</option><option value="futures">Futures</option><option value="stocks">Stocks</option><option value="crypto">Crypto</option></Select></Field><Field label="Base currency"><TextInput placeholder="EUR"/></Field><Field label="Quote currency"><TextInput placeholder="USD"/></Field></div>;
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
    case 'save-definitions':
      content = <><p>Export definitions for <strong>{selectedCount}</strong> selected dataset{selectedCount === 1 ? '' : 's'}.</p><Field label="Suggested file name"><TextInput defaultValue="Data.json"/></Field><MockBoundaryNote/></>;
      break;
    case 'load-definitions':
      content = <><Field label="Dataset definition file"><input className="file-input compact" type="file" accept=".json,application/json"/></Field><p className="callout">The JSON file will be validated for supported schema, contained values, and conflicting identities before definitions are applied.</p><MockBoundaryNote/></>;
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

  const informationOnly = ['dukascopy-information', 'data-usage-conditions'].includes(state.id);
  const agreementRequired = ['sq-equity-find', 'sq-futures-find'].includes(state.id);
  const primaryLabel = state.id === 'save-definitions' ? 'Download JSON' : state.id === 'load-definitions' ? 'Validate and load' : state.id === 'dependency-warning' ? 'Confirm deletion' : state.id === 'data-format-name' ? 'Save format' : state.id.includes('download') ? 'Start download' : state.id.includes('import') || state.id === 'mt5-import' ? 'Start import' : 'Save configuration';
  const primaryAction = async () => {
    if (state.id === 'dependency-warning') {
      const store = useDataManagerStore.getState();
      const ids = selectedIds || [];
      for (const id of ids) {
        try { await store.removeDataset(id); } catch { /* ignore */ }
      }
      onComplete(`Removed ${ids.length} dataset(s)`);
      return;
    }
    onComplete(`${titles[state.id]} completed`);
  };
  const wide = ['file-import', 'sq-equity-find', 'sq-futures-find', 'mt5-import'].includes(state.id);

  return <Modal title={titles[state.id]} onClose={onClose} width={wide ? 820 : 650} footer={<><Button onClick={onClose}>{informationOnly ? 'Close' : 'Cancel'}</Button>{!informationOnly && <Button className={state.id === 'dependency-warning' ? 'danger' : 'primary'} disabled={agreementRequired && !agreed} onClick={primaryAction}>{primaryLabel}</Button>}</>}>{content}</Modal>;
}

export function DataManager() {
  const definitions = useDataManagerStore(state => state.definitions);
  const savedDatasets = useDataManagerStore(state => state.savedDatasets);
  const brokerProfiles = useDataManagerStore(state => state.brokers);
  const brokerJob = useDataManagerStore(state => state.brokerJob);
  const download = useDukascopyDownloads();
  const td = useTickDownloader();
  const imports = useFileImports();
  const sq = useSQData();
  const darwinex = useDarwinex();
  const crypto = useCrypto();
  const yahoo = useYahoo();
  const mt5 = useMt5Import();
  const liveInstruments = useInstruments(state => state.instruments);
  const fileDefinitions = useFileSymbols(state => state.definitions);
  const customSessions = useSessions(state => state.sessions);
  const sessionOverrides = useSessions(state => state.overrides);
  const removedSessions = useSessions(state => state.removed);
  const exports = useDataExports();
  const tools = useDataTools();
  const externalIndicators = useExternalIndicators();
  const stockGroups = useStockGroups();
  useEffect(() => {
    void useSessions.getState().refreshFromServer();
  }, []);
  useEffect(() => { void useStockGroups.getState().syncRemote(); }, []);
  useEffect(() => { try { useStockGroups.getState().syncImports(imports.groups); } catch { /* surfaced by the store and later actions */ } }, [imports.groups]);
  useEffect(() => { if (stockGroups.job?.state !== 'running') return; const timer = window.setInterval(() => useStockGroups.getState().advance(), 220); return () => window.clearInterval(timer); }, [stockGroups.job?.state]);
  useEffect(() => { if (brokerJob?.state !== 'running') return; const timer = window.setInterval(() => useDataManagerStore.getState().advanceBrokerUpdate(), 220); return () => window.clearInterval(timer); }, [brokerJob?.state]);
  useEffect(() => { if (externalIndicators.job?.state !== 'running') return; const timer = window.setInterval(() => useExternalIndicators.getState().advance(), 220); return () => window.clearInterval(timer); }, [externalIndicators.job?.state]);
  useEffect(() => { if (tools.job?.state !== 'running') return; const timer = window.setInterval(() => useDataTools.getState().advance(), 180); return () => window.clearInterval(timer); }, [tools.job?.state]);
  useEffect(() => { if (exports.job?.state !== 'running') return; const timer = window.setInterval(() => useDataExports.getState().advance(), 180); return () => window.clearInterval(timer); }, [exports.job?.state]);
  useEffect(() => { if (mt5.job?.state !== 'running') return; const timer = window.setInterval(() => useMt5Import.getState().advance(), 250); return () => window.clearInterval(timer); }, [mt5.job?.state]);
  const [yahooDownloadTargets, setYahooDownloadTargets] = useState<YahooDefinition[]>([]);
  useEffect(() => { if (yahoo.job?.state !== 'running') return; const timer = window.setInterval(() => useYahoo.getState().advance(), 250); return () => window.clearInterval(timer); }, [yahoo.job?.state]);
  const [cryptoDownloadTargets, setCryptoDownloadTargets] = useState<CryptoDefinition[]>([]);
  useEffect(() => { if (crypto.job?.state !== 'running') return; const timer = window.setInterval(() => useCrypto.getState().advance(), 250); return () => window.clearInterval(timer); }, [crypto.job?.state]);
  const [darwinexDownloadTargets, setDarwinexDownloadTargets] = useState<DarwinexDefinition[]>([]);
  useEffect(() => { if (darwinex.job?.state !== 'running') return; const timer = window.setInterval(() => useDarwinex.getState().advance(), 250); return () => window.clearInterval(timer); }, [darwinex.job?.state]);
  const [fileTarget, setFileTarget] = useState<FileDefinition | null>(null);
  const [progressOwner, setProgressOwner] = useState<'download' | 'td' | 'file' | 'sq' | 'darwinex' | 'crypto' | 'yahoo' | 'mt5' | 'export' | 'tools' | 'external' | 'stock-groups' | 'broker'>(() => ['running','paused'].includes(brokerJob?.state??'')?'broker':stockGroupJobActive(stockGroups.job?.state) ? 'stock-groups' : externalJobActive(externalIndicators.job?.state) ? 'external' : toolsActive(tools.job?.state) ? 'tools' : exportActive(exports.job?.state) ? 'export' : mt5Active(mt5.job?.state) ? 'mt5' : yahooActive(yahoo.job?.state) ? 'yahoo' : cryptoActive(crypto.job?.state) ? 'crypto' : darwinexActive(darwinex.job?.state) ? 'darwinex' : sqActive(sq.job?.state) ? 'sq' : activeImport(imports.job?.state) ? 'file' : ['running', 'paused'].includes(download.job?.state ?? '') ? 'download' : activeImport(td.job?.state) ? 'td' : brokerJob?'broker':stockGroups.job ? 'stock-groups' : externalIndicators.job ? 'external' : tools.job ? 'tools' : exports.job ? 'export' : mt5.job ? 'mt5' : yahoo.job ? 'yahoo' : crypto.job ? 'crypto' : darwinex.job ? 'darwinex' : sq.job ? 'sq' : imports.job ? 'file' : td.job ? 'td' : 'download');
  const providerJob = progressOwner === 'broker'?brokerJob:progressOwner === 'stock-groups' ? stockGroups.job : progressOwner === 'external' ? externalIndicators.job : progressOwner === 'tools' ? tools.job : progressOwner === 'export' ? exports.job : progressOwner === 'mt5' ? mt5.job : progressOwner === 'yahoo' ? yahoo.job : progressOwner === 'crypto' ? crypto.job : progressOwner === 'darwinex' ? darwinex.job : progressOwner === 'sq' ? sq.job : progressOwner === 'file' ? imports.job : progressOwner === 'td' ? td.job : download.job;
  useEffect(() => { if (sq.job?.state !== 'running') return; const timer = window.setInterval(() => useSQData.getState().advance(), 250); return () => window.clearInterval(timer); }, [sq.job?.state]);
  const providerAction = progressOwner === 'broker'?useDataManagerStore.getState().brokerAction:progressOwner === 'stock-groups' ? stockGroups.action : progressOwner === 'external' ? externalIndicators.action : progressOwner === 'tools' ? tools.action : progressOwner === 'export' ? exports.action : progressOwner === 'mt5' ? mt5.action : progressOwner === 'yahoo' ? yahoo.action : progressOwner === 'crypto' ? crypto.action : progressOwner === 'darwinex' ? darwinex.action : progressOwner === 'sq' ? sq.action : progressOwner === 'file' ? imports.action : progressOwner === 'td' ? td.action : download.action;
  useEffect(() => {
    if (td.job?.state !== 'running') return;
    const timer = window.setInterval(() => useTickDownloader.getState().advance(), 250);
    return () => window.clearInterval(timer);
  }, [td.job?.state]);
  useEffect(() => { if (imports.job?.state !== 'running') return; const timer = window.setInterval(() => useFileImports.getState().advance(), 250); return () => window.clearInterval(timer); }, [imports.job?.state]);
  const [downloadTargets, setDownloadTargets] = useState<DownloadTarget[]>([]);
  useEffect(() => {
    if (download.job?.state !== 'running') return;
    const timer = window.setInterval(() => useDukascopyDownloads.getState().advance(), 250);
    return () => window.clearInterval(timer);
  }, [download.job?.state]);
  const [tab, setTab] = useState('Data sources');
  const { status: hostStatus } = useHostConnection();
  const [workspace, setWorkspace] = useState<WorkspaceLayout | null>(null);
  const [workspaceError, setWorkspaceError] = useState('');
  const [workspaceRetry, retryWorkspace] = useState(0);
  const [dockActivation, setDockActivation] = useState(0);
  const [arrangeOpen, setArrangeOpen] = useState(false);
  const [arrangeRequest, setArrangeRequest] = useState<WorkspaceArrangeRequest | null>(null);
  const arrangeRef = useRef<HTMLDivElement>(null);
  const [activeDatasetId, setActiveDatasetId] = useState<string | null>(null);
  const [selectedBarTime, setSelectedBarTime] = useState<number | null>(null);
  const [chartRequest, setChartRequest] = useState(0);
  const [linkedSnapshot, setLinkedSnapshot] = useState<WorkspaceSnapshot | null>(null);
  const [previewLoading, setPreviewLoading] = useState(false);
  const [previewError, setPreviewError] = useState('');
  const [previewRetry, retryPreview] = useState(0);
  const previewRequest = useRef({ datasetId: null as string | null, retry: 0 });
  useEffect(() => {
    setWorkspace(null); setWorkspaceError(''); setLinkedSnapshot(null);
    if (hostStatus !== 'online') { setActiveDatasetId(null); setSelectedBarTime(null); setChartRequest(0); useDataManagerStore.setState({ savedDatasets: null }); return; }
    const controller = new AbortController();
    fetchWorkspace({ signal: controller.signal }).then(setWorkspace).catch(cause => {
      if (!controller.signal.aborted) setWorkspaceError(cause instanceof Error ? cause.message : 'Unable to initialize workspace.');
    });
    return () => controller.abort();
  }, [hostStatus, workspaceRetry]);
  useEffect(() => {
    if (!workspace || hostStatus !== 'online') return;
    const controller = new AbortController();
    const reload = !linkedSnapshot || previewRequest.current.datasetId !== activeDatasetId || previewRequest.current.retry !== previewRetry;
    previewRequest.current = { datasetId: activeDatasetId, retry: previewRetry };
    if (reload) { setLinkedSnapshot(null); setPreviewLoading(true); }
    setPreviewError('');
    openWorkspaceTab(panelForTab[tab], activeDatasetId, { signal: controller.signal }).then(snapshot => {
      if (!controller.signal.aborted) setLinkedSnapshot(current => current?.selection?.id === snapshot.selection?.id && JSON.stringify(current?.preview) === JSON.stringify(snapshot.preview) ? { ...snapshot, preview: current!.preview } : snapshot);
    }).catch(cause => {
      if (!controller.signal.aborted) setPreviewError(cause instanceof Error ? cause.message : 'Unable to open workspace tab.');
    }).finally(() => { if (!controller.signal.aborted) setPreviewLoading(false); });
    return () => controller.abort();
  }, [workspace, hostStatus, tab, activeDatasetId, previewRetry]);
  useEffect(() => {
    if (activeDatasetId && savedDatasets !== null && !savedDatasets.some(row => row.id === activeDatasetId)) {
      setActiveDatasetId(null); setSelectedBarTime(null); setLinkedSnapshot(null);
    }
  }, [savedDatasets, activeDatasetId]);
  const activateDataset = (id: string) => { if (id !== activeDatasetId) setSelectedBarTime(null); setActiveDatasetId(id); setChartRequest(value => value + 1); };

  const [dialog, setDialog] = useState<DialogState | null>(null);
  const [instrumentDialog, setInstrumentDialog] = useState<InstrumentDialogState | null>(null);
  const [selectedInstrumentIds, setSelectedInstrumentIds] = useState<string[]>([]);
  useEffect(() => {
    if (hostStatus !== 'online') { useInstruments.getState().reset(); setInstrumentDialog(null); setSelectedInstrumentIds([]); return; }
    void useInstruments.getState().refreshFromServer();
    return () => { useInstruments.getState().reset(); };
  }, [hostStatus]);
  useEffect(() => {
    if (hostStatus === 'online' && tab === 'Instruments') void useInstruments.getState().refreshFromServer();
  }, [tab, hostStatus]);
  useEffect(() => { setSelectedInstrumentIds(current => current.filter(id => liveInstruments.some(row => row.id === id))); }, [liveInstruments]);
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
  useEffect(() => {
    if (savedDatasets !== null) setSelectedDatasetIds(current => current.filter(id => savedDatasets.some(row => row.id === id)));
  }, [savedDatasets]);
  const [progress, setProgress] = useState(0);
  const [operationState, setOperationState] = useState<OperationState>('idle');
  const [operationLabel, setOperationLabel] = useState('No active operations');
  const [selectionMessage, setSelectionMessage] = useState('');
  useEffect(() => { if (selectedDatasetIds.length > 0) setSelectionMessage(''); }, [selectedDatasetIds]);
  const [logEntries, setLogEntries] = useState<string[]>([]);
  const lastLoggedTransition = useRef('');
  const lastStockGroupTransition = useRef('');
  const lastBrokerTransition=useRef('');
  useEffect(()=>{if(!brokerJob)return;const transition=`${brokerJob.state}:${brokerJob.progress}`;if(lastBrokerTransition.current===transition)return;lastBrokerTransition.current=transition;if(brokerJob.progress%25!==0&&!['paused','failed','cancelled','completed'].includes(brokerJob.state))return;setLogEntries(current=>[...current,`${new Date().toLocaleString()} Broker data update — ${brokerJob.state} ${brokerJob.progress}%`].slice(-500));},[brokerJob]);
  useEffect(() => {
    if (!stockGroups.job) return;
    const transition = `${stockGroups.job.state}:${stockGroups.job.progress}`;
    if (lastStockGroupTransition.current === transition) return;
    lastStockGroupTransition.current = transition;
    if (stockGroups.job.progress % 25 !== 0 && !['paused','failed','cancelled','completed'].includes(stockGroups.job.state)) return;
    const timestamp = new Date().toLocaleString();
    setLogEntries(current => [...current, `${timestamp} Stock group data update — ${stockGroups.job!.state} ${stockGroups.job!.progress}%`].slice(-500));
  }, [stockGroups.job]);
  useEffect(() => {
    if (operationState === 'idle') return;
    const transition = operationLabel + ':' + operationState;
    if (lastLoggedTransition.current === transition) return;
    lastLoggedTransition.current = transition;
    const timestamp = new Date().toLocaleString();
    setLogEntries(current => [...current, timestamp + ' ' + operationLabel + ' — ' + operationState].slice(-500));
  }, [operationLabel, operationState]);

  useEffect(() => {
    if (tab === 'Log') {
      fetchLogs()
        .then(records => {
          if (records && records.length > 0) {
            const formatted = records.map(formatDataLogLine);
            setLogEntries(formatted);
          }
        })
        .catch(() => {
          // preserve existing local entries if fetch fails
        });
    }
  }, [tab]);

  useEffect(() => {
    if (hostStatus !== 'online') return;
    return subscribeDataLogStream({
      onEntry: record => {
        setLogEntries(current => [...current, formatDataLogLine(record)].slice(-500));
      },
      onSnapshot: records => {
        if (records.length > 0) setLogEntries(records.map(formatDataLogLine).slice(-500));
      },
      onCleared: () => {
        setLogEntries([]);
        setProgress(0);
      },
      onProgress: state => {
        if (state.status === 'running' || state.status === 'paused') {
          setProgress(state.progress);
          setOperationLabel(state.label);
        }
      },
    });
  }, [hostStatus]);

  const canCancelLogOperation =
    operationState === 'running' ||
    operationState === 'paused' ||
    ['running', 'paused'].includes(providerJob?.state ?? '');

  const handleCancelLogOperation = () => {
    setSelectionMessage('');
    if (providerJob && ['running', 'paused'].includes(providerJob.state)) {
      providerAction('stop');
    } else if (operationState === 'running' || operationState === 'paused') {
      setOperationState('cancelled');
    }
    void cancelLogOperation('', operationLabel).catch(() => undefined);
    notify(`${operationLabel} cancelled`);
  };

  const handleClearLog = async () => {
    try {
      await clearLogs();
    } catch {
      // reset local log and completed/cancelled progress even when offline
    }
    setLogEntries([]);
    setProgress(0);
    if (operationState === 'completed' || operationState === 'cancelled') {
      setOperationState('idle');
      setOperationLabel('No active operations');
    }
    notify('Logs cleared.');
  };
  const [lastControlId, setLastControlId] = useState<string | null>(null);
  const ribbonRef = useRef<HTMLDivElement>(null);
  const notify = useAppStore(state => state.notify);
  const downloadedExport = useRef(exports.job?.state === 'completed' ? exports.job.id : '');
  useEffect(() => {
    if (exports.job?.state !== 'completed' || downloadedExport.current === exports.job.id) return;
    downloadedExport.current = exports.job.id;
    downloadExportArtifacts(exports.job.artifacts);
    notify(`${exports.job.label} completed — ${exports.job.artifacts.length} file${exports.job.artifacts.length === 1 ? '' : 's'} downloaded`);
  }, [exports.job, notify]);

  useEffect(() => {
    if (operationState !== 'running') return;
    const timer = window.setInterval(() => setProgress(current => {
      const next = Math.min(100, current + 8);
      if (next === 100) window.setTimeout(() => { setOperationState('completed'); notify(`${operationLabel} completed`); }, 0);
      return next;
    }), 180);
    return () => window.clearInterval(timer);
  }, [notify, operationLabel, operationState]);

  useEffect(() => {
    const closeMenus = (event: MouseEvent) => { if (!ribbonRef.current?.contains(event.target as Node)) { setOpenMenu(null); setNestedOpen(false); } if (!arrangeRef.current?.contains(event.target as Node)) setArrangeOpen(false); };
    const closeOnEscape = (event: KeyboardEvent) => { if (event.key === 'Escape') { setOpenMenu(null); setNestedOpen(false); setArrangeOpen(false); } };
    document.addEventListener('mousedown', closeMenus);
    document.addEventListener('keydown', closeOnEscape);
    return () => { document.removeEventListener('mousedown', closeMenus); document.removeEventListener('keydown', closeOnEscape); };
  }, []);

  useEffect(() => {
    if (hostStatus === 'online' && ['Data sources', 'Export', 'Tools'].includes(tab)) void useDataManagerStore.getState().syncRemoteDatasets();
  }, [tab, hostStatus]);
  useEffect(() => { void useDataManagerStore.getState().syncBrokers(); }, []);
  useEffect(() => {
    if (providerJob?.state === 'completed') void useDataManagerStore.getState().syncRemoteDatasets();
  }, [providerJob?.state]);

  const startOperation = (label: string) => { if ([td.job?.state, download.job?.state, imports.job?.state, sq.job?.state, darwinex.job?.state, crypto.job?.state, yahoo.job?.state, mt5.job?.state, exports.job?.state, tools.job?.state, externalIndicators.job?.state, stockGroups.job?.state,brokerJob?.state].some(state => state === 'running' || state === 'paused')) { setSelectionMessage('Finish or stop the active data operation first.'); return; } setSelectionMessage(''); setOpenMenu(null); setNestedOpen(false); setOperationLabel(label); setProgress(4); setOperationState('running'); notify(`${label} started`); };
  const runDirectAction = (action: DirectDataSourceAction) => {
    if (action === 'sq-equity-update') { runEquityUpdate(startOperation); return; }
    if (action === 'sq-futures-update') { runFuturesUpdate(startOperation); return; }
    const labels: Record<Exclude<DirectDataSourceAction, 'sq-equity-update' | 'sq-futures-update'>, string> = {
      'update-all': 'All eligible dataset updates', 'update-selected': `${selectedDatasetIds.length} selected dataset update${selectedDatasetIds.length === 1 ? '' : 's'}`,
    };
    startOperation(labels[action]);
  };
  const selectCommand = (command: DataSourceCommand) => {
    if (['mt5-import', 'yahoo-add', 'yahoo-download', 'crypto-add', 'crypto-download', 'darwinex-add', 'darwinex-import', 'darwinex-download', 'sq-equity-find', 'sq-futures-find', 'tickdownloader-import', 'dukascopy-add', 'dukascopy-download', 'file-import', 'file-mass-import'].includes(command.dialog ?? '') && (activeImport(operationState) || [td.job?.state, download.job?.state, imports.job?.state, sq.job?.state, darwinex.job?.state, crypto.job?.state, yahoo.job?.state, mt5.job?.state, exports.job?.state, tools.job?.state, externalIndicators.job?.state, stockGroups.job?.state,brokerJob?.state].some(activeImport))) { setSelectionMessage('Finish or stop the active data operation first.'); setOpenMenu(null); return; }
    if (command.dialog === 'yahoo-download') {
      setOpenMenu(null); setNestedOpen(false);
      try { const targets = yahooTargets(yahoo.definitions.filter(row => selectedDatasetIds.includes(row.id))).map(row => ({ ...row, ...simulationSummary(row, yahoo.ranges[row.id] ?? []) })); setYahooDownloadTargets(targets); setSelectionMessage(''); setDialog({ id: 'yahoo-download' }); } catch (cause) { setSelectionMessage(cause instanceof Error ? cause.message : 'Unable to select Yahoo data.'); }
      return;
    }
    if (command.dialog === 'crypto-download') {
      setOpenMenu(null); setNestedOpen(false);
      try { const targets = cryptoTargets(crypto.definitions.filter(row => selectedDatasetIds.includes(row.id))).map(row => ({ ...row, ...simulationSummary(row, crypto.ranges[row.id] ?? []) })); setCryptoDownloadTargets(targets); setSelectionMessage(''); setDialog({ id: 'crypto-download' }); } catch (cause) { setSelectionMessage(cause instanceof Error ? cause.message : 'Unable to select Crypto data.'); }
      return;
    }
    if (command.dialog === 'darwinex-download') {
      setOpenMenu(null); setNestedOpen(false);
      try { const targets = darwinexTargets(darwinex.definitions.filter(row => selectedDatasetIds.includes(row.id))).map(row => ({ ...row, ...simulationSummary(row, darwinex.ranges[row.id] ?? []) })); setDarwinexDownloadTargets(targets); setSelectionMessage(''); setDialog({ id: 'darwinex-download' }); } catch (cause) { setSelectionMessage(cause instanceof Error ? cause.message : 'Unable to select data.'); }
      return;
    }
    if (command.dialog === 'file-import') {
      setOpenMenu(null); setNestedOpen(false);
      const rows = definitions.filter(row => selectedDatasetIds.includes(row.id) && row.source === 'File import');
      const row = rows[0];
      if (!row) { setSelectionMessage('You must select at least one File record.'); return; }
      if ('cloned' in row && row.cloned) { setSelectionMessage('Cannot import into cloned data.'); return; }
      const instrument = seedInstruments.find(item => item.symbol === row.symbol) ?? seedInstruments[0];
      const targetBarType: 'start' | 'end' = row.barType === 'end' ? 'end' : 'start';
      setFileTarget({ ...emptyFileRecord(row.symbol, instrument, targetBarType), ...row, barType: targetBarType }); setSelectionMessage(''); setDialog({ id: 'file-import' }); return;
    }
    if (command.dialog === 'dukascopy-download') {
      setOpenMenu(null); setNestedOpen(false);
      try {
        const selected = definitions.filter(row => selectedDatasetIds.includes(row.id));
        const eligible = eligibleTargets(selected, download.job).map(row => ({ ...row, ...simulationSummary(row, download.ranges[row.id] ?? []) }));
        setDownloadTargets(eligible); setSelectionMessage(''); setDialog({ id: 'dukascopy-download' });
      } catch (cause) { setSelectionMessage(cause instanceof Error ? cause.message : 'Unable to select data'); }
      return;
    }
    setOpenMenu(null); setNestedOpen(false); if (command.action) runDirectAction(command.action); if (command.dialog) setDialog({ id: command.dialog, exchange: command.exchange }); };
  const closeDialog = useCallback(() => {
    setDialog(null);
    setOpenMenu(null);
    setNestedOpen(false);
    if (lastControlId) window.setTimeout(() => document.querySelector<HTMLButtonElement>(`[data-control-id="${lastControlId}"]`)?.focus(), 0);
  }, [lastControlId]);
  const toggleDataset = (id: string) => setSelectedDatasetIds(current => current.includes(id) ? current.filter(item => item !== id) : [...current, id]);
  const toolRows: ToolTarget[] = definitions.map(row => ({
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
    sourceDataId: 'sourceDataId' in row && typeof (row as any).sourceDataId === 'string' ? (row as any).sourceDataId : undefined,
  }));
  const exportRows: ExportTarget[] = toolRows;
  const instrumentRows = liveInstruments;
  const instrumentBrokers: InstrumentBroker[] = [
    { id: '-1', name: 'Default', postfix: '', timezone: 'UTC' },
    ...brokerProfiles.filter(profile => profile.mtUse).map(profile => ({ id: profile.id, name: profile.name, postfix: profile.postfix, timezone: profile.timezone })),
  ];
  const sessionBrokers:SessionBroker[]=[{id:'-1',name:'Default',postfix:''},...brokerProfiles.filter(profile=>profile.mtUse).map(profile=>({id:profile.id,name:profile.name,postfix:profile.postfix}))];
  const sessionRows=effectiveSessions(customSessions,sessionOverrides,removedSessions);
  const selectedBrokers=brokerProfiles.filter(item=>selectedBrokerIds.includes(item.id));
  const requireBrokers=():BrokerProfile[]|null=>{if(selectedBrokers.length){setSelectionMessage('');return selectedBrokers;}setSelectionMessage('You have to select some broker.');return null;};
  const openBrokerEdit=(profile:BrokerProfile)=>{setSelectedBrokerIds([profile.id]);if(profile.system){setSelectionMessage("This broker can't be edited.");return;}setBrokerDialog({kind:'editor',mode:'edit',source:profile});};
  const updateBrokers=(items:BrokerProfile[])=>{try{if(anyDataActive)throw new Error('Finish or stop the active data operation first.');if(!items[0].stockPickerUse)throw new Error('This function is for stockpicking broker profile only.');useDataManagerStore.getState().startBrokerUpdate(items.map(row=>row.id),toolRows.map(row=>row.symbol));setProgressOwner('broker');setOperationState('idle');setSelectionMessage('');notify('Data update started, please check Log tab for more information.');}catch(cause){setSelectionMessage(cause instanceof Error?cause.message:'Unable to update broker data.');}};
  const selectedSessions=sessionRows.filter(item=>selectedSessionIds.includes(item.name));
  const requireSessions=():SessionDefinition[]|null=>{if(selectedSessions.length){setSelectionMessage('');return selectedSessions;}setSelectionMessage('You have to select some session.');return null;};
  const openSessionEdit=(item:SessionDefinition)=>{setSelectedSessionIds([item.name]);setSessionError('');setSessionDialog({kind:'editor',mode:'edit',source:item});};
  const openSessionDelete=(items:SessionDefinition[])=>{setSelectedSessionIds(items.map(item=>item.name));setSessionError('');setSessionDialog({kind:'delete',selected:items});};
  const removeSelectedSessions=()=>{if(sessionDialog?.kind!=='delete')return;try{const names=sessionDialog.selected.map(item=>item.name);useSessions.getState().remove(names,instrumentRows.map(item=>(item as {session?:string}).session??''));setSelectedSessionIds(current=>current.filter(name=>!names.includes(name)));notify(`${names.length} session${names.length===1?'':'s'} removed.`);setSessionDialog(null);setSessionError('');}catch(cause){setSessionError(cause instanceof Error?cause.message:'Unable to remove sessions.');}};
  const selectedExternal = externalIndicators.definitions.filter(item => selectedExternalNames.includes(item.name));
  const requireExternal = (): ExternalIndicatorDefinition[] | null => { if (selectedExternal.length) { setSelectionMessage(''); return selectedExternal; } setSelectionMessage('You have to select at least one indicator.'); return null; };
  const openExternalEdit = (item: ExternalIndicatorDefinition) => { setSelectedExternalNames([item.name]); setSelectionMessage(''); setExternalDialog({ kind: 'editor', mode: 'edit', source: item }); };
  const openExternalDelete = (items: ExternalIndicatorDefinition[]) => { setSelectedExternalNames(items.map(item => item.name)); setSelectionMessage(''); setExternalDialog({ kind: 'delete', selected: items }); };
  const selectedStockGroups = stockGroups.groups.filter(item => selectedStockGroupIds.includes(item.id));
  const requireStockGroups = (): StockGroupDefinition[] | null => { if (selectedStockGroups.length) { setSelectionMessage(''); return selectedStockGroups; } setSelectionMessage('You have to select some group.'); return null; };
  const openStockGroupEdit = (group: StockGroupDefinition) => { setSelectedStockGroupIds([group.id]); if (group.system) { setSelectionMessage("This group can't be edited."); return; } setStockGroupDialog({ kind: 'editor', mode: 'edit', source: group }); };
  const updateStockGroups = (items: StockGroupDefinition[]) => { try { useStockGroups.getState().start(items.map(item => item.id), toolRows.map(row => row.symbol), anyDataActive); setProgressOwner('stock-groups'); setOperationState('idle'); setSelectionMessage(''); notify('Data update started, please check Log tab for more information.'); } catch (cause) { setSelectionMessage(cause instanceof Error ? cause.message : 'Unable to update stock group.'); } };
  const selectedInstruments = instrumentRows.filter(item => selectedInstrumentIds.includes(item.id));
  const requireInstruments = (): CatalogInstrument[] | null => {
    if (selectedInstruments.length) { setSelectionMessage(''); return selectedInstruments; }
    setSelectionMessage('You have to select some record.');
    return null;
  };
  const openInstrumentEdit = (item: CatalogInstrument) => {
    setSelectedInstrumentIds([item.id]);
    setInstrumentDialog({ kind: 'editor', mode: 'edit', selected: [item] });
  };
  const otherProviderActive = activeImport(operationState) || [td.job?.state, download.job?.state, imports.job?.state, sq.job?.state, darwinex.job?.state, crypto.job?.state, yahoo.job?.state, mt5.job?.state, exports.job?.state, tools.job?.state, stockGroups.job?.state,brokerJob?.state].some(activeImport);
  const externalActive = otherProviderActive || externalJobActive(externalIndicators.job?.state);
  const otherDataActive = externalActive || exportActive(exports.job?.state);
  const anyDataActive = otherDataActive || toolsActive(tools.job?.state);
  const openExport = (kind: ExportKind) => { try { if (anyDataActive) throw new Error('Finish or stop the active data operation first.'); const targets = selectExportTargets(exportRows, selectedDatasetIds, kind); setExportDialog({ kind, targets }); setSelectionMessage(''); } catch (cause) { setSelectionMessage(cause instanceof Error ? cause.message : 'Unable to select data for export.'); } };
  const openClone = () => { try { if (anyDataActive) throw new Error('Finish or stop the active data operation first.'); const targets = selectCloneTargets(toolRows, selectedDatasetIds); setCloneTargets(targets); setSelectionMessage(''); } catch (cause) { setSelectionMessage(cause instanceof Error ? cause.message : 'Unable to select data to clone.'); } };
  const openReview = () => { try { if (anyDataActive) throw new Error('Cannot view data while an operation is in progress.'); const target = selectReviewTarget(toolRows, selectedDatasetIds); setReviewTarget(target); setSelectionMessage(''); } catch (cause) { setSelectionMessage(cause instanceof Error ? cause.message : 'Unable to view data.'); } };
  const progressText = selectionMessage || (operationState === 'idle' ? (providerJob ? `${progressOwner === 'broker'?'Broker data update':progressOwner === 'stock-groups' ? 'Stock group data update' : progressOwner === 'external' ? `Custom data import for '${externalIndicators.job?.indicator}'` : progressOwner === 'tools' ? 'Clone to timezone' : progressOwner === 'export' ? exports.job?.label : progressOwner === 'mt5' ? 'MT5 mock import' : progressOwner === 'yahoo' ? `Yahoo mock ${yahoo.job?.kind}` : progressOwner === 'crypto' ? `Crypto mock ${crypto.job?.kind}` : progressOwner === 'darwinex' ? `Darwinex mock ${darwinex.job?.kind}` : progressOwner === 'sq' && sq.job ? providerLabel(sq.job.provider) : progressOwner === 'file' ? 'File import' : progressOwner === 'td' ? 'TickDownloader mock import' : 'Dukascopy mock download'} ${providerJob.state} ${providerJob.progress}%${providerJob.error ? `: ${providerJob.error}` : progressOwner === 'external' && externalIndicators.job?.state === 'completed' && externalIndicators.job.ignored ? ` — ${externalIndicators.job.ignored} invalid rows ignored` : progressOwner === 'file' && imports.job?.state === 'completed' ? ` — ${imports.job.completed} imported, ${imports.job.skipped} skipped, ${imports.job.tasks.reduce((n, task) => n + task.ignored, 0)} invalid rows ignored` : ''}` : 'No active operations') : operationState === 'paused' ? `${operationLabel} paused at ${progress}%` : operationState === 'cancelled' ? `${operationLabel} cancelled` : operationState === 'completed' ? `${operationLabel} complete` : `${operationLabel}… ${progress}%`);

  const handleDeleteDatasetRow = (id: string) => {
    setSelectedDatasetIds([id]);
    setDialog({ id: 'mass-delete', targetIds: [id] });
  };

  const renderPanel = (id: WorkspaceTabId) => {
    switch (id) {
      case 'chart': return <DataManagerChart snapshot={linkedSnapshot} loading={previewLoading} error={previewError} selectedTime={selectedBarTime} onSelectTime={setSelectedBarTime} onRetry={() => retryPreview(value => value + 1)} />;
      case 'home': return <DataManagerHome onNavigateTab={setTab} onOpenImport={() => { setTab('Data sources'); setDialog({ id: 'file-import' }); }} onOpenDownload={() => { setTab('Data sources'); setDialog({ id: 'dukascopy-download' }); }} />;
      case 'data': return <DatasetTable onActivate={activateDataset} activeDatasetId={activeDatasetId} selectedIds={selectedDatasetIds} onToggle={toggleDataset} onSelect={setSelectedDatasetIds} onDeleteRow={handleDeleteDatasetRow}/>;
      case 'brokers': return <BrokerProfilesTable profiles={brokerProfiles} selected={selectedBrokerIds} instruments={instrumentRows} sessions={sessionRows} onSelect={setSelectedBrokerIds} onEdit={openBrokerEdit}/>;
      case 'stock-groups': return <StockGroupsTable groups={stockGroups.groups} selected={selectedStockGroupIds} datasets={toolRows} onSelect={setSelectedStockGroupIds} onEdit={openStockGroupEdit} onUpdate={group=>updateStockGroups([group])}/>;
      case 'custom-data': return <ExternalIndicatorsTable rows={externalIndicators.definitions} selected={selectedExternalNames} job={externalIndicators.job} onSelect={setSelectedExternalNames} onEdit={openExternalEdit} onDelete={item => openExternalDelete([item])}/>;
      case 'instruments': return <InstrumentTable selected={selectedInstrumentIds} onSelect={setSelectedInstrumentIds} onEdit={openInstrumentEdit} />;
      case 'sessions': return <SessionTable rows={sessionRows} selected={selectedSessionIds} onSelect={setSelectedSessionIds} onEdit={openSessionEdit} onDelete={item=>openSessionDelete([item])} brokers={sessionBrokers}/>;
      case 'log': return <main className="dm-log data-manager-log" data-testid="dm-tab-log"><div className="datamanager-help">Here is where you can see the download progress - you can see every symbol / year downloaded by the program.</div><header className="data-manager-log-buttons"><strong className="settings-title">Log</strong><button data-testid="dm-log-cancel-btn" className="cancel-log log-cancel-button" disabled={!canCancelLogOperation} onClick={handleCancelLogOperation}>Cancel operation</button><button data-testid="dm-data-log-clear-log-btn" className="clear-log log-clear-button" onClick={handleClearLog}>Clear log</button></header><div className="dm-log-progress" data-testid="dm-log-progress"><ProgressBar value={operationState === 'idle' && providerJob ? providerJob.progress : progress} label={progressText}/></div><div className="log-container"><div className="dm-log-output log-scroll-content" role="log" aria-label="Data Manager log">{logEntries.map((entry, index) => { const isError = isErrorLogRecord(entry); return <div key={index} className={isError ? 'dm-log-entry log-entry-error' : 'dm-log-entry'} data-error={isError ? 'true' : 'false'}>{entry}</div>; })}</div></div></main>;
    }
  };
  const triggerArrange = (action: WorkspaceArrangement) => { setArrangeOpen(false); setArrangeRequest(current => ({ seq: (current?.seq ?? 0) + 1, action, targetId: panelForTab[tab] })); };
  return <div className="data-manager"><div className="dm-title">Data Manager</div><div className="ribbon-tabs" role="navigation" aria-label="Data Manager workspace navigation">{tabs.map(item => <button key={item} className={tab === item ? 'active' : ''} onClick={() => { setArrangeOpen(false); setTab(item); setDockActivation(value => value + 1); }}>{item}</button>)}<div className="dm-arrange-menu" ref={arrangeRef}><button type="button" className={arrangeOpen ? 'active' : ''} aria-haspopup="menu" aria-expanded={arrangeOpen} onClick={() => setArrangeOpen(value => !value)}>Arrange</button>{arrangeOpen && <div className="dm-arrange-dropdown" role="menu" aria-label="Arrange workspace panel"><button type="button" role="menuitem" onClick={() => triggerArrange('right')}>Move panel right</button><button type="button" role="menuitem" onClick={() => triggerArrange('bottom')}>Move panel below</button><button type="button" role="menuitem" onClick={() => triggerArrange('main')}>Return to main group</button><button type="button" role="menuitem" onClick={() => triggerArrange('close')}>Close panel</button></div>}</div><HelpTooltip title="Data Manager Help" summary="Download, import, and export market data." topic={helpTopicForTab[tab] ?? 'overview'} availableTopics={['overview', 'data', 'import', 'export', 'instruments', 'sessions', 'brokers', 'custom-data', 'stock-groups', 'log', 'chart']} tutorials={DEFAULT_DM_TUTORIALS} loadGuide={fetchDataManagerHelp}/></div><div className="ribbon" ref={ribbonRef}>
    {['Home', 'Log', 'Chart'].includes(tab) && <p className="dm-context-note">{tab === 'Chart' ? 'Select a saved dataset to view its recorded history. Use Arrange to dock or close panels.' : tab === 'Home' ? 'Data Manager overview' : 'Data Manager operation log'}</p>}
    {tab === 'Data sources' && <div className="data-source-ribbon" aria-label="Data source operations"><div className="provider-actions">{dataSourceProviders.map(provider => <ProviderMenu key={provider.id} provider={provider} isOpen={openMenu === provider.id} nestedOpen={nestedOpen && openMenu === provider.id} onToggle={() => { setOpenMenu(current => current === provider.id ? null : provider.id); setNestedOpen(false); }} onToggleNested={() => setNestedOpen(current => !current)} onSelect={command => { setLastControlId(provider.id); selectCommand(command); }}/>)}</div><div className="context-actions">{dataSourceContextActions.map(action => { const Icon = contextIcons[action.id] ?? Database; return <button className={`data-source-button ${action.id === 'mass-delete' ? 'destructive' : ''}`} data-control-id={action.id} key={action.id} title={action.label} onClick={() => { setLastControlId(action.id); if (action.requiresSelection && selectedDatasetIds.length === 0) { setSelectionMessage('Select at least one dataset first'); return; } if (action.action) runDirectAction(action.action); if (action.dialog) setDialog({ id: action.dialog }); }}><Icon size={27}/><span>{action.label}</span></button>; })}</div></div>}
    {tab === 'Export' && <div className="export-actions" aria-label="Data export operations"><Button data-control-id="export-csv" className="export-csv" onClick={() => { setLastControlId('export-csv'); openExport('csv'); }}><FileSpreadsheet size={24} aria-hidden="true"/>Export to CSV</Button><Button data-control-id="export-mt4" className="export-mt4" title="Export to MetaTrader 4 (FXT & HST)" onClick={() => { setLastControlId('export-mt4'); openExport('mt4'); }}><MonitorDown size={24} aria-hidden="true"/>Export MT4 (FXT &amp; HST)</Button><Button data-control-id="export-mt5" className="export-mt5" title="Export to MetaTrader 5 data (99% test)" onClick={() => { setLastControlId('export-mt5'); openExport('mt5'); }}><ChartCandlestick size={24} aria-hidden="true"/>Export to MT5 data (99% test)</Button></div>}
    {tab === 'Tools' && <div className="data-tool-actions" aria-label="Data tools"><Button data-control-id="tool-timezone" className="tool-timezone" onClick={() => { setLastControlId('tool-timezone'); openClone(); }}><span className="timezone-tool-icon" aria-hidden="true"><Globe2 size={26}/><Clock size={13}/></span>Clone to timezone</Button><Button data-control-id="tool-analyze" className="tool-analyze" onClick={() => { setLastControlId('tool-analyze'); openReview(); }}><ChartCandlestick size={26} aria-hidden="true"/>View &amp; Analyze</Button></div>}
    {tab === 'Instruments' && <div className="management-actions" aria-label="Instrument operations">
      <Button id="datamanager-instruments-add" className="action-add" onClick={() => { setInstrumentDialog({ kind: 'editor', mode: 'add', selected: [] }); }}><CirclePlus size={26} aria-hidden="true"/>Add Instrument</Button>
      <Button id="datamanager-instruments-clone" className="action-clone" onClick={() => { const rows = requireInstruments(); if (rows) setInstrumentDialog({ kind: 'clone', source: rows[0] }); }}><CopyPlus size={26} aria-hidden="true"/>Clone Instrument</Button>
      <Button id="datamanager-instruments-edit" className="action-edit" onClick={() => { const rows = requireInstruments(); if (rows) setInstrumentDialog({ kind: 'editor', mode: rows.length === 1 ? 'edit' : 'mass', selected: rows }); }}><Settings2 size={26} aria-hidden="true"/>Mass Edit Instrument</Button>
      <Button id="datamanager-instruments-delete" className="action-delete" disabled title="Instrument deletion is not implemented"><Trash2 size={26} aria-hidden="true"/>Mass Delete</Button>
      <Button id="datamanager-instruments-save" className="action-save" onClick={() => { const rows = requireInstruments(); if (rows) setInstrumentDialog({ kind: 'transfer', mode: 'save', selected: rows }); }}><Save size={26} aria-hidden="true"/>Save</Button>
      <Button id="datamanager-instruments-load" className="action-load" disabled title="Instrument import is not implemented"><FolderOpen size={26} aria-hidden="true"/>Load</Button>
    </div>}
    {tab === 'Sessions' && <div className="management-actions" aria-label="Session operations">
      <Button className="action-add" onClick={()=>{setSessionError('');setSessionDialog({kind:'editor',mode:'add'});}}><CalendarPlus size={26} aria-hidden="true"/>Add Session</Button>
      <Button className="action-clone" onClick={()=>{const rows=requireSessions();if(rows)setSessionDialog({kind:'clone',source:rows[0]});}}><CopyPlus size={26} aria-hidden="true"/>Clone Session</Button>
      <Button className="action-delete" onClick={()=>{const rows=requireSessions();if(rows)openSessionDelete(rows);}}><Trash2 size={26} aria-hidden="true"/>Mass Delete</Button>
      <Button className="action-save" onClick={()=>{const rows=requireSessions();if(rows)setSessionDialog({kind:'transfer',mode:'save',selected:rows});}}><Save size={26} aria-hidden="true"/>Save</Button>
      <Button className="action-load" onClick={()=>setSessionDialog({kind:'transfer',mode:'load',selected:[]})}><FolderOpen size={26} aria-hidden="true"/>Load</Button>
      <Button id="datamanager-session-import-ninja-trader" className="action-import-nt" onClick={()=>setSessionDialog({kind:'import-nt'})}><Download size={26} aria-hidden="true"/>Import NinjaTrader sessions</Button>
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
      <Button className="action-save" onClick={() => { const rows=requireStockGroups(); if(rows){downloadTextFile('Groups.xml',serializeStockGroupsXml(rows));notify('Groups saved.');} }}><Save size={26} aria-hidden="true"/>Save</Button>
      <Button className="action-load" onClick={() => setStockGroupDialog({kind:'load'})}><FolderOpen size={26} aria-hidden="true"/>Load</Button>
    </div>}
    {tab === 'Broker profiles' && <div className="management-actions broker-actions" aria-label="Broker profile operations">
      <Button className="action-add" onClick={()=>setBrokerDialog({kind:'editor',mode:'add'})}><CirclePlus size={26} aria-hidden="true"/>Add new</Button>
      <Button className="action-clone" onClick={()=>{const rows=requireBrokers();if(rows)updateBrokers(rows);}}><RefreshCw size={26} aria-hidden="true"/>Update data for broker (automatic)</Button>
      <Button className="action-edit" onClick={()=>setBrokerDialog({kind:'import',recordType:'instrument'})}><FileInput size={26} aria-hidden="true"/>Import broker instruments from MT4/MT5</Button>
      <Button className="action-load" onClick={()=>setBrokerDialog({kind:'import',recordType:'session'})}><CalendarPlus size={26} aria-hidden="true"/>Import broker sessions from MT4/MT5</Button>
      <Button className="action-edit" onClick={()=>{const rows=requireBrokers();if(!rows)return;const row=rows[0];if(!row.stockPickerUse){setSelectionMessage("This broker profile can't hold any stocks.");return;}setBrokerDialog({kind:'stocks',source:row});}}><ListPlus size={26} aria-hidden="true"/>Edit stocks</Button>
      <Button className="action-delete" onClick={()=>{const rows=requireBrokers();if(!rows)return;if(rows.some(row=>instrumentRows.some(item=>item.broker===row.id)||sessionRows.some(item=>item.broker===row.id))){setSelectionMessage('You have to select broker which is not used by any instrument or session.');return;}const deletable=rows.filter(row=>!row.system);if(!deletable.length){setSelectionMessage('You have to select some non default broker.');return;}setBrokerDialog({kind:'delete',selected:deletable});}}><Trash2 size={26} aria-hidden="true"/>Mass delete</Button>
      <Button className="action-save" onClick={async ()=>{
        const rows=requireBrokers();
        if(!rows)return;
        const rowsWithStocks = await Promise.all(
          rows.map(async (row) => {
            if (row.stockPickerUse && (!row.stocks || row.stocks.length === 0)) {
              try {
                const fetched = await fetchBrokerStocks(row.id);
                return { ...row, stocks: fetched };
              } catch {
                return row;
              }
            }
            return row;
          })
        );
        downloadTextFile('Brokers.json',serializeBrokersJson(rowsWithStocks));
        notify('Brokers saved.');
      }}><Save size={26} aria-hidden="true"/>Save</Button>
      <Button className="action-load" onClick={()=>setBrokerDialog({kind:'load'})}><FolderOpen size={26} aria-hidden="true"/>Load</Button>
    </div>}
  </div><div className="dm-progress" role="status" aria-label="Data Manager progress"><strong>Progress</strong><ProgressBar value={operationState === 'idle' && providerJob ? providerJob.progress : progress} label={progressText}/><Button disabled={operationState !== 'running' && operationState !== 'paused' && !['running', 'paused'].includes(providerJob?.state ?? '')} onClick={() => { setSelectionMessage(''); if (['running', 'paused'].includes(providerJob?.state ?? '')) providerAction(providerJob?.state === 'paused' ? 'resume' : 'pause'); else setOperationState(current => current === 'paused' ? 'running' : 'paused'); }}>{operationState === 'paused' || providerJob?.state === 'paused' ? 'Resume all' : 'Pause all'}</Button><Button disabled={operationState !== 'running' && operationState !== 'paused' && !['running', 'paused'].includes(providerJob?.state ?? '')} onClick={() => { setSelectionMessage(''); if (providerJob && ['running', 'paused'].includes(providerJob.state)) { providerAction('stop'); return; } setOperationState('cancelled'); notify(`${operationLabel} cancelled`); }}>Stop all</Button></div>
  <div className="dm-body">{workspace ? <DataManagerDock layout={workspace} activeId={panelForTab[tab]} activation={dockActivation} chartRequest={chartRequest} arrangeRequest={arrangeRequest} renderPanel={renderPanel} onActivate={id => setTab(current => id === 'data' && ['Export', 'Tools'].includes(current) ? current : labelForPanel[id])} /> : <div className="dm-workspace-feedback">{workspaceError ? <><p role="alert">{workspaceError}</p><Button onClick={() => retryWorkspace(value => value + 1)}>Retry workspace</Button></> : <p role="status">{hostStatus === 'online' ? 'Loading Data Manager workspace…' : 'Connect to the host to open Data Manager.'}</p>}</div>}</div>
  {dialog?.id === 'dukascopy-information' && <DisclaimerPopup onClose={closeDialog}/>}
  <AddPopup open={dialog?.id === 'dukascopy-add'} onClose={closeDialog} onComplete={message => { notify(message); closeDialog(); }}/>{dialog?.id === 'dukascopy-download' && <ImportPopup targets={downloadTargets} onClose={closeDialog} onStarted={() => { setProgressOwner('download'); setOperationState('idle'); notify('Dukascopy download started (simulation)'); }}/>}
  {dialog?.id === 'darwinex-add' && <DarwinexAddDialog onClose={closeDialog} onStarted={() => { setProgressOwner('darwinex'); setOperationState('idle'); setSelectionMessage(''); }}/> }
  {dialog?.id === 'darwinex-import' && <DarwinexImportDialog onClose={closeDialog} onStarted={() => { setProgressOwner('darwinex'); setOperationState('idle'); setSelectionMessage(''); }}/> }
  {dialog?.id === 'darwinex-download' && <DarwinexDownloadDialog targets={darwinexDownloadTargets} onClose={closeDialog} onStarted={() => { setProgressOwner('darwinex'); setOperationState('idle'); setSelectionMessage(''); }}/> }
  {dialog?.id === 'crypto-add' && dialog.exchange && <CryptoAddDialog key={dialog.exchange} exchangeId={dialog.exchange as CryptoExchangeId} onClose={closeDialog} onStarted={() => { setProgressOwner('crypto'); setOperationState('idle'); setSelectionMessage(''); notify('Crypto symbols are being added (simulation)'); }}/>}
  {dialog?.id === 'crypto-download' && (
    <CryptoDownloadDialog targets={cryptoDownloadTargets} onClose={closeDialog} onStarted={() => { setProgressOwner('crypto'); setOperationState('idle'); setSelectionMessage(''); notify('Crypto download started (simulation)'); }}/>
  )}
  {dialog?.id === 'yahoo-add' && (
    <YahooAddDialog onClose={closeDialog} onStarted={() => { setProgressOwner('yahoo'); setOperationState('idle'); setSelectionMessage(''); notify('Yahoo symbols are being added (simulation)'); }}/>
  )}
  {dialog?.id === 'yahoo-download' && (
    <YahooDownloadDialog targets={yahooDownloadTargets} onClose={closeDialog} onStarted={() => { setProgressOwner('yahoo'); setOperationState('idle'); setSelectionMessage(''); notify('Yahoo download started (simulation)'); }}/>
  )}
  {dialog?.id === 'mt5-import' && (
    <Mt5ImportDialog onClose={closeDialog} onStarted={() => { setProgressOwner('mt5'); setOperationState('idle'); setSelectionMessage(''); notify('MT5 import started (simulation)'); }}/>
  )}
  {dialog?.id === 'sq-equity-find' && <SQEquityAddPopup onClose={closeDialog} onStarted={() => { setProgressOwner('sq'); setOperationState('idle'); setSelectionMessage(''); }}/>}
  {dialog?.id === 'sq-futures-find' && <SQFuturesAddPopup onClose={closeDialog} onStarted={() => { setProgressOwner('sq'); setOperationState('idle'); setSelectionMessage(''); }}/>}
  {dialog?.id === 'tickdownloader-import' && <TickDownloaderImportDialog onClose={closeDialog} onStarted={() => { setProgressOwner('td'); setOperationState('idle'); notify('TickDownloader import started (simulation)'); }}/>}
  {dialog?.id === 'file-add' && <FileSymbolDialog onClose={closeDialog} onSaved={() => notify('File symbol added')}/>}
  {dialog?.id === 'file-import' && fileTarget && <FileImportDialog target={fileTarget} onClose={closeDialog} onStarted={() => { setProgressOwner('file'); setOperationState('idle'); }}/>}
  {dialog?.id === 'file-mass-import' && <FileMassImportDialog onClose={closeDialog} onStarted={() => { setProgressOwner('file'); setOperationState('idle'); }}/>}
  {exportDialog?.kind === 'csv' && <CsvExportDialog targets={exportDialog.targets} externalActive={externalActive} onClose={() => setExportDialog(null)} onStarted={() => { setProgressOwner('export'); setOperationState('idle'); setSelectionMessage(''); notify('CSV export started (simulation)'); }}/>}
  {exportDialog?.kind === 'mt4' && <Mt4ExportDialog target={exportDialog.targets[0]} externalActive={externalActive} onClose={() => setExportDialog(null)} onStarted={() => { setProgressOwner('export'); setOperationState('idle'); setSelectionMessage(''); notify('MT4 mock export started'); }}/>}
  {exportDialog?.kind === 'mt5' && <Mt5ExportDialog target={exportDialog.targets[0]} externalActive={externalActive} onClose={() => setExportDialog(null)} onStarted={() => { setProgressOwner('export'); setOperationState('idle'); setSelectionMessage(''); notify('MT5 export started (simulation)'); }}/>}
  {cloneTargets && (
    <CloneTimezoneDialog targets={cloneTargets} existingNames={toolRows.map(row => row.symbol)} externalActive={otherDataActive} onClose={() => setCloneTargets(null)} onStarted={() => { setProgressOwner('tools'); setOperationState('idle'); setSelectionMessage(''); notify('Clone to timezone started (simulation)'); }}/>
  )}
  {reviewTarget && (
    <ViewAnalyzeDialog target={reviewTarget} externalActive={otherDataActive || toolsActive(tools.job?.state)} onClose={() => setReviewTarget(null)}/>
  )}
  {instrumentDialog?.kind === 'editor' && (
    <InstrumentsModal mode={instrumentDialog.mode} selected={instrumentDialog.selected} brokers={instrumentBrokers} onClose={() => setInstrumentDialog(null)} onSaved={message => notify(message)}/>
  )}
  {instrumentDialog?.kind === 'clone' && (
    <InstrumentsModal mode="clone" selected={[instrumentDialog.source]} brokers={instrumentBrokers} onClose={() => setInstrumentDialog(null)} onSaved={message => notify(message)}/>
  )}
  {instrumentDialog?.kind === 'transfer' && (
    <InstrumentTransferDialog mode={instrumentDialog.mode} selected={instrumentDialog.selected} all={instrumentRows} brokers={instrumentBrokers} onClose={() => setInstrumentDialog(null)} onSaved={message => notify(message)}/>
  )}
  {sessionDialog?.kind==='editor'&&<SessionTemplateDialog mode={sessionDialog.mode} source={sessionDialog.source} brokers={sessionBrokers} onClose={()=>setSessionDialog(null)} onSaved={message=>notify(message)}/>}
  {sessionDialog?.kind==='clone'&&<CloneSessionDialog source={sessionDialog.source} brokers={sessionBrokers} onClose={()=>setSessionDialog(null)} onSaved={message=>notify(message)}/>}
  {sessionDialog?.kind==='transfer'&&<SessionTransferDialog mode={sessionDialog.mode} selected={sessionDialog.selected} all={sessionRows} brokers={sessionBrokers} onClose={()=>setSessionDialog(null)} onSaved={message=>notify(message)}/>}
  {sessionDialog?.kind==='delete'&&<div className="sessions-flow"><Modal title="Removing sessions" width={520} onClose={()=>{setSessionDialog(null);setSessionError('');}} footer={<><Button onClick={()=>{setSessionDialog(null);setSessionError('');}}>No</Button><Button className="primary" onClick={removeSelectedSessions}>Yes</Button></>}>{sessionError&&<p role="alert" className="session-error">{sessionError}</p>}<p>Are you sure you want to remove selected sessions ({sessionDialog.selected.length})?</p></Modal></div>}
  {sessionDialog?.kind==='import-nt'&&<SessionNtImportDialog onClose={()=>setSessionDialog(null)} onSaved={message=>notify(message)}/>}
  {externalDialog?.kind === 'editor' && <ExternalIndicatorEditorDialog mode={externalDialog.mode} source={externalDialog.source} onClose={() => setExternalDialog(null)} onSaved={message => notify(message)}/>}
  {externalDialog?.kind === 'import' && <ExternalIndicatorImportDialog item={externalDialog.source} externalActive={otherProviderActive} onClose={() => setExternalDialog(null)} onStarted={() => { setProgressOwner('external'); setOperationState('idle'); setSelectionMessage(''); notify('Importing indicator data.'); }}/>}
  {externalDialog?.kind === 'recognize' && <ExternalIndicatorRecognizeDialog onClose={() => setExternalDialog(null)} onSaved={message => notify(message)}/>}
  {externalDialog?.kind === 'view' && <ExternalIndicatorViewDialog item={externalDialog.source} onClose={() => setExternalDialog(null)}/>}
  {externalDialog?.kind === 'delete' && <ExternalIndicatorDeleteDialog names={externalDialog.selected.map(item => item.name)} onClose={() => setExternalDialog(null)} onSaved={message => { setSelectedExternalNames([]); notify(message); }}/>}
  {externalDialog?.kind === 'transfer' && <ExternalIndicatorTransferDialog mode={externalDialog.mode} selected={externalDialog.selected} all={externalIndicators.definitions} onClose={() => setExternalDialog(null)} onSaved={message => notify(message)}/>}
  {stockGroupDialog?.kind === 'editor' && <StockGroupEditorDialog mode={stockGroupDialog.mode} source={stockGroupDialog.source} onClose={() => setStockGroupDialog(null)} onSaved={(message,item) => { setSelectedStockGroupIds([item.id]); notify(message); }}/>}
  {stockGroupDialog?.kind === 'stocks' && <StockGroupStocksDialog group={stockGroupDialog.source} onClose={() => setStockGroupDialog(null)} onSaved={message => notify(message)}/>}
  {stockGroupDialog?.kind === 'load' && <StockGroupTransferDialog onClose={() => setStockGroupDialog(null)} onSaved={message => notify(message)}/>}
  {stockGroupDialog?.kind === 'delete' && <div className="stock-groups-flow"><Modal title={stockGroupDialog.selected.length === 1 ? 'Remove group' : 'Remove groups'} width={520} onClose={() => { setStockGroupDialog(null); setStockGroupError(''); }} footer={<><Button onClick={() => { setStockGroupDialog(null); setStockGroupError(''); }}>No</Button><Button className="primary" onClick={() => { try { const ids=stockGroupDialog.selected.map(item=>item.id);useStockGroups.getState().remove(ids);setSelectedStockGroupIds(current=>current.filter(id=>!ids.includes(id)));notify(ids.length===1?'Group removed':'Groups removed');setStockGroupDialog(null);setStockGroupError(''); } catch(cause){setStockGroupError(cause instanceof Error?cause.message:'Unable to remove groups.');} }}>Yes</Button></>}>{stockGroupError&&<p role="alert" className="stock-group-error">{stockGroupError}</p>}<p>Are you sure you want to remove selected groups ({stockGroupDialog.selected.length})?</p></Modal></div>}
  {brokerDialog?.kind==='editor'&&<BrokerProfileEditorDialog mode={brokerDialog.mode} source={brokerDialog.source} canSetStockPicker={!brokerDialog.source?.stocks.length} canSetMt={!brokerDialog.source||(!instrumentRows.some(row=>row.broker===brokerDialog.source!.id)&&!sessionRows.some(row=>row.broker===brokerDialog.source!.id))} canSetTimezone={!brokerDialog.source||(!definitions.some(row=>row.broker===brokerDialog.source!.id)&&!fileDefinitions.some(row=>row.broker===brokerDialog.source!.id))} onClose={()=>setBrokerDialog(null)} onSaved={message=>notify(message)}/>}
  {brokerDialog?.kind==='stocks'&&<BrokerStocksDialog profile={brokerDialog.source} onClose={()=>setBrokerDialog(null)} onSaved={message=>notify(message)}/>}
  {brokerDialog?.kind==='import'&&<BrokerRecordImportDialog kind={brokerDialog.recordType} brokers={brokerProfiles} onClose={()=>setBrokerDialog(null)} onSaved={message=>notify(message)}/>}
  {brokerDialog?.kind==='load'&&<BrokerTransferDialog onClose={()=>setBrokerDialog(null)} onSaved={message=>notify(message)}/>}
  {brokerDialog?.kind==='delete'&&<div className="broker-flow"><Modal title={brokerDialog.selected.length===1?'Remove broker':'Remove brokers'} width={520} onClose={()=>{setBrokerDialog(null);setBrokerError('');}} footer={<><Button onClick={()=>{setBrokerDialog(null);setBrokerError('');}}>No</Button><Button className="primary" onClick={async ()=>{try{const ids=brokerDialog.selected.map(row=>row.id);await useDataManagerStore.getState().removeBrokers(ids);setSelectedBrokerIds(current=>current.filter(id=>!ids.includes(id)));notify(ids.length===1?'Broker removed':'Brokers removed');setBrokerDialog(null);setBrokerError('');}catch(cause){setBrokerError(cause instanceof Error?cause.message:'Unable to remove brokers.');}}}>Yes</Button></>}>{brokerError&&<p className="broker-error" role="alert">{brokerError}</p>}<p>Are you sure you want to remove selected brokers ({brokerDialog.selected.length})?</p></Modal></div>}
  {dialog && !['mt5-import', 'yahoo-add', 'yahoo-download', 'crypto-add', 'crypto-download', 'darwinex-add', 'darwinex-import', 'darwinex-download'].includes(dialog.id) && dialog.id !== 'sq-equity-find' && dialog.id !== 'sq-futures-find' && dialog.id !== 'file-import' && dialog.id !== 'file-mass-import' && dialog.id !== 'file-add' && dialog.id !== 'tickdownloader-import' && dialog.id !== 'dukascopy-information' && dialog.id !== 'dukascopy-add' && dialog.id !== 'dukascopy-download' && <DataSourceDialog state={dialog} selectedCount={dialog.targetIds ? dialog.targetIds.length : selectedDatasetIds.length} selectedIds={dialog.targetIds ?? selectedDatasetIds} onClose={closeDialog} onSecondary={id => setDialog({ id })} onComplete={message => { notify(message); closeDialog(); }}/>}</div>;
}
