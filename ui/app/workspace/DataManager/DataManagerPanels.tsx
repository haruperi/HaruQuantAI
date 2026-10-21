import { useState } from 'react';
import { Button } from '../../components/ui';
import { brokerCounts, type BrokerProfile } from '../../plugins/data_source/Catalogs/BrokerProfiles/brokerProfiles';
import { effectiveInstruments, type FileInstrument } from '../../plugins/data_source/FileImport/fileSymbols';
import { type SessionDefinition, type SessionBroker } from '../../plugins/data_source/Catalogs/Sessions/sessions';
import { summarizeGroup, type StockGroupDefinition } from '../../plugins/data_source/Catalogs/StockGroups/stockGroups';
import { activeExternalLines, externalTypeLabel, externalIndicatorTypes, type ExternalIndicatorDefinition } from '../../plugins/data_source/Indicators/externalIndicators';
import { useExternalIndicators } from '../../plugins/data_source/Indicators/externalIndicatorsStore';
import { normalizeRelativePath, useDataManagerStore, useDukascopyDownloads, useTickDownloader } from '../../plugins/data_source/Common/dataManagerStore';
import { useFileSymbols } from '../../plugins/data_source/FileImport/fileSymbolsStore';
import { useInstruments } from '../../plugins/data_source/Catalogs/Instruments/instrumentsStore';
import { useFileImports } from '../../plugins/data_source/FileImport/fileImportStore';
import { useSQData } from '../../plugins/data_source/SQData/sqDataStore';
import { useDarwinex } from '../../plugins/data_source/Darwinex/darwinexStore';
import { useCrypto } from '../../plugins/data_source/Crypto/cryptoStore';
import { useYahoo } from '../../plugins/data_source/Yahoo/yahooStore';
import { useMt5Import } from '../../plugins/data_source/MetaTrader/mt5ImportStore';
import { useDataExports } from '../../plugins/data_source/Export/dataExportStore';
import { useDataTools } from '../../plugins/data_source/Tools/dataToolsStore';
import { useStockGroups } from '../../plugins/data_source/Catalogs/StockGroups/stockGroupsStore';

export function BrokerProfilesTable({profiles,selected,instruments,sessions,onSelect,onEdit}:{profiles:BrokerProfile[];selected:string[];instruments:FileInstrument[];sessions:SessionDefinition[];onSelect:(ids:string[])=>void;onEdit:(profile:BrokerProfile)=>void}) {
  const allSelected=profiles.length>0&&profiles.every(row=>selected.includes(row.id));
  return <main className="full dataset-workspace" aria-label="Broker profiles">
    <div className="dataset-grid broker-profiles-grid"><table className="plain-table" aria-label="Broker profiles">
      <colgroup><col style={{ width:26 }}/><col style={{ width:250 }}/><col/><col style={{ width:100 }}/><col style={{ width:100 }}/><col style={{ width:130 }}/><col style={{ width:150 }}/><col style={{ width:140 }}/></colgroup>
      <thead><tr><th><input type="checkbox" aria-label="Select all broker profiles" checked={allSelected} disabled={!profiles.length} onChange={()=>onSelect(allSelected?[]:profiles.map(row=>row.id))}/></th>
        {['Name', 'Description', 'Postfix', 'Timezone', 'Customized stocks', 'Customized instruments', 'Customized sessions'].map(column => <th key={column}>{column}</th>)}
      </tr></thead><tbody>{profiles.map(profile=>{const count=brokerCounts(profile,instruments,sessions);return <tr key={profile.id} className={selected.includes(profile.id)?'selected':''} onDoubleClick={()=>onEdit(profile)}><td><input type="checkbox" aria-label={`Select broker ${profile.name}`} checked={selected.includes(profile.id)} onChange={()=>onSelect(selected.includes(profile.id)?selected.filter(id=>id!==profile.id):[...selected,profile.id])}/></td><td>{profile.name}</td><td>{profile.desc}</td><td>{profile.postfix}</td><td>{profile.timezone}</td><td>{count.stocks}</td><td>{count.instruments}</td><td>{count.sessions}</td></tr>;})}{!profiles.length&&<tr><td colSpan={8} className="dataset-empty">No brokers are defined.</td></tr>}</tbody>
    </table></div>
  </main>;
}

export function StockGroupsTable({ groups, selected, datasets: available, onSelect, onEdit, onUpdate }: { groups: StockGroupDefinition[]; selected: string[]; datasets: { symbol:string; from?:string; to?:string; bars?:number }[]; onSelect:(ids:string[])=>void; onEdit:(group:StockGroupDefinition)=>void; onUpdate:(group:StockGroupDefinition)=>void }) {
  const allSelected = groups.length > 0 && groups.every(group => selected.includes(group.id));
  return <main className="full dataset-workspace" aria-label="Stock groups">
    <div className="stock-groups-banner">
      Stock groups are - as name suggests - groups of stocks. It can be indexes like S&P500, which consists of 500 stocks, or you can define your own custom group of symbols. They support also complete history of index composition changes, which prevents survivorship bias. Default unmodifiable stock groups are enclosed in double braces [[ ]]. Stock groups must be fully downloaded and updated before they will be available to use.
    </div>
    <div className="dataset-grid stock-groups-grid"><table className="plain-table stock-group-table" aria-label="Stock groups">
      <colgroup><col style={{ width:26 }}/><col style={{ width:250 }}/><col style={{ width:100 }}/><col/><col style={{ width:130 }}/><col style={{ width:130 }}/><col style={{ width:110 }}/><col style={{ width:100 }}/><col style={{ width:100 }}/></colgroup>
      <thead><tr><th><input type="checkbox" aria-label="Select all stock groups" checked={allSelected} disabled={!groups.length} onChange={() => onSelect(allSelected ? [] : groups.map(group => group.id))}/></th>
        {['Name', 'Count', 'Description', 'Number of symbols', 'Downloaded', 'Ready to use?', 'Data from', 'Data to'].map(column => <th key={column}>{column}</th>)}
      </tr></thead><tbody>{groups.map(group => { const summary = summarizeGroup(group, available); return <tr key={group.id} className={selected.includes(group.id) ? 'selected' : ''} onDoubleClick={() => onEdit(group)}><td><input type="checkbox" aria-label={`Select stock group ${group.name}`} checked={selected.includes(group.id)} onChange={() => onSelect(selected.includes(group.id) ? selected.filter(id => id !== group.id) : [...selected, group.id])}/></td><td>{group.name}</td><td>{summary.active} / {summary.total}</td><td>{group.description}</td><td>{summary.numberOfSymbols}</td><td>{summary.downloaded} / {summary.total}</td><td>{summary.ready ? 'Yes' : <button className="stock-group-ready-link" title="Stock group is not ready for use, not all its symbols are downloaded" onClick={() => onUpdate(group)}>No, Update data</button>}</td><td>{summary.from || '-'}</td><td>{summary.to || '-'}</td></tr>; })}{!groups.length && <tr><td colSpan={9} className="dataset-empty">No groups of stocks are defined.</td></tr>}</tbody>
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
      <tbody>{rows.map(item => <tr key={item.name} className={selected.includes(item.name) ? 'selected' : ''} onDoubleClick={() => onEdit(item)}><td><input type="checkbox" aria-label={`Select indicator ${item.name}`} checked={selected.includes(item.name)} onChange={() => onSelect(selected.includes(item.name) ? selected.filter(name => name !== item.name) : [...selected, item.name])}/></td><td>{item.name}</td><td>{activeExternalLines(item).length}</td><td>{externalTypeLabel(item.type)}</td><td>{item.timeframe || '—'}</td><td>{item.dateFrom || '—'}</td><td>{item.dateTo || '—'}</td><td>{item.totalDays}</td><td>{item.records.length.toLocaleString()}</td><td className="indicator-status" aria-label={`Status for ${item.name}`}>{job?.indicator === item.name ? job.state === 'completed' ? 'Completed' : `${job.state} ${job.progress}%` : ''}</td><td><button className="instrument-remove" aria-label={`Delete indicator ${item.name}`} onClick={() => onDelete(item)}>×</button></td></tr>)}{!rows.length && <tr><td colSpan={11} className="dataset-empty">No External indicators defined.</td></tr>}</tbody>
    </table></div>
  </main>;
}

export function SessionTable({ rows:allRows, selected, onSelect, onEdit, onDelete, brokers }:{rows:SessionDefinition[];selected:string[];onSelect:(names:string[])=>void;onEdit:(item:SessionDefinition)=>void;onDelete:(item:SessionDefinition)=>void;brokers:SessionBroker[]}) {
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
        <td><input type="checkbox" aria-label={`Select session ${item.name}`} checked={selected.includes(item.name)} onChange={() => onSelect(selected.includes(item.name) ? selected.filter(name=>name!==item.name) : [...selected,item.name])}/></td>
        <td>{item.name}</td><td>{item.brokerName||'—'}</td><td/>
        <td><button className="instrument-remove" aria-label={`Delete session ${item.name}`} onClick={()=>onDelete(item)}>×</button></td>
      </tr>)}{!rows.length && <tr><td colSpan={5} className="dataset-empty">No matching sessions.</td></tr>}</tbody>
    </table></div>
  </main>;
}

export function InstrumentTable({ selected, onSelect, onEdit, onDelete }: {
  selected: string[]; onSelect: (symbols: string[]) => void;
  onEdit: (item: FileInstrument) => void; onDelete: (item: FileInstrument) => void;
}) {
  const instState = useInstruments();
  const fileState = useFileSymbols();
  const instruments = instState.instruments.length > 0
    ? instState.instruments
    : effectiveInstruments(fileState.instruments, fileState.overrides, fileState.removed);
  const [query, setQuery] = useState('');
  const [dataType, setDataType] = useState('');
  const [broker, setBroker] = useState('');
  const [descending, setDescending] = useState(false);
  const rows = instruments.filter(item => (!dataType || item.type === dataType)
    && (!broker || item.broker === broker)
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
  const td = useTickDownloader();
  const savedDatasets = useDataManagerStore(state => state.savedDatasets);
  const catalogLoading = useDataManagerStore(state => state.catalogLoading);
  const catalogError = useDataManagerStore(state => state.catalogError);
  const downloadJob = useDukascopyDownloads(state => state.job);
  const imports = useFileImports();
  const sq = useSQData();
  const darwinex = useDarwinex();
  const crypto = useCrypto();
  const yahoo = useYahoo();
  const mt5 = useMt5Import();
  const exports = useDataExports();
  const tools = useDataTools();
  const stockGroups = useStockGroups();
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
  const columns = ['Instrument', 'Broker profile', 'Underlying Symbol', 'Timeframe', 'Timezone',
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
        {columns.map(column => <th key={column}>{column}</th>)}<th aria-label="Status" style={{ minWidth: 120 }}/><th aria-label="Row actions" style={{ width: 36 }}/>
      </tr></thead>
      <tbody>{rows.map(row => {
        const days = row.totalDays ?? 0;
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
        const rowJob = row.id.startsWith('td:') && td.job?.request.symbols.some(symbol => `td:${symbol + td.job!.request.postfix}` === row.id) ? td.job : downloadJob?.request.targets.some(target => target.id === row.id) ? downloadJob : null;
        const rowPath = 'path' in row && typeof row.path === 'string' ? normalizeRelativePath(row.path) : '';
        return <tr key={row.id} className={selectedIds.includes(row.id) || activeDatasetId === row.id ? 'selected' : ''}>
          <td><input type="checkbox" aria-label={`Select ${row.symbol}`} checked={selectedIds.includes(row.id)} onChange={() => onToggle(row.id)}/></td>
          <td><button className="dataset-sort" aria-label={`Preview ${row.symbol} ${row.timeframe}`} onPointerDown={event => { if (event.button === 0) onActivate?.(row.id); }} onClick={event => { if (event.detail === 0) onActivate?.(row.id); }}><strong>{row.symbol}</strong></button></td><td>{row.instrument}</td><td>{row.brokerName}</td><td>{row.underlying}</td>
          <td>{row.timeframe}</td><td>{row.timezone}</td><td>{formatDateOnly(row.from)}</td><td>{formatDateOnly(row.to)}</td><td>{days.toLocaleString()}</td>
          <td>{row.bars.toLocaleString()}</td><td>{row.source}</td><td>{"barType" in row && (row.barType === "end" || row.barType === "End of bar") ? "End of bar" : "Start of bar"}</td><td>{row.category}</td>
          <td title={rowPath || '—'}>{rowPath || '—'}</td>
          <td aria-label={`Status for ${row.symbol}`} title={cloneIndex >= 0 ? tools.job?.error : exportIndex >= 0 ? exports.job?.error : mt5Index >= 0 ? mt5.job?.error : yahooIndex >= 0 ? yahoo.job?.error : cryptoIndex >= 0 ? crypto.job?.error : darwinexIndex >= 0 ? darwinex.job?.error : sqTaskIndex >= 0 ? sq.job?.error : fileTaskIndex >= 0 ? imports.job?.error : rowJob?.error}>{cloneStatus ? cloneStatus : exportStatus ? exportStatus : mt5Status ? mt5Status : yahooStatus ? yahooStatus : cryptoStatus ? cryptoStatus : darwinexStatus ? darwinexStatus : sqStatus ? sqStatus : fileTaskIndex >= 0 && imports.job ? fileTaskIndex < imports.job.completed ? 'Completed' : `${imports.job.state.charAt(0).toUpperCase()}${imports.job.state.slice(1)} ${imports.job.progress}%` : rowJob ? rowJob.state === 'completed' ? 'Completed' : `${rowJob.state.charAt(0).toUpperCase()}${rowJob.state.slice(1)} ${rowJob.progress}%` : row.bars > 0 ? 'Ready' : ''}</td>
          <td style={{ textAlign: 'center' }}><button className="instrument-remove" aria-label={`Delete dataset ${row.symbol}`} title="Delete or clear dataset" onClick={event => { event.stopPropagation(); onDeleteRow?.(row.id); }}>×</button></td>
        </tr>;
      })}{!rows.length && <tr><td colSpan={17} className="dataset-empty">{catalogLoading ? 'Loading saved dataset catalog…' : catalogError ? 'Saved dataset catalog unavailable.' : allDatasets.length ? 'No matching data.' : 'No saved datasets found in catalog.'}</td></tr>}</tbody>
    </table></div>
  </main>;
}
