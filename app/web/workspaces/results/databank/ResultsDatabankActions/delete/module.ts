/** Existing frontend Delete dispatch; host retains mutation authority. */
export function requestDeleteConfirmation(
  selectedIds: readonly string[],
  notify: (message: string) => void,
  openConfirm: () => void,
): void {
  if (!selectedIds.length) {
    notify('You have to select at least one strategy to delete');
    return;
  }
  openConfirm();
}

/** Dispatch confirmed removal without taking ownership of persistence. */
export function confirmDelete(
  selectedIds: string[],
  deleteStrategies: (ids: string[]) => void,
): void {
  deleteStrategies(selectedIds);
}
