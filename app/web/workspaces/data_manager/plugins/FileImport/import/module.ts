import type { DataSourceCommand } from '../../Common/dataSourceRibbon';
export { ImportPopup } from './importPopup';
export const importCommand = { id: 'file-import', label: 'Import one data file', icon: 'file-import', dialog: 'file-import' } as const satisfies DataSourceCommand;
