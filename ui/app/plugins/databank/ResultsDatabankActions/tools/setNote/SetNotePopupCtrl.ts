import { useState } from 'react';
import type { Strategy } from '../../../../../host/types';

/** Existing draft remains local to the dialog mount. */
export function useSetNoteDraft(currentNote: string) {
  const [note, setNote] = useState(currentNote);
  return { note, setNote };
}

export function applySetNote(
  selectedInBank: readonly Strategy[],
  note: string,
  renameStrategy: (id: string, name: string, note: string) => void,
  notify: (message: string) => void,
): void {
  for (const strategy of selectedInBank) renameStrategy(strategy.id, strategy.name, note);
  notify(`Note set on ${selectedInBank.length} strateg${selectedInBank.length === 1 ? 'y' : 'ies'}`);
}
