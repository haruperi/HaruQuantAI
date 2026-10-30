import { useSQDataAdd, type SQAddCallbacks } from '../../Equity/add/SQEquityDataAddCtrl';
import { futuresService } from '../SQFuturesDataService';
export function useSQFuturesDataAdd(callbacks: SQAddCallbacks) { return useSQDataAdd('futures', callbacks, futuresService); }
