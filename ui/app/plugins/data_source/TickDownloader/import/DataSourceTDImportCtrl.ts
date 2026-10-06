import { useEffect, useRef, useState, type ChangeEvent } from 'react';
import type { TDManifest } from '../tickDownloader';
import { useTickDownloader } from '../../Common/dataManagerStore';
import { tdService } from '../DataSourceTDService';
export interface TDImportCallbacks { onClose: () => void; onStarted: () => void }
export function useDataSourceTDImport({ onClose, onStarted }: TDImportCallbacks) {
  const saved = useTickDownloader();
  const [manifest, setManifest] = useState<TDManifest | null>(null);
  const [postfix, setPostfix] = useState(saved.postfix);
  const [selected, setSelected] = useState<string[]>([]);
  const [error, setError] = useState('');
  const picker = useRef<HTMLInputElement>(null);
  const root = useRef<HTMLDivElement>(null);
  const allCheck = useRef<HTMLInputElement>(null);
  const symbols = manifest?.symbols ?? [];
  const all = symbols.length > 0 && selected.length === symbols.length;
  useEffect(() => { if (allCheck.current) allCheck.current.indeterminate = selected.length > 0 && !all; }, [all, selected]);
  useEffect(() => { const previous = document.activeElement as HTMLElement | null; root.current?.querySelector<HTMLButtonElement>('button')?.focus(); return () => previous?.focus(); }, []);
  function start() {
    try {
      if (!manifest) throw new Error('Select a TickDownloader installation folder.');
      tdService.importData({ folder: manifest.folder, symbols: selected, postfix }, symbols);
      onStarted(); onClose();
    } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to import data.'); }
  }
  function selectFolder(event: ChangeEvent<HTMLInputElement>): void {
            if (!event.target.files?.length) return;
            setError(''); setSelected([]); setManifest(null);
            try { setManifest(tdService.loadAvailableSymbols(Array.from(event.target.files, file => file.webkitRelativePath))); }
            catch (cause) { setError(cause instanceof Error ? cause.message : 'Cannot load available symbols.'); }
            event.target.value = '';
  }
  return { saved, manifest, postfix, selected, error, picker, root, allCheck, symbols, all, start, selectFolder, setSelected, setPostfix, setError };
}
