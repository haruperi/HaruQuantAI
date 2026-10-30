import type { DataSourceCommand } from '../../Common/dataSourceRibbon';
export { AddPopup } from './addPopup';
export const addCommand = { id: 'darwinex-add', label: 'Add Darwinex data', icon: 'add', dialog: 'darwinex-add' } as const satisfies DataSourceCommand;
