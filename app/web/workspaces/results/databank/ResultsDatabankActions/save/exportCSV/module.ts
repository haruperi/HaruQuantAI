import { openSimulatedSave } from '../SaveButtonService';

export const label = 'Export databank contents';
/** Bind the existing option to the generic simulated dialog. */
export function openSave(openDialog: (format: string) => void): void {
  openSimulatedSave(label, openDialog);
}
