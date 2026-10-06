/** Existing menu label and deferred notice only; no strategy transfer. */
export const MOVE_TO_PC_LABEL = 'Move to Portfolio Composer';

export function requestMoveToPC(deferred: (label: string) => void): void {
  deferred(`Portfolio: ${MOVE_TO_PC_LABEL}`);
}
