import { useRef, useState, type ChangeEvent } from 'react';
import type { DarwinexManifest } from '../darwinex';
import { useDarwinex } from '../darwinexStore';
import { darwinexService } from '../DarwinexService';

export function useImportPopup(onClose: () => void, onStarted: () => void) {
  const store = useDarwinex(); const picker = useRef<HTMLInputElement>(null);
  const [manifest, setManifest] = useState<DarwinexManifest | null>(null), [selected, setSelected] = useState<string[]>([]), [postfix, setPostfix] = useState(store.postfix), [error, setError] = useState('');
  const symbols = manifest?.symbols ?? [];
  function start() { try { if (!manifest) throw new Error('Select Darwinex data folder.'); if (selected.some(symbol => !symbols.includes(symbol))) throw new Error('Select symbols from this folder.'); const context = darwinexService.context(); const definitions = darwinexService.definitions(selected, postfix, context.existing, undefined, {}, false); darwinexService.start('import', definitions, context.active, manifest.folder, postfix); onStarted(); onClose(); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Unable to import.'); } }
  const chooseFolder = (event: ChangeEvent<HTMLInputElement>) => { if (!event.target.files?.length) return; setSelected([]); setManifest(null); setError(''); try { setManifest(darwinexService.discover(Array.from(event.target.files, file => file.webkitRelativePath))); } catch (cause) { setError(cause instanceof Error ? cause.message : 'Cannot load symbols.'); } event.target.value = ''; };
  return { store, picker, manifest, selected, setSelected, postfix, setPostfix, error, setError, symbols, start, chooseFolder };
}
