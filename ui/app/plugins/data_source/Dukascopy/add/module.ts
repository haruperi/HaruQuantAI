import type { DataSourceCommand } from '../../Common/dataSourceRibbon';
export { AddPopup } from './addPopup';
export const addCommand = {
  id: 'dukascopy-add',
  label: 'Add new Dukascopy symbol',
  icon: 'add',
  dialog: 'dukascopy-add',
} as const satisfies DataSourceCommand;
