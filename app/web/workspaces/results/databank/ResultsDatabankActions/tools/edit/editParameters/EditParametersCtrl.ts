/** Existing mock edit action remains deferred. */
export function requestEditParameters(deferred: (label: string) => void): void {
  deferred('Tools: Edit:Parameters');
}
