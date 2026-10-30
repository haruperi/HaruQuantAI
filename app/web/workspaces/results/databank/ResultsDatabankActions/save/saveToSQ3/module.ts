import { openSimulatedSave } from '../SaveButtonService';

export const label = 'Save stats in SQ3 format';
/** Bind the existing option to the generic simulated dialog. */
export function openSave(openDialog: (format: string) => void): void {
  openSimulatedSave(label, openDialog);
}
