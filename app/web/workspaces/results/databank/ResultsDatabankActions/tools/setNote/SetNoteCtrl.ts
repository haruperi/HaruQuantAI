/** Preserve the latent note action's existing selected-in-bank guard. */
export function requestSetNote(
  selectedCount: number,
  notify: (message: string) => void,
  openDialog: () => void,
): void {
  if (!selectedCount) {
    notify('You have to select at least one strategy');
    return;
  }
  openDialog();
}
