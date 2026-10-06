import { futuresService } from '../SQFuturesDataService';
/** Attach to the existing host's guarded, generic progress simulation. */
export function runFuturesUpdate(dispatch: (label: string) => void): void { futuresService.update(dispatch); }
