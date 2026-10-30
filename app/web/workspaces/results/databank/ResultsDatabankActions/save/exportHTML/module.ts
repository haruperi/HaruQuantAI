import { openSimulatedSave } from '../SaveButtonService';

export const label = 'HTML report';
/** Bind the existing option to the generic simulated dialog. */
export function openSave(openDialog: (format: string) => void): void {
  openSimulatedSave(label, openDialog);
}
