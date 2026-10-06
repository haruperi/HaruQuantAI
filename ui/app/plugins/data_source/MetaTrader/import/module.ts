import type { DataSourceCommand } from '../../Common/dataSourceRibbon';
export { ImportPopup } from './importPopup';
export const importCommand = { id: 'mt5-import', label: 'Import data', icon: 'terminal-import', dialog: 'mt5-import' } as const satisfies DataSourceCommand;
