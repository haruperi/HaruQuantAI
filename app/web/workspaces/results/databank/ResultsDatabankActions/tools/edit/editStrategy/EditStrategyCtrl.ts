/** Existing mock edit action remains deferred. */
export function requestEditStrategy(deferred: (label: string) => void): void {
  deferred('Tools: Edit:Strategy');
}
