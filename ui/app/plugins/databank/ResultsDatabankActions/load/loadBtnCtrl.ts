/** Dispatch the existing Load action to its simulated popup owner. */
export function openMockLoad(openPopup: () => void): void {
  openPopup();
}
