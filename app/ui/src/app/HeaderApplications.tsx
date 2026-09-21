import { useEffect, useMemo, useState } from 'react';
import { Bug, ChartArea, Grid2X2, RefreshCw, TriangleAlert } from 'lucide-react';
import { Button, Modal, Select, TextInput } from '../components/ui';
import { useAppStore } from './store';
import type { Job } from './types';

export const HEADER_APPLICATION_ACTIONS = [
  { id: 'volume-profile', title: 'Volume & Market Profile Addon' },
  { id: 'debugconsole', title: 'Debug Console' },
  { id: 'gridcontrol', title: 'Grid Control' },
] as const;

export const VOLUME_PROFILE_ACTIONS = ['Learn more', 'Upgrade to Ultimate', 'Pro V&MP monthly subscription', 'Pro V&MP yearly subscription'] as const;

export interface DebugLogEntry { id: string; time: string; category: string; message: string; }
export interface GridJobRow { id: string; groupId: string; type: 'Continuous' | 'One time'; status: string; created: string; started: string; duration: string; progress: string; error?: string; }
export interface GridSections { running: GridJobRow[]; waiting: GridJobRow[]; finished: GridJobRow[]; }

const FINISHED_FIXTURES: GridJobRow[] = [
  { id: 'job-history-001', groupId: 'research', type: 'One time', status: 'Success', created: '2026-09-20 09:40:12', started: '2026-09-20 09:40:13', duration: '00:02:18', progress: '100%' },
  { id: 'job-history-002', groupId: 'data', type: 'One time', status: 'Error', created: '2026-09-20 08:14:03', started: '2026-09-20 08:14:04', duration: '00:00:07', progress: '42%', error: 'The simulated worker stopped while validating the input data.' },
];

const statusTime = (job: Job) => job.startedAt ? job.startedAt.replace('T', ' ').slice(0, 19) : '—';

function jobToGridRow(job: Job, key: string): GridJobRow {
  const time = statusTime(job);
  return { id: job.id || key, groupId: key, type: 'One time', status: job.status === 'completed' ? 'Success' : job.status === 'failed' ? 'Error' : job.status[0].toUpperCase() + job.status.slice(1), created: time, started: job.status === 'queued' ? '—' : time, duration: ['completed', 'failed', 'cancelled'].includes(job.status) ? '00:00:12' : 'Running', progress: job.progress < 0 ? 'N/A' : `${Math.round(job.progress)}%`, error: job.status === 'failed' ? (job.message || 'The simulated job failed.') : undefined };
}

export function classifyGridJobs(jobs: Record<string, Job>): GridSections {
  const rows = Object.entries(jobs).map(([key, job]) => jobToGridRow(job, key));
  const running = rows.filter(row => ['Running', 'Paused'].includes(row.status));
  const waiting = rows.filter(row => ['Queued', 'Idle'].includes(row.status));
  const currentFinished = rows.filter(row => ['Success', 'Error', 'Cancelled'].includes(row.status));
  const fixtureIds = new Set(currentFinished.map(row => row.id));
  return { running, waiting, finished: [...currentFinished, ...FINISHED_FIXTURES.filter(row => !fixtureIds.has(row.id))].slice(0, 100) };
}

export function deriveDebugLog(jobs: Record<string, Job>, notifications: string[]): DebugLogEntry[] {
  const jobEntries = Object.entries(jobs).map(([key, job], index) => ({ id: `job-${key}-${job.status}`, time: statusTime(job) === '—' ? `16:${String(30 - index).padStart(2, '0')}:00` : statusTime(job).slice(11), category: 'Jobs', message: `${job.kind || key}: ${job.message || job.status} (${Math.round(job.progress)}%)` }));
  const notificationEntries = notifications.map((message, index) => ({ id: `notice-${index}-${message}`, time: `16:${String(20 - index).padStart(2, '0')}:00`, category: 'Application', message }));
  const baseline: DebugLogEntry[] = [{ id: 'system-ready', time: '16:00:00', category: 'System', message: 'Frontend research workspace initialized.' }, { id: 'mock-engine', time: '16:00:01', category: 'Engine', message: 'Deterministic mock engine is ready; no backend is connected.' }];
  let length = 0;
  return [...jobEntries, ...notificationEntries, ...baseline].filter(entry => { length += `${entry.time} ${entry.category} - ${entry.message}`.length; return length <= 10_000; });
}

export function filterDebugLog(entries: DebugLogEntry[], category: string, text: string): DebugLogEntry[] {
  const query = text.trim().toLocaleLowerCase();
  return entries.filter(entry => (category === 'All' || entry.category === category) && (!query || entry.message.toLocaleLowerCase().includes(query)));
}

export function debugCategories(entries: DebugLogEntry[]): string[] { return ['All', ...new Set(entries.map(entry => entry.category))]; }

export function HeaderApplicationActions() {
  const module = useAppStore(s => s.module); const setModule = useAppStore(s => s.setModule); const [volumeOpen, setVolumeOpen] = useState(false);
  return <>
    <button className="top-action" title="Volume & Market Profile Addon" aria-label="Volume & Market Profile Addon" onClick={() => setVolumeOpen(true)}><ChartArea/></button>
    <button className={`top-action ${module === 'debugconsole' ? 'active' : ''}`} title="Debug Console" aria-label="Debug Console" onClick={() => setModule('debugconsole')}><Bug/></button>
    <button className={`top-action ${module === 'gridcontrol' ? 'active' : ''}`} title="Grid Control" aria-label="Grid Control" onClick={() => setModule('gridcontrol')}><Grid2X2/></button>
    {volumeOpen && <VolumeProfileDialog onClose={() => setVolumeOpen(false)}/>}
  </>;
}

function VolumeProfileDialog({ onClose }: { onClose: () => void }) {
  const notify = useAppStore(s => s.notify);
  const unavailable = (label: string) => notify(`${label} is not configured for this HaruQuantAI workspace`);
  return <Modal title="Volume & Market Profile Addon" onClose={onClose} width={650} footer={<Button onClick={onClose}>Close</Button>}>
    <div className="volume-profile-dialog">
      <h3>Volume &amp; Market Profile Addon</h3>
      <p>New HaruQuantAI addon that allows you to use Volume &amp; Market Profile indicators and building blocks.</p>
      <p>Available in HaruQuantAI Ultimate edition or as a paid addon in HaruQuantAI Pro edition.</p>
      <Button onClick={() => unavailable(VOLUME_PROFILE_ACTIONS[0])}>Learn more about Volume &amp; Market Profile in HaruQuantAI</Button>
      <p className="addon-inactive">🔒 <span>You don't have this addon active.</span></p>
      <div className="addon-actions">{VOLUME_PROFILE_ACTIONS.slice(1).map(label => <Button className="primary" key={label} onClick={() => unavailable(label)}>{label}</Button>)}</div>
    </div>
  </Modal>;
}

export function DebugConsole() {
  const jobs = useAppStore(s => s.jobs); const notifications = useAppStore(s => s.notifications); const [category, setCategory] = useState('All'); const [query, setQuery] = useState(''); const [cleared, setCleared] = useState(false);
  const entries = useMemo(() => cleared ? [] : deriveDebugLog(jobs, notifications), [cleared, jobs, notifications]); const categories = debugCategories(entries); const visible = filterDebugLog(entries, category, query);
  return <section className="header-app debug-console" aria-labelledby="debug-console-title">
    <header className="header-app-title"><div><h1 id="debug-console-title">Debug Console</h1><span>Application diagnostic log</span></div></header>
    <div className="debug-toolbar"><label>Category<Select value={category} onChange={setCategory}>{categories.map(item => <option key={item}>{item}</option>)}</Select></label><label>Filter<TextInput value={query} onChange={event => setQuery(event.target.value)} placeholder="Filter messages"/></label></div>
    <div className="debug-log" role="log" aria-live="polite">{visible.length ? visible.map(entry => <div key={entry.id}><time>{entry.time}</time><strong>{entry.category}</strong><span>- {entry.message}</span></div>) : <p className="debug-empty">No log entries match the current filter.</p>}</div>
    <button className="clear-debug-log" onClick={() => setCleared(true)} disabled={!entries.length}>Clear log</button>
  </section>;
}

function EmptyRow({ columns, children }: { columns: number; children: string }) { return <tr><td colSpan={columns} className="grid-empty">{children}</td></tr>; }

function GridPanel({ title, rows, kind, onError }: { title: string; rows: GridJobRow[]; kind: 'running' | 'waiting' | 'finished'; onError: (row: GridJobRow) => void }) {
  return <fieldset className="grid-control-panel"><legend>{title}</legend>{kind !== 'finished' && <span className="grid-records">Records: {rows.length}</span>}<div className="plain-table-wrap"><table className="plain-table grid-jobs"><thead><tr><th>Job ID</th><th>Job group ID</th><th>Type</th>{kind === 'running' && <th>Status</th>}<th>Created</th>{kind !== 'waiting' && <th>Started</th>}{kind === 'running' && <th>Run time</th>}{kind === 'finished' && <th>Duration</th>}{kind !== 'waiting' && <th>{kind === 'finished' ? 'Status' : 'Progress'}</th>}</tr></thead><tbody>{rows.length ? rows.map(row => <tr key={row.id} className={row.error ? 'grid-job-error' : ''}><td>{row.id}</td><td>{row.groupId}</td><td>{row.type}</td>{kind === 'running' && <td>{row.status}</td>}<td>{row.created}</td>{kind !== 'waiting' && <td>{row.started}</td>}{kind === 'running' && <td>{row.duration}</td>}{kind === 'finished' && <td>{row.duration}</td>}{kind !== 'waiting' && <td>{row.error ? <button className="grid-error-link" onClick={() => onError(row)}>Error</button> : kind === 'finished' ? row.status : row.progress}</td>}</tr>) : <EmptyRow columns={kind === 'running' ? 8 : kind === 'waiting' ? 4 : 7}>{kind === 'running' ? 'No jobs in progress.' : kind === 'waiting' ? 'No waiting jobs.' : 'No finished jobs.'}</EmptyRow>}</tbody></table></div></fieldset>;
}

export function GridControl() {
  const jobs = useAppStore(s => s.jobs); const sections = useMemo(() => classifyGridJobs(jobs), [jobs]); const [refreshedAt, setRefreshedAt] = useState(() => new Date()); const [error, setError] = useState<GridJobRow | null>(null);
  useEffect(() => { const timer = window.setInterval(() => setRefreshedAt(new Date()), 3000); return () => window.clearInterval(timer); }, []);
  const refresh = () => setRefreshedAt(new Date());
  return <section className="header-app grid-control" aria-labelledby="grid-control-title"><div className="grid-control-scroll"><h1 id="grid-control-title">Grid engine overview</h1><fieldset className="grid-control-panel grid-control-toolbar"><span>Auto-refresh every 3 seconds</span><label>Grid<Select value="Local grid" onChange={() => undefined}><option>Local grid</option></Select></label><Button title="Refresh data" aria-label="Refresh data" onClick={refresh}><RefreshCw/> Refresh</Button><small>Last refreshed {refreshedAt.toLocaleTimeString()}</small></fieldset><GridPanel title="Jobs in progress" rows={sections.running} kind="running" onError={setError}/><GridPanel title="Waiting jobs" rows={sections.waiting} kind="waiting" onError={setError}/><GridPanel title="Last 100 finished jobs" rows={sections.finished} kind="finished" onError={setError}/></div>{error && <Modal title="Errors" onClose={() => setError(null)} width={560} footer={<Button onClick={() => setError(null)}>Close</Button>}><div className="grid-error-dialog"><TriangleAlert/><div><strong>{error.id}</strong><p>{error.error}</p></div></div></Modal>}</section>;
}
