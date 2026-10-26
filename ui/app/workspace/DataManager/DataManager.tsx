import { HistoricalSourceDialog } from '../../plugins/data_source/Common/HistoricalSourceDialog';
import { normalizeSource, sourceActive, useHistoricalSources, type SourceRecord } from '../../plugins/data_source/Common/historicalSourceStore';
import { BrokerBulkEditDialog } from '../../plugins/data_source/Catalogs/BrokerProfiles/BrokerBulkEditDialog';
import { saveBrokerCatalog } from '../../plugins/data_source/Catalogs/BrokerProfiles/brokerApiClient';
import { createSymbolDataClient } from '../../plugins/data_source/Common/symbolContract';
import { useHostConnection } from '../../host/HostConnection';
import { DataManagerDock, type WorkspaceArrangeRequest, type WorkspaceArrangement } from './DataManagerDock';
import { DataManagerChart } from './DataManagerChart';
import { fetchWorkspace, openWorkspaceTab, type WorkspaceLayout, type WorkspaceSnapshot, type WorkspaceTabId } from './dataManagerWorkspaceClient';
import { BrokerProfilesTable, StockGroupsTable, ExternalIndicatorsTable, SessionTable, SymbolTable, DatasetTable, getBrokerDisplayName } from './DataManagerPanels';
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
import { seedSymbols, type FileDefinition, type SymbolBroker } from '../../plugins/data_source/FileImport/fileSymbols';
import { AddPopup as FileSymbolDialog } from '../../plugins/data_source/FileImport/add/module';
import { useFileSymbols } from '../../plugins/data_source/FileImport/fileSymbolsStore';
import { useSymbols } from '../../plugins/data_source/Catalogs/Symbols/symbolsStore';
import { SymbolsModal } from '../../plugins/data_source/Catalogs/Symbols/SymbolsModal';
import type { CatalogSymbol } from '../../plugins/data_source/Catalogs/Symbols/symbolsApiClient';
import { SymbolTransferDialog } from '../../plugins/data_source/Catalogs/Symbols/SymbolTransferDialog';
import { SessionsModal } from '../../plugins/data_source/Catalogs/Sessions/SessionsModal';
import { SessionTransferDialog } from '../../plugins/data_source/Catalogs/Sessions/SessionTransferDialog';
import { SessionNtImportDialog } from '../../plugins/data_source/Catalogs/Sessions/SessionNtImportDialog';
import { type SessionBroker, type CatalogSession } from '../../plugins/data_source/Catalogs/Sessions/sessions';
import { useSessions } from '../../plugins/data_source/Catalogs/Sessions/sessionStore';
import { ExternalIndicatorEditorDialog } from '../../plugins/data_source/Indicators/ExternalIndicatorEditorDialog';
import { ExternalIndicatorImportDialog } from '../../plugins/data_source/Indicators/ExternalIndicatorImportDialog';
import { ExternalIndicatorRecognizeDialog } from '../../plugins/data_source/Indicators/ExternalIndicatorRecognizeDialog';
import { ExternalIndicatorViewDialog } from '../../plugins/data_source/Indicators/ExternalIndicatorViewDialog';
import { ExternalIndicatorDeleteDialog } from '../../plugins/data_source/Indicators/ExternalIndicatorDeleteDialog';
import { ExternalIndicatorTransferDialog } from '../../plugins/data_source/Indicators/ExternalIndicatorTransferDialog';
import { activeExternalLines, externalIndicatorTypes, externalTypeLabel, type ExternalIndicatorDefinition } from '../../plugins/data_source/Indicators/externalIndicators';
import { externalJobActive, useExternalIndicators } from '../../plugins/data_source/Indicators/externalIndicatorsStore';
import { updateCotIndicators } from '../../plugins/data_source/Indicators/externalIndicatorsApiClient';
import { StockGroupsModal } from '../../plugins/data_source/Catalogs/StockGroups/StockGroupsModal';
import { StockGroupStocksDialog } from '../../plugins/data_source/Catalogs/StockGroups/StockGroupStocksDialog';
import { StockGroupTransferDialog } from '../../plugins/data_source/Catalogs/StockGroups/StockGroupTransferDialog';
import { summarizeGroup, type StockGroupDefinition } from '../../plugins/data_source/Catalogs/StockGroups/stockGroups';
import { exportStockGroupCatalog } from '../../plugins/data_source/Catalogs/StockGroups/stockGroupApiClient';
import { stockGroupJobActive, useStockGroups } from '../../plugins/data_source/Catalogs/StockGroups/stockGroupsStore';
import { BrokerProfilesModal } from '../../plugins/data_source/Catalogs/BrokerProfiles/BrokerProfilesModal';
import { BrokerStocksDialog } from '../../plugins/data_source/Catalogs/BrokerProfiles/BrokerStocksDialog';
import { BrokerTransferDialog } from '../../plugins/data_source/Catalogs/BrokerProfiles/BrokerTransferDialog';
import { brokerCounts, type BrokerProfile } from '../../plugins/data_source/Catalogs/BrokerProfiles/brokerProfiles';
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
import { clearLogs, fetchLogs, fetchActiveLogs, formatDataLogLine, isErrorLogRecord, subscribeDataLogStream } from './dataManagerLogClient';
import { useCallback, useEffect, useRef, useState, type ComponentType } from 'react';
import {
  Bitcoin, ChartCandlestick, ChevronDown, ChevronRight, CircleDollarSign,
  CirclePlus, Clock, Cloud, CloudDownload, Coins, Database, DollarSign, Download,
  FileInput, FileUp, Files, FileSpreadsheet, FolderInput, FolderOpen, Landmark, ListPlus,
  MonitorDown, Network, Plus, RefreshCw, Save, Search, Server,
  Settings2, Trash2, Globe2, Info, CopyPlus, CalendarPlus, FileSearch,
} from 'lucide-react';

import { useAppStore } from '../../host/store';

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

export const helpTopicForTab: Record<string, string> = { Home: 'overview', 'Data sources': 'data', Export: 'export', Tools: 'data', Symbols: 'symbols', Sessions: 'sessions', 'External indicators': 'custom-data', 'Stock groups': 'stock-groups', 'Broker profiles': 'brokers', Log: 'log', Chart: 'chart' };
export const DEFAULT_DM_TUTORIALS: HelpTutorialItem[] = [
  { id: 'tick-precision-testing', test_id: 'dm-help-openlink-btn', title: 'Test strategies with tick precision', summary: 'Configure tick-level datasets and verify symbol spread rules.', steps: ['Select a tick or M1 dataset in Data sources.', 'Verify point value, tick size, and decimals in Symbols.', 'Export or link the dataset for high-precision evaluation.'] },
  { id: 'platform-data-export', test_id: 'dm-help-openlink-btn-2', title: 'Export data from Data Manager to external trading platforms', summary: 'Generate formatted bar and tick archives for external terminals.', steps: ['Select one or more saved datasets in the Data table.', 'Open the Export ribbon tab and select the target format.', 'Confirm date boundaries and download the exported artifacts.'] },
  { id: 'historical-data-import', test_id: 'dm-help-openlink-btn-3', title: 'Import historical bar and tick data from files', summary: 'Create a file symbol record and parse custom OHLCV CSV files.', steps: ['Add a symbol definition mapped to an existing Symbol.', 'Choose Import data file and verify column and date formatting.', 'Inspect the imported record count and preview bars in Chart.'] },
];
export const fetchDataManagerHelp = async (
  requestedTopic = 'overview',
  options?: Parameters<typeof createSymbolDataClient>[1],
): Promise<HelpGuidePayload> => {
  const client = createSymbolDataClient('/data', options);
  return client.get<HelpGuidePayload>(`/help?topic=${encodeURIComponent(requestedTopic)}`);
};

const tabs = ['Home', 'Data sources', 'Export', 'Tools', 'Symbols', 'Sessions', 'External indicators', 'Stock groups', 'Broker profiles', 'Log', 'Chart'];
const panelForTab: Record<string, WorkspaceTabId> = { Home: 'home', 'Data sources': 'data', Export: 'data', Tools: 'data', Symbols: 'symbols', Sessions: 'sessions', 'External indicators': 'custom-data', 'Stock groups': 'stock-groups', 'Broker profiles': 'brokers', Log: 'log', Chart: 'chart' };
const labelForPanel: Record<WorkspaceTabId, string> = { home: 'Home', data: 'Data sources', symbols: 'Symbols', sessions: 'Sessions', 'custom-data': 'External indicators', 'stock-groups': 'Stock groups', brokers: 'Broker profiles', log: 'Log', chart: 'Chart' };
type OperationState = 'idle' | 'running' | 'paused' | 'completed' | 'cancelled';
interface DialogState { id: DataSourceDialogId; exchange?: string; targetIds?: string[] }
type SymbolDialogState =
  | { kind: 'editor'; mode: 'add' | 'edit' | 'mass'; selected: CatalogSymbol[] }
  | { kind: 'clone'; source: CatalogSymbol }
  | { kind: 'transfer'; mode: 'save' | 'load'; selected: CatalogSymbol[] }
  | { kind: 'delete'; selected: CatalogSymbol[] };
type SessionDialogState =
  | { kind:'editor'; mode:'add'|'edit'; source?:CatalogSession }
  | { kind:'clone'; source:CatalogSession }
  | { kind:'delete'; selected:CatalogSession[] }
  | { kind:'transfer'; mode:'save'|'load'; selected:CatalogSession[] }
  | { kind:'import-nt' };
type ExternalIndicatorDialogState =
  | { kind: 'editor'; mode: 'add' | 'edit'; source?: ExternalIndicatorDefinition }
  | { kind: 'import'; source: ExternalIndicatorDefinition }
  | { kind: 'recognize' }
  | { kind: 'view'; source: ExternalIndicatorDefinition }
  | { kind: 'delete'; selected: ExternalIndicatorDefinition[] }
  | { kind: 'transfer'; mode: 'save' | 'load'; selected: ExternalIndicatorDefinition[] };
type StockGroupDialogState =
  | { kind: 'editor'; mode: 'add'|'edit'; source?: StockGroupDefinition;selected?:StockGroupDefinition[] }
  | { kind: 'stocks'; source: StockGroupDefinition }
  | { kind: 'delete'; selected: StockGroupDefinition[] }
  | { kind: 'load' };
type BrokerDialogState =
  | {kind:'editor';mode:'add'|'edit';source?:BrokerProfile}
  | {kind:'bulk-edit';ids:string[]}
  | {kind:'stocks';source:BrokerProfile}
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
    'new-symbol': 'Add symbol',
    'dukascopy-add': 'Add Dukascopy data', 'dukascopy-download': 'Download Dukascopy data',
    'dukascopy-information': 'Dukascopy data disclaimer', 'tickdownloader-import': 'Import data from TickDownloader',
    'file-add': 'Add symbol', 'file-import': 'Import one data file', 'file-mass-import': 'Import multiple data files',
    'sq-equity-find': 'Find and add Equity data',
    'sq-futures-find': 'Find and add Futures data', 'darwinex-add': 'Add Darwinex Tick Data',
    'darwinex-import': 'Import data from a Darwinex folder', 'darwinex-download': 'Download Darwinex data',
    'crypto-add': `Add ${state.exchange ?? 'crypto'} symbols`, 'crypto-download': 'Download Crypto data',
    'yahoo-add': 'Add Yahoo data', 'yahoo-download': 'Download Yahoo data', 'mt5-import': 'Import data from MT5',
    'mass-delete': 'Delete data', 'save-definitions': 'Save selected dataset definitions',
    'load-definitions': 'Load dataset definitions', 'symbol-identification': 'Identify symbols for imported symbols',
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
    case 'new-symbol':
      content = <div className="form-grid two"><Field label="Symbol symbol"><TextInput placeholder="EURUSD"/></Field><Field label="Symbol type"><Select value="forex" onChange={() => {}}><option value="forex">Forex</option><option value="futures">Futures</option><option value="stocks">Stocks</option><option value="crypto">Crypto</option></Select></Field><Field label="Base currency"><TextInput placeholder="EUR"/></Field><Field label="Quote currency"><TextInput placeholder="USD"/></Field></div>;
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
    case 'symbol-identification':
      content = <><p>Map each provider symbol to an existing symbol or skip it. Automatic guessing is never silently accepted.</p><div className="form-grid two"><Field label="Provider symbol"><TextInput value="EURUSD" readOnly/></Field><Field label="Target symbol"><Select value="EURUSD" onChange={() => {}}><option>EURUSD</option><option>Default symbol</option><option>Skip this symbol</option></Select></Field></div></>;
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
  const brokerLoading = useDataManagerStore(state => state.brokerLoading);
  const brokerLoadError = useDataManagerStore(state => state.brokerError);
  const brokerJob = useDataManagerStore(state => state.brokerJob);
  const download = useDukascopyDownloads();
  const td = useTickDownloader();
  const imports = useFileImports();
  const sq = useSQData();
  const historical = useHistoricalSources();
  const [historicalDialog, setHistoricalDialog] = useState<{provider: string; targets: SourceRecord[]} | null>(null);
  useEffect(() => {
    // Preserve old browser data, but retired simulations must not lock real jobs.
    useDarwinex.setState({job:null}); useCrypto.setState({job:null});
    useYahoo.setState({job:null}); useSQData.setState({job:null}); useMt5Import.setState({job:null});
  }, []);
  useEffect(() => {
    if (!sourceActive(historical.job?.status)) return;
    void useHistoricalSources.getState().poll();
    const timer = window.setInterval(() => void useHistoricalSources.getState().poll(), 1000);
    return () => window.clearInterval(timer);
  }, [historical.job?.job_id, historical.job?.status]);
  const historicalJob = historical.job ? {state: historical.job.status === 'PAUSED' ? 'paused' : ['QUEUED','RUNNING'].includes(historical.job.status) ? 'running' : historical.job.status === 'COMPLETED' ? 'completed' : historical.job.status === 'CANCELLED' ? 'cancelled' : 'failed', progress: historical.job.progress, error: historical.job.error_message ?? undefined} : null;
  const darwinex = useDarwinex();
  const crypto = useCrypto();
  const yahoo = useYahoo();
  const mt5 = useMt5Import();
  const liveSymbols = useSymbols(state => state.symbols);
  const canImportMt5 = useSymbols(state => state.loaded && !state.isSyncing && !state.error && state.symbols.length === 0);
  const fileDefinitions = useFileSymbols(state => state.definitions);
  const customSessions = useSessions(state => state.sessions);
  const exports = useDataExports();
  const tools = useDataTools();
  const externalIndicators = useExternalIndicators();
  const stockGroups = useStockGroups();
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
  const [symbolJob, setSymbolJob] = useState<{ label: string; state: 'running' | 'completed' | 'failed'; progress: number; error?: string } | null>(null);
  const [progressOwner, setProgressOwner] = useState<'market' | 'symbols' | 'download' | 'td' | 'file' | 'sq' | 'darwinex' | 'crypto' | 'yahoo' | 'mt5' | 'export' | 'tools' | 'external' | 'stock-groups' | 'broker'>(() => sourceActive(historical.job?.status) ? 'market' : ['running','paused'].includes(brokerJob?.state??'')?'broker':stockGroupJobActive(stockGroups.job?.state) ? 'stock-groups' : externalJobActive(externalIndicators.job?.state) ? 'external' : toolsActive(tools.job?.state) ? 'tools' : exportActive(exports.job?.state) ? 'export' : mt5Active(mt5.job?.state) ? 'mt5' : yahooActive(yahoo.job?.state) ? 'yahoo' : cryptoActive(crypto.job?.state) ? 'crypto' : darwinexActive(darwinex.job?.state) ? 'darwinex' : sqActive(sq.job?.state) ? 'sq' : activeImport(imports.job?.state) ? 'file' : ['running', 'paused'].includes(download.job?.state ?? '') ? 'download' : activeImport(td.job?.state) ? 'td' : brokerJob?'broker':stockGroups.job ? 'stock-groups' : externalIndicators.job ? 'external' : tools.job ? 'tools' : exports.job ? 'export' : mt5.job ? 'mt5' : yahoo.job ? 'yahoo' : crypto.job ? 'crypto' : darwinex.job ? 'darwinex' : sq.job ? 'sq' : imports.job ? 'file' : td.job ? 'td' : historical.job ? 'market' : 'download');
  const providerJob = progressOwner === 'market' ? historicalJob : progressOwner === 'symbols' ? symbolJob : progressOwner === 'broker'?brokerJob:progressOwner === 'stock-groups' ? stockGroups.job : progressOwner === 'external' ? externalIndicators.job : progressOwner === 'tools' ? tools.job : progressOwner === 'export' ? exports.job : progressOwner === 'mt5' ? mt5.job : progressOwner === 'yahoo' ? yahoo.job : progressOwner === 'crypto' ? crypto.job : progressOwner === 'darwinex' ? darwinex.job : progressOwner === 'sq' ? sq.job : progressOwner === 'file' ? imports.job : progressOwner === 'td' ? td.job : download.job;
  useEffect(() => { if (sq.job?.state !== 'running') return; const timer = window.setInterval(() => useSQData.getState().advance(), 250); return () => window.clearInterval(timer); }, [sq.job?.state]);
  const providerAction = progressOwner === 'market' ? historical.action : progressOwner === 'symbols' ? (() => undefined) : progressOwner === 'broker'?useDataManagerStore.getState().brokerAction:progressOwner === 'stock-groups' ? stockGroups.action : progressOwner === 'external' ? externalIndicators.action : progressOwner === 'tools' ? tools.action : progressOwner === 'export' ? exports.action : progressOwner === 'mt5' ? mt5.action : progressOwner === 'yahoo' ? yahoo.action : progressOwner === 'crypto' ? crypto.action : progressOwner === 'darwinex' ? darwinex.action : progressOwner === 'sq' ? sq.action : progressOwner === 'file' ? imports.action : progressOwner === 'td' ? td.action : download.action;
  useEffect(() => {
    if (td.job?.state !== 'running') return;
    const timer = window.setInterval(() => useTickDownloader.getState().advance(), 250);
    return () => window.clearInterval(timer);
  }, [td.job?.state]);
  useEffect(() => { if (imports.job?.state !== 'running') return; const timer = window.setInterval(() => useFileImports.getState().advance(), 250); return () => window.clearInterval(timer); }, [imports.job?.state]);
  const [downloadTargets, setDownloadTargets] = useState<DownloadTarget[]>([]);
  useEffect(() => {
    if (!['running','paused'].includes(download.job?.state ?? '')) return;
    void useDukascopyDownloads.getState().advance();
    const timer = window.setInterval(() => { void useDukascopyDownloads.getState().advance(); }, 1000);
    return () => window.clearInterval(timer);
  }, [download.job?.state, download.job?.jobId]);
  const [tab, setTab] = useState('Data sources');
  const { status: hostStatus } = useHostConnection();
  useEffect(() => {
    if (hostStatus === 'online') {
      void useStockGroups.getState().syncRemote();
      void useExternalIndicators.getState().syncRemote();
    }
  }, [hostStatus]);

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
  const [symbolDialog, setSymbolDialog] = useState<SymbolDialogState | null>(null);
  const [selectedSymbolIds, setSelectedSymbolIds] = useState<string[]>([]);
  useEffect(() => {
    if (hostStatus !== 'online') { useSymbols.getState().reset(); setSymbolDialog(null); setSelectedSymbolIds([]); return; }
    void useSymbols.getState().refreshFromServer();
    return () => { useSymbols.getState().reset(); };
  }, [hostStatus]);
  useEffect(() => {
    if (hostStatus === 'online' && tab === 'Symbols') void useSymbols.getState().refreshFromServer();
  }, [tab, hostStatus]);
  useEffect(() => { setSelectedSymbolIds(current => current.filter(id => liveSymbols.some(row => row.id === id))); }, [liveSymbols]);
  const [sessionDialog,setSessionDialog]=useState<SessionDialogState|null>(null);
  const [selectedSessionIds,setSelectedSessionIds]=useState<string[]>([]);
  const [sessionError,setSessionError]=useState('');
  const [sessionDeleting,setSessionDeleting]=useState(false);
  const sessionDeleteBusy=useRef(false);
  useEffect(()=>{
    if(hostStatus!=='online'){useSessions.getState().reset();setSessionDialog(null);setSelectedSessionIds([]);return;}
    void useSessions.getState().refreshFromServer();
    return()=>useSessions.getState().reset();
  },[hostStatus]);
  useEffect(()=>{if(hostStatus==='online'&&tab==='Sessions')void useSessions.getState().refreshFromServer();},[hostStatus,tab]);
  useEffect(()=>{setSelectedSessionIds(current=>current.filter(id=>customSessions.some(row=>row.id===id)));},[customSessions]);
  const [externalDialog, setExternalDialog] = useState<ExternalIndicatorDialogState | null>(null);
  const [selectedExternalNames, setSelectedExternalNames] = useState<string[]>([]);
  const [stockGroupDialog, setStockGroupDialog] = useState<StockGroupDialogState | null>(null);
  const [selectedStockGroupIds, setSelectedStockGroupIds] = useState<string[]>([]);
  const [stockGroupError, setStockGroupError] = useState('');
  const [stockGroupDeleting,setStockGroupDeleting]=useState(false);
  const [brokerDialog,setBrokerDialog]=useState<BrokerDialogState|null>(null);
  const [selectedBrokerIds,setSelectedBrokerIds]=useState<string[]>([]);
  const [brokerError,setBrokerError]=useState('');
  const [brokerDeleting,setBrokerDeleting]=useState(false);
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
  const [logError, setLogError] = useState('');
  const logRevision = useRef(0);
  const [activeLogTasks, setActiveLogTasks] = useState<string[]>([]);
  useEffect(() => {
    if (tab !== 'Log' || hostStatus !== 'online') return;
    let disposed = false;
    let pending = false;
    const refresh = async () => {
      if (pending) return;
      pending = true;
      const revision = logRevision.current;
      try {
        const [records, active] = await Promise.all([fetchLogs(1000), fetchActiveLogs()]);
        if (!disposed && revision === logRevision.current) {
          setLogEntries(records.map(formatDataLogLine));
          setActiveLogTasks(active.map(item => `${item.symbol}: ${item.progress ?? 0}% — ${item.message}`));
          setLogError('');
        }
      } catch (error) {
        if (!disposed) setLogError(error instanceof Error ? error.message : 'Unable to load logs.');
      } finally { pending = false; }
    };
    void refresh();
    const timer = setInterval(() => { void refresh(); }, 2000);
    const unsubscribe = subscribeDataLogStream({onEntry: () => { void refresh(); }, onCleared: () => {setLogEntries([]); void refresh();}, onProgress: () => { void refresh(); }});
    return () => { disposed = true; clearInterval(timer); unsubscribe(); };
  }, [tab, hostStatus]);

  const handleClearLog = async () => {
    try {
      await clearLogs();
      logRevision.current++;
      setLogEntries([]);
      setLogError('');
      notify('Logs cleared.');
    } catch (error) {
      setLogError(error instanceof Error ? error.message : 'Unable to clear logs.');
    }
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
  useEffect(() => { if (hostStatus === 'online') void useDataManagerStore.getState().syncBrokers(); }, [hostStatus]);
  useEffect(() => {
    if (providerJob?.state === 'completed') void useDataManagerStore.getState().syncRemoteDatasets();
  }, [providerJob?.state]);

  const startOperation = (label: string) => { if ([td.job?.state, download.job?.state, imports.job?.state, sq.job?.state, darwinex.job?.state, crypto.job?.state, yahoo.job?.state, mt5.job?.state, exports.job?.state, tools.job?.state, externalIndicators.job?.state, stockGroups.job?.state,brokerJob?.state].some(state => state === 'running' || state === 'paused')) { setSelectionMessage('Finish or stop the active data operation first.'); return; } setSelectionMessage(''); setOpenMenu(null); setNestedOpen(false); setOperationLabel(label); setProgress(4); setOperationState('running'); notify(`${label} started`); };
  const runDirectAction = (action: DirectDataSourceAction) => {
    if (sourceActive(historical.job?.status) || activeImport(download.job?.state)) { setSelectionMessage('Finish or stop the active download first.'); return; }
    let rows = savedDatasets ?? [];
    if (action === 'sq-equity-update') rows = rows.filter(row => row.source === 'sq_equity');
    else if (action === 'sq-futures-update') rows = rows.filter(row => row.source === 'sq_futures');
    else if (action === 'update-selected') rows = rows.filter(row => selectedDatasetIds.includes(row.id));
    rows = rows.filter(row => ['dukascopy','darwinex','binance','binance_coinm','binance_usdtm','bitfinex','coinbase','poloniex','yahoo','sq_equity','sq_futures','mt5'].includes(row.source));
    if (!rows.length) { setSelectionMessage('Select saved historical datasets first.'); return; }
    setHistoricalDialog({provider: rows[0].source, targets: rows}); setOpenMenu(null);
  };
  const selectCommand = (command: DataSourceCommand) => {
    if (sourceActive(historical.job?.status) || historical.pending) { setSelectionMessage('Finish or stop the active historical download first.'); setOpenMenu(null); return; }
    const realSources: Record<string,string> = {'darwinex-add':'darwinex','darwinex-import':'darwinex','darwinex-download':'darwinex','yahoo-add':'yahoo','yahoo-download':'yahoo','crypto-add':normalizeSource(command.exchange ?? 'binance'),'crypto-download':'crypto','sq-equity-find':'sq_equity','sq-futures-find':'sq_futures','mt5-import':'mt5'};
    const source = realSources[command.dialog ?? ''];
    if (source) {
      setOpenMenu(null); setNestedOpen(false); setSelectionMessage('');
      if (activeImport(operationState) || activeImport(download.job?.state) || activeImport(imports.job?.state)) { setSelectionMessage('Finish or stop the active data operation first.'); return; }
      const selected = (savedDatasets ?? []).filter(row => selectedDatasetIds.includes(row.id) && (source === 'crypto' ? ['binance','binance_coinm','binance_usdtm','bitfinex','coinbase','poloniex'].includes(row.source) : row.source.toLowerCase() === source));
      if (command.dialog?.endsWith('-download') && !selected.length) { setSelectionMessage('Select saved datasets for this source first.'); return; }
      setHistoricalDialog({provider: source === 'crypto' ? selected[0].source : source, targets: command.dialog?.endsWith('-download') ? selected : []}); return;
    }
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
      const symbolDefinition = seedSymbols.find(item => item.symbol === row.symbol) ?? seedSymbols[0];
      const targetBarType: 'start' | 'end' = row.barType === 'end' ? 'end' : 'start';
      setFileTarget({ ...emptyFileRecord(row.symbol, symbolDefinition, targetBarType), ...row, barType: targetBarType }); setSelectionMessage(''); setDialog({ id: 'file-import' }); return;
    }
    if (command.dialog === 'dukascopy-download') {
      setOpenMenu(null); setNestedOpen(false);
      try {
        let selected = definitions.filter(row => selectedDatasetIds.includes(row.id));
        if (!selected.length) {
          const allDukas = definitions.filter(row => (row.source || '').toLowerCase() === 'dukascopy');
          if (allDukas.length === 1) {
            selected = allDukas;
          }
        }
        const eligible = eligibleTargets(selected, download.job);
        setDownloadTargets(eligible); setSelectionMessage(''); setDialog({ id: 'dukascopy-download' });
      } catch (cause) {
        const msg = cause instanceof Error ? cause.message : 'Unable to select data';
        setSelectionMessage(msg);
        notify(msg);
      }
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
    symbolDefinition: row.symbolDefinition || row.symbol,
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
  const symbolRows = liveSymbols;
  const symbolBrokers: SymbolBroker[] = [
    { id: '-1', name: 'Default', postfix: '', timezone: 'UTC' },
    ...brokerProfiles.filter(profile => profile.mtUse).map(profile => ({ id: profile.id, name: profile.name, postfix: profile.postfix, timezone: profile.timezone })),
  ];
  const sessionBrokers:SessionBroker[]=[{id:'-1',name:'Default',postfix:''},...brokerProfiles.filter(profile=>profile.mtUse).map(profile=>({id:profile.id,name:profile.name,postfix:profile.postfix}))];
  const sessionRows=customSessions;
  const selectedBrokers=brokerProfiles.filter(item=>selectedBrokerIds.includes(item.id));
  const requireBrokers=():BrokerProfile[]|null=>{if(selectedBrokers.length){setSelectionMessage('');return selectedBrokers;}setSelectionMessage('You have to select some broker.');return null;};
  const openBrokerEdit=(profile:BrokerProfile)=>{setSelectedBrokerIds([profile.id]);setBrokerDialog({kind:'editor',mode:'edit',source:profile});};

  const selectedSessions=sessionRows.filter(item=>selectedSessionIds.includes(item.id));
  const requireSessions=():CatalogSession[]|null=>{if(selectedSessions.length){setSelectionMessage('');return selectedSessions;}setSelectionMessage('You have to select some session.');return null;};
  const openSessionEdit=(item:CatalogSession)=>{setSelectedSessionIds([item.id]);setSessionError('');setSessionDialog({kind:'editor',mode:'edit',source:item});};
  const openSessionDelete=(items:CatalogSession[])=>{setSelectedSessionIds(items.map(item=>item.id));setSessionError('');setSessionDialog({kind:'delete',selected:items});};
  const removeSelectedSessions=async()=>{
    if(sessionDialog?.kind!=='delete'||sessionDeleteBusy.current)return;
    sessionDeleteBusy.current=true;setSessionDeleting(true);setSessionError('');
    const epoch=useSessions.getState().epoch;
    try{
      const result=await useSessions.getState().remove(sessionDialog.selected.map(row=>row.id));
      if(epoch!==useSessions.getState().epoch)return;
      setSelectedSessionIds(current=>current.filter(id=>!result.deleted.includes(id)));
      if(result.failed.length){
        setSessionDialog({kind:'delete',selected:sessionDialog.selected.filter(row=>result.failed.includes(row.id))});
        setSessionError(`${result.deleted.length} deleted; ${result.failed.length} could not be deleted. Retry the remaining sessions.`);
      }else{notify(`${result.deleted.length} sessions deleted.`);setSessionDialog(null);}
    }catch(cause){if(epoch===useSessions.getState().epoch)setSessionError(cause instanceof Error?cause.message:'Unable to delete sessions.');}
    finally{sessionDeleteBusy.current=false;setSessionDeleting(false);}
  };
  const selectedExternal = externalIndicators.definitions.filter(item => selectedExternalNames.includes(item.name));
  const requireExternal = (): ExternalIndicatorDefinition[] | null => { if (selectedExternal.length) { setSelectionMessage(''); return selectedExternal; } setSelectionMessage('You have to select at least one indicator.'); return null; };
  const openExternalEdit = (item: ExternalIndicatorDefinition) => { setSelectedExternalNames([item.name]); setSelectionMessage(''); setExternalDialog({ kind: 'editor', mode: 'edit', source: item }); };
  const openExternalDelete = (items: ExternalIndicatorDefinition[]) => { setSelectedExternalNames(items.map(item => item.name)); setSelectionMessage(''); setExternalDialog({ kind: 'delete', selected: items }); };
  const selectedStockGroups = stockGroups.groups.filter(item => selectedStockGroupIds.includes(item.id));
  const requireStockGroups = (): StockGroupDefinition[] | null => { if (selectedStockGroups.length) { setSelectionMessage(''); return selectedStockGroups; } setSelectionMessage('You have to select some group.'); return null; };
  const openStockGroupEdit = (group: StockGroupDefinition) => { setSelectedStockGroupIds([group.id]); if (group.system) { setSelectionMessage("This group can't be edited."); return; } setStockGroupDialog({ kind: 'editor', mode: 'edit', source: group }); };
  const updateStockGroups = async(items:StockGroupDefinition[])=>{try{setProgressOwner('stock-groups');setOperationState('idle');setSelectionMessage('');await useStockGroups.getState().start(items.map(item=>item.id),toolRows.map(row=>row.symbol),anyDataActive);notify('Stock group data update started.');}catch(cause){setSelectionMessage(cause instanceof Error?cause.message:'Unable to update stock groups');}};
  const selectedSymbols = symbolRows.filter(item => selectedSymbolIds.includes(item.id));
  const requireSymbols = (): CatalogSymbol[] | null => {
    if (selectedSymbols.length) { setSelectionMessage(''); return selectedSymbols; }
    setSelectionMessage('You have to select some record.');
    return null;
  };
  const openSymbolEdit = (item: CatalogSymbol) => {
    setSelectedSymbolIds([item.id]);
    setSymbolDialog({ kind: 'editor', mode: 'edit', selected: [item] });
  };
  useEffect(() => {
    if (symbolJob?.state !== 'running') return;
    const timer = window.setInterval(() => setSymbolJob(job => job && job.state === 'running' ? { ...job, progress: Math.min(90, job.progress + 5) } : job), 250);
    return () => window.clearInterval(timer);
  }, [symbolJob?.state]);
  const runSymbolJob = async (label: string, work: () => Promise<string>) => {
    if (symbolJob?.state === 'running') return;
    setSelectionMessage(''); setProgressOwner('symbols'); setSymbolJob({ label, state: 'running', progress: 5 });
    try {
      const message = await work();
      setSymbolJob({ label, state: 'completed', progress: 100 }); notify(message);
    } catch (cause) {
      const error = cause instanceof Error ? cause.message : 'Symbol operation failed.';
      setSymbolJob({ label, state: 'failed', progress: 100, error }); setSelectionMessage(error);
    }
  };
  const refreshSelectedSymbols = () => {
    void useSymbols.getState().refreshFromServer();
  };
  const removeSymbolRows = (rows: CatalogSymbol[]) => void runSymbolJob(`Deleting ${rows.length} symbol${rows.length === 1 ? '' : 's'}`, async () => { const count = await useSymbols.getState().removeSymbols(rows.map(item => item.id)); setSelectedSymbolIds(current => current.filter(id => !rows.some(item => item.id === id))); return `Deleted ${count} symbol${count === 1 ? '' : 's'}.`; });
  const otherProviderActive = activeImport(operationState) || [symbolJob?.state, td.job?.state, download.job?.state, imports.job?.state, sq.job?.state, darwinex.job?.state, crypto.job?.state, yahoo.job?.state, mt5.job?.state, exports.job?.state, tools.job?.state, stockGroups.job?.state,brokerJob?.state].some(activeImport);
  const externalActive = otherProviderActive || externalJobActive(externalIndicators.job?.state);
  const otherDataActive = externalActive || exportActive(exports.job?.state);
  const anyDataActive = otherDataActive || toolsActive(tools.job?.state);
  const openExport = (kind: ExportKind) => { try { if (anyDataActive) throw new Error('Finish or stop the active data operation first.'); const targets = selectExportTargets(exportRows, selectedDatasetIds, kind); setExportDialog({ kind, targets }); setSelectionMessage(''); } catch (cause) { setSelectionMessage(cause instanceof Error ? cause.message : 'Unable to select data for export.'); } };
  const openClone = () => { try { if (anyDataActive) throw new Error('Finish or stop the active data operation first.'); const targets = selectCloneTargets(toolRows, selectedDatasetIds); setCloneTargets(targets); setSelectionMessage(''); } catch (cause) { setSelectionMessage(cause instanceof Error ? cause.message : 'Unable to select data to clone.'); } };
  const openReview = () => { try { if (anyDataActive) throw new Error('Cannot view data while an operation is in progress.'); const target = selectReviewTarget(toolRows, selectedDatasetIds); setReviewTarget(target); setSelectionMessage(''); } catch (cause) { setSelectionMessage(cause instanceof Error ? cause.message : 'Unable to view data.'); } };
  const progressText = selectionMessage || (progressOwner === 'market' ? historical.error : '') || (progressOwner === 'download' ? download.storageError : '') || (operationState === 'idle' ? (providerJob ? `${progressOwner === 'market' ? 'Historical download' : progressOwner === 'symbols' ? symbolJob?.label : progressOwner === 'broker'?'Broker data update':progressOwner === 'stock-groups' ? 'Stock group data update' : progressOwner === 'external' ? `Custom data import for '${externalIndicators.job?.indicator}'` : progressOwner === 'tools' ? 'Clone to timezone' : progressOwner === 'export' ? exports.job?.label : progressOwner === 'mt5' ? 'MT5 mock import' : progressOwner === 'yahoo' ? `Yahoo mock ${yahoo.job?.kind}` : progressOwner === 'crypto' ? `Crypto mock ${crypto.job?.kind}` : progressOwner === 'darwinex' ? `Darwinex mock ${darwinex.job?.kind}` : progressOwner === 'sq' && sq.job ? providerLabel(sq.job.provider) : progressOwner === 'file' ? 'File import' : progressOwner === 'td' ? 'TickDownloader import' : 'Dukascopy download'} ${providerJob.state} ${providerJob.progress}%${providerJob.error ? `: ${providerJob.error}` : progressOwner === 'external' && externalIndicators.job?.state === 'completed' && externalIndicators.job.ignored ? ` — ${externalIndicators.job.ignored} invalid rows ignored` : progressOwner === 'file' && imports.job?.state === 'completed' ? ` — ${imports.job.completed} imported, ${imports.job.skipped} skipped, ${imports.job.tasks.reduce((n, task) => n + task.ignored, 0)} invalid rows ignored` : ''}` : 'No active operations') : operationState === 'paused' ? `${operationLabel} paused at ${progress}%` : operationState === 'cancelled' ? `${operationLabel} cancelled` : operationState === 'completed' ? `${operationLabel} complete` : `${operationLabel}… ${progress}%`);

  const handleDeleteDatasetRow = (id: string) => {
    setSelectedDatasetIds([id]);
    setDialog({ id: 'mass-delete', targetIds: [id] });
  };

  const renderPanel = (id: WorkspaceTabId) => {
    switch (id) {
      case 'chart': return <DataManagerChart snapshot={linkedSnapshot} loading={previewLoading} error={previewError} selectedTime={selectedBarTime} onSelectTime={setSelectedBarTime} onRetry={() => retryPreview(value => value + 1)} />;
      case 'home': return <DataManagerHome onNavigateTab={setTab} onOpenImport={() => { setTab('Data sources'); setDialog({ id: 'file-import' }); }} onOpenDownload={() => { setTab('Data sources'); setDialog({ id: 'dukascopy-download' }); }} />;
      case 'data': return <DatasetTable onActivate={activateDataset} activeDatasetId={activeDatasetId} selectedIds={selectedDatasetIds} onToggle={toggleDataset} onSelect={setSelectedDatasetIds} onDeleteRow={handleDeleteDatasetRow}/>;
      case 'brokers': return <BrokerProfilesTable loading={brokerLoading} error={brokerLoadError} profiles={brokerProfiles} selected={selectedBrokerIds} symbols={symbolRows} sessions={sessionRows} onSelect={setSelectedBrokerIds} onEdit={openBrokerEdit}/>;
      case 'stock-groups': return <StockGroupsTable groups={stockGroups.groups} selected={selectedStockGroupIds} datasets={toolRows} onSelect={setSelectedStockGroupIds} onEdit={openStockGroupEdit} onUpdate={group=>updateStockGroups([group])}/>;
      case 'custom-data': return <ExternalIndicatorsTable rows={externalIndicators.definitions} selected={selectedExternalNames} job={externalIndicators.job} onSelect={setSelectedExternalNames} onEdit={openExternalEdit} onDelete={item => openExternalDelete([item])}/>;
      case 'symbols': return <SymbolTable selected={selectedSymbolIds} onSelect={setSelectedSymbolIds} onEdit={openSymbolEdit} onRefresh={refreshSelectedSymbols} onDelete={item => setSymbolDialog({ kind: 'delete', selected: [item] })} busy={symbolJob?.state === 'running'} />;
      case 'sessions': return <SessionTable rows={sessionRows} selected={selectedSessionIds} onSelect={setSelectedSessionIds} onEdit={openSessionEdit} onDelete={item=>openSessionDelete([item])} brokers={sessionBrokers}/>;
      case 'log': return <main className="dm-log data-manager-log" data-testid="dm-tab-log"><div className="datamanager-help">Here is where you can see the download progress - you can see every symbol / year downloaded by the program.</div><header className="data-manager-log-buttons"><strong className="settings-title">Log</strong><button data-testid="dm-data-log-clear-log-btn" className="clear-log log-clear-button" onClick={handleClearLog}>Clear log</button></header><div className="dm-log-progress" data-testid="dm-log-progress"><ProgressBar value={operationState === 'idle' && providerJob ? providerJob.progress : progress} label={progressText}/></div>{logError && <p role="alert">{logError}</p>}<div aria-label="Active log tasks">{activeLogTasks.map(task => <div key={task}>{task}</div>)}</div><div className="log-container"><div className="dm-log-output log-scroll-content" role="log" aria-label="Data Manager log">{logEntries.map((entry, index) => { const isError = isErrorLogRecord(entry); return <div key={index} className={isError ? 'dm-log-entry log-entry-error' : 'dm-log-entry'} data-error={isError ? 'true' : 'false'}>{entry}</div>; })}</div></div></main>;
    }
  };
  const triggerArrange = (action: WorkspaceArrangement) => { setArrangeOpen(false); setArrangeRequest(current => ({ seq: (current?.seq ?? 0) + 1, action, targetId: panelForTab[tab] })); };
  return <div className="data-manager"><div className="dm-title">Data Manager</div><div className="ribbon-tabs" role="navigation" aria-label="Data Manager workspace navigation">{tabs.map(item => <button key={item} className={tab === item ? 'active' : ''} onClick={() => { setArrangeOpen(false); setTab(item); setDockActivation(value => value + 1); }}>{item}</button>)}<div className="dm-arrange-menu" ref={arrangeRef}><button type="button" className={arrangeOpen ? 'active' : ''} aria-haspopup="menu" aria-expanded={arrangeOpen} onClick={() => setArrangeOpen(value => !value)}>Arrange</button>{arrangeOpen && <div className="dm-arrange-dropdown" role="menu" aria-label="Arrange workspace panel"><button type="button" role="menuitem" onClick={() => triggerArrange('right')}>Move panel right</button><button type="button" role="menuitem" onClick={() => triggerArrange('bottom')}>Move panel below</button><button type="button" role="menuitem" onClick={() => triggerArrange('main')}>Return to main group</button><button type="button" role="menuitem" onClick={() => triggerArrange('close')}>Close panel</button></div>}</div><HelpTooltip title="Data Manager Help" summary="Download, import, and export market data." topic={helpTopicForTab[tab] ?? 'overview'} availableTopics={['overview', 'data', 'import', 'export', 'symbols', 'sessions', 'brokers', 'custom-data', 'stock-groups', 'log', 'chart']} tutorials={DEFAULT_DM_TUTORIALS} loadGuide={fetchDataManagerHelp}/></div><div className="ribbon" ref={ribbonRef}>
    {['Home', 'Log', 'Chart'].includes(tab) && <p className="dm-context-note">{tab === 'Chart' ? 'Select a saved dataset to view its recorded history. Use Arrange to dock or close panels.' : tab === 'Home' ? 'Data Manager overview' : 'Data Manager operation log'}</p>}
    {tab === 'Data sources' && <div className="data-source-ribbon" aria-label="Data source operations"><div className="provider-actions">{dataSourceProviders.map(provider => <ProviderMenu key={provider.id} provider={provider} isOpen={openMenu === provider.id} nestedOpen={nestedOpen && openMenu === provider.id} onToggle={() => { setOpenMenu(current => current === provider.id ? null : provider.id); setNestedOpen(false); }} onToggleNested={() => setNestedOpen(current => !current)} onSelect={command => { setLastControlId(provider.id); selectCommand(command); }}/>)}</div><div className="context-actions">{dataSourceContextActions.map(action => { const Icon = contextIcons[action.id] ?? Database; return <button className={`data-source-button ${action.id === 'mass-delete' ? 'destructive' : ''}`} data-control-id={action.id} key={action.id} title={action.label} onClick={() => { setLastControlId(action.id); if (action.requiresSelection && selectedDatasetIds.length === 0) { setSelectionMessage('Select at least one dataset first'); return; } if (action.action) runDirectAction(action.action); if (action.dialog) setDialog({ id: action.dialog }); }}><Icon size={27}/><span>{action.label}</span></button>; })}</div></div>}
    {tab === 'Export' && <div className="export-actions" aria-label="Data export operations"><Button data-control-id="export-csv" className="export-csv" onClick={() => { setLastControlId('export-csv'); openExport('csv'); }}><FileSpreadsheet size={24} aria-hidden="true"/>Export to CSV</Button><Button data-control-id="export-mt4" className="export-mt4" title="Export to MetaTrader 4 (FXT & HST)" onClick={() => { setLastControlId('export-mt4'); openExport('mt4'); }}><MonitorDown size={24} aria-hidden="true"/>Export MT4 (FXT &amp; HST)</Button><Button data-control-id="export-mt5" className="export-mt5" title="Export to MetaTrader 5 data (99% test)" onClick={() => { setLastControlId('export-mt5'); openExport('mt5'); }}><ChartCandlestick size={24} aria-hidden="true"/>Export to MT5 data (99% test)</Button></div>}
    {tab === 'Tools' && <div className="data-tool-actions" aria-label="Data tools"><Button data-control-id="tool-timezone" className="tool-timezone" onClick={() => { setLastControlId('tool-timezone'); openClone(); }}><span className="timezone-tool-icon" aria-hidden="true"><Globe2 size={26}/><Clock size={13}/></span>Clone to timezone</Button><Button data-control-id="tool-analyze" className="tool-analyze" onClick={() => { setLastControlId('tool-analyze'); openReview(); }}><ChartCandlestick size={26} aria-hidden="true"/>View &amp; Analyze</Button></div>}
    {tab === 'Symbols' && <div className="management-actions" aria-label="Symbol operations">
      <Button id="datamanager-symbols-add" className="action-add" onClick={() => { setSymbolDialog({ kind: 'editor', mode: 'add', selected: [] }); }}><CirclePlus size={26} aria-hidden="true"/>Add Symbol</Button>
      <Button id="datamanager-symbols-clone" className="action-clone" onClick={() => { const rows = requireSymbols(); if (rows?.length === 1) setSymbolDialog({ kind: 'clone', source: rows[0] }); else if (rows) setSelectionMessage('Select exactly one symbol to clone.'); }}><CopyPlus size={26} aria-hidden="true"/>Clone Symbol</Button>
      <Button id="datamanager-symbols-edit" className="action-edit" onClick={() => { const rows = requireSymbols(); if (rows) setSymbolDialog({ kind: 'editor', mode: rows.length === 1 ? 'edit' : 'mass', selected: rows }); }}><Settings2 size={26} aria-hidden="true"/>Mass Edit Symbol</Button>
      <Button id="datamanager-symbols-delete" className="action-delete" disabled={symbolJob?.state === 'running'} onClick={() => { const rows = requireSymbols(); if (rows) setSymbolDialog({ kind: 'delete', selected: rows }); }}><Trash2 size={26} aria-hidden="true"/>Mass Delete</Button>
      <Button id="datamanager-symbols-update" className="action-update" disabled={symbolJob?.state === 'running' || (!selectedSymbolIds.length && !canImportMt5)} onClick={() => { if (canImportMt5) { void runSymbolJob('Importing all MT5 symbols', async () => `Imported ${await useSymbols.getState().updateFromMt5([])} symbols from MT5.`); return; } const rows = requireSymbols(); if (rows) void runSymbolJob(`Updating ${rows.length} symbols from MT5`, async () => `Updated ${await useSymbols.getState().updateFromMt5(rows.map(row => row.id))} symbols from MT5.`); }}><RefreshCw size={26} aria-hidden="true"/>Update from MT5</Button>
      <Button id="datamanager-symbols-save" className="action-save" onClick={() => { setSymbolDialog({ kind: 'transfer', mode: 'save', selected: symbolRows.filter(row => selectedSymbolIds.includes(row.id)) }); }}><Save size={26} aria-hidden="true"/>Save</Button>
      <Button id="datamanager-symbols-load" className="action-load" onClick={() => setSymbolDialog({ kind: 'transfer', mode: 'load', selected: [] })}><FolderOpen size={26} aria-hidden="true"/>Load</Button>
    </div>}
    {tab === 'Sessions' && <div className="management-actions" aria-label="Session operations">
      <Button disabled={selectedSessions.length!==1} onClick={()=>openSessionEdit(selectedSessions[0])}>Edit Session</Button>
      <Button className="action-add" onClick={()=>{setSessionError('');setSessionDialog({kind:'editor',mode:'add'});}}><CalendarPlus size={26} aria-hidden="true"/>Add Session</Button>
      <Button className="action-clone" onClick={()=>{const rows=requireSessions();if(rows)setSessionDialog({kind:'clone',source:rows[0]});}}><CopyPlus size={26} aria-hidden="true"/>Clone Session</Button>
      <Button className="action-delete" onClick={()=>{const rows=requireSessions();if(rows)openSessionDelete(rows);}}><Trash2 size={26} aria-hidden="true"/>Mass Delete</Button>
      <Button className="action-save" onClick={()=>setSessionDialog({kind:'transfer',mode:'save',selected:[]})}><Save size={26} aria-hidden="true"/>Save</Button>
      <Button className="action-load" onClick={()=>setSessionDialog({kind:'transfer',mode:'load',selected:[]})}><FolderOpen size={26} aria-hidden="true"/>Load</Button>
      <Button id="datamanager-session-import-ninja-trader" className="action-import-nt" disabled title="Session import is not implemented"><Download size={26} aria-hidden="true"/>Import NinjaTrader sessions</Button>
    </div>}
    {tab === 'External indicators' && <div className="management-actions" aria-label="External indicator operations">
      <Button className="action-add" onClick={() => setExternalDialog({ kind: 'editor', mode: 'add' })}><CirclePlus size={26} aria-hidden="true"/>Add new</Button>
      <Button className="action-clone" onClick={() => { const rows = requireExternal(); if (rows) setExternalDialog({ kind: 'import', source: rows[0] }); }}><FileInput size={26} aria-hidden="true"/>Import indicator data</Button>
      <Button className="action-edit" onClick={() => setExternalDialog({ kind: 'recognize' })}><FileSearch size={26} aria-hidden="true"/>Recognize from file</Button>
      <Button className="action-edit" onClick={() => { const rows = requireExternal(); if (!rows) return; const hasData = rows[0].records.length > 0 || rows[0].totalDays > 0 || Boolean(rows[0].dateFrom) || Boolean((rows[0] as any).total_records); if (!hasData) { setSelectionMessage(`Custom indicator '${rows[0].name}' doesn't contain any data`); return; } setExternalDialog({ kind: 'view', source: rows[0] }); }}><ChartCandlestick size={26} aria-hidden="true"/>View &amp; Analyze</Button>
      <Button className="action-delete" onClick={() => { const rows = requireExternal(); if (rows) openExternalDelete(rows); }}><Trash2 size={26} aria-hidden="true"/>Mass delete</Button>
      <Button className="action-save" onClick={() => { const rows = requireExternal(); if (rows) setExternalDialog({ kind: 'transfer', mode: 'save', selected: rows }); }}><Save size={26} aria-hidden="true"/>Save</Button>
      <Button className="action-load" onClick={() => setExternalDialog({ kind: 'transfer', mode: 'load', selected: [] })}><FolderOpen size={26} aria-hidden="true"/>Load</Button>
      <Button className="action-refresh" onClick={async () => {
        try {
          notify('Updating COT data...');
          const res = await updateCotIndicators();
          notify(`Updated ${res.updated_count} COT indicators (${res.records} records).`);
          void useExternalIndicators.getState().syncRemote();
        } catch (cause) {
          setSelectionMessage(cause instanceof Error ? cause.message : 'Unable to update COT data.');
        }
      }}><RefreshCw size={26} aria-hidden="true"/>Update COT data</Button>
    </div>}
    {tab === 'Stock groups' && <div className="management-actions" aria-label="Stock group operations">
      <Button className="action-add" onClick={() => setStockGroupDialog({ kind:'editor', mode:'add' })}><CirclePlus size={26} aria-hidden="true"/>Add new</Button>
      <Button className="action-edit" onClick={()=>{const rows=requireStockGroups();if(!rows)return;if(rows.some(row=>row.system)){setSelectionMessage("System stock groups cannot be edited.");return;}setStockGroupDialog({kind:'editor',mode:'edit',source:rows.length===1?rows[0]:undefined,selected:rows.length>1?rows:undefined});}}><Settings2 size={26} aria-hidden="true"/>Edit selected</Button>
      <Button className="action-clone" disabled={stockGroupJobActive(stockGroups.job?.state)} onClick={()=>{const rows=requireStockGroups();if(rows)void updateStockGroups(rows);}}><RefreshCw size={26} aria-hidden="true"/>Update data in group (automatic)</Button>
      <Button className="action-edit" onClick={() => { const rows=requireStockGroups(); if(!rows)return; if(rows[0].system){setSelectionMessage("This group can't be edited.");return;} setStockGroupDialog({kind:'stocks',source:rows[0]}); }}><ListPlus size={26} aria-hidden="true"/>Edit stocks</Button>
      <Button className="action-delete" disabled={stockGroupDeleting} onClick={()=>{const groups=requireStockGroups();if(!groups)return;if(groups.some(group=>group.system)){setSelectionMessage('System stock groups cannot be deleted.');return;}setStockGroupError('');setStockGroupDialog({kind:'delete',selected:groups});}}><Trash2 size={26} aria-hidden="true"/>Mass delete</Button>
      <Button className="action-save" onClick={async()=>{const rows=requireStockGroups();if(!rows)return;try{downloadTextFile('Groups.json',await exportStockGroupCatalog(rows.map(row=>row.id)));notify('Groups saved.');}catch(cause){setSelectionMessage(cause instanceof Error?cause.message:'Unable to save groups');}}}><Save size={26} aria-hidden="true"/>Save</Button>
      <Button className="action-load" onClick={() => setStockGroupDialog({kind:'load'})}><FolderOpen size={26} aria-hidden="true"/>Load</Button>
    </div>}
    {tab === 'Broker profiles' && <div className="management-actions broker-actions" aria-label="Broker profile operations">
      <Button className="action-add" onClick={()=>setBrokerDialog({kind:'editor',mode:'add'})}><CirclePlus size={26} aria-hidden="true"/>Add new</Button>
      <Button className="action-edit" onClick={()=>{const rows=requireBrokers();if(!rows)return;if(rows.length===1)openBrokerEdit(rows[0]);else setBrokerDialog({kind:'bulk-edit',ids:rows.map(row=>row.id)});}}><Settings2 size={26} aria-hidden="true"/>Edit selected</Button>
      <Button className="action-edit" onClick={()=>{const rows=requireBrokers();if(!rows)return;const row=rows[0];if(!row.stockPickerUse){setSelectionMessage("This broker profile can't hold any stocks.");return;}setBrokerDialog({kind:'stocks',source:row});}}><ListPlus size={26} aria-hidden="true"/>Edit stocks</Button>
      <Button className="action-delete" disabled={brokerDeleting} onClick={()=>{const rows=requireBrokers();if(!rows)return;setBrokerError('');setBrokerDialog({kind:'delete',selected:rows});}}><Trash2 size={26} aria-hidden="true"/>Mass delete</Button>
      <Button className="action-save" onClick={async ()=>{
        try {downloadTextFile('Brokers.json',await saveBrokerCatalog());notify('Broker catalog saved.');}
        catch(cause){setSelectionMessage(cause instanceof Error?cause.message:'Unable to save brokers.');}
      }}><Save size={26} aria-hidden="true"/>Save</Button>
      <Button className="action-load" onClick={()=>setBrokerDialog({kind:'load'})}><FolderOpen size={26} aria-hidden="true"/>Load</Button>
    </div>}
  </div><div className="dm-progress" role="status" aria-label="Data Manager progress"><strong>Progress</strong><ProgressBar value={operationState === 'idle' && providerJob ? providerJob.progress : progress} label={progressText}/><Button disabled={(progressOwner==='stock-groups'&&!stockGroups.job?.jobId)||(operationState !== 'running' && operationState !== 'paused' && !['running', 'paused'].includes(providerJob?.state ?? ''))} onClick={() => { setSelectionMessage(''); if (['running', 'paused'].includes(providerJob?.state ?? '')) providerAction(providerJob?.state === 'paused' ? 'resume' : 'pause'); else setOperationState(current => current === 'paused' ? 'running' : 'paused'); }}>{operationState === 'paused' || providerJob?.state === 'paused' ? 'Resume all' : 'Pause all'}</Button><Button disabled={(progressOwner==='stock-groups'&&!stockGroups.job?.jobId)||(operationState !== 'running' && operationState !== 'paused' && !['running', 'paused'].includes(providerJob?.state ?? ''))} onClick={() => { setSelectionMessage(''); if (providerJob && ['running', 'paused'].includes(providerJob.state)) { providerAction('stop'); return; } setOperationState('cancelled'); notify(`${operationLabel} cancelled`); }}>Stop all</Button></div>
  <div className="dm-body">{workspace ? <DataManagerDock layout={workspace} activeId={panelForTab[tab]} activation={dockActivation} chartRequest={chartRequest} arrangeRequest={arrangeRequest} renderPanel={renderPanel} onActivate={id => setTab(current => id === 'data' && ['Export', 'Tools'].includes(current) ? current : labelForPanel[id])} /> : <div className="dm-workspace-feedback">{workspaceError ? <><p role="alert">{workspaceError}</p><Button onClick={() => retryWorkspace(value => value + 1)}>Retry workspace</Button></> : <p role="status">{hostStatus === 'online' ? 'Loading Data Manager workspace…' : 'Connect to the host to open Data Manager.'}</p>}</div>}</div>
  {dialog?.id === 'dukascopy-information' && <DisclaimerPopup onClose={closeDialog}/>}
  {historicalDialog && <HistoricalSourceDialog provider={historicalDialog.provider} targets={historicalDialog.targets} onClose={() => setHistoricalDialog(null)} onStarted={() => { setProgressOwner('market'); setOperationState('idle'); setSelectionMessage(''); }}/>}
  <AddPopup open={dialog?.id === 'dukascopy-add'} onClose={closeDialog} onComplete={message => { notify(message); closeDialog(); }}/>{dialog?.id === 'dukascopy-download' && <ImportPopup targets={downloadTargets} onClose={closeDialog} onStarted={() => { setProgressOwner('download'); setOperationState('idle'); notify('Dukascopy download started'); }}/>}
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
  {symbolDialog?.kind === 'editor' && (
    <SymbolsModal mode={symbolDialog.mode} selected={symbolDialog.selected} brokers={symbolBrokers} onClose={() => setSymbolDialog(null)} onSaved={message => notify(message)}/>
  )}
  {symbolDialog?.kind === 'clone' && (
    <SymbolsModal mode="clone" selected={[symbolDialog.source]} brokers={symbolBrokers} onClose={() => setSymbolDialog(null)} onSaved={message => notify(message)}/>
  )}
  {symbolDialog?.kind === 'delete' && (
    <Modal title="Removing symbols" width={520} onClose={() => setSymbolDialog(null)} footer={<><Button onClick={() => setSymbolDialog(null)}>No</Button><Button className="primary" onClick={() => { const rows = symbolDialog.selected; setSymbolDialog(null); removeSymbolRows(rows); }}>Yes</Button></>}>
      <p>Are you sure you want to remove the selected symbols ({symbolDialog.selected.length})?</p><p>{symbolDialog.selected.slice(0, 10).map(item => item.symbol).join(', ')}{symbolDialog.selected.length > 10 ? '…' : ''}</p>
    </Modal>
  )}
  {symbolDialog?.kind === 'transfer' && (
    <SymbolTransferDialog mode={symbolDialog.mode} selected={symbolDialog.selected} all={symbolRows} brokers={symbolBrokers} onClose={() => setSymbolDialog(null)} onSaved={message => notify(message)}/>
  )}
  {sessionDialog?.kind==='editor'&&<SessionsModal mode={sessionDialog.mode} source={sessionDialog.source} brokers={sessionBrokers} onClose={()=>setSessionDialog(null)} onSaved={message=>notify(message)}/>}
  {sessionDialog?.kind==='clone'&&<SessionsModal mode="clone" source={sessionDialog.source} brokers={sessionBrokers} onClose={()=>setSessionDialog(null)} onSaved={message=>notify(message)}/>}
  {sessionDialog?.kind==='transfer'&&<SessionTransferDialog mode={sessionDialog.mode} selected={sessionDialog.selected} all={sessionRows} brokers={sessionBrokers} onClose={()=>setSessionDialog(null)} onSaved={message=>notify(message)}/>}
  {sessionDialog?.kind==='delete'&&<div className="sessions-flow"><Modal title="Removing sessions" width={520} onClose={()=>{if(!sessionDeleteBusy.current){setSessionDialog(null);setSessionError('');}}} footer={<><Button disabled={sessionDeleting} onClick={()=>{setSessionDialog(null);setSessionError('');}}>No</Button><Button disabled={sessionDeleting} className="primary" onClick={()=>void removeSelectedSessions()}>{sessionDeleting?'Deleting…':'Yes'}</Button></>}>{sessionError&&<p role="alert" className="session-error">{sessionError}</p>}<p>Are you sure you want to remove selected sessions ({sessionDialog.selected.length})?</p></Modal></div>}
  {sessionDialog?.kind==='import-nt'&&<SessionNtImportDialog onClose={()=>setSessionDialog(null)} onSaved={message=>notify(message)}/>}
  {externalDialog?.kind === 'editor' && <ExternalIndicatorEditorDialog mode={externalDialog.mode} source={externalDialog.source} onClose={() => setExternalDialog(null)} onSaved={message => notify(message)}/>}
  {externalDialog?.kind === 'import' && <ExternalIndicatorImportDialog item={externalDialog.source} externalActive={otherProviderActive} onClose={() => setExternalDialog(null)} onStarted={() => { setProgressOwner('external'); setOperationState('idle'); setSelectionMessage(''); notify('Importing indicator data.'); }}/>}
  {externalDialog?.kind === 'recognize' && <ExternalIndicatorRecognizeDialog onClose={() => setExternalDialog(null)} onSaved={message => notify(message)}/>}
  {externalDialog?.kind === 'view' && <ExternalIndicatorViewDialog item={externalDialog.source} onClose={() => setExternalDialog(null)}/>}
  {externalDialog?.kind === 'delete' && <ExternalIndicatorDeleteDialog names={externalDialog.selected.map(item => item.name)} onClose={() => setExternalDialog(null)} onSaved={message => { setSelectedExternalNames([]); notify(message); }}/>}
  {externalDialog?.kind === 'transfer' && <ExternalIndicatorTransferDialog mode={externalDialog.mode} selected={externalDialog.selected} all={externalIndicators.definitions} onClose={() => setExternalDialog(null)} onSaved={message => notify(message)}/>}
  {stockGroupDialog?.kind === 'editor' && <StockGroupsModal mode={stockGroupDialog.mode} source={stockGroupDialog.source} selected={stockGroupDialog.selected} onClose={() => setStockGroupDialog(null)} onSaved={(message,item) => { setSelectedStockGroupIds([item.id]); notify(message); }}/>}
  {stockGroupDialog?.kind === 'stocks' && <StockGroupStocksDialog group={stockGroupDialog.source} onClose={() => setStockGroupDialog(null)} onSaved={message => notify(message)}/>}
  {stockGroupDialog?.kind === 'load' && <StockGroupTransferDialog onClose={() => setStockGroupDialog(null)} onSaved={message => notify(message)}/>}
  {stockGroupDialog?.kind === 'delete' && <div className="stock-groups-flow"><Modal title={stockGroupDialog.selected.length === 1 ? 'Remove group' : 'Remove groups'} width={520} onClose={() => { if(!stockGroupDeleting){setStockGroupDialog(null); setStockGroupError('');} }} footer={<><Button disabled={stockGroupDeleting} onClick={() => { setStockGroupDialog(null); setStockGroupError(''); }}>No</Button><Button className="primary" disabled={stockGroupDeleting} onClick={async () => { if(stockGroupDeleting)return;setStockGroupDeleting(true);setStockGroupError('');try { const ids=stockGroupDialog.selected.map(item=>item.id);await useStockGroups.getState().remove(ids);setSelectedStockGroupIds(current=>current.filter(id=>!ids.includes(id)));notify(ids.length===1?'Group removed':'Groups removed');setStockGroupDialog(null);setStockGroupError(''); } catch(cause){setStockGroupError(cause instanceof Error?cause.message:'Unable to remove groups.');}finally{setStockGroupDeleting(false);} }}>Yes</Button></>}>{stockGroupError&&<p role="alert" className="stock-group-error">{stockGroupError}</p>}<p>Are you sure you want to remove selected groups ({stockGroupDialog.selected.length})? Their full membership history will also be removed. Downloaded data will be kept.</p></Modal></div>}
  {brokerDialog?.kind==='bulk-edit'&&<BrokerBulkEditDialog ids={brokerDialog.ids} onClose={()=>setBrokerDialog(null)} onSaved={message=>notify(message)}/>}
  {brokerDialog?.kind==='editor'&&<BrokerProfilesModal mode={brokerDialog.mode} source={brokerDialog.source} canSetStockPicker={!brokerDialog.source?.stocks.length} canSetMt={!brokerDialog.source||(!symbolRows.some(row=>row.broker===brokerDialog.source!.id)&&!sessionRows.some(row=>row.broker===brokerDialog.source!.id))} canSetTimezone={!brokerDialog.source||(!definitions.some(row=>row.broker===brokerDialog.source!.id)&&!fileDefinitions.some(row=>row.broker===brokerDialog.source!.id))} onClose={()=>setBrokerDialog(null)} onSaved={message=>notify(message)}/>}
  {brokerDialog?.kind==='stocks'&&<BrokerStocksDialog profile={brokerDialog.source} onClose={()=>setBrokerDialog(null)} onSaved={message=>notify(message)}/>}
  {brokerDialog?.kind==='load'&&<BrokerTransferDialog onClose={()=>setBrokerDialog(null)} onSaved={message=>notify(message)}/>}
  {brokerDialog?.kind==='delete'&&<div className="broker-flow"><Modal title={brokerDialog.selected.length===1?'Remove broker':'Remove brokers'} width={520} onClose={()=>{if(!brokerDeleting){setBrokerDialog(null);setBrokerError('');}}} footer={<><Button disabled={brokerDeleting} onClick={()=>{setBrokerDialog(null);setBrokerError('');}}>No</Button><Button className="primary" disabled={brokerDeleting} onClick={async ()=>{if(brokerDeleting)return;setBrokerDeleting(true);setBrokerError('');try{const ids=brokerDialog.selected.map(row=>row.id);await useDataManagerStore.getState().removeBrokers(ids);setSelectedBrokerIds(current=>current.filter(id=>!ids.includes(id)));notify(ids.length===1?'Broker removed':'Brokers removed');setBrokerDialog(null);setBrokerError('');}catch(cause){setBrokerError(cause instanceof Error?cause.message:'Unable to remove brokers.');}finally{setBrokerDeleting(false);}}}>Yes</Button></>}>{brokerError&&<p className="broker-error" role="alert">{brokerError}</p>}<p>Are you sure you want to remove selected brokers ({brokerDialog.selected.length})? Their stock memberships will also be removed. Profiles used by symbols, sessions or saved datasets cannot be removed.</p></Modal></div>}
  {dialog && !['mt5-import', 'yahoo-add', 'yahoo-download', 'crypto-add', 'crypto-download', 'darwinex-add', 'darwinex-import', 'darwinex-download'].includes(dialog.id) && dialog.id !== 'sq-equity-find' && dialog.id !== 'sq-futures-find' && dialog.id !== 'file-import' && dialog.id !== 'file-mass-import' && dialog.id !== 'file-add' && dialog.id !== 'tickdownloader-import' && dialog.id !== 'dukascopy-information' && dialog.id !== 'dukascopy-add' && dialog.id !== 'dukascopy-download' && <DataSourceDialog state={dialog} selectedCount={dialog.targetIds ? dialog.targetIds.length : selectedDatasetIds.length} selectedIds={dialog.targetIds ?? selectedDatasetIds} onClose={closeDialog} onSecondary={id => setDialog({ id })} onComplete={message => { notify(message); closeDialog(); }}/>}</div>;
}
