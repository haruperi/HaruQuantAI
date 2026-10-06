/** Open the existing confirmation without adding selection guards. */
export function requestClearAllConfirmation(openConfirm: () => void): void {
  openConfirm();
}

/** Delegate confirmed clearing to the existing host mutation authority. */
export function confirmClearAll(
  strategyIds: string[],
  deleteStrategies: (ids: string[]) => void,
  notify: (message: string) => void,
): void {
  deleteStrategies(strategyIds);
  notify('Databank cleared');
}
