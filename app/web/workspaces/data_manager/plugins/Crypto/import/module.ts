import type { DataSourceCommand } from '../../Common/dataSourceRibbon';
export { ImportPopup } from './importPopup';
export const importCommand = { id: 'crypto-download', label: 'Download data for existing symbol', icon: 'download', dialog: 'crypto-download' } as const satisfies DataSourceCommand;
