import type { DataSourceProvider } from '../Common/dataSourceRibbon';
import { addCommand } from './add/module';
import { importCommand } from './import/module';
export const cryptoProvider = { id: 'crypto', label: 'Crypto', commands: [addCommand, importCommand] } as const satisfies DataSourceProvider;
