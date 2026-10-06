export { runFuturesUpdate } from './SQFuturesDataUpdateCtrl';
export const futuresUpdateCommand = { id: 'sq-futures-update', label: 'Update Futures datasets', icon: 'refresh', action: 'sq-futures-update' } as const;
