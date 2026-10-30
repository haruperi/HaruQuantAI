import { useCallback, useMemo, useRef, useState, type ChangeEvent } from 'react';
import { useFileImports } from '../fileImportStore';
import { builtInFormats, customFormat, detectFormat, importedRecord, parseImport, previewRows, type ImportFormat } from '../fileImport';
import type { FileDefinition } from '../fileSymbols';
import { filesService } from '../DataSourceFilesService';

export function useFilesImport(target: FileDefinition, onClose: () => void, onStarted: () => void) {
  const store = useFileImports();
  const [format, setFormat] = useState(customFormat);
  const [timezone, setTimezone] = useState(store.timezone);
  const [timeframe, setTimeframe] = useState('auto');
  const [ignore, setIgnore] = useState(false);
  const [text, setText] = useState(''); const [filename, setFilename] = useState('');
  const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  const [page, setPage] = useState<'main' | 'save' | 'delete'>('main'); const [name, setName] = useState('');
  const chosenFile = useRef<File | null>(null);
  const picker = useRef<HTMLInputElement>(null); const generation = useRef(0);
  const formats = [customFormat(), ...builtInFormats, ...store.formats];
  const preview = useMemo(() => { try { const rows = text ? previewRows(text, format) : []; return { rows: rows.slice(0, 50), count: rows.length, error: '' }; } catch (cause) { return { rows: [], count: 0, error: String(cause) }; } }, [text, format]);
  const width = Math.max(format.columns.length, ...preview.rows.map(row => row.length), 0);
  const close = useCallback(() => { if (page !== 'main') { setPage('main'); setError(''); } else { generation.current++; onClose(); } }, [page, onClose]);
  function change(patch: Partial<ImportFormat>) { setFormat(current => ({ ...current, ...patch })); }
  async function start() {
    try {
      if (!filename) throw new Error('Choose a data file.');
      if (chosenFile.current && !/\.(csv|txt|tsv)$/i.test(chosenFile.current.name)) {
        await filesService.start([{filename,file:chosenFile.current, record:{...target,timeframe:timeframe === 'auto' ? 'auto' : timeframe,timestamps:[],unknownBars:0},ignored:0}],timezone,'',0); onStarted(); onClose(); return;
      }
      if (preview.error) throw new Error(preview.error);
      const mapped = { ...format, columns: Array.from({ length: width }, (_, i) => format.columns[i] ?? '') };
      const result = parseImport(text, mapped, timeframe, ignore);
      const record = importedRecord(target, result, timezone, store.records.find(row => row.id === target.id));
      await filesService.start([{ filename, content: text, format: mapped, ignoreErrors: ignore, record, ignored: result.ignored, error: result.error }], timezone, '', 0);
      onStarted(); onClose();
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to import file.'); }
  }
  function saveFormat(asNew: boolean) {
    try { if (asNew || format.name === 'Custom') { setName(''); setPage('save'); setError(''); return; } filesService.saveFormat(format, true); setError(''); }
    catch (cause) { setError(String(cause)); }
  }
  function submit(): void {
    if (page === 'main') start();
    else try { if (page === 'save') { filesService.saveFormat({ ...format, name }); change({ name: name.trim(), predefined: false }); } else { filesService.deleteFormat(format.name); change({ name: 'Custom', predefined: false }); } setPage('main'); setError(''); } catch (cause) { setError(String(cause)); }
  }
  async function chooseFile(event: ChangeEvent<HTMLInputElement>): Promise<void> {
        const file = event.target.files?.[0]; if (!file) return; chosenFile.current=file; if (!/\.(csv|txt|tsv)$/i.test(file.name)) {setFilename(file.name);setText('');setError('');return;} const token = ++generation.current; setBusy(true); setError(''); setFilename(''); setText('');
        try { const content = await filesService.read(file); const detected = detectFormat(content); if (token !== generation.current) return; setText(content); setFilename(file.name); setFormat(detected); }
        catch (cause) { if (token === generation.current) setError(String(cause)); } finally { if (token === generation.current) setBusy(false); }
  }
  return { store, format, setFormat, timezone, setTimezone, timeframe, setTimeframe, ignore, setIgnore, filename, error, setError, busy, page, setPage, name, setName, picker, formats, preview, width, close, change, saveFormat, submit, chooseFile };
}
