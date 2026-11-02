import { useHistoricalSources } from './plugins/Common/historicalSourceStore';
import { useSessions } from './plugins/Catalogs/Sessions/sessionStore';
import { useEffect, useState } from 'react';
import { Button, Field, Modal, TextInput } from '../../common/components/ui';
import { brokerCounts, type BrokerProfile } from './plugins/Catalogs/BrokerProfiles/brokerProfiles';
import { type FileSymbol } from './plugins/FileImport/fileSymbols';
import { type SessionDefinition, type CatalogSession, type SessionBroker } from './plugins/Catalogs/Sessions/sessions';
import { summarizeGroup, type StockGroupDefinition } from './plugins/Catalogs/StockGroups/stockGroups';
import { activeExternalLines, externalTypeLabel, externalIndicatorTypes, type ExternalIndicatorDefinition } from './plugins/Indicators/externalIndicators';
import { useExternalIndicators } from './plugins/Indicators/externalIndicatorsStore';
import { normalizeRelativePath, useDataManagerStore, useDukascopyDownloads } from './plugins/Common/dataManagerStore';
import { useFileSymbols } from './plugins/FileImport/fileSymbolsStore';
import { commissionInfo, type CatalogSymbol } from './plugins/Catalogs/Symbols/symbolsApiClient';
import { useSymbols } from './plugins/Catalogs/Symbols/symbolsStore';
import { useFileImports } from './plugins/FileImport/fileImportStore';
import { useSQData } from './plugins/SQData/sqDataStore';
import { useDarwinex } from './plugins/Darwinex/darwinexStore';
import { useCrypto } from './plugins/Crypto/cryptoStore';
import { useYahoo } from './plugins/Yahoo/yahooStore';
import { useMt5Import } from './plugins/MetaTrader/mt5ImportStore';
import { useDataExports } from './plugins/Export/dataExportStore';
import { useDataTools } from './plugins/Tools/dataToolsStore';
import { useStockGroups } from './plugins/Catalogs/StockGroups/stockGroupsStore';

export function BrokerProfilesTable({loading,error,profiles,selected,symbols,sessions,onSelect,onEdit}:{loading:boolean;error:string;profiles:BrokerProfile[];selected:string[];symbols:FileSymbol[];sessions:SessionDefinition[];onSelect:(ids:string[])=>void;onEdit:(profile:BrokerProfile)=>void}) {
  const allSelected=profiles.length>0&&profiles.every(row=>selected.includes(row.id));
  return <main className="full dataset-workspace" aria-label="Broker profiles">
    {loading && <p role="status">Loading broker profiles…</p>}{error && <div role="alert" className="broker-error">{error} <Button disabled={loading} onClick={()=>void useDataManagerStore.getState().syncBrokers()}>Retry broker profiles</Button></div>}
    <div className="dataset-grid broker-profiles-grid"><table className="plain-table" aria-label="Broker profiles">
      <colgroup><col style={{ width:26 }}/><col style={{ width:250 }}/><col/><col style={{ width:100 }}/><col style={{ width:100 }}/><col style={{ width:70 }}/><col style={{ width:130 }}/><col style={{ width:150 }}/><col style={{ width:140 }}/></colgroup>
      <thead><tr><th><input type="checkbox" aria-label="Select all broker profiles" checked={allSelected} disabled={!profiles.length} onChange={()=>onSelect(allSelected?[]:profiles.map(row=>row.id))}/></th>
        {['Name', 'Description', 'Postfix', 'Timezone', 'Enabled', 'Customized stocks', 'Customized symbols', 'Customized sessions'].map(column => <th key={column}>{column}</th>)}
      </tr></thead><tbody>{profiles.map(profile=>{const count=brokerCounts(profile,symbols,sessions);return <tr key={profile.id} className={selected.includes(profile.id)?'selected':''} onDoubleClick={()=>onEdit(profile)}><td><input type="checkbox" aria-label={`Select broker ${profile.name}`} checked={selected.includes(profile.id)} onChange={()=>onSelect(selected.includes(profile.id)?selected.filter(id=>id!==profile.id):[...selected,profile.id])}/></td><td>{profile.name}</td><td>{profile.desc}</td><td>{profile.postfix}</td><td>{profile.timezone}</td><td>{profile.enabled===false?'No':'Yes'}</td><td>{count.stocks}</td><td>{count.symbols}</td><td>{count.sessions}</td></tr>;})}{!profiles.length&&<tr><td colSpan={9} className="dataset-empty">{loading ? 'Loading broker profiles…' : error ? 'Broker profiles could not be loaded.' : 'No brokers are defined.'}</td></tr>}</tbody>
    </table></div>
  </main>;
}

export function StockGroupsTable({ groups, selected, datasets: available, onSelect, onEdit, onUpdate }: { groups: StockGroupDefinition[]; selected: string[]; datasets: { symbol:string; from?:string; to?:string; bars?:number }[]; onSelect:(ids:string[])=>void; onEdit:(group:StockGroupDefinition)=>void; onUpdate:(group:StockGroupDefinition)=>void }) {
  const loading=useStockGroups(state=>state.loading);const loadError=useStockGroups(state=>state.storageError);
  const allSelected = groups.length > 0 && groups.every(group => selected.includes(group.id));
  return <main className="full dataset-workspace" aria-label="Stock groups" aria-busy={loading}>
    {loading&&<p role="status">Loading stock groups…</p>}{loadError&&<p role="alert">{loadError} <Button disabled={loading} onClick={()=>void useStockGroups.getState().syncRemote()}>Retry stock groups</Button></p>}
    <div className="stock-groups-banner">
      Stock groups are - as name suggests - groups of stocks. It can be indexes like S&P500, which consists of 500 stocks, or you can define your own custom group of symbols. They support also complete history of index composition changes, which prevents survivorship bias. Default unmodifiable stock groups are enclosed in double braces [[ ]]. Stock groups must be fully downloaded and updated before they will be available to use.
    </div>
    <div className="dataset-grid stock-groups-grid"><table className="plain-table stock-group-table" aria-label="Stock groups">
      <colgroup><col style={{ width:26 }}/><col style={{ width:250 }}/><col style={{ width:100 }}/><col/><col style={{ width:130 }}/><col style={{ width:130 }}/><col style={{ width:110 }}/><col style={{ width:100 }}/><col style={{ width:100 }}/></colgroup>
      <thead><tr><th><input type="checkbox" aria-label="Select all stock groups" checked={allSelected} disabled={!groups.length} onChange={() => onSelect(allSelected ? [] : groups.map(group => group.id))}/></th>
        {['Name', 'Count', 'Description', 'Number of symbols', 'Downloaded', 'Ready to use?', 'Data from', 'Data to'].map(column => <th key={column}>{column}</th>)}
      </tr></thead><tbody>{groups.map(group => { const summary = summarizeGroup(group, available); return <tr key={group.id} className={selected.includes(group.id) ? 'selected' : ''} onDoubleClick={() => onEdit(group)}><td><input type="checkbox" aria-label={`Select stock group ${group.name}`} checked={selected.includes(group.id)} onChange={() => onSelect(selected.includes(group.id) ? selected.filter(id => id !== group.id) : [...selected, group.id])}/></td><td>{group.name}</td><td>{summary.active} / {summary.total}</td><td>{group.description}</td><td>{summary.numberOfSymbols}</td><td>{summary.downloaded} / {summary.total}</td><td>{summary.ready ? 'Yes' : <Button aria-label={`Update group ${group.name}`} onClick={()=>onUpdate(group)}>No — update data</Button>}</td><td>{summary.from || '-'}</td><td>{summary.to || '-'}</td></tr>; })}{!groups.length && <tr><td colSpan={9} className="dataset-empty">No groups of stocks are defined.</td></tr>}</tbody>
    </table></div>
  </main>;
}

export function ExternalIndicatorsTable({ rows: allRows, selected, job, onSelect, onEdit, onDelete }: { rows: ExternalIndicatorDefinition[]; selected: string[]; job: ReturnType<typeof useExternalIndicators.getState>['job']; onSelect: (names: string[]) => void; onEdit: (item: ExternalIndicatorDefinition) => void; onDelete: (item: ExternalIndicatorDefinition) => void }) {
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
      <tbody>{rows.map(item => <tr key={item.name} className={selected.includes(item.name) ? 'selected' : ''} onDoubleClick={() => onEdit(item)}><td><input type="checkbox" aria-label={`Select indicator ${item.name}`} checked={selected.includes(item.name)} onChange={() => onSelect(selected.includes(item.name) ? selected.filter(name => name !== item.name) : [...selected, item.name])}/></td><td>{item.name}</td><td>{activeExternalLines(item).length}</td><td>{externalTypeLabel(item.type)}</td><td>{item.timeframe || '—'}</td><td>{item.dateFrom || '—'}</td><td>{item.dateTo || '—'}</td><td>{item.totalDays}</td><td>{item.records.length.toLocaleString()}</td><td className="indicator-status" aria-label={`Status for ${item.name}`}>{job?.indicator === item.name ? job.state === 'completed' ? 'Completed' : `${job.state} ${job.progress}%` : ''}</td><td><button className="symbol-remove" aria-label={`Delete indicator ${item.name}`} onClick={() => onDelete(item)}>×</button></td></tr>)}{!rows.length && <tr><td colSpan={11} className="dataset-empty">No External indicators defined.</td></tr>}</tbody>
    </table></div>
  </main>;
}

export function SessionTable({ rows:allRows, selected, onSelect, onEdit, onDelete, brokers }:{rows:CatalogSession[];selected:string[];onSelect:(names:string[])=>void;onEdit:(item:CatalogSession)=>void;onDelete:(item:CatalogSession)=>void;brokers:SessionBroker[]}) {
  const sessionState=useSessions();
  const [query, setQuery] = useState('');
  const [broker,setBroker]=useState('');
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const filtered=allRows.filter(item=>(!broker||item.broker===broker)&&(item.name+' '+item.brokerName).toLowerCase().includes(query.toLowerCase())).sort((a,b)=>a.name.localeCompare(b.name));
  const pages = Math.max(1, Math.ceil(filtered.length / pageSize));
  const currentPage = Math.min(page, pages);
  useEffect(() => setPage(1), [query, broker, pageSize]);
  useEffect(() => setPage(currentPage), [currentPage]);
  const rows = filtered.slice((currentPage - 1) * pageSize, currentPage * pageSize);
  const allSelected = rows.length > 0 && rows.every(item => selected.includes(item.id));
  return <main className="full dataset-workspace" aria-label="Sessions">
    {sessionState.error&&<p role="alert">{sessionState.loaded?'Showing the last server snapshot. ':''}{sessionState.error}</p>}
    {sessionState.isSyncing&&<p role="status">Loading session profiles…</p>}
    <div className="dataset-filters">
      <input className="text-input" aria-label="Filter sessions" placeholder="Filter items" value={query} onChange={event => setQuery(event.target.value)}/>
      <select className="text-input" aria-label="Session broker profile" value={broker} onChange={event=>setBroker(event.target.value)}><option value="">All broker profiles</option>{brokers.map(item=><option value={item.id} key={item.id}>{item.name}</option>)}</select>
      <Button disabled={sessionState.isSyncing} onClick={()=>void sessionState.refreshFromServer()}>Refresh sessions</Button>
    </div>
    <div className="dataset-filters" aria-label="Session pagination">
      <Button disabled={currentPage===1} onClick={()=>setPage(currentPage-1)}>Previous</Button>
      <span>Page {currentPage} of {pages} | {filtered.length} sessions | {selected.length} selected</span>
      <Button disabled={currentPage===pages} onClick={()=>setPage(currentPage+1)}>Next</Button>
      <label>Rows per page <select aria-label="Sessions per page" value={pageSize} onChange={event=>setPageSize(Number(event.target.value))}>{[25,50,100,250].map(size=><option key={size} value={size}>{size}</option>)}</select></label>
    </div>
    <div className="dataset-grid session-grid"><table className="plain-table session-table" aria-label="Sessions">

      <thead><tr>
        <th><input type="checkbox" aria-label="Select all visible sessions" checked={allSelected} disabled={!rows.length} onChange={() => onSelect(allSelected ? selected.filter(name => !rows.some(item=>item.id===name)) : [...new Set([...selected, ...rows.map(item=>item.id)])])}/></th>
        <th>Session Name</th><th>Description</th><th>Timezone</th><th>Intervals</th><th>Holidays</th><th aria-label="Row actions"/>
      </tr></thead>
      <tbody>{rows.map(item => <tr key={item.name} className={selected.includes(item.id) ? 'selected' : ''} onDoubleClick={()=>onEdit(item)}>
        <td><input type="checkbox" aria-label={`Select session ${item.name}`} checked={selected.includes(item.id)} onChange={() => onSelect(selected.includes(item.id) ? selected.filter(name=>name!==item.id) : [...selected,item.id])}/></td>
        <td>{item.name}</td><td>{item.description}</td><td>{item.timezone}</td>
        <td>{item.elements.map((el,index)=><span className="session-calendar-line" key={index}>{el.dayFrom} {el.timeFrom}–{el.dayTo} {el.timeTo}</span>)}</td>
        <td>{item.holidays.map(day=><span className="session-calendar-line" key={day.date_str}>{day.date_str} {day.description}</span>)}</td>
        <td><button className="symbol-remove" aria-label={`Delete session ${item.name}`} onClick={()=>onDelete(item)}>×</button></td>
      </tr>)}{!rows.length && <tr><td colSpan={7} className="dataset-empty">{sessionState.isSyncing ? 'Loading session profiles...' : sessionState.error ? 'Session profiles could not be loaded.' : sessionState.loaded ? 'No matching sessions.' : 'Session profiles have not been loaded.'}</td></tr>}</tbody>
    </table></div>
  </main>;
}

export function SymbolTable({ selected, onSelect, onEdit, onRefresh, onDelete, busy }: {
  onRefresh: () => void; onDelete: (item: CatalogSymbol) => void; busy: boolean;
  selected: string[]; onSelect: (symbols: string[]) => void;
  onEdit: (item: CatalogSymbol) => void;
}) {
  const instState = useSymbols();
  const symbols = instState.symbols;
  const [query, setQuery] = useState('');
  const [dataType, setDataType] = useState('');
  const [broker, setBroker] = useState('');
  const [descending, setDescending] = useState(false);
  const [page, setPage] = useState(1);
  const [pageSize, setPageSize] = useState(50);
  const filteredRows = symbols.filter(item => (!dataType || item.type === dataType)
    && (!broker || item.broker === broker)
    && (item.symbol + ' ' + item.name).toLowerCase().includes(query.toLowerCase()))
    .sort((a, b) => a.symbol.localeCompare(b.symbol) * (descending ? -1 : 1));
  const pages = Math.max(1, Math.ceil(filteredRows.length / pageSize));
  const currentPage = Math.min(page, pages);
  const start = (currentPage - 1) * pageSize;
  const rows = filteredRows.slice(start, start + pageSize);
  const allSelected = rows.length > 0 && rows.every(item => selected.includes(item.id));
  const columns = ['Description', 'Broker profile', 'Point value', 'Pip/Tick size', 'Pip/Tick step', 'Default spread', 'Default slippage', 'Commissions', 'Swap', 'Data type', 'Order size mult.', 'Order size step'];
  return <main className="full dataset-workspace" aria-label="Symbols">
    {instState.error && <p role="alert">{instState.loaded ? 'Showing the last server snapshot. ' : ''}{instState.error}</p>}
    {instState.isSyncing && <p role="status">Loading symbol catalog…</p>}
    <div className="dataset-filters">
      <input className="text-input" aria-label="Filter symbols" placeholder="Filter items" value={query} onChange={event => { setQuery(event.target.value); setPage(1); }}/>
      <select className="text-input" aria-label="Symbol data type" value={dataType} onChange={event => { setDataType(event.target.value); setPage(1); }}>
        <option value="">All data types</option>{[...new Set(symbols.map(item => item.type))].map(type => <option key={type}>{type}</option>)}
      </select>
      <select className="text-input" aria-label="Symbol broker profile" value={broker} onChange={event => { setBroker(event.target.value); setPage(1); }}><option value="">All broker profiles</option>{[...new Map(symbols.map(item => [item.broker, item.brokerName])).entries()].map(([id, name]) => <option value={id} key={id}>{name}</option>)}</select>
      <Button disabled={instState.isSyncing || busy} onClick={onRefresh}>Refresh symbols</Button>
    </div>
    <div className="dataset-filters" aria-label="Symbol pagination">
      <Button disabled={currentPage === 1} onClick={() => setPage(currentPage - 1)}>Previous</Button>
      <span role="status">Page {currentPage} of {pages} | Symbols {filteredRows.length ? start + 1 : 0}-{Math.min(start + pageSize, filteredRows.length)} of {filteredRows.length} | {selected.length} selected</span>
      <Button disabled={currentPage === pages} onClick={() => setPage(currentPage + 1)}>Next</Button>
      <label>Rows per page <select aria-label="Symbols per page" className="text-input" value={pageSize} onChange={event => { setPageSize(Number(event.target.value)); setPage(1); }}>{[25,50,100].map(size => <option key={size} value={size}>{size}</option>)}</select></label>
    </div>
    <div className="dataset-grid"><table className="plain-table symbol-table" aria-label="Symbols">
      <thead><tr>
        <th><input type="checkbox" aria-label="Select all visible symbols" checked={allSelected} disabled={!rows.length} onChange={() => onSelect(allSelected ? selected.filter(symbol => !rows.some(item => item.id === symbol)) : [...new Set([...selected, ...rows.map(item => item.id)])])}/></th>
        <th aria-sort={descending ? 'descending' : 'ascending'}><button className="dataset-sort" onClick={() => setDescending(value => !value)}>Symbol <span aria-hidden="true">{descending ? '▾' : '▴'}</span></button></th>
        {columns.map(column => <th key={column}>{column}</th>)}<th aria-label="Row actions"/>
      </tr></thead>
      <tbody>{rows.map(item => { const commission = commissionInfo(item.record.commissions); return <tr key={item.symbol} className={selected.includes(item.id) ? 'selected' : ''} onDoubleClick={() => onEdit(item)}>
        <td><input type="checkbox" aria-label={`Select symbol ${item.symbol}`} checked={selected.includes(item.id)} onChange={() => onSelect(selected.includes(item.id) ? selected.filter(symbol => symbol !== item.id) : [...selected, item.id])}/></td>
        <td><strong>{item.symbol}</strong></td><td title={item.name}>{item.name}</td><td>{item.brokerName}</td>
        <td>{item.pointValue.toLocaleString()}</td><td>{item.tickSize}</td><td>{item.tickStep}</td><td>{item.spread}</td>
        <td>{item.slippage}</td><td title={commission.details}>{commission.summary}</td><td>{item.record.swap_settings === null ? `${item.record.swap_long} / ${item.record.swap_short}` : item.swap.use ? item.swap.type : "None"}</td><td>{item.type}</td><td>{item.multiplier}</td><td>{item.sizeStep}</td>
        <td><button className="symbol-remove" disabled={busy} aria-label={`Delete symbol ${item.symbol}`} onClick={() => onDelete(item)}>×</button></td>
      </tr>; })}{!rows.length && <tr><td colSpan={15} className="dataset-empty">No matching symbols.</td></tr>}</tbody>
    </table></div>
  </main>;
}

export function getBrokerDisplayName(brokerName: string | undefined, brokerId: string | undefined, brokers: BrokerProfile[]): string {
  const raw = (brokerName || '').trim();
  if (!raw || raw === '-1' || brokerId === '-1') return 'Default';
  if (raw.startsWith('[[') && raw.endsWith(']]')) return raw.slice(2, -2).trim();
  const match = brokers.find(b => b.id === raw || b.id === brokerId);
  if (match) return match.name.replace(/^\[\[/, '').replace(/\]\]$/, '').trim();
  return raw;
}

function formatDateOnly(value: string | undefined): string {
  if (!value) return '—';
  const match = value.match(/^\d{4}-\d{2}-\d{2}/);
  return match ? match[0] : value.split(/[T ]/)[0] || '—';
}

export function DatasetTable({ selectedIds, onToggle, onSelect, onDeleteRow, onActivate, activeDatasetId }: {
  selectedIds: string[]; onToggle: (id: string) => void; onSelect: (ids: string[]) => void;
  onDeleteRow?: (id: string) => void;
  onActivate?: (id: string) => void; activeDatasetId?: string | null;
}) {
  const savedDatasets = useDataManagerStore(state => state.savedDatasets);
  const catalogLoading = useDataManagerStore(state => state.catalogLoading);
  const catalogError = useDataManagerStore(state => state.catalogError);
  const downloadJob = useDukascopyDownloads(state => state.job);
  const historicalJob = useHistoricalSources(state => state.job);
  const imports = useFileImports();
  const sq = useSQData();
  const darwinex = useDarwinex();
  const crypto = useCrypto();
  const yahoo = useYahoo();
  const mt5 = useMt5Import();
  const exports = useDataExports();
  const tools = useDataTools();
  const stockGroups = useStockGroups();
  const [editingDataset,setEditingDataset] = useState<import('./plugins/Common/dataManagerStore').MockDefinition | null>(null);
  const [stockGroup, setStockGroup] = useState('');
  const allDatasets = savedDatasets ?? [];
  const [query, setQuery] = useState('');
  const [source, setSource] = useState('');
  const [dataType, setDataType] = useState('');
  const [brokerFilter,setBrokerFilter]=useState('');
  const [descending, setDescending] = useState(false);
  const rows = allDatasets.filter(row => (!source || row.source === source)
    && (!stockGroup || stockGroups.groups.find(group => group.id === stockGroup)?.members.some(member => member.ticker === row.symbol))
    && (!dataType || row.category === dataType)
    && (!brokerFilter || row.brokerName === brokerFilter)
    && (row.symbol + ' ' + row.source).toLowerCase().includes(query.toLowerCase()))
    .sort((a, b) => a.symbol.localeCompare(b.symbol) * (descending ? -1 : 1));
  const allSelected = rows.length > 0 && rows.every(row => selectedIds.includes(row.id));
  const columns = ['Symbol', 'Broker profile', 'Underlying Symbol', 'Timeframe', 'Timezone',
    'Date from', 'Date to', 'Total Days', 'Total Records', 'Source', 'Bar type', 'Data type', 'Path'];
  return <main className="full dataset-workspace" aria-label="Historical data" aria-busy={catalogLoading}>
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
      <Button disabled={catalogLoading} onClick={() => { void useDataManagerStore.getState().syncRemoteDatasets(); }}>
        {catalogLoading ? 'Loading dataset catalog…' : catalogError ? 'Retry dataset catalog' : 'Refresh dataset catalog'}
      </Button>
    </div>
    {catalogError && <div role="alert" className="callout">Unable to load saved dataset catalog: {catalogError}{savedDatasets !== null && ' Showing the last successful catalog; it may be out of date.'}</div>}
    <div className="dataset-grid"><table className="plain-table" aria-label="Historical data">
      <thead><tr>
        <th><input type="checkbox" aria-label="Select all visible datasets" checked={allSelected} disabled={!rows.length} onChange={() => onSelect(allSelected ? selectedIds.filter(id => !rows.some(row => row.id === id)) : [...new Set([...selectedIds, ...rows.map(row => row.id)])])}/></th>
        <th aria-sort={descending ? 'descending' : 'ascending'}><button className="dataset-sort" onClick={() => setDescending(value => !value)}>Symbol Name <span aria-hidden="true">{descending ? '▾' : '▴'}</span></button></th>
        {columns.map(column => <th key={column}>{column}</th>)}<th aria-label="Status" style={{ minWidth: 120 }}/><th aria-label="Row actions" style={{ width: 100 }}/>
      </tr></thead>
      <tbody>{rows.map(row => {
        const days = row.totalDays ?? 0;
        const marketStatus = historicalJob?.targets?.includes(row.id) ? `${historicalJob.status} ${historicalJob.progress}%` : '';
        const darwinexIndex = darwinex.job?.definitions.findIndex(item => item.id === row.id) ?? -1;
        const darwinexStatus = darwinexIndex >= 0 ? darwinexIndex < darwinex.job!.completed ? 'Completed' : `${darwinex.job!.state} ${darwinex.job!.progress}%` : darwinex.definitions.some(item => item.id === row.id) ? 'Completed' : '';
        const cryptoIndex = crypto.job?.definitions.findIndex(item => item.id === row.id) ?? -1;
        const cryptoStatus = cryptoIndex >= 0 ? cryptoIndex < crypto.job!.completed ? 'Completed' : `${crypto.job!.state} ${crypto.job!.progress}%` : crypto.definitions.some(item => item.id === row.id) ? 'Completed' : '';
        const yahooIndex = yahoo.job?.definitions.findIndex(item => item.id === row.id) ?? -1;
        const yahooStatus = yahooIndex >= 0 ? yahooIndex < yahoo.job!.completed ? 'Completed' : `${yahoo.job!.state} ${yahoo.job!.progress}%` : yahoo.definitions.some(item => item.id === row.id) ? 'Completed' : '';
        const mt5Index = mt5.job?.definitions.findIndex(item => item.id === row.id) ?? -1;
        const mt5Status = mt5Index >= 0 ? mt5Index < mt5.job!.completed ? 'Completed' : `${mt5.job!.state} ${mt5.job!.progress}%` : mt5.definitions.some(item => item.id === row.id) ? 'Completed' : '';
        const sqTaskIndex = sq.job?.definitions.findIndex(item => item.id === row.id) ?? -1;
        const sqStatus = sqTaskIndex >= 0 ? sqTaskIndex < sq.job!.completed ? 'Completed' : `${sq.job!.state} ${sq.job!.progress}%` : sq.definitions.some(item => item.id === row.id) ? 'Completed' : '';
        const fileTaskIndex = imports.job?.tasks.findIndex(task => task.record.id === row.id) ?? -1;
        const exportIndex = exports.job?.targetIds.indexOf(row.id) ?? -1;
        const exportStatus = exportIndex >= 0 && exports.job ? exports.job.state === 'completed' ? 'Completed' : `${exports.job.state.charAt(0).toUpperCase()}${exports.job.state.slice(1)} ${exports.job.progress}%` : '';
        const cloneIndex = tools.job?.tasks.findIndex(task => task.source.id === row.id || task.definition.id === row.id) ?? -1;
        const cloneStatus = cloneIndex >= 0 && tools.job ? cloneIndex < tools.job.completed || tools.job.state === 'completed' ? 'Completed' : `${tools.job.state.charAt(0).toUpperCase()}${tools.job.state.slice(1)} ${tools.job.progress}%` : tools.definitions.some(item => item.id === row.id) ? 'Completed' : '';
        const rowJob = downloadJob?.request.targets.some(target => target.id === row.id) ? downloadJob : null;
        const rowPath = 'path' in row && typeof row.path === 'string' ? normalizeRelativePath(row.path) : '';
        return <tr key={row.id} className={selectedIds.includes(row.id) || activeDatasetId === row.id ? 'selected' : ''}>
          <td><input type="checkbox" aria-label={`Select ${row.symbol}`} checked={selectedIds.includes(row.id)} onChange={() => onToggle(row.id)}/></td>
          <td><button className="dataset-sort" aria-label={`Preview ${row.symbol} ${row.timeframe}`} onPointerDown={event => { if (event.button === 0) onActivate?.(row.id); }} onClick={event => { if (event.detail === 0) onActivate?.(row.id); }}><strong>{row.symbol}</strong></button></td><td>{row.symbolDefinition}</td><td>{row.brokerName}</td><td>{row.underlying}</td>
          <td>{row.timeframe}</td><td>{row.timezone}</td><td>{formatDateOnly(row.from)}</td><td>{formatDateOnly(row.to)}</td><td>{days.toLocaleString()}</td>
          <td>{row.bars.toLocaleString()}</td><td>{row.source}</td><td>{"barType" in row && (row.barType === "end" || row.barType === "End of bar") ? "End of bar" : "Start of bar"}</td><td>{row.category}</td>
          <td title={rowPath || '—'}>{rowPath || '—'}</td>
          <td aria-label={`Status for ${row.symbol}`} title={cloneIndex >= 0 ? tools.job?.error : exportIndex >= 0 ? exports.job?.error : mt5Index >= 0 ? mt5.job?.error : yahooIndex >= 0 ? yahoo.job?.error : cryptoIndex >= 0 ? crypto.job?.error : darwinexIndex >= 0 ? darwinex.job?.error : sqTaskIndex >= 0 ? sq.job?.error : fileTaskIndex >= 0 ? imports.job?.error : rowJob?.error}>{marketStatus || (cloneStatus ? cloneStatus : exportStatus ? exportStatus : mt5Status ? mt5Status : yahooStatus ? yahooStatus : cryptoStatus ? cryptoStatus : darwinexStatus ? darwinexStatus : sqStatus ? sqStatus : fileTaskIndex >= 0 && imports.job ? fileTaskIndex < imports.job.completed ? 'Completed' : `${imports.job.state.charAt(0).toUpperCase()}${imports.job.state.slice(1)} ${imports.job.progress}%` : rowJob ? rowJob.state === 'completed' ? 'Completed' : `${rowJob.state.charAt(0).toUpperCase()}${rowJob.state.slice(1)} ${rowJob.progress}%` : row.bars > 0 ? 'Ready' : '')}</td>
          <td style={{ textAlign: 'center' }}><button aria-label={`Edit dataset ${row.symbol}`} onClick={event=>{event.stopPropagation();setEditingDataset(row);}}>Edit</button><button className="symbol-remove" aria-label={`Delete dataset ${row.symbol}`} title="Delete or clear dataset" onClick={event => { event.stopPropagation(); onDeleteRow?.(row.id); }}>×</button></td>
        </tr>;
      })}{!rows.length && <tr><td colSpan={17} className="dataset-empty">{catalogLoading ? 'Loading saved dataset catalog…' : catalogError ? 'Saved dataset catalog unavailable.' : allDatasets.length ? 'No matching data.' : 'No saved datasets found in catalog.'}</td></tr>}</tbody>
    </table></div>
  {editingDataset && <DatasetEditDialog row={editingDataset} onClose={()=>setEditingDataset(null)}/>}
  </main>;
}


export function DatasetEditDialog({row,onClose}:{row:import('./plugins/Common/dataManagerStore').MockDefinition;onClose:()=>void}) {
  const [value,setValue] = useState({...row}); const [pending,setPending] = useState(false); const [error,setError] = useState('');
  const brokers=useDataManagerStore(state=>state.brokers); const symbols=useSymbols(state=>state.symbols); const sessions=useSessions(state=>state.sessions);
  async function save() {setPending(true);setError('');try{await useDataManagerStore.getState().editDataset(row.id,value);onClose();}catch(cause){setError(String(cause));}finally{setPending(false);}}
  return <Modal title="Dataset properties" width={600} onClose={onClose} footer={<><Button disabled={pending} onClick={onClose}>Close</Button><Button disabled={pending} onClick={()=>void save()}>Save properties</Button></>}>
    {error && <p role="alert">{error}</p>}
    <Field label="Dataset name"><TextInput value={value.symbol} disabled={pending} onChange={event=>setValue({...value,symbol:event.target.value})}/></Field>
    <Field label="Broker profile"><select value={value.broker} onChange={event=>setValue({...value,broker:event.target.value})}><option value={row.broker}>{row.brokerName}</option>{brokers.map(broker=><option key={broker.id} value={broker.name}>{broker.name}</option>)}</select></Field>
    <Field label="Symbol specification"><select value={value.symbol_definition_id ?? ''} onChange={event=>setValue({...value,symbol_definition_id:event.target.value ? Number(event.target.value) : null})}><option value="">No specification</option>{symbols.map(symbol=><option key={symbol.id} value={symbol.id}>{symbol.symbol}</option>)}</select></Field>
    <Field label="Trading session"><select value={value.session_id ?? ''} onChange={event=>setValue({...value,session_id:event.target.value ? Number(event.target.value) : null})}><option value="">No session</option>{sessions.map(session=><option key={session.id} value={session.id}>{session.name}</option>)}</select></Field>
    <Field label="Category"><TextInput value={value.category} onChange={event=>setValue({...value,category:event.target.value})}/></Field>
    <Field label="Display timezone"><TextInput value={value.timezone} onChange={event=>setValue({...value,timezone:event.target.value})}/></Field><p>Changing the display timezone preserves recorded instants. Use Clone to shift timestamps.</p>
  </Modal>;
}
