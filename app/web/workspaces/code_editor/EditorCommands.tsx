import { useEffect, useMemo, useRef, useState } from 'react';
import { createCodeEditorClient, type CompilationDto, type FormatDto, type RepairDto } from './codeEditorClient';
import type { CodeEditorState } from './useCodeEditorWorkspace';

const terminal = new Set(['COMPLETED', 'FAILED', 'CANCELLED', 'INTERRUPTED']);

export function EditorCommands({ workspace: w }: { workspace: CodeEditorState }) {
  const client = useMemo(() => createCodeEditorClient(), []);
  const job = w.compilation;
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [repair, setRepair] = useState<RepairDto | null>(null);
  const [selections, setSelections] = useState<Record<string, string>>({});
  const [formats, setFormats] = useState<FormatDto[]>([]);
  const [format, setFormat] = useState('python');
  const [staleDiagnostics, setStaleDiagnostics] = useState(false);
  const generation = useRef(0);
  const current = useRef(w);
  current.current = w;
  const repairSource = useRef<{ path: string; content: string } | null>(null);
  const report = (e: unknown) => setError(e instanceof Error ? e.message : String(e));

  const publish = (snapshot: CompilationDto) => {
    current.current.setCompilation(snapshot);
  };

  useEffect(() => {
    let active = true;
    client.compilation().then(snapshot => { if (active && snapshot) current.current.setCompilation(previous => previous ?? snapshot); }).catch(e => { if (active) report(e); });
    client.exportFormats().then(value => { if (active) setFormats(value); }).catch(e => { if (active) report(e); });
    return () => { active = false; generation.current++; };
  }, [client]);

  useEffect(() => {
    if (!job || terminal.has(job.status)) return;
    let active = true;
    let timer: number;
    const poll = () => {
      client.compilation(job.job_id).then(snapshot => {
        if (active && snapshot && snapshot.job_id === job.job_id) current.current.setCompilation(previous => previous?.job_id === snapshot.job_id ? snapshot : previous);
      }).catch(e => { if (active) report(e); }).finally(() => { if (active) timer = window.setTimeout(poll, 400); });
    };
    timer = window.setTimeout(poll, 400);
    return () => { active = false; window.clearTimeout(timer); };
  }, [client, job]);

  useEffect(() => {
    const result = job?.results.find(item => item.file === w.activeFilePath);
    let active = true;
    setStaleDiagnostics(false);
    if (result) {
      const expected = job?.source_hashes?.[result.file];
      if (!expected) w.publishDiagnostics(result.file, result.errors);
      else crypto.subtle.digest('SHA-256', new TextEncoder().encode(w.activeContent)).then(bytes => {
        if (!active) return;
        const actual = Array.from(new Uint8Array(bytes), byte => byte.toString(16).padStart(2, '0')).join('');
        setStaleDiagnostics(actual !== expected);
        w.publishDiagnostics(result.file, actual === expected ? result.errors : []);
      }).catch(report);
    }
    return () => { active = false; };
  }, [job, w.activeFilePath, w.activeContent]);

  const start = async (scope: 'file' | 'package' | 'all' | 'registered') => {
    let path = w.activeFilePath ?? undefined;
    if (scope === 'package') {
      const answer = prompt('Python package directory:', w.selectedNavPath ?? 'app/include/user');
      if (!answer) return;
      path = answer;
    }
    setBusy(true); setError('');
    const token = ++generation.current;
    try {
      const snapshot = await client.startCompilation(scope, path, scope === 'file' ? w.activeContent : undefined);
      if (token === generation.current) publish(snapshot);
    } catch (e) { report(e); } finally { setBusy(false); }
  };

  const fix = async (chosen: Record<string, string> = {}) => {
    if (!w.activeFilePath) return;
    const source = repairSource.current && Object.keys(chosen).length ? repairSource.current : { path: w.activeFilePath, content: w.activeContent };
    repairSource.current = source;
    setBusy(true); setError('');
    try {
      const result = await client.repairImports(source.path, source.content, chosen);
      const now = current.current;
      if (now.activeFilePath !== source.path || now.activeContent !== source.content) throw new Error('Buffer changed; run import repair again.');
      setRepair(result);
      if (result.unresolved.length === 0) { now.handleContentChange(result.content); setRepair(null); }
    } catch (e) { report(e); } finally { setBusy(false); }
  };

  const createExport = async () => {
    if (!w.activeFilePath) return;
    const extension = formats.find(item => item.format_id === format)?.extension;
    if (!extension) return;
    const path = prompt('Export template destination:', `app/include/user/code_templates/${format}/template${extension}`);
    if (!path) return;
    setBusy(true); setError('');
    try {
      const result = await client.createExportTemplate([w.activeFilePath], path, format);
      await w.refreshNavigator();
      await w.handleOpenPath(result.file_path);
    } catch (e) { report(e); } finally { setBusy(false); }
  };

  const running = Boolean(job && !terminal.has(job.status));
  return <section aria-label="Editor commands" className="px-3 py-1 border-b border-slate-800 text-xs space-y-1">
    <div className="flex gap-3 flex-wrap items-center">
      <button onClick={w.handleReload} disabled={!w.activeFilePath || busy || w.isDocumentCommandRunning}>Reload from disk</button>
      <button onClick={() => void fix()} disabled={!w.activeFilePath || busy || w.isDocumentCommandRunning}>Fix imports</button>
      <button onClick={() => void start('package')} disabled={busy || running}>Compile package/plugin</button>
      <button onClick={() => void start('all')} disabled={busy || running}>Compile all</button>
      <button onClick={() => void start('registered')} disabled={busy || running}>Reload extensions</button>
      <button disabled={!running || job?.cancellation_requested} onClick={() => {
        if (job) client.cancelCompilation(job.job_id).then(publish).catch(report);
      }}>Cancel compilation</button>
      <label>Navigator ownership <select aria-label="Navigator ownership" value={w.ownershipFilter} onChange={e => w.setOwnershipFilter(e.target.value)}>
        <option value="all">All</option><option value="builtin">Builtin</option><option value="user">User</option>
      </select></label>
      <select aria-label="Export template format" value={format} onChange={e => setFormat(e.target.value)}>
        {formats.map(item => <option key={item.format_id} value={item.format_id}>{item.name}</option>)}
      </select>
      <button disabled={!w.activeFilePath || busy || !formats.length} onClick={() => void createExport()}>Create export template</button>
    </div>
    {job && <div role="status">{job.job_id}: {job.status} — {Math.round(job.progress)}% — {job.message}
      <progress aria-label="Compilation progress" value={job.progress} max={100} />
      {job.results.map(result => <div key={result.file}><button onClick={() => { void w.handleOpenPath(result.file); }}>{result.file}: {result.success ? 'Passed' : 'Failed'}</button></div>)}
      {staleDiagnostics && <div>Diagnostics are from an earlier source version. Compile the current buffer to refresh them.</div>}
    </div>}
    {repair && <div aria-label="Import candidates">{repair.unresolved.map(choice => <label key={choice.symbol}>{choice.symbol}
      <select aria-label={`Import ${choice.symbol}`} value={selections[choice.symbol] ?? ''} onChange={e => setSelections(previous => ({ ...previous, [choice.symbol]: e.target.value }))}>
        <option value="">{choice.candidates.length ? 'Choose module' : 'No indexed candidate'}</option>
        {choice.candidates.map(candidate => <option key={candidate}>{candidate}</option>)}
      </select>
    </label>)}<button onClick={() => void fix(selections)} disabled={busy}>Apply import selections</button></div>}
    {error && <div role="alert">{error}</div>}
  </section>;
}
