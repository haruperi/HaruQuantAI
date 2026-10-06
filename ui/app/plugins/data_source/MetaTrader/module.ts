import type { DataSourceProvider } from '../Common/dataSourceRibbon';
import { importCommand } from './import/module';
export const mt5Provider = { id: 'mt5', label: 'MT5 import', commands: [importCommand] } as const satisfies DataSourceProvider;
