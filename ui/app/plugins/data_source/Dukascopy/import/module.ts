import type { DataSourceCommand } from '../../Common/dataSourceRibbon';
export { ImportPopup } from './importPopup';
export const importCommand = {
  id: 'dukascopy-download',
  label: 'Download data for existing symbol',
  icon: 'download',
  dialog: 'dukascopy-download',
} as const satisfies DataSourceCommand;
