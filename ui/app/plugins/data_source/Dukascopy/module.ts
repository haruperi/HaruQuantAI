import type { DataSourceProvider } from '../Common/dataSourceRibbon';
import { addCommand } from './add/module';
import { importCommand } from './import/module';
import { disclaimerCommand } from './disclaimer/module';

export const dukascopyProvider = {
  id: 'dukascopy',
  label: 'Dukascopy data',
  commands: [addCommand, importCommand, disclaimerCommand],
} as const satisfies DataSourceProvider;
