import type { DataSourceProvider } from '../Common/dataSourceRibbon';
import { addCommand } from './add/module';
import { importCommand } from './import/module';
import { massImportCommand } from './massImport/module';
export const filesProvider = { id: 'file-import', label: 'File import', commands: [addCommand, importCommand, massImportCommand] } as const satisfies DataSourceProvider;
