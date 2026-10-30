import { equityService } from '../SQEquityDataService';
/** Attach to the existing host's guarded, generic progress simulation. */
export function runEquityUpdate(dispatch: (label: string) => void): void { equityService.update(dispatch); }
