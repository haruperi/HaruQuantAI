import { useEffect, useMemo, useRef, useState } from 'react';
import { createColumnHelper, flexRender, getCoreRowModel, useReactTable } from '@tanstack/react-table';
import { useVirtualizer } from '@tanstack/react-virtual';
import { Button, Field, Modal, Select, TextInput } from '../../../components/ui';
import { availableReviewTimeframes, type ReviewRow, type ToolTarget } from './dataTools';
import { useDataTools } from './dataToolsStore';
import { DataReviewChart } from './DataReviewChart';
import './dataTools.css';
import { fetchRemoteSessions } from '../Catalogs/Sessions/sessionApiClient';

type Tab = 'data' | 'chart' | 'quality';
const column = createColumnHelper<ReviewRow>();

function ReviewGrid({ rows, tick, selected, changed, deleted, onSelect, onChange }: {
  rows: ReviewRow[]; tick: boolean; selected: string; changed: Record<string, Partial<ReviewRow>>; deleted: string[];
  onSelect: (id: string) => void; onChange: (id: string, key: keyof ReviewRow, value: number) => void;
}) {
  const editable = selected && Object.hasOwn(changed, selected); const fields = tick ? ['bid','ask','volume'] as const : ['open','high','low','close','volume'] as const;
  const columns = useMemo(() => [column.accessor('date', { header: 'Date', cell: info => new Date(info.getValue()).toLocaleString() }), ...fields.map(key => column.accessor(key, { header: key[0].toUpperCase() + key.slice(1), cell: info => editable && info.row.original.id === selected ? <input aria-label={`Edit ${key}`} type="number" step="any" value={Number(changed[selected]?.[key] ?? info.getValue())} onChange={event => onChange(selected, key, Number(event.target.value))}/> : info.getValue() }))], [changed, editable, fields, onChange, selected]);
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
  const [remote, setRemote] = useState<{rows: ReviewRow[]; total: number; revision: string}>({rows: [], total: 0, revision: ''});
  const [page, setPage] = useState(0); const [reload, setReload] = useState(0); const [loading, setLoading] = useState(false);
  const [quality, setQuality] = useState<{counts: Record<string, number>; issues: {date: string; kind: string}[]; issue_count: number; gap_policy: string} | null>(null);
  useEffect(() => { let active = true; setLoading(true); setError('');
    store.fetchReviewRows(target.id, 500, page * 500, timeframe, session === 'Dataset session' ? undefined : session).then(value => {if (active) setRemote(value);}).catch(cause => {if (active) {setRemote({rows:[],total:0,revision:''}); setError(String(cause));}}).finally(() => {if(active) setLoading(false);});
    return () => {active = false;};
  }, [target.id, timeframe, session, page, reload]);
  useEffect(() => { if (tab !== 'quality') return; let active = true; setQuality(null);
    store.fetchQualityDetails(target.id, 500, page * 500, timeframe, session === 'Dataset session' ? undefined : session).then(value => {if(active) setQuality(value as NonNullable<typeof quality>);}).catch(cause => {if(active) setError(String(cause));});
    return () => {active = false;};
  }, [tab, target.id, page, reload, timeframe, session]);
  const visibleRows = remote.rows;
  const pendingRows = useMemo(() => visibleRows.filter(row => !deleted.includes(row.id)).map(row => ({...row, ...editing[row.id]})), [visibleRows, editing, deleted]);
  const tick = timeframe === 'TICK'; const dirty = Object.keys(editing).length > 0 || deleted.length > 0;
  function changeView(nextFrame: string, nextSession = session): void { setTimeframe(nextFrame); setSession(nextSession); setPage(0); setSelected(''); setEditing({}); setDeleted([]); setError(''); }
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
    <div><Button disabled={page === 0 || dirty || loading} onClick={() => setPage(value => value - 1)}>Previous</Button> <span>{page * 500 + 1}–{Math.min((page + 1) * 500, remote.total)} of {remote.total}</span> <Button disabled={(page + 1) * 500 >= remote.total || dirty || loading} onClick={() => setPage(value => value + 1)}>Next</Button></div>
    <fieldset className="review-metadata"><div><Field label="Symbol name"><TextInput value={target.symbol} readOnly/></Field><Field label="Symbol"><TextInput value={target.symbolDefinition} readOnly/></Field><Field label="Date from"><TextInput value={target.from} readOnly/></Field><Field label="Date to"><TextInput value={target.to} readOnly/></Field><Field label="Imported timeframe"><TextInput value={target.timeframe} readOnly/></Field><Field label="Imported records"><TextInput value={target.bars.toLocaleString()} readOnly/></Field><Field label="View timeframe"><Select value={timeframe} onChange={value => changeView(value)}>{frames.map(item => <option key={item}>{item}</option>)}</Select></Field><Field label="Session"><Select value={session} onChange={value => changeView(timeframe, value)}>{sessions.map(item => <option key={item}>{item}</option>)}</Select></Field></div></fieldset>
    <div className="review-tabs" role="tablist">{([['data','Data'],['chart','Chart'],['quality','Analyze data quality']] as const).map(([id,label]) => <button role="tab" aria-selected={tab === id} key={id} onClick={() => setTab(id)}>{label}</button>)}</div>
    <section className="review-tab-panel" role="tabpanel">
      {tab === 'data' && <><div className="review-data-toolbar"><div><Field label="Skip to data"><TextInput aria-label="Skip to data" type="date" min={target.from} max={target.to} value={skipDate} onChange={event => setSkipDate(event.target.value)}/></Field><Button onClick={skip}>Skip</Button></div><div><Button disabled={!selected} onClick={edit}>Edit line</Button><Button disabled={!selected} onClick={toggleDelete}>{deleted.includes(selected) ? 'Restore line' : 'Delete line'}</Button></div></div><ReviewGrid rows={visibleRows} tick={tick} selected={selected} changed={editing} deleted={deleted} onSelect={setSelected} onChange={(id, field, value) => setEditing(current => ({ ...current, [id]: { ...(current[id] ?? {}), [field]: value } }))}/></>}
      {tab === 'chart' && <DataReviewChart rows={pendingRows} tick={tick}/>}
      {tab === 'quality' && quality && <div className="quality-view"><p>{quality.issue_count} issues. Gap policy: {quality.gap_policy}. Spike threshold: 10% between observations.</p><p>{Object.entries(quality.counts).map(([name, count]) => `${name}: ${count}`).join(' · ')}</p><table><thead><tr><th>Date</th><th>Issue</th></tr></thead><tbody>{quality.issues.map((issue, index) => <tr key={index}><td>{issue.date}</td><td>{issue.kind}</td></tr>)}</tbody></table></div>}

    </section><p className="tools-mock-note">Recorded history. Saving edits updates the authoritative stored dataset.</p>
  </Modal>{discardOpen && <Modal title="Unsaved data changes" width={440} onClose={() => setDiscardOpen(false)} footer={<><Button onClick={() => setDiscardOpen(false)}>Keep editing</Button><Button className="danger" onClick={onClose}>Discard changes</Button></>}><p>Close View &amp; Analyze and discard the unsaved row changes?</p></Modal>}</div>;
}
