import type { DataSourceCommand } from '../../Common/dataSourceRibbon';
export { MassImportPopup } from './massImportPopup';
export const massImportCommand = { id: 'file-mass-import', label: 'Import multiple files from a folder', icon: 'mass-import', dialog: 'file-mass-import' } as const satisfies DataSourceCommand;
