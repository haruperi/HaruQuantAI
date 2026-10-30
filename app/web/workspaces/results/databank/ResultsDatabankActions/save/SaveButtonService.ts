/** Open the existing generic dialog, preserving the selected label. */
export function openSimulatedSave(format: string, openDialog: (format: string) => void): void {
  openDialog(format);
}

/** Existing deferred completion performs no export or file write. */
export function completeSimulatedSave(format: string, deferred: (label: string) => void): void {
  deferred(`Save: ${format}`);
}
