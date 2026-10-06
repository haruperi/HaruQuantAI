import type { DataSourceCommand } from '../../Common/dataSourceRibbon';
export { ImportPopup } from './importPopup';
export const importCommand = { id: 'darwinex-import', label: 'Import data from a Darwinex folder', icon: 'folder-import', dialog: 'darwinex-import' } as const satisfies DataSourceCommand;
