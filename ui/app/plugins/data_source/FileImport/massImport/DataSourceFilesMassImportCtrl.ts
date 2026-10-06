import { useCallback, useRef, useState, type ChangeEvent } from 'react';
import { useFileImports } from '../fileImportStore';
import { emptyFileRecord, importedRecord, limits, massSymbol, parseImport, type ImportTask } from '../fileImport';
import type { FileDefinition, FileInstrument } from '../fileSymbols';
import { filesService } from '../DataSourceFilesService';

export function useFilesMassImport(onClose: () => void) {
  const store = useFileImports(); const picker = useRef<HTMLInputElement>(null);
  const [files, setFiles] = useState<File[]>([]); const [folder, setFolder] = useState(''); const [error, setError] = useState(''); const [busy, setBusy] = useState(false);
  const cancelled = useRef(false);
  const close = useCallback(() => { cancelled.current = true; onClose(); }, [onClose]);
  const [timezone, setTimezone] = useState('EETUS'); const [timeframe, setTimeframe] = useState('D1'); const [dateFormat, setDateFormat] = useState('ddMMyyyy');
  const [group, setGroup] = useState(false); const [policy, setPolicy] = useState<'overwrite' | 'skip' | 'create'>('overwrite'); const [postfix, setPostfix] = useState('');
  async function start(instrument: FileInstrument, barType: 'start' | 'end') {
    if (!files.length) throw new Error('Choose a source data folder.');
    if (files.length > limits.files || files.reduce((n, file) => n + file.size, 0) > limits.folder) throw new Error('Folder limit: 500 files / 50 MiB.');
    const existing = filesService.massContext(store.records);
    const tasks: ImportTask[] = []; const seen = new Set<string>(); let skipped = 0;
    setBusy(true); setError('');
    try {
      for (const file of files) {
        if (cancelled.current) return false;
        const stem = file.name.replace(/\.[^.]+$/, '');
        if (seen.has(stem) && policy !== 'create') throw new Error(`Multiple files use the name ${stem}; choose Create new ticker or select an unambiguous folder.`);
        seen.add(stem);
        const symbol = massSymbol(stem, postfix, existing, policy); if (!symbol) { skipped++; continue; }
        const text = await filesService.read(file);
        const parsed = parseImport(text, { name: 'Folder CSV', separator: ',', skipRows: 0, skipColumns: 0, dateFormat, columns: timeframe === 'TICK' ? ['Date & Time', 'Ask', 'Bid', 'Volume'] : ['Date', 'Open', 'High', 'Low', 'Close', 'Volume'] }, timeframe, false);
        const previous = existing.find(row => row.symbol === symbol);
        const base: FileDefinition = { ...emptyFileRecord(symbol, instrument, barType), id: previous?.id ?? `file:${symbol}` };
        tasks.push({ filename: file.name, record: importedRecord(base, parsed, timezone, undefined, true), ignored: parsed.ignored, error: parsed.error });
        existing.push(base);
      }
      if (cancelled.current) return false;
      filesService.start(tasks, timezone, group ? folder || 'Imported symbols' : '', skipped);
      return true;
    } finally { setBusy(false); }
  }
  function chooseFolder(event: ChangeEvent<HTMLInputElement>): void {
      const chosen = Array.from(event.target.files ?? []).sort((a, b) => (a.webkitRelativePath || a.name).localeCompare(b.webkitRelativePath || b.name));
      setFiles(chosen); setFolder(chosen[0]?.webkitRelativePath.split('/')[0] || (chosen.length ? 'Selected files' : '')); setError('');
  }
  return { store, picker, files, folder, error, busy, close, timezone, setTimezone, timeframe, setTimeframe, dateFormat, setDateFormat, group, setGroup, policy, setPolicy, postfix, setPostfix, start, chooseFolder };
}
