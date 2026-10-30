export { runEquityUpdate } from './SQEquityDataUpdateCtrl';
export const equityUpdateCommand = { id: 'sq-equity-update', label: 'Update Equity datasets', icon: 'refresh', action: 'sq-equity-update' } as const;
