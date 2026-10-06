import type { DataSourceCommand } from '../../Common/dataSourceRibbon';
export { AddPopup } from './addPopup';
export const addCommand = { id: 'file-add', label: 'Add symbol', icon: 'add', dialog: 'file-add' } as const satisfies DataSourceCommand;
