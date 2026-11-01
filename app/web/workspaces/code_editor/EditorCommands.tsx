import { useEffect, useMemo, useRef, useState } from 'react';
import {
  AlertTriangle, CheckCircle2, ChevronDown, ChevronUp, FileCode2, Layers3,
  LoaderCircle, Package, RefreshCw, RotateCcw, Settings2, Wrench, XCircle,
} from 'lucide-react';
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
  const [showOptions, setShowOptions] = useState(false);
  const [showDetails, setShowDetails] = useState(false);
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
      const answer = prompt('Python package directory:', w.selectedNavPath ?? 'app/extend/user');
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
    const path = prompt('Export template destination:', `app/extend/user/code_templates/${format}/template${extension}`);
    if (!path) return;
    setBusy(true); setError('');
    try {
      const result = await client.createExportTemplate([w.activeFilePath], path, format);
      await w.refreshNavigator();
      await w.handleOpenPath(result.file_path);
    } catch (e) { report(e); } finally { setBusy(false); }
  };

  const running = Boolean(job && !terminal.has(job.status));
  const failures = job?.results.filter(result => !result.success).length ?? 0;
  const completedSuccessfully = job?.status === 'COMPLETED' && failures === 0;
  const hasProblems = failures > 0 || job?.status === 'FAILED' || job?.status === 'INTERRUPTED';
  const statusTone = completedSuccessfully ? 'text-emerald-400' : hasProblems ? 'text-amber-400' : 'text-sky-400';
  const progressTone = completedSuccessfully ? 'bg-emerald-500' : hasProblems ? 'bg-amber-500' : 'bg-sky-500';
  const actionClass = 'inline-flex h-7 shrink-0 items-center gap-1.5 rounded-md border border-slate-700/70 bg-slate-900/70 px-2.5 font-medium text-slate-300 transition-colors hover:border-slate-600 hover:bg-slate-800 hover:text-white disabled:cursor-not-allowed disabled:opacity-35';
  const iconClass = 'h-3.5 w-3.5 shrink-0';

  return (
    <section aria-label="Editor commands" className="relative z-30 shrink-0 border-b border-slate-800 bg-slate-950/95 text-xs">
      <div className="flex min-w-0 items-center gap-2 px-3 py-1.5">
        <div role="group" aria-label="File and compilation actions" className="flex min-w-0 flex-1 items-center gap-1.5 overflow-x-auto whitespace-nowrap [scrollbar-width:thin]">
          <button className={actionClass} onClick={w.handleReload} disabled={!w.activeFilePath || busy || w.isDocumentCommandRunning}>
            <RefreshCw className={iconClass} aria-hidden="true" />Reload from disk
          </button>
          <button className={actionClass} onClick={() => void fix()} disabled={!w.activeFilePath || busy || w.isDocumentCommandRunning}>
            <Wrench className={iconClass} aria-hidden="true" />Fix imports
          </button>
          <button className={actionClass} onClick={() => void start('package')} disabled={busy || running}>
            <Package className={iconClass} aria-hidden="true" />Compile package/plugin
          </button>
          <button className={actionClass} onClick={() => void start('all')} disabled={busy || running}>
            <Layers3 className={iconClass} aria-hidden="true" />Compile all
          </button>
          <button className={actionClass} onClick={() => void start('registered')} disabled={busy || running}>
            <RotateCcw className={iconClass} aria-hidden="true" />Reload extensions
          </button>
          <button className={actionClass} disabled={!running || job?.cancellation_requested} onClick={() => {
            if (job) client.cancelCompilation(job.job_id).then(publish).catch(report);
          }}>
            <XCircle className={iconClass} aria-hidden="true" />Cancel compilation
          </button>
        </div>

        <div className="flex shrink-0 items-center gap-2 border-l border-slate-800 pl-2">
          <div className="relative">
            <button
              type="button"
              aria-expanded={showOptions}
              aria-controls="editor-command-options"
              onClick={() => { setShowOptions(value => !value); setShowDetails(false); }}
              className={actionClass}
            >
              <Settings2 className={iconClass} aria-hidden="true" />
              Options
              <ChevronDown className="h-3 w-3" aria-hidden="true" />
            </button>
            {showOptions && (
              <div id="editor-command-options" className="absolute right-0 top-full z-50 mt-2 w-72 space-y-3 rounded-lg border border-slate-700 bg-slate-900 p-3 shadow-2xl">
                <label className="flex items-center justify-between gap-3 text-slate-300">
                  Navigator ownership
                  <select
                    aria-label="Navigator ownership"
                    value={w.ownershipFilter}
                    onChange={e => w.setOwnershipFilter(e.target.value)}
                    className="min-w-24 rounded-md border border-slate-700 bg-slate-950 px-2 py-1 text-slate-100"
                  >
                    <option value="all">All</option>
                    <option value="builtin">Builtin</option>
                    <option value="user">User</option>
                  </select>
                </label>
                <label className="flex items-center justify-between gap-3 text-slate-300">
                  Export template format
                  <select
                    aria-label="Export template format"
                    value={format}
                    onChange={e => setFormat(e.target.value)}
                    className="min-w-28 rounded-md border border-slate-700 bg-slate-950 px-2 py-1 text-slate-100"
                  >
                    {formats.map(item => <option key={item.format_id} value={item.format_id}>{item.name}</option>)}
                  </select>
                </label>
                <button
                  className={actionClass + ' w-full justify-center'}
                  disabled={!w.activeFilePath || busy || !formats.length}
                  onClick={() => void createExport()}
                >
                  <FileCode2 className={iconClass} aria-hidden="true" />Create export template
                </button>
              </div>
            )}
          </div>

          {job && (
            <div className="flex max-w-[410px] min-w-0 items-center gap-2 border-l border-slate-800 pl-2">
              <div role="status" aria-label="Compilation status" className="flex min-w-0 items-center gap-2" title={job.job_id}>
                {completedSuccessfully
                  ? <CheckCircle2 className={'h-4 w-4 shrink-0 ' + statusTone} aria-hidden="true" />
                  : hasProblems
                    ? <AlertTriangle className={'h-4 w-4 shrink-0 ' + statusTone} aria-hidden="true" />
                    : <LoaderCircle className={'h-4 w-4 shrink-0 ' + statusTone + (running ? ' animate-spin' : '')} aria-hidden="true" />}
                <div className="min-w-0 max-w-44">
                  <div className={'truncate font-semibold ' + statusTone}>
                    {job.status}{failures > 0 && <span> · {failures} failed</span>}
                  </div>
                  <div className="truncate text-[10px] text-slate-400">{job.message || 'Compilation job'}</div>
                  <span className="sr-only">{job.job_id}</span>
                </div>
                <div className="flex shrink-0 flex-col items-end gap-1">
                  <span className="font-mono text-[10px] text-slate-300">{Math.round(job.progress)}%</span>
                  <div className="h-1 w-16 overflow-hidden rounded-full bg-slate-800" aria-hidden="true">
                    <div className={'h-full rounded-full transition-all ' + progressTone} style={{ width: Math.max(0, Math.min(100, job.progress)) + '%' }} />
                  </div>
                  <progress aria-label="Compilation progress" className="sr-only" value={job.progress} max={100} />
                </div>
              </div>
              <button
                type="button"
                aria-label="Compilation details"
                aria-expanded={showDetails}
                aria-controls="editor-compilation-details"
                onClick={() => { setShowDetails(value => !value); setShowOptions(false); }}
                className="rounded-md p-1.5 text-slate-400 transition-colors hover:bg-slate-800 hover:text-slate-100"
                title="Show compilation details"
              >
                {showDetails ? <ChevronUp className="h-4 w-4" aria-hidden="true" /> : <ChevronDown className="h-4 w-4" aria-hidden="true" />}
              </button>
            </div>
          )}
        </div>
      </div>

      {showDetails && job && (
        <div id="editor-compilation-details" role="region" aria-label="Compilation details panel" className="absolute right-3 top-full z-50 mt-1 w-[min(34rem,calc(100vw-1.5rem))] rounded-lg border border-slate-700 bg-slate-900 p-3 shadow-2xl">
          <div className="flex items-center justify-between gap-2 border-b border-slate-700/70 pb-2">
            <span className="font-semibold text-slate-100">Compilation details</span>
            <span className={'text-[11px] font-semibold ' + statusTone}>{job.status}</span>
          </div>
          <div className="mt-2 break-all font-mono text-[10px] text-slate-400">Job: {job.job_id}</div>
          <p className="mt-2 text-slate-300">{job.message}</p>
          <p className="mt-2 text-[11px] text-slate-400">
            {job.results.length} file(s) checked · {failures} failed · {Math.round(job.progress)}% complete
          </p>
          <div className="mt-2 max-h-48 space-y-1 overflow-y-auto">
            {job.results.map(result => (
              <button
                key={result.file}
                title={result.file}
                className="flex w-full items-center gap-2 rounded-md px-2 py-1.5 text-left text-[11px] text-slate-300 hover:bg-slate-800"
                onClick={() => { void w.handleOpenPath(result.file); }}
              >
                {result.success ? <CheckCircle2 className="h-3.5 w-3.5 shrink-0 text-emerald-400" aria-hidden="true" /> : <AlertTriangle className="h-3.5 w-3.5 shrink-0 text-amber-400" aria-hidden="true" />}
                <span className="min-w-0 flex-1 truncate">{result.file}</span>
                <span className={result.success ? 'text-emerald-400' : 'text-amber-400'}>{result.success ? 'Passed' : 'Failed'}</span>
              </button>
            ))}
            {job.results.length === 0 && <p className="px-2 py-1 text-slate-500">No file results yet.</p>}
          </div>
        </div>
      )}
      {staleDiagnostics && (
        <div className="border-t border-amber-500/20 bg-amber-950/30 px-3 py-1.5 text-amber-300">
          Diagnostics are from an earlier source version. Compile the current buffer to refresh them.
        </div>
      )}
      {repair && (
        <div aria-label="Import candidates" className="flex flex-wrap items-center gap-3 border-t border-slate-800 px-3 py-2">
          {repair.unresolved.map(choice => (
            <label className="flex items-center gap-2" key={choice.symbol}>
              {choice.symbol}
              <select
                aria-label={'Import ' + choice.symbol}
                value={selections[choice.symbol] ?? ''}
                onChange={e => setSelections(previous => ({ ...previous, [choice.symbol]: e.target.value }))}
                className="rounded-md border border-slate-700 bg-slate-900 px-2 py-1"
              >
                <option value="">{choice.candidates.length ? 'Choose module' : 'No indexed candidate'}</option>
                {choice.candidates.map(candidate => <option key={candidate}>{candidate}</option>)}
              </select>
            </label>
          ))}
          <button className={actionClass} onClick={() => void fix(selections)} disabled={busy}>Apply import selections</button>
        </div>
      )}
      {error && <div role="alert" className="border-t border-rose-500/20 bg-rose-950/30 px-3 py-1.5 text-rose-300">{error}</div>}
    </section>
  );
}
