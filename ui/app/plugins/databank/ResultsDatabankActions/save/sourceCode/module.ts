import { openSimulatedSave } from '../SaveButtonService';

export const label = 'Source code';

/** Preserve the single flat choice and its generic deferred Save dialog. */
export function openSave(openDialog: (format: string) => void): void {
  openSimulatedSave(label, openDialog);
}
