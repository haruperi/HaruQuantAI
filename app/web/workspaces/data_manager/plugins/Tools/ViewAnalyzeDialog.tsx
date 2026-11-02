import { useEffect, useMemo, useRef, useState } from 'react';
import { createColumnHelper, flexRender, getCoreRowModel, useReactTable } from '@tanstack/react-table';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Button, Field, Modal, Select, TextInput } from '../../../../common/components/ui';
import { availableReviewTimeframes, type ReviewRow, type ToolTarget, type ReviewPage, type RemoteQualityResult } from './dataTools';
import { useDataTools } from './dataToolsStore';
import { DataReviewChart } from './DataReviewChart';
import './dataTools.css';
import { fetchRemoteSessions } from '../Catalogs/Sessions/sessionApiClient';

type Tab = 'data' | 'chart' | 'quality';
const column = createColumnHelper<ReviewRow>();

function ReviewGrid({ rows, tick, selected, changed, deleted, onSelect, onChange, digits }: {
  rows: ReviewRow[]; tick: boolean; selected: string; changed: Record<string, Partial<ReviewRow>>; deleted: string[];
  digits?: number; onSelect: (id: string) => void; onChange: (id: string, key: keyof ReviewRow, value: number) => void;
}) {
  const editable = selected && Object.hasOwn(changed, selected); const fields = tick ? ['bid','ask','volume'] as const : ['open','high','low','close','volume'] as const;
  const columns = useMemo(() => [column.accessor('date', { header: 'Date', cell: info => new Date(info.getValue()).toLocaleString() }), ...fields.map(key => column.accessor(key, { header: key[0].toUpperCase() + key.slice(1), cell: info => editable && info.row.original.id === selected ? <input aria-label={`Edit ${key}`} type="number" step="any" value={Number(changed[selected]?.[key] ?? info.getValue())} onChange={event => onChange(selected, key, Number(event.target.value))}/> : key !== 'volume' && digits !== undefined ? info.getValue().toFixed(digits) : info.getValue() }))], [changed, editable, fields, onChange, selected, digits]);
  const table = useReactTable({ data: rows, columns, getCoreRowModel: getCoreRowModel() }); const parentRef = useRef<HTMLDivElement>(null); const tableRows = table.getRowModel().rows;
  const virtual = useVirtualizer({ count: tableRows.length, getScrollElement: () => parentRef.current, estimateSize: () => 28, overscan: 12 });
  useEffect(() => { const index = rows.findIndex(row => row.id === selected); if (index >= 0) virtual.scrollToIndex(index, { align: 'center' }); }, [rows, selected, virtual]);
  return <div className="review-virtual-table"><div className="review-grid-header" style={{ gridTemplateColumns: `180px repeat(${fields.length}, minmax(92px,1fr))` }}>{table.getHeaderGroups()[0].headers.map(header => <strong key={header.id}>{flexRender(header.column.columnDef.header, header.getContext())}</strong>)}</div>
    <div className="review-grid-scroll" ref={parentRef}><div style={{ height: virtual.getTotalSize(), position:'relative' }}>{virtual.getVirtualItems().map(item => { const row = tableRows[item.index]; return <button type="button" key={row.id} onClick={() => onSelect(row.original.id)} className={`${selected === row.original.id ? 'selected' : ''} ${deleted.includes(row.original.id) ? 'deleted' : ''} ${Object.hasOwn(changed, row.original.id) ? 'changed' : ''}`} style={{ transform:`translateY(${item.start}px)`, gridTemplateColumns:`180px repeat(${fields.length}, minmax(92px,1fr))` }}>{row.getVisibleCells().map(cell => <span key={cell.id}>{flexRender(cell.column.columnDef.cell, cell.getContext())}</span>)}</button>; })}</div></div></div>;
}

export function ViewAnalyzeDialog({ target, externalActive, onClose }: { target: ToolTarget; externalActive: boolean; onClose: () => void }) {
  const store = useDataTools(); const frames = availableReviewTimeframes(target.timeframe); const [timeframe, setTimeframe] = useState(frames[0]); const [session, setSession] = useState<string>('Dataset session'); const [tab, setTab] = useState<Tab>('data');
  const [sessions, setSessions] = useState<string[]>(['Dataset session', 'No Session']);
  useEffect(() => { let active = true; fetchRemoteSessions().then(rows => {if(active) setSessions(['Dataset session', 'No Session', ...rows.map(row => row.name)]);}).catch(cause => {if(active) setError(String(cause));}); return () => {active = false;}; }, []);
  const [selected, setSelected] = useState(''); const [editing, setEditing] = useState<Record<string, Partial<ReviewRow>>>({}); const [deleted, setDeleted] = useState<string[]>([]); const [skipDate, setSkipDate] = useState(target.from); const [error, setError] = useState(''); const [discardOpen, setDiscardOpen] = useState(false);
  const [remote, setRemote] = useState<ReviewPage>({rows: [], total: 0, revision: ''});
  const [page, setPage] = useState(0); const [reload, setReload] = useState(0); const [loading, setLoading] = useState(false);
  const [quality, setQuality] = useState<RemoteQualityResult | null>(null);
  const [qualityPage, setQualityPage] = useState(0); const [qualityLoading, setQualityLoading] = useState(false);
  const [qualityError, setQualityError] = useState(''); const [qualityRetry, setQualityRetry] = useState(0);
  useEffect(() => { let active = true; setLoading(true); setError('');
    store.fetchReviewRows(target.id, 500, page * 500, timeframe, session === 'Dataset session' ? undefined : session).then(value => {if (active) setRemote(value);}).catch(cause => {if (active) {setRemote({rows:[],total:0,revision:''}); setError(String(cause));}}).finally(() => {if(active) setLoading(false);});
    return () => {active = false;};
  }, [target.id, timeframe, session, page, reload]);
  useEffect(() => { if (tab !== 'quality') return; let active = true; setQuality(null); setQualityError(''); setQualityLoading(true);
    store.fetchQualityDetails(target.id, 500, qualityPage * 500, timeframe, session === 'Dataset session' ? undefined : session)
      .then(value => { if (active) setQuality(value); })
      .catch(cause => { if (active) setQualityError(cause instanceof Error ? cause.message : 'Quality analysis failed.'); })
      .finally(() => { if (active) setQualityLoading(false); });
    return () => { active = false; };
  }, [tab, target.id, qualityPage, reload, timeframe, session, qualityRetry]);
  const visibleRows = remote.rows;
  const pendingRows = useMemo(() => visibleRows.filter(row => !deleted.includes(row.id)).map(row => ({...row, ...editing[row.id]})), [visibleRows, editing, deleted]);
  const tick = timeframe === 'TICK'; const dirty = Object.keys(editing).length > 0 || deleted.length > 0;
  function changeView(nextFrame: string, nextSession = session): void { setTimeframe(nextFrame); setSession(nextSession); setPage(0); setQualityPage(0); setSelected(''); setEditing({}); setDeleted([]); setError(''); }
  function edit(): void { const row = visibleRows.find(item => item.id === selected); if (row) setEditing(current => ({ ...current, [selected]: current[selected] ?? { ...row } })); }
  function toggleDelete(): void { if (!selected) return; setDeleted(current => current.includes(selected) ? current.filter(id => id !== selected) : [...current, selected]); }
  async function save(): Promise<void> { try {
    if (externalActive || loading) throw new Error('Finish the active operation first.');
    if (timeframe !== frames[0]) throw new Error('Edit the stored timeframe, not aggregated bars.');
    await store.saveRemoteReviewChanges(target.id, Object.entries(editing).map(([id, patch]) => ({...visibleRows.find(row => row.id === id), ...patch})), deleted, remote.revision);
    setEditing({}); setDeleted([]); setReload(value => value + 1); setError('');
  } catch(cause) {setError(String(cause));} }
  function close(): void { if (dirty) setDiscardOpen(true); else onClose(); }
  async function skip(): Promise<void> { try { const index = await store.getIndexForDate(target.id, skipDate); setPage(Math.floor(index / 500)); } catch(cause) {setError(String(cause));} }
  return <div className="data-tools-flow"><Modal title={`View data for '${target.symbol}'`} width={860} onClose={close} footer={<>{dirty && <span className="review-unsaved">Data contains unsaved changes</span>}<Button onClick={close}>Close</Button><Button className="primary" disabled={!dirty} onClick={save}>Save</Button></>}>
    {(error || store.storageError) && <p className="tools-error" role="alert">{error || store.storageError}</p>}
    {loading && <p role="status">Loading recorded prices…</p>}
    {tab !== 'quality' && <div><Button disabled={page === 0 || dirty || loading} onClick={() => setPage(value => value - 1)}>Previous</Button> <span>{page * 500 + 1}–{Math.min((page + 1) * 500, remote.total)} of {remote.total}</span> <Button disabled={(page + 1) * 500 >= remote.total || dirty || loading} onClick={() => setPage(value => value + 1)}>Next</Button></div>}
    <fieldset className="review-metadata"><div><Field label="Symbol name"><TextInput value={target.symbol} readOnly/></Field><Field label="Symbol"><TextInput value={target.symbolDefinition} readOnly/></Field><Field label="Date from"><TextInput value={target.from} readOnly/></Field><Field label="Date to"><TextInput value={target.to} readOnly/></Field><Field label="Imported timeframe"><TextInput value={target.timeframe} readOnly/></Field><Field label="Imported records"><TextInput value={target.bars.toLocaleString()} readOnly/></Field><Field label="View timeframe"><Select value={timeframe} onChange={value => changeView(value)}>{frames.map(item => <option key={item}>{item}</option>)}</Select></Field><Field label="Session"><Select value={session} onChange={value => changeView(timeframe, value)}>{sessions.map(item => <option key={item}>{item}</option>)}</Select></Field></div></fieldset>
    <div className="review-tabs" role="tablist">{([['data','Data'],['chart','Chart'],['quality','Analyze data quality']] as const).map(([id,label]) => <button role="tab" aria-selected={tab === id} key={id} onClick={() => setTab(id)}>{label}</button>)}</div>
    <section className="review-tab-panel" role="tabpanel">
      {tab === 'data' && <><div className="review-data-toolbar"><div><Field label="Skip to data"><TextInput aria-label="Skip to data" type="date" min={target.from} max={target.to} value={skipDate} onChange={event => setSkipDate(event.target.value)}/></Field><Button onClick={skip}>Skip</Button></div><div><Button disabled={!selected} onClick={edit}>Edit line</Button><Button disabled={!selected} onClick={toggleDelete}>{deleted.includes(selected) ? 'Restore line' : 'Delete line'}</Button></div></div><ReviewGrid rows={visibleRows} tick={tick} selected={selected} changed={editing} deleted={deleted} onSelect={setSelected} digits={remote.price_digits} onChange={(id, field, value) => setEditing(current => ({ ...current, [id]: { ...(current[id] ?? {}), [field]: value } }))}/></>}
      {tab === 'chart' && <DataReviewChart rows={pendingRows} tick={tick} digits={remote.price_digits}/>}
      {tab === 'quality' && <div className="quality-view">
        {qualityLoading && <p role="status">Analyzing recorded history…</p>}
        {qualityError && <div className="tools-error" role="alert">{qualityError} <Button onClick={() => setQualityRetry(value => value + 1)}>Retry quality analysis</Button></div>}
        {quality && <QualityView result={quality} tick={tick} page={qualityPage} onPage={setQualityPage}/>}
      </div>}


    </section><p className="tools-mock-note">Recorded history. Saving edits updates the authoritative stored dataset.</p>
  </Modal>{discardOpen && <Modal title="Unsaved data changes" width={440} onClose={() => setDiscardOpen(false)} footer={<><Button onClick={() => setDiscardOpen(false)}>Keep editing</Button><Button className="danger" onClick={onClose}>Discard changes</Button></>}><p>Close View &amp; Analyze and discard the unsaved row changes?</p></Modal>}</div>;
}

function QualityView({ result, tick, page, onPage }: { result: RemoteQualityResult; tick: boolean; page: number; onPage: (value: number) => void }) {
  const days = new Map(result.coverage.map(day => [day.date, day]));
  const years = [...new Set(result.coverage.map(day => Number(day.date.slice(0, 4))))].sort((a, b) => a - b);
  return <>
    <h3>Summary</h3><div className="quality-summary">{['Gap', 'Spike', tick ? 'Invalid quote' : 'Bad OHLC'].map(kind => <table key={kind} aria-label={`${kind} summary`}><thead><tr><th>Issue</th><th>Count</th><th>% of data</th></tr></thead><tbody><tr><th>{kind === 'Gap' ? 'Gaps' : kind === 'Spike' ? 'Spikes' : kind}</th><td>{(result.counts[kind] ?? 0).toLocaleString()}</td><td>{(result.percents[kind] ?? 0).toFixed(3)}</td></tr></tbody></table>)}</div>
    <p>{result.total.toLocaleString()} observations · {result.issue_count.toLocaleString()} issues · Gap policy: {result.gap_policy}. Spike threshold: {result.spike_threshold * 100}%.</p>
    <h3>Graphical view</h3>
    <p className="quality-legend"><span className="quality-key recorded"/>Recorded, no detected issues <span className="quality-key issue"/>One or more issues <span className="quality-key empty"/>No observed or expected data. Each cell is one UTC day.</p>
    <div className="quality-calendar" aria-label="Daily data quality">{years.map(year => {
      const count = (Date.UTC(year + 1, 0, 1) - Date.UTC(year, 0, 1)) / 86400000;
      return <div className="quality-year" key={year}><strong>{year}</strong>{Array.from({ length: count }, (_, index) => {
        const date = new Date(Date.UTC(year, 0, index + 1)).toISOString().slice(0, 10); const day = days.get(date);
        const state = day?.issues ? 'issue' : day?.observed ? 'recorded' : 'empty';
        return <span key={date} className={`quality-day ${state}`} role="img" aria-label={`${date}: ${day?.observed ?? 0} observations, ${day?.issues ?? 0} issues`} title={`${date}: ${day?.observed ?? 0} observations, ${day?.expected ?? 0} expected, ${day?.issues ?? 0} issues`}/>;
      })}</div>;
    })}{!years.length && <p>No observations available for quality analysis.</p>}</div>
    <div className="quality-pagination"><Button disabled={page === 0} onClick={() => onPage(page - 1)}>Previous issues</Button><span>{result.issue_count ? result.offset + 1 : 0}–{Math.min(result.offset + result.issues.length, result.issue_count)} of {result.issue_count} issues</span><Button disabled={result.offset + result.limit >= result.issue_count} onClick={() => onPage(page + 1)}>Next issues</Button></div>
    <div className="quality-details"><table aria-label="Quality issues"><thead><tr><th>Date (UTC)</th><th>Issue</th></tr></thead><tbody>{result.issues.map((issue, index) => <tr key={`${issue.date}:${issue.kind}:${index}`}><td>{issue.date}</td><td>{issue.kind}</td></tr>)}{!result.issue_count && <tr><td colSpan={2}>No issues detected.</td></tr>}</tbody></table></div>
  </>;
}
