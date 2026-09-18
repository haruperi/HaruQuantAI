import { useCallback, useEffect, useRef, useState, type ComponentType } from 'react';
import {
  Bitcoin, ChartCandlestick, ChevronDown, ChevronRight, CircleDollarSign,
  CirclePlus, Clock, Cloud, CloudDownload, Coins, Database, DollarSign, Download,
  FileInput, FileUp, Files, FileSpreadsheet, FolderInput, FolderOpen, Landmark, ListPlus,
  MonitorDown, Network, PackageOpen, Plus, RefreshCw, Save, Search, Server,
  Settings2, Trash2, Globe2, Info, CopyPlus, CalendarPlus, FileSearch,
} from 'lucide-react';

import { useAppStore } from '../../app/store';
import { Button, Checkbox, Field, Modal, ProgressBar, Section, Select, TextInput } from '../../components/ui';
import { datasets, instruments } from '../../mocks/fixtures';
import {
  dataSourceContextActions, dataSourceProviders, type DataSourceCommand,
  type DataSourceCommandIcon, type DataSourceDialogId, type DataSourceProvider,
  type DirectDataSourceAction,
} from './dataSourceRibbon';

const tabs = ['Data sources', 'Export', 'Tools', 'Instruments', 'Sessions', 'External indicators', 'Stock groups', 'Broker profiles', 'Log'];
type OperationState = 'idle' | 'running' | 'paused' | 'completed' | 'cancelled';
interface DialogState { id: DataSourceDialogId; exchange?: string }

const providerIcons: Record<string, ComponentType<{ size?: number }>> = {
  dukascopy: Plus, tickdownloader: Download, 'file-import': FileUp,
  'sq-equity': Database, 'sq-futures': Server, darwinex: Cloud, crypto: Coins,
  yahoo: Search, mt5: MonitorDown,
};
const contextIcons: Record<string, ComponentType<{ size?: number }>> = {
  'update-all': RefreshCw, 'update-selected': RefreshCw, 'mass-delete': Trash2,
  'save-definitions': Save, 'load-definitions': FolderOpen,
};
const commandIcons: Record<DataSourceCommandIcon, ComponentType<{ className?: string; size?: number }>> = {
  add: CirclePlus, 'application-import': PackageOpen, binance: Bitcoin,
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

function DataSourceDialog({ state, selectedCount, onClose, onSecondary, onComplete }: {
  state: DialogState; selectedCount: number; onClose: () => void;
  onSecondary: (id: DataSourceDialogId) => void; onComplete: (message: string) => void;
}) {
  const [agreed, setAgreed] = useState(false);
  const [createStockGroup, setCreateStockGroup] = useState(false);
  const titles: Record<DataSourceDialogId, string> = {
    'new-instrument': 'Add instrument',
    'dukascopy-add': 'Add Dukascopy data', 'dukascopy-download': 'Download Dukascopy data',
    'dukascopy-information': 'Dukascopy data usage information', 'tickdownloader-import': 'Import data from TickDownloader',
    'file-add': 'Add data symbol', 'file-import': 'Import one data file', 'file-mass-import': 'Import multiple data files',
    'file-application-import': 'Import application data', 'sq-equity-find': 'Find and add SQ Equity data',
    'sq-futures-find': 'Find and add SQ Futures data', 'darwinex-add': 'Add Darwinex Tick Data',
    'darwinex-import': 'Import data from a Darwinex folder', 'darwinex-download': 'Download Darwinex data',
    'crypto-add': `Add ${state.exchange ?? 'crypto'} symbols`, 'crypto-download': 'Download Crypto data',
    'yahoo-add': 'Add Yahoo data', 'yahoo-download': 'Download Yahoo data', 'mt5-import': 'Import data from MetaTrader 5',
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
    case 'dukascopy-add':
      content = <><div className="form-grid two"><Field label="Show instruments"><Select value="all" onChange={() => {}}><option value="all">All available types</option><option value="forex">Forex</option><option value="cfd">CFD and metals</option></Select></Field><Field label="Search symbols"><TextInput placeholder="EURUSD, GBPJPY"/></Field><Field label="Data precision"><Select value="TICK" onChange={() => {}}><option>TICK</option><option>M1</option></Select></Field><Field label="Broker profile"><Select value="SQ default" onChange={() => {}}><option>SQ default</option><option>Example MT5 broker profile</option></Select></Field><Field label="Data-name postfix"><TextInput placeholder="Optional"/></Field></div><div className="mock-symbol-list"><strong>Available symbols</strong><span>EURUSD · GBPUSD · USDJPY · XAUUSD</span></div><Button onClick={() => onSecondary('instrument-identification')}>Review instrument mappings</Button><MockBoundaryNote/></>;
      break;
    case 'dukascopy-download':
      content = <><DateRangeFields/><ExistingDataPolicy/><Field label="Download mode"><Select value="standard" onChange={() => {}}><option value="standard">Standard provider download</option><option value="accelerated">Accelerated verified download (unavailable in simulation)</option></Select></Field><MockBoundaryNote/></>;
      break;
    case 'dukascopy-information':
      content = <><p>Dukascopy datasets may be configured as Tick or M1 data. Availability, licensing, completeness, and provider uptime are external conditions and are not guaranteed by this application.</p><MockBoundaryNote/></>;
      break;
    case 'tickdownloader-import':
      content = <><Field label="TickDownloader data folder"><input className="file-input compact" type="file" multiple/></Field><div className="mock-symbol-list"><strong>Discovered symbols</strong><span>No folder selected</span></div><Field label="Data-name postfix"><TextInput placeholder="Optional"/></Field><MockBoundaryNote/></>;
      break;
    case 'file-add':
      content = <div className="form-grid two"><Field label="Data symbol"><TextInput placeholder="EURUSD_CUSTOM"/></Field><Field label="Instrument"><Select value="EURUSD" onChange={() => {}}><option>EURUSD</option><option>USDJPY</option><option>Add a new instrument…</option></Select></Field><Field label="Bar timestamp convention"><Select value="start" onChange={() => {}}><option value="start">Timestamp marks start of bar</option><option value="end">Timestamp marks end of bar</option></Select></Field></div>;
      break;
    case 'file-import':
      content = <><Field label="Data file"><input className="file-input compact" type="file" accept=".csv,.tsv,.txt"/></Field><div className="form-grid three"><Field label="Imported timezone"><Select value="UTC" onChange={() => {}}><option>UTC</option><option>Europe/London</option><option>America/New_York</option></Select></Field><Field label="Imported timeframe"><Select value="auto" onChange={() => {}}><option value="auto">Detect automatically</option><option>TICK</option><option>M1</option><option>H1</option><option>D1</option></Select></Field><Field label="Predefined format"><Select value="MetaTrader 4 bars" onChange={() => {}}><option>MetaTrader 4 bars</option><option>Generic OHLCV</option><option>Custom mapping</option></Select></Field><Field label="Skip rows"><TextInput type="number" min="0" defaultValue="0"/></Field><Field label="Skip columns"><TextInput type="number" min="0" defaultValue="0"/></Field><Field label="Separator"><Select value="," onChange={() => {}}><option value=",">Comma</option><option value=";">Semicolon</option><option value="tab">Tab</option></Select></Field><Field label="Date format"><TextInput defaultValue="yyyy.MM.dd"/></Field><Field label="Error handling"><Select value="stop" onChange={() => {}}><option value="stop">Stop on the first invalid row</option><option value="skip">Skip invalid rows and report them</option></Select></Field><Field label="Column mapping"><TextInput defaultValue="Date, Time, Open, High, Low, Close, Volume"/></Field></div><Button onClick={() => onSecondary('data-format-name')}>Save format as…</Button><MockBoundaryNote/></>;
      break;
    case 'file-mass-import':
      content = <><Field label="Source data files"><input className="file-input compact" type="file" multiple accept=".csv,.tsv,.txt"/></Field><div className="form-grid three"><Field label="Imported timezone"><Select value="UTC" onChange={() => {}}><option>UTC</option><option>Europe/London</option></Select></Field><Field label="Imported timeframe"><Select value="M1" onChange={() => {}}><option>M1</option><option>D1</option><option>Detect automatically</option></Select></Field><Field label="Date format"><TextInput defaultValue="yyyy-MM-dd"/></Field><Field label="Existing symbol policy"><Select value="overwrite" onChange={() => {}}><option value="overwrite">Overwrite</option><option value="skip">Skip</option><option value="create">Create a distinct symbol</option></Select></Field><Field label="Bar timestamp convention"><Select value="start" onChange={() => {}}><option value="start">Start of bar</option><option value="end">Timestamp marks end of bar</option></Select></Field><Field label="Data-name postfix"><TextInput placeholder="Optional"/></Field></div><Checkbox label="Create a stock group from imported symbols" checked={createStockGroup} onChange={setCreateStockGroup}/><MockBoundaryNote/></>;
      break;
    case 'file-application-import':
      content = <><Field label="Application data export"><input className="file-input compact" type="file" multiple/></Field><p>Select a contained export created by a supported research-data application. Files are validated before any mock definition is added.</p><MockBoundaryNote/></>;
      break;
    case 'sq-equity-find':
    case 'sq-futures-find':
      content = <><div className="form-grid two"><Field label="Ticker or instrument name"><TextInput placeholder={state.id === 'sq-equity-find' ? 'AAPL or Apple' : 'NQ or Nasdaq futures'}/></Field><Field label="Search scope"><Select value="ticker-and-name" onChange={() => {}}><option value="ticker-and-name">Ticker and name</option><option value="ticker">Ticker only</option><option value="name">Name only</option></Select></Field><Field label="Data-name postfix"><TextInput placeholder="Optional"/></Field><Field label="Bar timestamp convention"><Select value={state.id === 'sq-equity-find' ? 'start' : 'end'} onChange={() => {}}><option value="start">Start of bar</option><option value="end">End of bar</option></Select></Field>{state.id === 'sq-futures-find' && <Field label="Dataset timezone"><Select value="exchange" onChange={() => {}}><option value="exchange">Exchange timezone</option><option value="fixed">Fixed offset</option><option value="named">Named timezone</option></Select></Field>}</div><div className="mock-symbol-list"><strong>Search results</strong><span>Ticker · Name · Exchange · Available range</span></div><Button onClick={() => onSecondary('data-usage-conditions')}>Review data usage conditions</Button><Checkbox label="I agree to the applicable data usage conditions" checked={agreed} onChange={setAgreed}/><MockBoundaryNote/></>;
      break;
    case 'darwinex-add':
      content = <><div className="form-grid two"><Field label="Search available symbols"><TextInput placeholder="EURUSD"/></Field><Field label="Broker profile"><Select value="SQ default" onChange={() => {}}><option>SQ default</option><option>Example MT5 broker profile</option></Select></Field><Field label="Data-name postfix"><TextInput placeholder="Optional"/></Field></div><div className="mock-symbol-list"><strong>Available symbols</strong><span>Symbol · Available data range</span></div><Button onClick={() => onSecondary('instrument-identification')}>Review instrument mappings</Button><MockBoundaryNote/></>;
      break;
    case 'darwinex-import':
      content = <><Field label="Darwinex data folder"><input className="file-input compact" type="file" multiple/></Field><Field label="Data-name postfix"><TextInput placeholder="Optional"/></Field><div className="mock-symbol-list"><strong>Discovered symbols</strong><span>No folder selected</span></div><MockBoundaryNote/></>;
      break;
    case 'darwinex-download':
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
    case 'mt5-import':
      content = <><Field label="MetaTrader 5 source"><Select value="installed" onChange={() => {}}><option value="installed">Most recently used installed terminal</option><option value="portable">Portable installation folder</option></Select></Field><Field label="MT5 installation folder"><input className="file-input compact" type="file" multiple/></Field><Button>Fetch symbols</Button><div className="form-grid two"><Field label="Show instrument types"><Select value="all" onChange={() => {}}><option>All types</option><option>Forex</option><option>Futures</option><option>Stocks</option></Select></Field><Field label="Symbols"><TextInput placeholder="Select fetched symbols"/></Field></div><DateRangeFields/><div className="form-grid two"><Field label="Data precision"><Select value="TICK" onChange={() => {}}><option>TICK</option><option>M1</option></Select></Field><Field label="Broker profile"><Select value="Detected MT5 profile" onChange={() => {}}><option>Detected MT5 profile</option><option>SQ default</option></Select></Field><Field label="Data-name postfix"><TextInput placeholder="Optional"/></Field></div><MockBoundaryNote/></>;
      break;
    case 'mass-delete':
      content = <><p><strong>{selectedCount}</strong> selected dataset{selectedCount === 1 ? '' : 's'} will be affected.</p><Field label="Requested operation"><Select value="remove" onChange={() => {}}><option value="remove">Remove dataset definitions and their mock data</option><option value="clear">Keep definitions and clear their mock data</option></Select></Field><p className="callout">A dependency check is required before this destructive operation can continue.</p></>;
      break;
    case 'save-definitions':
      content = <><p>Export definitions for <strong>{selectedCount}</strong> selected dataset{selectedCount === 1 ? '' : 's'}.</p><Field label="Suggested file name"><TextInput defaultValue="Data.xml"/></Field><MockBoundaryNote/></>;
      break;
    case 'load-definitions':
      content = <><Field label="Dataset definition file"><input className="file-input compact" type="file" accept=".xml"/></Field><p className="callout">The file will be validated for supported schema, contained values, and conflicting identities before any mock definitions are applied.</p><MockBoundaryNote/></>;
      break;
    case 'instrument-identification':
      content = <><p>Map each provider symbol to an existing instrument or skip it. Automatic guessing is never silently accepted.</p><div className="form-grid two"><Field label="Provider symbol"><TextInput value="EURUSD" readOnly/></Field><Field label="Target instrument"><Select value="EURUSD" onChange={() => {}}><option>EURUSD</option><option>SQ default instrument</option><option>Skip this symbol</option></Select></Field></div></>;
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
  const primaryLabel = state.id === 'mass-delete' ? 'Review dependency warning' : state.id === 'save-definitions' ? 'Download XML' : state.id === 'load-definitions' ? 'Validate and load' : state.id === 'dependency-warning' ? 'Confirm simulated deletion' : state.id === 'data-format-name' ? 'Save format' : state.id.includes('download') ? 'Start simulated download' : state.id.includes('import') || state.id === 'mt5-import' ? 'Start simulated import' : 'Save simulated configuration';
  const primaryAction = () => state.id === 'mass-delete' ? onSecondary('dependency-warning') : onComplete(`${titles[state.id]} completed as a simulation`);
  const wide = ['file-import', 'sq-equity-find', 'sq-futures-find', 'mt5-import'].includes(state.id);

  return <Modal title={titles[state.id]} onClose={onClose} width={wide ? 820 : 650} footer={<><Button onClick={onClose}>{informationOnly ? 'Close' : 'Cancel'}</Button>{!informationOnly && <Button className={state.id === 'dependency-warning' ? 'danger' : 'primary'} disabled={agreementRequired && !agreed} onClick={primaryAction}>{primaryLabel}</Button>}</>}>{content}</Modal>;
}

function BrokerProfilesTable() {
  return <main className="full dataset-workspace" aria-label="Broker profiles">
    <div className="dataset-grid broker-profiles-grid"><table className="plain-table" aria-label="Broker profiles">
      <colgroup><col style={{ width:26 }}/><col style={{ width:250 }}/><col/><col style={{ width:100 }}/><col style={{ width:100 }}/><col style={{ width:130 }}/><col style={{ width:150 }}/><col style={{ width:140 }}/></colgroup>
      <thead><tr><th><input type="checkbox" aria-label="Select all broker profiles" disabled/></th>
        {['Name', 'Description', 'Postfix', 'Timezone', 'Customized stocks', 'Customized instruments', 'Customized sessions'].map(column => <th key={column}>{column}</th>)}
      </tr></thead><tbody><tr><td colSpan={8} className="dataset-empty">No broker profiles defined.</td></tr></tbody>
    </table></div>
  </main>;
}

function StockGroupsTable() {
  return <main className="full dataset-workspace" aria-label="Stock groups">
    <div className="dataset-grid stock-groups-grid"><table className="plain-table" aria-label="Stock groups">
      <colgroup><col style={{ width:26 }}/><col style={{ width:250 }}/><col style={{ width:100 }}/><col/><col style={{ width:130 }}/><col style={{ width:130 }}/><col style={{ width:110 }}/><col style={{ width:100 }}/><col style={{ width:100 }}/></colgroup>
      <thead><tr><th><input type="checkbox" aria-label="Select all stock groups" disabled/></th>
        {['Name', 'Count', 'Description', 'Number of symbols', 'Downloaded', 'Ready to use?', 'Data from', 'Data to'].map(column => <th key={column}>{column}</th>)}
      </tr></thead><tbody><tr><td colSpan={9} className="dataset-empty">No stock groups defined.</td></tr></tbody>
    </table></div>
  </main>;
}

function ExternalIndicatorsTable() {
  const [query, setQuery] = useState('');
  return <main className="full dataset-workspace" aria-label="External indicators">
    <div className="dataset-filters">
      <input className="text-input" aria-label="Filter external indicators" placeholder="Filter items" value={query} onChange={event => setQuery(event.target.value)}/>
      <select className="text-input" aria-label="External indicator data type" disabled title="No external indicators defined"><option>All data types</option></select>
      <span role="status">Records: 0</span>
    </div>
    <div className="dataset-grid external-indicators-grid"><table className="plain-table" aria-label="External indicators">
      <colgroup><col style={{ width:26 }}/><col style={{ width:145 }}/><col style={{ width:160 }}/><col style={{ width:160 }}/><col style={{ width:90 }}/><col style={{ width:108 }}/><col style={{ width:108 }}/><col style={{ width:108 }}/><col style={{ width:108 }}/><col/></colgroup>
      <thead><tr><th><input type="checkbox" aria-label="Select all external indicators" disabled/></th>
        {['Name', 'Values', 'Data type', 'Timeframe', 'Date from', 'Date to', 'Total Days', 'Total Records'].map(column => <th key={column}>{column}</th>)}<th aria-label="Unused space"/>
      </tr></thead>
      <tbody><tr><td colSpan={10} className="dataset-empty">No External indicators defined.</td></tr></tbody>
    </table></div>
  </main>;
}

function SessionTable() {
  const [query, setQuery] = useState('');
  const [selected, setSelected] = useState<string[]>([]);
  const sessions = Array.from(new Set(instruments.map(item => item.session)));
  const rows = sessions.filter(name => name.toLowerCase().includes(query.toLowerCase()))
    .sort((a, b) => a.localeCompare(b));
  const allSelected = rows.length > 0 && rows.every(name => selected.includes(name));
  return <main className="full dataset-workspace" aria-label="Sessions">
    <div className="dataset-filters">
      <input className="text-input" aria-label="Filter sessions" placeholder="Filter items" value={query} onChange={event => setQuery(event.target.value)}/>
      <select className="text-input" aria-label="Session broker profile" disabled title="No broker profiles assigned"><option>All broker profiles</option></select>
    </div>
    <div className="dataset-grid session-grid"><table className="plain-table session-table" aria-label="Sessions">
      <colgroup><col style={{ width: 26 }}/><col style={{ width: 500 }}/><col style={{ width: 150 }}/><col/><col style={{ width: 26 }}/></colgroup>
      <thead><tr>
        <th><input type="checkbox" aria-label="Select all visible sessions" checked={allSelected} disabled={!rows.length} onChange={() => setSelected(current => allSelected ? current.filter(name => !rows.includes(name)) : [...new Set([...current, ...rows])])}/></th>
        <th>Session Name</th><th>Broker profile</th><th aria-label="Unused space"/><th aria-label="Row actions"/>
      </tr></thead>
      <tbody>{rows.map(name => <tr key={name} className={selected.includes(name) ? 'selected' : ''}>
        <td><input type="checkbox" aria-label={`Select session ${name}`} checked={selected.includes(name)} onChange={() => setSelected(current => current.includes(name) ? current.filter(item => item !== name) : [...current, name])}/></td>
        <td>{name}</td><td>—</td><td/>
        <td><button className="instrument-remove" disabled aria-label={`Delete session ${name}`} title="Session deletion is not implemented">×</button></td>
      </tr>)}{!rows.length && <tr><td colSpan={5} className="dataset-empty">No matching sessions.</td></tr>}</tbody>
    </table></div>
  </main>;
}

function InstrumentTable() {
  const [query, setQuery] = useState('');
  const [dataType, setDataType] = useState('');
  const [descending, setDescending] = useState(false);
  const [selected, setSelected] = useState<string[]>([]);
  const rows = instruments.filter(item => (!dataType || item.type === dataType)
    && (item.symbol + ' ' + item.name).toLowerCase().includes(query.toLowerCase()))
    .sort((a, b) => a.symbol.localeCompare(b.symbol) * (descending ? -1 : 1));
  const allSelected = rows.length > 0 && rows.every(item => selected.includes(item.symbol));
  const columns = ['Description', 'Broker profile', 'Point value', 'Pip/Tick size', 'Pip/Tick step',
    'Default spread', 'Default slippage', 'Commissions', 'Swap', 'Data type', 'Order size mult.', 'Order size step'];
  return <main className="full dataset-workspace" aria-label="Instruments">
    <div className="dataset-filters">
      <input className="text-input" aria-label="Filter instruments" placeholder="Filter items" value={query} onChange={event => setQuery(event.target.value)}/>
      <select className="text-input" aria-label="Instrument data type" value={dataType} onChange={event => setDataType(event.target.value)}>
        <option value="">All data types</option>{[...new Set(instruments.map(item => item.type))].map(type => <option key={type}>{type}</option>)}
      </select>
      <select className="text-input" aria-label="Instrument broker profile" disabled title="No broker profiles assigned"><option>All broker profiles</option></select>
    </div>
    <div className="dataset-grid"><table className="plain-table instrument-table" aria-label="Instruments">
      <thead><tr>
        <th><input type="checkbox" aria-label="Select all visible instruments" checked={allSelected} disabled={!rows.length} onChange={() => setSelected(current => allSelected ? current.filter(symbol => !rows.some(item => item.symbol === symbol)) : [...new Set([...current, ...rows.map(item => item.symbol)])])}/></th>
        <th aria-sort={descending ? 'descending' : 'ascending'}><button className="dataset-sort" onClick={() => setDescending(value => !value)}>Instrument <span aria-hidden="true">{descending ? '▾' : '▴'}</span></button></th>
        {columns.map(column => <th key={column}>{column}</th>)}<th aria-label="Row actions"/>
      </tr></thead>
      <tbody>{rows.map(item => <tr key={item.symbol} className={selected.includes(item.symbol) ? 'selected' : ''}>
        <td><input type="checkbox" aria-label={`Select instrument ${item.symbol}`} checked={selected.includes(item.symbol)} onChange={() => setSelected(current => current.includes(item.symbol) ? current.filter(symbol => symbol !== item.symbol) : [...current, item.symbol])}/></td>
        <td><strong>{item.symbol}</strong></td><td title={item.name}>{item.name}</td><td>—</td>
        <td>{item.pointValue.toLocaleString()}</td><td>—</td><td>—</td><td>{item.spread}</td>
        <td>—</td><td>—</td><td>—</td><td>{item.type}</td><td>—</td><td>—</td>
        <td><button className="instrument-remove" disabled aria-label={`Delete instrument ${item.symbol}`} title="Instrument deletion is not implemented">×</button></td>
      </tr>)}{!rows.length && <tr><td colSpan={15} className="dataset-empty">No matching instruments.</td></tr>}</tbody>
    </table></div>
  </main>;
}

function DatasetTable({ selectedIds, onToggle, onSelect }: {
  selectedIds: string[]; onToggle: (id: string) => void; onSelect: (ids: string[]) => void;
}) {
  const [query, setQuery] = useState('');
  const [source, setSource] = useState('');
  const [dataType, setDataType] = useState('');
  const [hiddenIds, setHiddenIds] = useState<string[]>([]);
  const [descending, setDescending] = useState(false);
  const rows = datasets.filter(row => (!source || row.source === source)
    && (!dataType || instruments.find(item => item.symbol === row.symbol)?.type === dataType)
    && (row.symbol + ' ' + row.source).toLowerCase().includes(query.toLowerCase()))
    .sort((a, b) => a.symbol.localeCompare(b.symbol) * (descending ? -1 : 1));
  const allSelected = rows.length > 0 && rows.every(row => selectedIds.includes(row.id));
  const columns = ['Instrument', 'Broker profile', 'Underlying Symbol', 'Timeframe', 'Timezone',
    'Date from', 'Date to', 'Total Days', 'Total Records', 'Source', 'Bar type', 'Data type', 'Hide'];
  return <main className="full dataset-workspace" aria-label="Historical data">
    <div className="dataset-filters">
      <input className="text-input" aria-label="Filter items" placeholder="Filter items" value={query} onChange={event => setQuery(event.target.value)}/>
      <select className="text-input" aria-label="Data source" value={source} onChange={event => setSource(event.target.value)}>
        <option value="">All data sources</option>{[...new Set(datasets.map(row => row.source))].map(value => <option key={value}>{value}</option>)}
      </select>
      <select className="text-input" aria-label="Data type" value={dataType} onChange={event => setDataType(event.target.value)}>
        <option value="">All data types</option>{[...new Set(instruments.map(item => item.type))].map(value => <option key={value}>{value}</option>)}
      </select>
      <select className="text-input" aria-label="Stock group" disabled title="No stock groups configured"><option>By stock group - none</option></select>
      <select className="text-input" aria-label="Broker profile" disabled title="No broker profiles assigned"><option>All broker profiles</option></select>
      <span role="status">Records: {rows.length}</span>
    </div>
    <div className="dataset-grid"><table className="plain-table" aria-label="Historical data">
      <thead><tr>
        <th><input type="checkbox" aria-label="Select all visible datasets" checked={allSelected} disabled={!rows.length} onChange={() => onSelect(allSelected ? selectedIds.filter(id => !rows.some(row => row.id === id)) : [...new Set([...selectedIds, ...rows.map(row => row.id)])])}/></th>
        <th aria-sort={descending ? 'descending' : 'ascending'}><button className="dataset-sort" onClick={() => setDescending(value => !value)}>Symbol Name <span aria-hidden="true">{descending ? '▾' : '▴'}</span></button></th>
        {columns.map(column => <th key={column}>{column}</th>)}
      </tr></thead>
      <tbody>{rows.map(row => {
        const instrument = instruments.find(item => item.symbol === row.symbol);
        const days = Math.floor((Date.parse(row.to) - Date.parse(row.from)) / 86400000) + 1;
        return <tr key={row.id} className={selectedIds.includes(row.id) ? 'selected' : ''}>
          <td><input type="checkbox" aria-label={`Select ${row.symbol}`} checked={selectedIds.includes(row.id)} onChange={() => onToggle(row.id)}/></td>
          <td><strong>{row.symbol}</strong></td><td>{instrument?.symbol ?? '—'}</td><td>—</td><td>—</td>
          <td>{row.timeframe}</td><td>—</td><td>{row.from}</td><td>{row.to}</td><td>{days.toLocaleString()}</td>
          <td>{row.bars.toLocaleString()}</td><td>{row.source}</td><td>—</td><td>{instrument?.type ?? '—'}</td>
          <td><input type="checkbox" aria-label={`Hide ${row.symbol}`} checked={hiddenIds.includes(row.id)} onChange={() => setHiddenIds(current => current.includes(row.id) ? current.filter(id => id !== row.id) : [...current, row.id])}/></td>
        </tr>;
      })}{!rows.length && <tr><td colSpan={15} className="dataset-empty">{datasets.length ? 'No matching data.' : 'No data defined.'}</td></tr>}</tbody>
    </table></div>
  </main>;
}

export function DataManager() {
  const [tab, setTab] = useState('Data sources');
  const [dialog, setDialog] = useState<DialogState | null>(null);
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

  const startOperation = (label: string) => { setSelectionMessage(''); setOpenMenu(null); setNestedOpen(false); setOperationLabel(label); setProgress(4); setOperationState('running'); notify(`${label} queued as a simulation`); };
  const runDirectAction = (action: DirectDataSourceAction) => {
    const labels: Record<DirectDataSourceAction, string> = {
      'sq-equity-update': 'SQ Equity dataset update', 'sq-futures-update': 'SQ Futures dataset update',
      'update-all': 'All eligible dataset updates', 'update-selected': `${selectedDatasetIds.length} selected dataset update${selectedDatasetIds.length === 1 ? '' : 's'}`,
    };
    startOperation(labels[action]);
  };
  const selectCommand = (command: DataSourceCommand) => { setOpenMenu(null); setNestedOpen(false); if (command.action) runDirectAction(command.action); if (command.dialog) setDialog({ id: command.dialog, exchange: command.exchange }); };
  const closeDialog = useCallback(() => {
    setDialog(null);
    setOpenMenu(null);
    setNestedOpen(false);
    if (lastControlId) window.setTimeout(() => document.querySelector<HTMLButtonElement>(`[data-control-id="${lastControlId}"]`)?.focus(), 0);
  }, [lastControlId]);
  const toggleDataset = (id: string) => setSelectedDatasetIds(current => current.includes(id) ? current.filter(item => item !== id) : [...current, id]);
  const progressText = selectionMessage || (operationState === 'idle' ? 'No active operations' : operationState === 'paused' ? `${operationLabel} paused at ${progress}%` : operationState === 'cancelled' ? `${operationLabel} cancelled` : operationState === 'completed' ? `${operationLabel} complete` : `${operationLabel}… ${progress}%`);

  return <div className={`data-manager ${tab === 'Log' ? 'show-log' : ''}`}><div className="dm-title">Data Manager</div><div className="ribbon-tabs">{tabs.map(item => <button key={item} className={tab === item ? 'active' : ''} onClick={() => setTab(item)}>{item}</button>)}</div><div className="ribbon" ref={ribbonRef}>
    {tab === 'Data sources' && <div className="data-source-ribbon" aria-label="Data source operations"><div className="provider-actions">{dataSourceProviders.map(provider => <ProviderMenu key={provider.id} provider={provider} isOpen={openMenu === provider.id} nestedOpen={nestedOpen && openMenu === provider.id} onToggle={() => { setOpenMenu(current => current === provider.id ? null : provider.id); setNestedOpen(false); }} onToggleNested={() => setNestedOpen(current => !current)} onSelect={command => { setLastControlId(provider.id); selectCommand(command); }}/>)}</div><div className="context-actions">{dataSourceContextActions.map(action => { const Icon = contextIcons[action.id] ?? Database; return <button className={`data-source-button ${action.id === 'mass-delete' ? 'destructive' : ''}`} data-control-id={action.id} key={action.id} title={action.label} onClick={() => { setLastControlId(action.id); if (action.requiresSelection && selectedDatasetIds.length === 0) { setSelectionMessage('Select at least one dataset first'); return; } if (action.action) runDirectAction(action.action); if (action.dialog) setDialog({ id: action.dialog }); }}><Icon size={27}/><span>{action.label}</span></button>; })}</div></div>}
    {tab === 'Export' && <div className="export-actions" aria-label="Data export operations"><Button className="export-csv"><FileSpreadsheet size={24} aria-hidden="true"/>Export CSV</Button><Button className="export-mt4" title="Export to MetaTrader 4 (FXT & HST)"><MonitorDown size={24} aria-hidden="true"/>Export MT4 (FXT &amp; HST)</Button><Button className="export-mt5" title="Export to MetaTrader 5"><ChartCandlestick size={24} aria-hidden="true"/>Export MT5</Button></div>}
    {tab === 'Tools' && <div className="data-tool-actions" aria-label="Data tools"><Button className="tool-timezone"><span className="timezone-tool-icon" aria-hidden="true"><Globe2 size={26}/><Clock size={13}/></span>Clone to timezone</Button><Button className="tool-analyze"><ChartCandlestick size={26} aria-hidden="true"/>View &amp; Analyze</Button></div>}
    {tab === 'Instruments' && <div className="management-actions" aria-label="Instrument operations">
      <Button className="action-add" onClick={() => setDialog({ id: 'new-instrument' })}><CirclePlus size={26} aria-hidden="true"/>Add Instrument</Button>
      <Button className="action-clone"><CopyPlus size={26} aria-hidden="true"/>Clone Instrument</Button>
      <Button className="action-edit"><Settings2 size={26} aria-hidden="true"/>Mass Edit Instrument</Button>
      <Button className="action-delete"><Trash2 size={26} aria-hidden="true"/>Mass Delete</Button>
      <Button className="action-save"><Save size={26} aria-hidden="true"/>Save</Button>
      <Button className="action-load"><FolderOpen size={26} aria-hidden="true"/>Load</Button>
    </div>}
    {tab === 'Sessions' && <div className="management-actions" aria-label="Session operations">
      <Button className="action-add"><CalendarPlus size={26} aria-hidden="true"/>Add Session</Button>
      <Button className="action-clone"><CopyPlus size={26} aria-hidden="true"/>Clone Session</Button>
      <Button className="action-delete"><Trash2 size={26} aria-hidden="true"/>Mass Delete</Button>
      <Button className="action-save"><Save size={26} aria-hidden="true"/>Save</Button>
      <Button className="action-load"><FolderOpen size={26} aria-hidden="true"/>Load</Button>
    </div>}
    {tab === 'External indicators' && <div className="management-actions" aria-label="External indicator operations">
      <Button className="action-add"><CirclePlus size={26} aria-hidden="true"/>Add new</Button>
      <Button className="action-clone"><FileInput size={26} aria-hidden="true"/>Import indicator data</Button>
      <Button className="action-edit"><FileSearch size={26} aria-hidden="true"/>Recognize from file</Button>
      <Button className="action-delete"><Trash2 size={26} aria-hidden="true"/>Mass delete</Button>
      <Button className="action-save"><Save size={26} aria-hidden="true"/>Save</Button>
      <Button className="action-load"><FolderOpen size={26} aria-hidden="true"/>Load</Button>
    </div>}
    {tab === 'Stock groups' && <div className="management-actions" aria-label="Stock group operations">
      <Button className="action-add"><CirclePlus size={26} aria-hidden="true"/>Add new</Button>
      <Button className="action-edit"><ListPlus size={26} aria-hidden="true"/>Edit stocks</Button>
      <Button className="action-clone"><RefreshCw size={26} aria-hidden="true"/>Update data in group (automatic)</Button>
      <Button className="action-delete"><Trash2 size={26} aria-hidden="true"/>Mass delete</Button>
      <Button className="action-save"><Save size={26} aria-hidden="true"/>Save</Button>
      <Button className="action-load"><FolderOpen size={26} aria-hidden="true"/>Load</Button>
    </div>}
    {tab === 'Broker profiles' && <div className="management-actions broker-actions" aria-label="Broker profile operations">
      <Button className="action-add"><CirclePlus size={26} aria-hidden="true"/>Add new</Button>
      <Button className="action-clone"><RefreshCw size={26} aria-hidden="true"/>Update data for broker (automatic)</Button>
      <Button className="action-edit"><FileInput size={26} aria-hidden="true"/>Import broker instruments from XML</Button>
      <Button className="action-load"><CalendarPlus size={26} aria-hidden="true"/>Import broker sessions from XML</Button>
      <Button className="action-edit"><ListPlus size={26} aria-hidden="true"/>Edit stocks</Button>
      <Button className="action-delete"><Trash2 size={26} aria-hidden="true"/>Mass delete</Button>
      <Button className="action-save"><Save size={26} aria-hidden="true"/>Save</Button>
      <Button className="action-load"><FolderOpen size={26} aria-hidden="true"/>Load</Button>
    </div>}
  </div><div className="dm-progress"><strong>Progress</strong><ProgressBar value={progress} label={progressText}/><Button disabled={operationState !== 'running' && operationState !== 'paused'} onClick={() => setOperationState(current => current === 'paused' ? 'running' : 'paused')}>{operationState === 'paused' ? 'Resume all' : 'Pause all'}</Button><Button disabled={operationState !== 'running' && operationState !== 'paused'} onClick={() => { setOperationState('cancelled'); notify(`${operationLabel} cancelled`); }}>Stop all</Button></div>
  <div className="dm-body">{tab === 'Log' ? <main className="dm-log"><header><strong>Log</strong><button className="clear-log" onClick={() => setLogEntries([])}>Clear log</button></header><div className="dm-log-output" role="log" aria-label="Data Manager log">{logEntries.map((entry, index) => <div key={index}>{entry}</div>)}</div></main> : ['Data sources', 'Export', 'Tools'].includes(tab) ? <DatasetTable selectedIds={selectedDatasetIds} onToggle={toggleDataset} onSelect={setSelectedDatasetIds}/> : tab === 'Broker profiles' ? <BrokerProfilesTable/> : tab === 'Stock groups' ? <StockGroupsTable/> : tab === 'External indicators' ? <ExternalIndicatorsTable/> : tab === 'Instruments' ? <InstrumentTable/> : tab === 'Sessions' ? <SessionTable/> : <div className="dm-config"><Section title={tab}><div className="cards-list">{Array.from({ length: 6 }, (_, index) => <button key={index}><Database size={22}/><strong>{tab.replace(/s$/, '')} {index + 1}</strong><span>{index % 2 ? 'Configured · mock adapter' : 'Ready for configuration'}</span></button>)}</div></Section></div>}</div>
  {dialog && <DataSourceDialog state={dialog} selectedCount={selectedDatasetIds.length} onClose={closeDialog} onSecondary={id => setDialog({ id })} onComplete={message => { notify(message); closeDialog(); }}/>}</div>;
}
