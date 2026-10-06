/** Existing menu label and deferred notice only; no strategy transfer. */
export const MOVE_TO_PM_LABEL = 'Move to Portfolio Master';

export function requestMoveToPM(deferred: (label: string) => void): void {
  deferred(`Portfolio: ${MOVE_TO_PM_LABEL}`);
}
