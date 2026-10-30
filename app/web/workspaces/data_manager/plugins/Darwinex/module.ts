import type { DataSourceProvider } from '../Common/dataSourceRibbon';
import { addCommand } from './add/module';
import { importCommand } from './import/module';
import { downloadCommand } from './download/module';
export const darwinexProvider = { id: 'darwinex', label: 'Darwinex Tick Data', commands: [addCommand, importCommand, downloadCommand] } as const satisfies DataSourceProvider;
