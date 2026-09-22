import { useMemo, useState } from 'react';
import { Select, TextInput } from '../../components/ui';
import { useAppStore } from '../../app/store';
import type { Job } from '../../app/types';

export interface DebugLogEntry { id: string; time: string; category: string; message: string; }

const statusTime = (job: Job) => job.startedAt ? job.startedAt.replace('T', ' ').slice(0, 19) : '—';

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

export function DebugConsoleWorkspace() {
  const jobs = useAppStore(s => s.jobs); const notifications = useAppStore(s => s.notifications); const [category, setCategory] = useState('All'); const [query, setQuery] = useState(''); const [cleared, setCleared] = useState(false);
  const entries = useMemo(() => cleared ? [] : deriveDebugLog(jobs, notifications), [cleared, jobs, notifications]); const categories = debugCategories(entries); const visible = filterDebugLog(entries, category, query);
  return <section className="header-app debug-console" aria-labelledby="debug-console-title">
    <header className="header-app-title"><div><h1 id="debug-console-title">Debug Console</h1><span>Application diagnostic log</span></div></header>
    <div className="debug-toolbar"><label>Category<Select value={category} onChange={setCategory}>{categories.map(item => <option key={item}>{item}</option>)}</Select></label><label>Filter<TextInput value={query} onChange={event => setQuery(event.target.value)} placeholder="Filter messages"/></label></div>
    <div className="debug-log" role="log" aria-live="polite">{visible.length ? visible.map(entry => <div key={entry.id}><time>{entry.time}</time><strong>{entry.category}</strong><span>- {entry.message}</span></div>) : <p className="debug-empty">No log entries match the current filter.</p>}</div>
    <button className="clear-debug-log" onClick={() => setCleared(true)} disabled={!entries.length}>Clear log</button>
  </section>;
}
